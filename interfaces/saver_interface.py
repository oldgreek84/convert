from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path, PosixPath


class SaverProtocol(ABC):
    """
    Class provides the possibility to save data.
    """

    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        """
        Set up the saver with destination and other specific options.
        For a local saver, kwargs might include 'destination_path'.
        For a remote saver, kwargs might include 'remote_url', 'bucket_name', 'credentials', etc.
        This method should be called before 'save'.
        """

    @abstractmethod
    def save(self, source_path: str | None = None) -> str | Path | PosixPath:
        """
        Save job result from source_path to the pre-configured destination.
        If source_path is None, use the path from setup().
        """
