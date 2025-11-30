"""Format repository for storing and retrieving format classes.

This module implements the Repository Pattern for format management,
providing a centralized location for format registration and retrieval.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from formats.metadata import FormatMetadata

if TYPE_CHECKING:
    from interfaces.format_instance import Format


class FormatRepositoryError(Exception):
    """Exception raised for format repository operations."""


class FormatRepository:
    """Repository for format class registration and retrieval.

    Provides a collection-like interface for managing format classes
    and their metadata. Handles storage, retrieval, and instantiation
    of format classes.

    Attributes:
        _registry: Dictionary mapping format names to format classes
        _metadata: Dictionary mapping format names to FormatMetadata

    Example:
        >>> repo = FormatRepository()
        >>> repo.register('pdf', PdfFormat, 'PDF', 'Portable Document Format')
        >>> pdf_class = repo.get_class('pdf')
        >>> pdf_instance = repo.create_instance('pdf', dpi=300)
    """

    def __init__(self) -> None:
        """Initialize an empty format repository."""
        self._registry: dict[str, type[Format]] = {}
        self._metadata: dict[str, FormatMetadata] = {}

    def register(
        self,
        name: str,
        format_class: type[Format],
        display_name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Register a format class with the repository.

        Creates metadata from the format class and stores both the class
        and metadata for later retrieval.

        Args:
            name: Unique identifier for the format (e.g., 'pdf', 'mobi')
            format_class: The format class to register
            display_name: Human-readable name (defaults to uppercase name)
            description: Brief description (defaults to '{name} format')

        Note:
            If a format with the same name is already registered,
            this method does nothing (no overwriting).
        """
        if name not in self._registry:
            self._registry[name] = format_class
            # Create temporary instance to get extension property
            temp_instance = format_class(name)
            self._metadata[name] = FormatMetadata(
                name=name,
                extension=temp_instance.extension,
                display_name=display_name or name.upper(),
                description=description or f"{name} format",
            )

    def get_class(self, name: str) -> type[Format]:
        """Retrieve a registered format class by name.

        Args:
            name: The format identifier

        Returns:
            The registered format class

        Raises:
            FormatRepositoryError: If the format is not registered
        """
        if name not in self._registry:
            msg = f"Class '{name}' is not registered"
            raise FormatRepositoryError(msg)
        return self._registry[name]

    def create_instance(self, name: str, **kwargs: Any) -> Format:
        """Create an instance of a registered format.

        Args:
            name: The format identifier
            **kwargs: Additional arguments to pass to the format constructor

        Returns:
            A new instance of the format class

        Raises:
            FormatRepositoryError: If the format is not registered
        """
        format_class = self.get_class(name)
        return format_class(name, **kwargs)

    def get_metadata(self, name: str) -> FormatMetadata:
        """Retrieve metadata for a registered format.

        Args:
            name: The format identifier

        Returns:
            FormatMetadata object with format information

        Raises:
            FormatRepositoryError: If the format is not registered
        """
        if name not in self._metadata:
            raise FormatRepositoryError(f"Metadata for '{name}' not found")
        return self._metadata[name]

    def get_all(self) -> list[FormatMetadata]:
        """Retrieve metadata for all registered formats.

        Returns:
            List of FormatMetadata objects for all registered formats
        """
        return list(self._metadata.values())

    def exists(self, name: str) -> bool:
        """Check if a format is registered.

        Args:
            name: The format identifier to check

        Returns:
            True if the format is registered, False otherwise
        """
        return name in self._registry
