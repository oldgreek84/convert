"""Format service layer for business logic operations.

This module implements the Service Layer pattern, providing high-level
operations for format management and conversion validation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import config
import exceptions
from formats.metadata import FormatMetadata
from formats.repository import FormatRepositoryError
from interfaces.repository_protocol import FormatRepositoryProtocol

if TYPE_CHECKING:
    from interfaces.format_instance import Format

logger = logging.getLogger(__name__)


class FormatService:
    """Service layer for format-related business logic.

    Provides high-level operations for format management, including
    format retrieval, conversion validation, and target configuration.
    Uses dependency injection - accepts any repository that implements
    FormatRepositoryProtocol.

    This design follows SOLID principles:
    - Single Responsibility: Only handles format business logic
    - Open/Closed: Can extend with new methods without modification
    - Dependency Inversion: Depends on protocol, not concrete class

    Attributes:
        _repository: The format repository for data access

    Example:
        >>> from formats.repository import FormatRepository
        >>> repository = FormatRepository()
        >>> service = FormatService(repository)
        >>> source = service.get_source_format('fb2')
        >>> targets = service.list_available_targets(source)

        # For testing with mock:
        >>> mock_repo = MockRepository()
        >>> test_service = FormatService(mock_repo)
    """

    def __init__(self, repository: FormatRepositoryProtocol) -> None:
        """Initialize the format service with dependency injection.

        Args:
            repository: Any object implementing FormatRepositoryProtocol.
                       This allows injecting different implementations
                       for production vs testing.
        """
        self._repository = repository

    def get_source_format(self, name: str) -> Format:
        """Retrieve a source format instance by name.

        Args:
            name: The format identifier (e.g., 'pdf', 'fb2')

        Returns:
            An instance of the requested format

        Raises:
            exceptions.FormatError: If the format is not registered
        """
        if not self._repository.exists(name):
            raise exceptions.FormatError(f"Format '{name}' does not exist")
        return self._repository.create_instance(name)

    def get_target_format(self, name: str, **options: Any) -> Format:
        """Retrieve a target format instance with options.

        Args:
            name: The format identifier
            **options: Format-specific options to pass to the constructor

        Returns:
            An instance of the requested format configured with options

        Raises:
            exceptions.FormatError: If the format is not registered
        """
        try:
            return self._repository.create_instance(name, **options)
        except FormatRepositoryError as err:
            raise exceptions.FormatError(str(err)) from err

    def validate_conversion(self, from_fmt: str, to_fmt: str) -> bool:
        """Validate that a conversion between formats is allowed.

        Checks that both formats exist and that the target format
        accepts the source format for conversion.

        Args:
            from_fmt: Source format identifier
            to_fmt: Target format identifier

        Returns:
            True if the conversion is valid

        Raises:
            exceptions.FormatError: If either format doesn't exist or
                                   conversion is not allowed
        """
        if not self._repository.exists(from_fmt):
            raise exceptions.FormatError(f"Source format '{from_fmt}' does not exist")
        if not self._repository.exists(to_fmt):
            raise exceptions.FormatError(f"Target format '{to_fmt}' does not exist")

        to_instance = self._repository.create_instance(to_fmt)
        if from_fmt not in to_instance.get_allowed_formats():
            raise exceptions.FormatError(
                f"Conversion from '{from_fmt}' to '{to_fmt}' is not allowed"
            )
        return True

    def create_target_object(self, name: str, **options: Any) -> config.Target:
        """Create a Target configuration object for a format.

        Args:
            name: The format identifier
            **options: Format-specific options

        Returns:
            Configured Target object ready for conversion

        Raises:
            exceptions.FormatError: If the format is not registered
        """
        try:
            target_instance = self._repository.create_instance(name, **options)
            return config.Target(
                target=target_instance.name,
                category=getattr(target_instance, "category", "unknown"),
                options=target_instance.get_options(),
            )
        except FormatRepositoryError as err:
            raise exceptions.FormatError(str(err)) from err

    def list_available_targets(self, source_format: Format) -> list[FormatMetadata]:
        """Get list of available target formats for a source format.

        Filters out formats that are listed in allowed_formats but not
        registered. Logs a warning for unregistered formats to help
        developers identify configuration issues.

        Args:
            source_format: The source format instance

        Returns:
            List of FormatMetadata for registered target formats
        """
        result: list[FormatMetadata] = []
        allowed = source_format.get_allowed_formats()

        for name in allowed:
            try:
                metadata = self._repository.get_metadata(name)
                result.append(metadata)
            except FormatRepositoryError:
                logger.warning(
                    "Format '%s' is listed in allowed_formats for '%s' "
                    "but is not registered. Skipping this format.",
                    name,
                    source_format.name,
                )
        return result

    def get_available_targets_by_name(self, source_format_name: str) -> list[FormatMetadata]:
        """Get available target formats by source format name.

        Convenience method that creates the source format instance
        and returns available targets.

        Args:
            source_format_name: Source format identifier

        Returns:
            List of FormatMetadata for valid conversion targets

        Raises:
            exceptions.FormatError: If source format doesn't exist
        """
        source_format = self.get_source_format(source_format_name)
        return self.list_available_targets(source_format)


def create_format_service(
    repository: FormatRepositoryProtocol | None = None,
) -> FormatService:
    """Factory function to create FormatService with default or custom repository.

    This is the recommended way to create a FormatService instance.
    It handles the default case (using the global registry) while
    allowing custom repositories for testing.

    Args:
        repository: Optional custom repository. If None, uses global registry.

    Returns:
        Configured FormatService instance

    Example:
        # Production use:
        >>> service = create_format_service()

        # Testing use:
        >>> mock_repo = MockRepository()
        >>> test_service = create_format_service(mock_repo)
    """
    if repository is None:
        from formats import registry

        repository = registry
    return FormatService(repository)


# Global service instance for convenience
# Uses lazy initialization to avoid circular imports
_format_service: FormatService | None = None


def get_format_service() -> FormatService:
    """Get the global FormatService instance (lazy initialization).

    Returns:
        The global FormatService instance

    Example:
        >>> service = get_format_service()
        >>> source = service.get_source_format('fb2')
    """
    global _format_service
    if _format_service is None:
        _format_service = create_format_service()
    return _format_service


# Backward compatibility - direct instance access
# Note: Prefer using get_format_service() or create_format_service()
format_service: FormatService = None  # type: ignore[assignment]


def __getattr__(name: str) -> Any:
    """Module-level getattr for lazy initialization of format_service."""
    if name == "format_service":
        return get_format_service()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
