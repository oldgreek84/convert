"""Format registration and management package.

This package provides the format registry system, including:
- FormatRepository: Storage and retrieval of format classes
- FormatService: Business logic for format operations
- FormatMetadata: Immutable format information
- register_format: Decorator for registering format classes

Usage:
    from formats import register_format, format_service

    @register_format('pdf', display_name='PDF', description='PDF format')
    class PdfFormat(Format):
        ...

    # Get a format instance
    pdf = format_service.get_source_format('pdf')
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING, Callable

from formats.repository import FormatRepository

if TYPE_CHECKING:
    from interfaces.format_instance import Format

# Global registry instance
registry = FormatRepository()


def load_formats() -> None:
    """Dynamically load all format modules and register their format classes.

    This function imports all Python modules in the formats package,
    ensuring that all @register_format decorators are executed and
    format classes are properly registered in the global registry.

    The function uses pkgutil to discover all modules in the package
    and imports them using importlib. This allows the format system
    to automatically detect and register new format implementations
    without requiring manual registration.

    Side Effects:
        - Imports all modules in the formats package
        - Executes @register_format decorators
        - Populates the global format registry
    """
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{module_name}"
        importlib.import_module(full_name)


def register_format(
    name: str,
    display_name: str | None = None,
    description: str | None = None,
) -> Callable[[type[Format]], type[Format]]:
    """Decorator factory for registering format classes.

    Creates a decorator that registers the decorated class with the
    global format registry, along with its display name and description.

    Args:
        name: Unique identifier for the format (e.g., 'pdf', 'mobi')
        display_name: Human-readable name for display (optional)
        description: Brief description of the format (optional)

    Returns:
        A decorator function that registers the class

    Example:
        @register_format('pdf', display_name='PDF', description='PDF format')
        class PdfFormat(Format):
            ...
    """

    def decorator(cls: type[Format]) -> type[Format]:
        registry.register(name, cls, display_name, description)
        return cls

    return decorator


# Backward compatibility aliases
get_class = registry.get_class
create_format = registry.create_instance


# Export commonly used items
__all__ = [
    "create_format",
    "get_class",
    "load_formats",
    "register_format",
    "registry",
]
