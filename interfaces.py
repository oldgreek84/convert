from __future__ import annotations

from typing import Any, Callable, Protocol, TextIO, Union
from pathlib import Path
from config import JobConfig as Config


class UIProtocol(Protocol):
    def run(self, converter) -> None:
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


class JobProcessorProtocol(Protocol):
    def is_completed(self) -> bool:
        """return True if job is completed"""

    def send_job_data(self, path_to_file: str, file_data: TextIO, options: dict) -> str:
        """send job data for processing. Return job ID"""

    def get_job_status(self, job_id: str) -> Any:
        """return job status by job ID"""

    def get_job_result(self, job_id: str) -> Union[Path, str]:
        """get job data by job ID after processing and return it"""

    def save_file(self, path_to_result: str, path_to_save: Union[Path, str]) -> Path:
        """save job result after processing and return path to file"""


class WorkerProtocol(Protocol):
    def is_completed(self):
        raise NotImplementedError

    def get_result(self):
        raise NotImplementedError

    def execute(self, func, *args, **kwargs):
        raise NotImplementedError

    def set_error_handler(self, handler: Callable) -> None:
        raise NotImplementedError
