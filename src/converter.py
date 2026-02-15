from __future__ import annotations

import os
from functools import partial
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING

from src.config import ConverterStatus
from src.config import JobConfig as Config
from src.event_emitter import EventEmitter
from src.exceptions import ConverterError, create_error_context

if TYPE_CHECKING:
    import io
    from collections.abc import Callable

    from interfaces.processor_interface import JobProcessor
    from interfaces.saver_interface import SaverProtocol
    from interfaces.worker_interface import Worker
    from src.config import Target


# TODO(SRP-1): Extract validation logic to a separate Validator class.
#     Current: validate_config() and validate_path() are validation responsibilities
#     mixed with orchestration. Create a ConfigValidator or ConversionValidator
#     that can be injected, allowing different validation strategies.
#     Files to create: src/validators/config_validator.py

# TODO(SRP-2): Extract status management to a separate StatusManager class.
#     Current: set_status(), get_status() and status attribute management is
#     a separate concern from conversion orchestration. StatusManager could
#     handle state transitions and emit events.
#     Files to create: src/status_manager.py

# TODO(SRP-3): Extract error handling/formatting to a separate ErrorHandler class.
#     Current: error_handler() contains error formatting logic with DEBUG check.
#     This should be injectable to support different error formatting strategies
#     (verbose, minimal, structured JSON, etc.).
#     Files to create: src/error_handler.py

# TODO(OCP-1): Make execution strategy injectable instead of hardcoded.
#     Current: setup_converter_executor() has hardcoded logic for worker wrapping.
#     Create an ExecutionStrategy interface with SyncStrategy and AsyncStrategy
#     implementations. Converter should accept strategy via constructor.
#     Files to create: interfaces/execution_strategy.py, src/strategies/

# TODO(OCP-2): Make message formatting configurable/injectable.
#     Current: Hardcoded message formats like "Job ID: {job_id}" and
#     "{message} [{status}]" in send_job() and get_result(). Create a
#     MessageFormatter protocol that can be injected for customization.
#     Files to create: interfaces/message_formatter.py

# TODO(DIP-1): Inject debug mode via config instead of using os.getenv().
#     Current: error_handler() directly calls os.getenv("DEBUG"). This is a
#     concrete dependency on environment. Debug mode should be passed via
#     a DebugConfig or as constructor parameter.
#     Modify: __init__ to accept debug: bool = False parameter

# TODO(DIP-2): Inject file system operations for better testability.
#     Current: validate_path() uses Path(path_to_file).is_file() directly.
#     Create a FileSystem protocol with exists(), is_file() methods that
#     can be mocked in tests without touching real filesystem.
#     Files to create: interfaces/filesystem.py

# TODO(LSP-1): Ensure config is never None after convert() is called.
#     Current: self.config can be None, causing type checker warnings.
#     Consider using a state pattern or ensuring config is always set
#     before operations that need it (validate in convert() entry point).


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
        worker: Worker | None = None,
    ) -> None:
        self.processor = processor
        self.saver = saver
        self.worker = worker
        self.config: Config | None = None

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
        self.set_config(config)

        run_process = self.setup_converter_executor()
        run_process()

    def set_config(self, config: Config) -> None:
        """Set converter configuration.

        Args:
            config: Job configuration to use for conversion.
        """
        self.config = config

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
        self.validate_config()

        job_id = self.send_job()

        result_file_name, source_data = self.get_result(job_id)

        if result_file_name:
            self.save(result_file_name, source_data)

        self.set_status(ConverterStatus.COMPLETED)

    def prepare_params(self, options) -> Target:
        """Prepare conversion parameters using processor.

        Args:
            options: Raw options dictionary to prepare.

        Returns:
            Target object with prepared conversion parameters.
        """
        return self.processor.prepare_params(options)

    # TODO(SRP-1): Move validate_config() to injected ConfigValidator class.
    def validate_config(self) -> None:
        """Validate that converter configuration is set and valid.

        Raises:
            ConverterError: If config is not set or invalid.
        """
        if not self.config or not self.config.get_config():
            error_msg = "Converter`s config was not set"
            raise ConverterError(error_msg)

    # TODO(SRP-1): Move validate_path() to ConfigValidator class.
    # TODO(DIP-2): Use injected FileSystem protocol instead of Path directly.
    @staticmethod
    def validate_path(path_to_file: str) -> bool:
        """Validate that file path exists and is a file.

        Args:
            path_to_file: Path to the file to validate.

        Returns:
            True if path is valid.

        Raises:
            ConverterError: If path does not exist or is not a file.
        """
        if not Path(path_to_file).is_file():
            msg = f"Invalid file path: {path_to_file}"
            raise ConverterError(msg)
        return True

    def get_file_path(self) -> str:
        """Get the source file path from configuration.

        Returns:
            Path to the file to be converted.
        """
        return self.config.path_to_file

    def get_job_options(self) -> dict:
        """Get conversion options from configuration.

        Returns:
            Dictionary with conversion parameters.
        """
        return self.config.get_config()

    # TODO(OCP-2): Use injected MessageFormatter for "Job ID: {job_id}" message.
    def send_job(self) -> int:
        """Send conversion job to processor.

        Validates file path, prepares options, and sends job to processor.
        Emits message event with job ID.

        Returns:
            Job ID from processor.

        Raises:
            ConverterError: If file path is invalid.
        """
        path_to_file = self.get_file_path()
        self.validate_path(path_to_file)
        options = self.get_job_options()

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

    # TODO(SRP-3): Extract to injectable ErrorHandler class.
    # TODO(DIP-1): Replace os.getenv("DEBUG") with injected debug config.
    def error_handler(self, error: Exception) -> None:
        """Handle conversion errors.

        Formats error message (with debug context if DEBUG=1), sets status
        to FAILED, and emits error event.

        Args:
            error: Exception that occurred during conversion.
        """
        error_message = str(error)
        if os.getenv("DEBUG", "0") == "1":
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
