from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from src.exceptions import ConverterError

if TYPE_CHECKING:
    from src.config import JobConfig


class FileChecker(Protocol):
    def is_file(self, file_path: str) -> bool: ...


class ValidatorStep(Protocol):
    def validate(self) -> None: ...


class DefaultFileChecker:
    def is_file(self, file_path: str) -> bool:
        return Path(file_path).is_file()


class FilePathValidator:
    def __init__(self, file_path: str, file_checker: FileChecker | None = None) -> None:
        self.file_path = file_path
        self.file_checker = file_checker or DefaultFileChecker()

    def validate(self) -> None:
        if not self.file_checker.is_file(self.file_path):
            msg = f"Invalid file path: {self.file_path}"
            raise ConverterError(msg)


class ConfigValidator:
    def __init__(self, config: JobConfig | None) -> None:
        self.config = config

    def validate(self) -> None:
        if not self.config or not self.config.get_config():
            error_msg = "Converter`s config was not set"
            raise ConverterError(error_msg)


class Validator:
    def __init__(self) -> None:
        self._validators: list[ValidatorStep] = []

    def validate(self) -> None:
        for validator in self._validators:
            validator.validate()
        self._validators.clear()

    def add(self, validator: ValidatorStep) -> None:
        self._validators.append(validator)
