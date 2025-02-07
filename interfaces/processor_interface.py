from __future__ import annotations

from typing import Generator, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class JobProcessor(Protocol):
    """
    Class provide possibility to send and processing data.
    """
    def set_status(self, status: str) -> None:
        """set status of processor"""

    def is_completed(self) -> bool:
        """return True if job is completed"""

    def send_job(self, filename: str, options: None | dict = None) -> int:
        """Method to send data to processing"""

    def get_job_status(self, job_id: int) -> Generator:
        """return job status by job ID"""

    def get_job_result(self, job_id: int) -> str:
        """get job data by job ID after processing and return it"""

    def save_file(self, path_to_result: str, path_to_save: Union[str, Path]) -> Union[str, Path, PosixPath]:
        """save job result after processing and return path to file"""
