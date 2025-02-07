from __future__ import annotations

from typing import Protocol, Union, TYPE_CHECKING

from config import JobConfig as Config

if TYPE_CHECKING:
    from pathlib import Path
    from converter import Converter


class UIProtocol(Protocol):
    def run(self, converter: Converter) -> None:
        raise NotImplementedError

    def setup(self) -> Config | bool:
        raise NotImplementedError

    def convert(self, config: Config) -> None:
        raise NotImplementedError

    def display_job_status(self, status: str) -> None:
        raise NotImplementedError

    def display_job_result(self, result: Union[Path, str]) -> None:
        raise NotImplementedError

    def display_job_id(self, job_id: str) -> None:
        raise NotImplementedError

    def display_common_info(self, message: str, status: str | None = None) -> None:
        raise NotImplementedError

    def display_error(self, error: str) -> None:
        raise NotImplementedError
