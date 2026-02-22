from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from src.config import ConverterStatus
from src.config import JobConfig as Config
from src.event_emitter import EventEmitter
from src.exceptions import ConverterError, create_error_context
from src.validator import ConfigValidator, FilePathValidator, Validator

if TYPE_CHECKING:
    import io
    from collections.abc import Callable
    from pathlib import Path, PosixPath

    from interfaces.processor_interface import JobProcessor
    from interfaces.saver_interface import SaverProtocol
    from interfaces.worker_interface import Worker


# TODO(SRP-2): Extract status management to a separate StatusManager class.

# TODO(OCP-1): Make execution strategy injectable instead of hardcoded.

# TODO(OCP-2): Make message formatting configurable/injectable.


class Converter:
    """Business layer orchestrator for e-book conversion operations.

    Part of Two-Layer Orchestration Pattern:
    - AppPresenter: Presentation layer - coordinates View and Converter
    - Converter: Business layer - coordinates Processor, Saver, Worker

    Architecture:
        ┌─────────────────────────────────────────────────────────┐
        │                    AppPresenter                         │
        │              (Presentation Layer Orchestrator)          │
        ├─────────────────────────────────────────────────────────┤
        │                      Converter                          │ <-- You are here
        │               (Business Layer Orchestrator)             │
        │         Coordinates: Processor -> Saver -> Worker       │
        └─────────────────────────────────────────────────────────┘

    The Converter has no UI knowledge. It emits events via EventEmitter
    that the presentation layer (AppPresenter) subscribes to and forwards
    to the View. This enables reuse across different UIs (CLI, GUI, API).

    Conversion Workflow:
        1. Validates configuration and file paths
        2. Sends conversion jobs to processor
        3. Monitors processing status (emits 'message' events)
        4. Retrieves and saves conversion results
        5. Emits 'status', 'error', 'result' events

    Attributes:
        processor: Handles actual file conversion (local, Docker, remote).
        saver: Handles saving converted files (local filesystem, cloud).
        worker: Optional async execution wrapper.
        config: Current job configuration.
        status: Current conversion status.
        events: EventEmitter for decoupled notifications.

    Example:
        >>> converter = Converter(
        ...     processor=LocalProcessor(),
        ...     saver=LocalFileSaver()
        ... )
        >>> converter.events.on("status", print)
        >>> converter.convert(job_config)
    """

    def __init__(
        self,
        processor: JobProcessor,
        saver: SaverProtocol,
        validator: Validator | None = None,
        worker: Worker | None = None,
        debug: bool = False,
    ) -> None:
        self.processor = processor
        self.saver = saver
        self.worker = worker
        self.config: Config | None = None
        self.debug = debug
        self.validator = validator or Validator()

        self.events = EventEmitter()
        self.set_status(ConverterStatus.READY)

    # TODO(SRP-2): Move get_status() to StatusManager class.
    def get_status(self) -> str:
        """Return current conversion status.

        Returns:
            Current status string from ConverterStatus enum.
        """
        return self.status

    # TODO(SRP-2): Move set_status() to StatusManager class.
    def set_status(self, status: ConverterStatus) -> None:
        """Set converter status and emit status event.

        Args:
            status: New status to set from ConverterStatus enum.
        """
        self.status = status
        self.events.emit("status", self.status)

    def convert(self, config: Config) -> None:
        """Run the conversion process for the given configuration.

        Args:
            config: Job configuration containing file path and conversion options.
        """
        self.set_status(ConverterStatus.PROCESSING)
        self.config = config

        run_process = self.setup_converter_executor()
        run_process()

    # TODO(OCP-1): Replace with injectable ExecutionStrategy.
    def setup_converter_executor(self) -> Callable:
        """Create and return the conversion executor.

        Returns:
            Callable that executes the conversion flow, optionally wrapped
            with worker for async execution.
        """
        executor = self._convert
        if self.worker:
            executor = partial(self.worker.execute, self._convert)
            self.worker.set_error_handler(self.error_handler)
        return executor

    def _convert(self) -> None:
        """Execute the internal conversion workflow.

        Validates config, sends job to processor, retrieves result,
        and saves the converted file.

        Raises:
            ConverterError: If config is invalid or file path doesn't exist.
        """
        self.validator.add(ConfigValidator(self.config))
        self.validator.validate()

        assert self.config is not None  # noqa: S101

        job_id = self._send_job()

        result_file_name, source_data = self.get_result(job_id)

        if not result_file_name:
            raise ConverterError('There is not result.')

        self.save(result_file_name, source_data)
        self.set_status(ConverterStatus.COMPLETED)

    # TODO(OCP-2): Use injected MessageFormatter for "Job ID: {job_id}" message.
    def _send_job(self) -> int:
        """Send conversion job to processor.

        Validates file path, prepares options, and sends job to processor.
        Emits message event with job ID.

        Returns:
            Job ID from processor.

        Raises:
            ConverterError: If file path is invalid.
        """
        path_to_file = self.config.path_to_file

        self.validator.add(FilePathValidator(path_to_file))
        self.validator.validate()

        options = self.config.get_config()
        job_id = self.processor.send_job(path_to_file, options)

        self.events.emit("message", f"Job ID: {job_id}")

        return job_id

    # TODO(OCP-2): Use injected MessageFormatter for "{message} [{status}]" format.
    def get_result(self, job_id: int) -> tuple[str, io.BytesIO]:
        """Get conversion result from processor.

        Polls processor for job status, emitting message events for each
        status update, then retrieves the final result.

        Args:
            job_id: Job identifier returned from send_job().

        Returns:
            Tuple of (result filename, bytes data stream).
        """
        processor_info = self.processor.get_job_status(job_id)
        for message in processor_info:
            self.events.emit("message", f"{message} [{ConverterStatus.PROCESSING}]")

        return self.processor.get_job_result(job_id)

    def error_handler(self, error: Exception) -> None:
        """Handle conversion errors.

        Formats error message (with debug context if DEBUG=1), sets status
        to FAILED, and emits error event.

        Args:
            error: Exception that occurred during conversion.
        """
        error_message = str(error)
        if self.debug:
            context = create_error_context(error=error)
            error_message = f"{error} | Context: {context}"

        self.set_status(ConverterStatus.FAILED)
        self.events.emit("error", f"Converter got an error: {error_message}")

    def save(self, source_name: str, source_data: io.BytesIO) -> str | Path | PosixPath:
        """Save conversion result using configured saver.

        Sets up the saver with source data and destination path from config,
        then saves the file and emits result event.

        Args:
            source_name: Filename for the converted file.
            source_data: Bytes stream containing the converted data.

        Returns:
            Path to the saved file.
        """
        self.saver.setup(
            source_name=source_name,
            source_data=source_data,
            destination_path=self.config.path_to_save,
        )
        result = self.saver.save()
        self.events.emit("result", result)
        return result
