from __future__ import annotations

import os
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

from interfaces.saver_interface import SaverProtocol

if TYPE_CHECKING:
    import io
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
        source_name: Source file path or URL to save from

    Example:
        >>> saver = LocalFileSaver()
        >>> saver.setup(
        ...     source_name='/tmp/converted.mobi',
        ...     destination_path='/home/user/books'
        ... )
        >>> saved_path = saver.save()
    """

    def __init__(self) -> None:
        self.destination_path: Path | None = None
        self.source_name: str | None = None
        self.source_data: io.BytesIO | None = None

    def setup(self, **kwargs: Any) -> None:
        """Configure the local file saver with destination and source paths.

        Args:
            **kwargs: Configuration parameters including:
                destination_path: Directory where files will be saved
                source_name: Source file path or URL to save from

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

        source_name = kwargs.get("source_name")
        if not source_name:
            msg = "source_name must be provided for LocalFileSaver setup"
            raise ValueError(msg)

        self.source_name = source_name

        source_data = kwargs.get("source_data")
        if not source_data:
            msg = "source_data must be provided for LocalFileSaver setup"
            raise ValueError(msg)

        self.source_data = source_data

    @staticmethod
    def _get_unique_filepath(filepath: Path) -> Path:
        """Generate a unique filepath if the original is not writable.

        If the file exists and cannot be overwritten (permission error),
        adds a numeric suffix to create a unique filename.

        Args:
            filepath: The original target file path

        Returns:
            A writable file path (original or with numeric suffix)
        """
        if not filepath.exists():
            return filepath

        # Check if we can write to existing file
        if os.access(filepath, os.W_OK):
            return filepath

        # Generate unique filename with suffix
        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent

        counter = 1
        while True:
            new_filepath = parent / f"{stem}_{counter}{suffix}"
            if not new_filepath.exists():
                return new_filepath
            if os.access(new_filepath, os.W_OK):
                return new_filepath
            counter += 1

    def save(self) -> str | Path | PosixPath:
        """Save the file to the configured destination."""
        if not self.destination_path:
            msg = "LocalFileSaver not set up. Call setup() first."
            raise RuntimeError(msg)

        filepath = self.destination_path / Path(self.source_name).name
        filepath = self._get_unique_filepath(filepath)
        stream = self.source_data
        stream.seek(0)
        with open(filepath, "wb") as f:
            f.write(stream.read())
        return filepath
