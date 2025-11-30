"""Abstract base class for format implementations.

This module defines the Format ABC that all format implementations
must inherit from. It provides the interface contract for format
capabilities, options, and file extensions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Format(ABC):
    """Abstract base class for format definitions and capabilities.

    This class defines the interface that all format implementations
    must follow. Format classes provide information about conversion
    capabilities, options, and file extensions for specific formats.

    Subclasses should implement all abstract methods to define:
    - Which formats this format can be converted to
    - Format-specific conversion options
    - File extension information

    Attributes:
        name: String identifier for this format (e.g., 'fb2', 'mobi')
        category: Optional category for the format (e.g., 'ebook', 'document')

    Example:
        >>> class PdfFormat(Format):
        ...     def __init__(self, name: str):
        ...         super().__init__(name)
        ...         self._extension = '.pdf'
        ...
        ...     def get_allowed_formats(self) -> list[str]:
        ...         return ['mobi', 'epub']
        ...
        ...     def get_options(self) -> dict[str, Any]:
        ...         return {}
    """

    name: str
    category: str

    def __init__(self, name: str) -> None:
        """Initialize the format with its identifier.

        Args:
            name: String identifier for this format (e.g., 'fb2', 'mobi')
        """
        self.name = name
        self._extension = ""

    @abstractmethod
    def get_allowed_formats(self) -> list[str]:
        """Get the list of formats this format can be converted to.

        Returns:
            List of format identifiers that this format supports as conversion targets
        """
        ...

    @abstractmethod
    def get_options(self) -> dict[str, Any]:
        """Get format-specific conversion options.

        Returns:
            Dictionary of options specific to this format's conversion process
        """
        ...

    @property
    def extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            String file extension including the dot (e.g., '.fb2', '.mobi')
        """
        return self._extension
