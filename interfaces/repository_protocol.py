"""Repository protocol definition.

This module defines the protocol (interface) for format repositories,
enabling dependency injection with different implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from formats.metadata import FormatMetadata
    from interfaces.format_instance import Format


class FormatRepositoryProtocol(Protocol):
    """Protocol defining the interface for format repositories.

    This protocol enables dependency injection by allowing any class
    that implements these methods to be used as a repository.

    This follows the Dependency Inversion Principle (DIP):
    - High-level modules (FormatService) depend on abstractions (this protocol)
    - Low-level modules (FormatRepository) implement the abstraction

    Example:
        >>> class MockRepository:
        ...     def exists(self, name: str) -> bool:
        ...         return name == 'pdf'
        ...     # ... implement other methods
        ...
        >>> service = FormatService(MockRepository())  # Works!
    """

    def register(
        self,
        name: str,
        format_class: type[Format],
        display_name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Register a format class with the repository."""
        ...

    def get_class(self, name: str) -> type[Format]:
        """Retrieve a registered format class by name."""
        ...

    def create_instance(self, name: str, **kwargs: Any) -> Format:
        """Create an instance of a registered format."""
        ...

    def get_metadata(self, name: str) -> FormatMetadata:
        """Retrieve metadata for a registered format."""
        ...

    def get_all(self) -> list[FormatMetadata]:
        """Retrieve metadata for all registered formats."""
        ...

    def exists(self, name: str) -> bool:
        """Check if a format is registered."""
        ...
