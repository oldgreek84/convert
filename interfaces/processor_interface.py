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
    4. Optionally save the result to a specific location

    Implementations must handle their specific processing environments while
    maintaining a consistent interface for the Converter class.

    Methods:
        send_job: Submit a file for conversion processing
        get_job_status: Monitor the progress of a conversion job
        get_job_result: Retrieve the converted file path or data
        save_file: Save the conversion result to a specified location
    """

    @abstractmethod
    def send_job(self, filename: str, options: dict | None = None) -> int:
        """Submit a file for conversion processing.

        Initiates a conversion job with the specified file and conversion options.
        The implementation should validate the file, prepare necessary resources,
        and start the conversion process.

        Args:
            filename: Path to the source file to be converted
            options: Dictionary containing conversion parameters like target format,
                    category, and format-specific options

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
    def get_job_result(self, job_id: int) -> str:
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

    @abstractmethod
    def save_file(self, path_to_result: str, path_to_save: str | Path) -> str | Path | PosixPath:
        """Save the conversion result to a specified location.

        Moves or copies the converted file from the processor's working location
        to the desired destination. This method handles the final step of making
        the converted file available to the user.

        Args:
            path_to_result: Source path where the converted file is located
            path_to_save: Destination directory or path for the final file

        Returns:
            Final path where the file has been saved

        Raises:
            ProcessorError: If the file cannot be saved due to permissions,
                           disk space, or other I/O issues
        """
