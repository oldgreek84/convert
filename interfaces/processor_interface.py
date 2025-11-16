from __future__ import annotations

from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path, PosixPath


class JobProcessor(ABC):
    """Abstract base class defining the interface for conversion processors.

    This class establishes the contract for all processor implementations that handle
    the actual conversion of files from one format to another. Processors can work
    locally, in Docker containers, or communicate with remote services.

    The processor interface follows a job-based workflow:
    1. Send a conversion job with file and options
    2. Monitor job status until completion
    3. Retrieve the conversion result

    Implementations must handle their specific processing environments while
    maintaining a consistent interface for the Converter class.

    Methods:
        send_job: Submit a file for conversion processing
        get_job_status: Monitor the progress of a conversion job
        get_job_result: Retrieve the converted file path or data
    """

    @abstractmethod
    def send_job(self, filename: str, format_options: dict | None = None) -> int:
        """Submit a file for conversion processing.

        Initiates a conversion job with the specified file and conversion format_options.
        The implementation should validate the file, prepare necessary resources,
        and start the conversion process.

        Args:
            filename: Path to the source file to be converted
            format_options: Dictionary containing conversion parameters like target format,
                    category, and format-specific format_options

        Returns:
            Unique job identifier for tracking the conversion progress

        Raises:
            ProcessorError: If the job cannot be started due to invalid input
                           or processor-specific issues
        """

    @abstractmethod
    def get_job_status(self, job_id: int) -> Generator:
        """Monitor the progress of a conversion job.

        Yields status updates for the specified job until completion or failure.
        This method should provide real-time feedback about the conversion progress,
        allowing the UI to display meaningful status information to users.

        Args:
            job_id: Unique identifier of the job to monitor

        Yields:
            Status messages or progress information as strings

        Raises:
            ProcessorError: If the job ID is invalid or monitoring fails
        """

    @abstractmethod
    def get_job_result(self, job_id: int) -> tuple(str, io.BytesIO):
        """Retrieve the result of a completed conversion job.

        Returns the path or location of the converted file after successful
        completion. The exact format of the return value depends on the
        processor implementation (local path, URL, etc.).

        Args:
            job_id: Unique identifier of the completed job

        Returns:
            Path, URL, or identifier where the converted file can be accessed

        Raises:
            ProcessorError: If the job failed, is not complete, or result
                           cannot be retrieved
        """
