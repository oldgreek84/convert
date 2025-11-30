from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from exceptions import ConfigurationError

if TYPE_CHECKING:
    from interfaces.format_instance import Format


class ConverterStatus(StrEnum):
    """Enumeration of possible conversion status states.

    This enum defines the different states a conversion operation can be in,
    providing a standardized way to track and communicate conversion progress.

    Values:
        READY: Converter is initialized and ready to start processing
        PROCESSING: Conversion is currently in progress
        FAILED: Conversion encountered an error and failed
        COMPLETED: Conversion finished successfully
    """

    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class Target:
    """Configuration object that defines the conversion target format and options.

    This dataclass encapsulates information about the desired output format,
    category, and any format-specific conversion options.

    Attributes:
        target: The target file format (e.g., 'mobi', 'fb2', 'epub')
        category: The category of the file being converted (e.g., 'ebook')
        options: Dictionary of format-specific conversion options

    Example:
        >>> target = Target(
        ...     target='mobi',
        ...     category='ebook',
        ...     options={'--enable-heuristics': True}
        ... )
    """

    target: str
    category: str
    options: dict = field(default_factory=dict)


@dataclass
class JobConfig:
    """Complete configuration for a conversion job.

    This dataclass contains all the information needed to execute a conversion job,
    including the target format configuration, source file path, and destination path.
    It provides convenient properties to access target-specific information and
    generates processor-compatible configuration dictionaries.

    Attributes:
        target: Target configuration specifying format and options
        path_to_file: Path to the source file to be converted
        path_to_save: Directory path where the converted file will be saved

    Properties:
        job_target: Convenience property to access target format
        job_category: Convenience property to access target category
        job_options: Convenience property to access conversion options

    Example:
        >>> target = Target('mobi', 'ebook')
        >>> config = JobConfig(
        ...     target=target,
        ...     path_to_file='/path/to/book.fb2',
        ...     path_to_save='/output/directory'
        ... )
        >>> config.get_config()
        {'category': 'ebook', 'target': 'mobi', 'options': {}}
    """

    target: Target
    path_to_file: str
    path_to_save: str = "books"

    @property
    def job_target(self):
        """Get the target format from the target configuration."""
        return self.target.target

    @property
    def job_category(self):
        """Get the category from the target configuration."""
        return self.target.category

    @property
    def job_options(self):
        """Get the conversion options from the target configuration."""
        return self.target.options

    def get_config(self) -> dict:
        """Generate a processor-compatible configuration dictionary.

        Returns:
            Dictionary containing category, target, and options for processors.
        """
        return {
            "category": self.job_category,
            "target": self.job_target,
            "options": self.job_options,
        }


# TODO: implement processing with setup with Format classes
class SetupConfig:
    """Configuration validation for format conversion direction.

    This class validates that the requested conversion direction (from one format
    to another) is supported and valid.

    Attributes:
        format_from: Source format identifier
        format_to: Target format identifier or list of supported formats

    Example:
        >>> config = SetupConfig('fb2', ['mobi', 'epub'])
        >>> config.check_direction()  # Validates conversion is possible
    """

    def __init__(self, format_from: Format, format_to: Format) -> None:
        """Initialize setup configuration.

        Args:
            format_from: Source format to convert from
            format_to: Target format or list of supported target formats
        """
        self.format_from = format_from
        self.format_to = format_to

    def check_direction(self) -> None:
        """Validate that the conversion direction is supported.

        Raises:
            ConfigurationError: If the source format is not supported for the target format.
        """
        if self.format_from.name not in self.format_to.get_allowed_formats():
            msg = (
                f"Wrong direction {self.format_from.extension} "
                f"for direction {self.format_to.extension}"
            )
            raise ConfigurationError(msg)
