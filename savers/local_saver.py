from __future__ import annotations

import shutil
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

from interfaces.saver_interface import SaverProtocol
from utils.common_utils import save_from_url

if TYPE_CHECKING:
    from pathlib import PosixPath


class LocalFileSaver(SaverProtocol):
    """Local filesystem implementation of the SaverProtocol.

    This saver handles saving converted files to the local filesystem,
    supporting both local file copying and URL-based file downloads.
    It automatically creates destination directories and handles various
    source file types including temporary files and remote URLs.

    Features:
        - Local file copying and moving
        - URL-based file downloads
        - Automatic directory creation
        - Path resolution and validation
        - Support for temporary file cleanup

    The saver follows the two-phase setup-then-save pattern:
    1. setup() configures destination path and source information
    2. save() performs the actual file operation

    Attributes:
        destination_path: Target directory for saving files
        source_path: Source file path or URL to save from

    Example:
        >>> saver = LocalFileSaver()
        >>> saver.setup(
        ...     source_path='/tmp/converted.mobi',
        ...     destination_path='/home/user/books'
        ... )
        >>> saved_path = saver.save()
    """

    def __init__(self) -> None:
        self.destination_path: Path | None = None
        self.source_path: str | None = None

    def setup(self, **kwargs: Any) -> None:
        """Configure the local file saver with destination and source paths.

        Args:
            **kwargs: Configuration parameters including:
                destination_path: Directory where files will be saved
                source_path: Source file path or URL to save from

        Raises:
            ValueError: If required parameters are missing
        """
        destination_path = kwargs.get("destination_path")
        if not destination_path:
            msg = "destination_path must be provided for LocalFileSaver setup"
            raise ValueError(msg)

        self.destination_path = Path(destination_path).resolve()
        if not self.destination_path.exists():
            self.destination_path.mkdir(parents=True, exist_ok=True)

        source_path = kwargs.get("source_path")
        if not source_path:
            msg = "source_path must be provided for LocalFileSaver setup"
            raise ValueError(msg)

        self.source_path = source_path

    def save(self, source_path: str | None = None) -> str | Path | PosixPath:
        """Save the file to the configured destination.

        Args:
            source_path: Optional override for the source file path.
                        If None, uses the path from setup()

        Returns:
            Path where the file has been successfully saved

        Raises:
            RuntimeError: If setup() has not been called first
            FileNotFoundError: If the source file does not exist
            TypeError: If source_path is not provided and not configured
        """
        if not self.destination_path:
            msg = "LocalFileSaver not set up. Call setup() first."
            raise RuntimeError(msg)

        effective_source_path = source_path or self.source_path
        if not effective_source_path:
            msg = "No source path provided"
            raise ValueError(msg)

        if not isinstance(effective_source_path, str):
            msg = f"Invalid source path type: {type(effective_source_path)}"
            raise TypeError(msg)

        # Handle URL downloads
        if effective_source_path.startswith(("http://", "https://")):
            return save_from_url(effective_source_path, str(self.destination_path))

        # Handle local files
        source_file_path = Path(effective_source_path)
        if not source_file_path.is_file():
            msg = f"Source file not found: {effective_source_path}"
            raise FileNotFoundError(msg)

        destination_file_path = self.destination_path / source_file_path.name
        shutil.copy(effective_source_path, destination_file_path)
        return destination_file_path
