from __future__ import annotations

from typing import Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path

    from config import ConverterStatus
    from config import JobConfig as Config
    from converter import Converter


class UIProtocol(Protocol):
    """Protocol defining the interface for user interface implementations.

    This protocol establishes a consistent interface for all user interface
    implementations, whether they are command-line, graphical, web-based, or
    other interaction methods. The protocol ensures that different UI types
    can be used interchangeably with the Converter class.

    The UI protocol handles two main responsibilities:
    1. User interaction for configuration and control
    2. Status and result display for feedback

    Implementations should provide appropriate user experiences while
    maintaining the same functional interface for consistency and
    substitutability.

    Methods:
        run: Start the UI and handle user interaction
        setup: Collect configuration parameters from user
        convert: Initiate conversion with user feedback
        display_*: Show various types of information to user
    """

    def run(self, converter: Converter) -> None:
        """Start the user interface and handle user interaction.

        This method begins the UI session, presenting the interface to the user
        and handling their interactions. It should integrate with the provided
        converter instance to perform actual conversion operations.

        Args:
            converter: The converter instance to use for processing

        Note:
            This method typically runs in a loop (for CLI) or event loop (for GUI)
            until the user chooses to exit the application.
        """
        raise NotImplementedError

    def setup(self) -> Config | bool:
        """Collect and validate conversion configuration from the user.

        Prompts the user to provide necessary configuration parameters such as
        source file, target format, and destination. The method should validate
        user input and return a properly configured JobConfig object.

        Returns:
            JobConfig object with user-specified parameters, or False if
            configuration collection was cancelled or failed

        Raises:
            ParamsError: If user input is invalid or incomplete
        """
        raise NotImplementedError

    def convert(self, config: Config) -> None:
        """Initiate conversion process with user feedback.

        Starts the conversion process using the provided configuration and
        handles user feedback during processing. This method typically
        coordinates with display methods to show progress and results.

        Args:
            config: Complete job configuration for the conversion

        Raises:
            ConvertError: If conversion cannot be started or fails
        """
        raise NotImplementedError

    def display_job_status(self, status: str) -> None:
        """Display the current conversion status to the user.

        Shows the current state of the conversion process (ready, processing,
        completed, failed) in a format appropriate for the UI implementation.

        Args:
            status: Current conversion status message
        """
        raise NotImplementedError

    def display_job_result(self, result: Path | str) -> None:
        """Display the final conversion result to the user.

        Shows the location or identifier of the successfully converted file,
        allowing the user to access their converted content.

        Args:
            result: Path or identifier where the converted file is located
        """
        raise NotImplementedError

    def display_job_id(self, job_id: str) -> None:
        """Display the unique job identifier to the user.

        Shows the job ID that can be used to track the conversion progress,
        particularly useful for long-running or remote conversions.

        Args:
            job_id: Unique identifier for the conversion job
        """
        raise NotImplementedError

    def display_common_info(self, message: str, status: str | None = None) -> None:
        """Display general information messages to the user.

        Shows informational messages, progress updates, or other general
        communication to keep the user informed about the conversion process.

        Args:
            message: Information message to display
            status: Optional status context for the message
        """
        raise NotImplementedError

    def display_error(self, error: str, status: ConverterStatus) -> None:
        """Display error messages to the user.

        Shows error information when conversion fails or encounters problems,
        providing the user with actionable feedback about what went wrong.

        Args:
            error: Descriptive error message
            status: Current conversion status (typically FAILED)
        """
        raise NotImplementedError
