from __future__ import annotations

from typing import Protocol, Union, TYPE_CHECKING

from config import JobConfig as Config

if TYPE_CHECKING:
    from pathlib import Path
    from converter import Converter


class UIProtocol(Protocol):
    def run(self, converter: Converter) -> None:
        """Run the UI to show common info."""
        raise NotImplementedError

    def setup(self) -> Config | bool:
        """Setup converter by different params."""
        raise NotImplementedError

    def convert(self, config: Config) -> None:
        """Run convert processing via the UI."""
        raise NotImplementedError

    def display_job_status(self, status: str) -> None:
        """Show status of processing on the UI."""
        raise NotImplementedError

    def display_job_result(self, result: Union[Path, str]) -> None:
        """Show result of processing on the UI."""
        raise NotImplementedError

    def display_job_id(self, job_id: str) -> None:
        """Show the unique job id on the UI."""
        raise NotImplementedError

    def display_common_info(self, message: str, status: str | None = None) -> None:
        """Show common info on the UI."""
        raise NotImplementedError

    def display_error(self, error: str) -> None:
        """Show error messages on the UI."""
        raise NotImplementedError
