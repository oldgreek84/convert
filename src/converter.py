from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from src.config import ConverterStatus
from src.config import JobConfig as Config
from src.event_emitter import EventEmitter
from src.exceptions import create_error_context

if TYPE_CHECKING:
    from collections.abc import Callable

    from interfaces.worker_interface import Worker
    from src.conversion_service import ConversionService


class Converter:
    """Thin orchestration shell for e-book conversion.

    Manages status, events, worker wrapping, and error handling.
    Delegates all business logic to ConversionService.
    """

    def __init__(
        self,
        service: ConversionService,
        worker: Worker | None = None,
        debug: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        self.service = service
        self.worker = worker
        self.debug = debug
        self.config: Config | None = None
        self.events = EventEmitter()

        self.service.set_on_message(lambda msg: self.events.emit("message", msg))
        self._set_status(ConverterStatus.READY)

    @property
    def status(self) -> ConverterStatus:
        return self._status

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

    def setup_converter_executor(self) -> Callable:
        """Create the conversion executor, optionally wrapped with worker."""
        executor = self._convert
        if self.worker:
            executor = partial(self.worker.execute, self._convert)
            self.worker.set_error_handler(self.error_handler)
        return executor

    def _convert(self) -> None:
        result = self.service.execute(self.config)
        self.events.emit("result", result)
        self._set_status(ConverterStatus.COMPLETED)

    def error_handler(self, error: Exception) -> None:
        """Set status to FAILED and emit error event (with debug context if enabled)."""
        error_message = str(error)
        if self.debug:
            context = create_error_context(error=error)
            error_message = f"{error} | Context: {context}"

        self._set_status(ConverterStatus.FAILED)
        self.events.emit("error", f"Converter got an error: {error_message}")
