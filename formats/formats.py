"""Ebook format implementations.

This module contains concrete format implementations for ebook conversion.
All format classes are automatically registered with the format registry
using the @register_format decorator.
"""

from __future__ import annotations

from typing import Any

from formats import register_format
from interfaces.format_instance import Format


class EbookFormat(Format):
    """Base class for ebook format implementations.

    Provides common functionality for ebook formats including
    category assignment.

    Attributes:
        category: Set to 'ebook' for all ebook formats
    """

    def __init__(self, name: str) -> None:
        """Initialize ebook format.

        Args:
            name: Format identifier
        """
        super().__init__(name)
        self.category = "ebook"


@register_format(
    "fb2",
    display_name="FB2",
    description="Ebook format for general purposes",
)
class Fb2Format(EbookFormat):
    """FictionBook 2.0 format handler.

    FB2 is an open XML-based e-book format popular in Russia
    and Eastern Europe.
    """

    def __init__(self, name: str) -> None:
        """Initialize FB2 format.

        Args:
            name: Format identifier
        """
        super().__init__(name)
        self._extension = ".fb2"

    def get_allowed_formats(self) -> list[str]:
        """Get formats that FB2 can be converted to."""
        return ["mobi", "txt", "pdf"]

    def get_options(self) -> dict[str, Any]:
        """Get FB2-specific conversion options."""
        return {}


# Uncomment to register TXT format:
# @register_format("txt", display_name="TXT", description="Common text format")
class TxtFormat(EbookFormat):
    """Plain text format handler.

    Simple text format without formatting. Useful for basic
    text extraction and conversion.
    """

    def __init__(self, name: str) -> None:
        """Initialize TXT format.

        Args:
            name: Format identifier
        """
        super().__init__(name)
        self._extension = ".txt"

    def get_allowed_formats(self) -> list[str]:
        """Get formats that TXT can be converted to."""
        return ["mobi", "fb2", "pdf"]

    def get_options(self) -> dict[str, Any]:
        """Get TXT-specific conversion options."""
        return {}


@register_format(
    "mobi",
    display_name="MOBI",
    description="Amazon Kindle Format",
)
class MobiFormat(EbookFormat):
    """Kindle MOBI format handler.

    MOBI is Amazon's proprietary e-book format used by
    Kindle devices and applications.
    """

    def __init__(self, name: str) -> None:
        """Initialize MOBI format.

        Args:
            name: Format identifier
        """
        super().__init__(name)
        self._extension = ".mobi"

    def get_allowed_formats(self) -> list[str]:
        """Get formats that MOBI can be converted to."""
        return ["fb2", "txt", "pdf"]

    def get_options(self) -> dict[str, Any]:
        """Get MOBI-specific conversion options."""
        return {}


@register_format(
    "pdf",
    display_name="PDF",
    description="Portable Document Format",
)
class PdfFormat(EbookFormat):
    """PDF format handler with customizable settings.

    Example of a format with additional initialization parameters.
    This demonstrates how the factory pattern handles formats with
    different initialization requirements.

    Attributes:
        dpi: Resolution for images (default: 150)
        color_mode: Color mode - 'RGB' or 'CMYK' (default: 'RGB')
        compression: Enable PDF compression (default: True)
    """

    def __init__(
        self,
        name: str,
        dpi: int = 150,
        color_mode: str = "RGB",
        compression: bool = True,
    ) -> None:
        """Initialize PDF format with optional parameters.

        Args:
            name: Format identifier
            dpi: Resolution for images (default: 150)
            color_mode: Color mode - 'RGB' or 'CMYK' (default: 'RGB')
            compression: Enable PDF compression (default: True)
        """
        super().__init__(name)
        self.dpi = dpi
        self.color_mode = color_mode
        self.compression = compression
        self._extension = ".pdf"

    def get_allowed_formats(self) -> list[str]:
        """Get formats that PDF can be converted to."""
        return ["fb2", "mobi", "txt", "epub"]

    def get_options(self) -> dict[str, Any]:
        """Return PDF-specific conversion options."""
        return {
            "dpi": self.dpi,
            "color_mode": self.color_mode,
            "compression": self.compression,
        }
