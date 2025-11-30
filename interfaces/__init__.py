"""Interfaces package for abstract protocols and base classes.

This package contains:
- Format: Abstract base class for format implementations
- FormatRepositoryProtocol: Protocol for repository implementations
- Other interface definitions for processors, savers, workers, and UI
"""

from interfaces.format_instance import Format
from interfaces.repository_protocol import FormatRepositoryProtocol

__all__ = [
    "Format",
    "FormatRepositoryProtocol",
]
