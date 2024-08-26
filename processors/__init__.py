from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, Union

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class ProcessorError(Exception):
    """common except type for errors"""


class JobProcessorInterface(ABC):
    @abstractmethod
    def is_completed(self) -> bool:
        """return True if job is completed"""

    @abstractmethod
    def send_job(self, filename: str, options: None | dict = None) -> int:
        """Method to send data to processing"""

    @abstractmethod
    def get_job_status(self, job_id: int) -> Generator:
        """return job status by job ID"""

    @abstractmethod
    def get_job_result(self, job_id: int) -> str:
        """get job data by job ID after processing and return it"""

    @abstractmethod
    def save_file(self, path_to_result: str, path_to_save: Union[str, Path]) -> Union[str, Path, PosixPath]:
        """save job result after processing and return path to file"""
