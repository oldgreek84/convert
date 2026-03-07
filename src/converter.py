from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from src.config import ConverterStatus
from src.config import JobConfig as Config
from src.event_emitter import EventEmitter
from src.exceptions import ConverterError, create_error_context
from src.validator import (
    ConfigValidator,
    ConversionDirectionValidator,
    FilePathValidator,
    Validator,
)

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

    Coordinates Processor, Saver, and Worker to execute conversions.
    Has no UI knowledge — emits events via EventEmitter that the
    presentation layer (AppPresenter) subscribes to and forwards
    to the View.
    """

    def __init__(
        self,
        processor: JobProcessor,
        saver: SaverProtocol,
        validator: Validator | None = None,
        worker: Worker | None = None,
        debug: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        self.processor = processor
        self.saver = saver
        self.worker = worker
        self.config: Config | None = None
        self.debug = debug
        self.validator = validator or Validator()

        self.events = EventEmitter()
        self._set_status(ConverterStatus.READY)

    @property
    def status(self) -> ConverterStatus:
        return self._status

    # TODO(SRP-2): Move set_status() to StatusManager class.
    def _set_status(self, status: ConverterStatus) -> None:
        """Set converter status and emit status event."""
        self._status = status
        self.events.emit("status", self.status)

    def convert(self, config: Config) -> None:
        """Run the conversion process for the given configuration."""
        self._set_status(ConverterStatus.PROCESSING)
        self.config = config

        run_process = self.setup_converter_executor()
        run_process()

    # TODO(OCP-1): Replace with injectable ExecutionStrategy.
    def setup_converter_executor(self) -> Callable:
        """Create the conversion executor, optionally wrapped with worker."""
        executor = self._convert
        if self.worker:
            executor = partial(self.worker.execute, self._convert)
            self.worker.set_error_handler(self.error_handler)
        return executor

    def _convert(self) -> None:
        """Execute the internal conversion workflow."""
        assert self.config is not None  # noqa: S101

        self.validator.add(ConfigValidator(self.config))
        self.validator.add(
            ConversionDirectionValidator(
                fmt_from=self.config.fmt_from.name,
                fmt_to=self.config.fmt_to.name,
            )
        )
        self.validator.validate()

        job_id = self._send_job()

        result_file_name, source_data = self.get_result(job_id)

        if not result_file_name:
            raise ConverterError("There is not result.")

        self.save(result_file_name, source_data)
        self._set_status(ConverterStatus.COMPLETED)

    # TODO(OCP-2): Use injected MessageFormatter for "Job ID: {job_id}" message.
    def _send_job(self) -> int:
        """Validate file path, send conversion job to processor, return job ID."""
        path_to_file = self.config.path_to_file

        self.validator.add(FilePathValidator(path_to_file))
        self.validator.validate()

        options = self.config.get_config()
        job_id = self.processor.send_job(path_to_file, options)

        self.events.emit("message", f"Job ID: {job_id}")

        return job_id

    # TODO(OCP-2): Use injected MessageFormatter for "{message} [{status}]" format.
    def get_result(self, job_id: int) -> tuple[str, io.BytesIO]:
        """Poll processor for job status, then retrieve the final result."""
        processor_info = self.processor.get_job_status(job_id)
        for message in processor_info:
            self.events.emit("message", f"{message} [{ConverterStatus.PROCESSING}]")

        return self.processor.get_job_result(job_id)

    def error_handler(self, error: Exception) -> None:
        """Set status to FAILED and emit error event (with debug context if enabled)."""
        error_message = str(error)
        if self.debug:
            context = create_error_context(error=error)
            error_message = f"{error} | Context: {context}"

        self._set_status(ConverterStatus.FAILED)
        self.events.emit("error", f"Converter got an error: {error_message}")

    def save(self, source_name: str, source_data: io.BytesIO) -> str | Path | PosixPath:
        """Save conversion result and emit result event."""
        self.saver.setup(
            source_name=source_name,
            source_data=source_data,
            destination_path=self.config.path_to_save,
        )
        result = self.saver.save()
        self.events.emit("result", result)
        return result
