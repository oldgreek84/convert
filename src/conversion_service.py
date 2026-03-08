import io
from collections.abc import Callable
from pathlib import Path

from interfaces.processor_interface import JobProcessor
from interfaces.saver_interface import SaverProtocol
from src.config import JobConfig as Config
from src.exceptions import ConverterError
from src.validator import (
    ConfigValidator,
    ConversionDirectionValidator,
    FilePathValidator,
    Validator,
)


class ConversionService:
    """Pure business logic for e-book conversion.

    Coordinates validation, job submission, polling, and saving.
    Has no knowledge of events, status, or workers.
    """

    def __init__(
        self,
        processor: JobProcessor,
        saver: SaverProtocol,
        validator: Validator,
        on_message: Callable[[str], None] | None = None,
    ) -> None:
        self.processor = processor
        self.saver = saver
        self.validator = validator
        self._on_message = on_message or (lambda _: None)

    def set_on_message(self, callback: Callable[[str], None]) -> None:
        self._on_message = callback

    def execute(self, config: Config) -> Path:
        """Run the full conversion workflow: validate, send, poll, save."""
        self.validator.add(ConfigValidator(config))
        self.validator.add(
            ConversionDirectionValidator(
                fmt_from=config.fmt_from.name,
                fmt_to=config.fmt_to.name,
            )
        )
        self.validator.validate()

        job_id = self.send_job(config)
        self._on_message(f"Job ID: {job_id}")

        result_file_name, source_data = self.get_result(job_id)

        if not result_file_name:
            msg = "There is not result."
            raise ConverterError(msg)

        return self.save(result_file_name, source_data, config.path_to_save)

    def send_job(self, config: Config) -> int:
        """Validate file path and send conversion job to processor."""
        path_to_file = config.path_to_file

        self.validator.add(FilePathValidator(path_to_file))
        self.validator.validate()

        options = config.get_config()
        return self.processor.send_job(path_to_file, options)

    def get_result(self, job_id: int) -> tuple[str, io.BytesIO]:
        """Poll processor for job status, then retrieve result."""
        processor_info = self.processor.get_job_status(job_id)
        for message in processor_info:
            self._on_message(message)

        return self.processor.get_job_result(job_id)

    def save(
        self, source_name: str, source_data: io.BytesIO, path_to_save: str | Path
    ) -> str | Path:
        """Configure saver and save the converted file."""
        self.saver.setup(
            source_name=source_name,
            source_data=source_data,
            destination_path=path_to_save,
        )

        return self.saver.save()

