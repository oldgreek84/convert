from __future__ import annotations

import shutil
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

from utils import save_from_url
from interfaces.saver_interface import SaverProtocol

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class LocalFileSaver(SaverProtocol):
    """
    Concrete implementation of SaverProtocol to save files to the local filesystem.
    """

    def __init__(self) -> None:
        self.destination_path: Path | None = None
        self.source_path: str | None = None

    def setup(self, **kwargs: Any) -> None:
        destination_path = kwargs.get("destination_path")
        if not destination_path:
            raise ValueError("destination_path must be provided for LocalFileSaver setup")
        self.destination_path = Path(destination_path).resolve()
        if not self.destination_path.exists():
            self.destination_path.mkdir(parents=True, exist_ok=True)

        source_path = kwargs.get("source_path")
        if not destination_path:
            raise ValueError("source_path must be provided for LocalFileSaver setup")
        self.source_path = source_path

    def save(self) -> str | Path | PosixPath:
        if not self.destination_path:
            raise RuntimeError("LocalFileSaver not set up. Call setup() first.")

        source_path = self.source_path
        source_file_path = Path(source_path)
        if not source_file_path.is_file():
            # If the source is a URL, download it. Otherwise, raise an error.
            if source_path.startswith(("http://", "https://")):
                return save_from_url(source_path, str(self.destination_path))
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Assuming source_path is a temporary file created by the processor
        # and we need to move/copy it to the destination.
        # For simplicity, let's just copy the file.
        # In a real scenario, you might want to move it or handle different source types.
        destination_file_path = self.destination_path / source_file_path.name

        # If the source is a local file, copy it
        shutil.copy(source_path, destination_file_path)
        return destination_file_path
