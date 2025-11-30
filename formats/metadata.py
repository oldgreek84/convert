"""Format metadata value object.

This module defines the FormatMetadata dataclass which represents
immutable format information without needing format instances.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatMetadata:
    """Immutable value object representing format metadata.

    This is a Value Object - two instances with the same values
    are considered equal. The frozen=True ensures immutability.

    Attributes:
        name: Internal format identifier (e.g., 'pdf', 'mobi')
        extension: File extension including dot (e.g., '.pdf')
        display_name: Human-readable format name (e.g., 'PDF Document')
        description: Brief description of the format
    """

    name: str
    extension: str
    display_name: str
    description: str

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"{self.display_name} - {self.description}"
