from __future__ import annotations

from typing import Generator, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class JobProcessor(ABC):
    """
    Class provide possibility to send and processing data.
    """

    @abstractmethod
    def send_job(self, filename: str, options: dict | None = None) -> int:
        """Method to send data to processing"""

    @abstractmethod
    def get_job_status(self, job_id: int) -> Generator:
        """Return job status by job ID"""

    @abstractmethod
    def get_job_result(self, job_id: int) -> str:
        """Get job data by job ID after processing and return it"""

    @abstractmethod
    def save_file(self, path_to_result: str, path_to_save: str | Path) -> str | Path | PosixPath:
        """Save job result after processing and return path to file"""
