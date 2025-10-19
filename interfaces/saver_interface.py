from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class SaverProtocol(ABC):
    """Abstract base class defining the interface for file saving operations.

    This protocol establishes a consistent interface for saving converted files
    to various destinations, including local filesystems, cloud storage services,
    or other storage backends. The design follows the setup-then-save pattern
    to accommodate different storage requirements and configurations.

    The saver protocol supports flexible configuration through the setup method,
    allowing each implementation to define its specific requirements while
    maintaining interface compatibility. This enables the open-closed principle
    where new storage backends can be added without modifying existing code.

    Workflow:
        1. Call setup() with destination and storage-specific parameters
        2. Call save() to perform the actual file storage operation

    Implementations might include:
        - Local filesystem saver
        - Cloud storage (Google Drive, AWS S3, etc.)
        - Network file systems
        - Database storage
    """

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """Configure the saver with destination and storage-specific options.

        This method initializes the saver with all necessary information for
        the save operation. The flexible kwargs approach allows each saver
        implementation to define its own configuration requirements.

        Common parameters:
            source_path: Path to the file to be saved
            destination_path: Target location for the saved file

        Storage-specific parameters might include:
            - For local saver: directory permissions, file naming patterns
            - For cloud saver: credentials, bucket names, access keys
            - For network saver: connection parameters, authentication

        Args:
            **kwargs: Storage-specific configuration parameters

        Raises:
            ValueError: If required parameters are missing or invalid
            ConnectionError: If remote storage cannot be accessed
        """

    @abstractmethod
    def save(self, source_path: str | None = None) -> str | Path | PosixPath:
        """Save the file to the configured destination.

        Performs the actual file saving operation using the configuration
        established in the setup() method. If source_path is provided,
        it overrides the path configured during setup.

        The method should handle various source types:
        - Local file paths
        - URLs for remote downloads
        - Temporary files from processors

        Args:
            source_path: Optional override for the source file path.
                        If None, uses the path from setup()

        Returns:
            Path or identifier where the file has been successfully saved

        Raises:
            RuntimeError: If setup() has not been called first
            FileNotFoundError: If the source file does not exist
            PermissionError: If destination is not writable
            StorageError: If storage backend is unavailable or fails
        """
