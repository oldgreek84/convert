from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from exceptions import ConfigurationError

if TYPE_CHECKING:
    from formats import Format


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

    def check_direction(self):
        """Validate that the conversion direction is supported.

        Raises:
            ConfigurationError: If the source format is not supported for the target format.
        """
        if self.format_from not in self.format_to.allowed_formats():
            msg = f"Wrong direction {self.format_from.get_extension()} \
                for direction {self.format_to.get_extension()}"
            raise ConfigurationError(msg)


class APIConfig:
    """Configuration management for remote API authentication and communication.

    This class manages API credentials, URLs, and HTTP headers for communicating
    with remote conversion services. It supports both direct parameter passing
    and environment variable configuration.

    The class automatically generates appropriate HTTP headers for API requests,
    including authentication tokens and standard cache control directives.

    Attributes:
        token: API authentication token
        url: Base URL for the remote conversion service
        headers: Dictionary of pre-configured HTTP headers

    Environment Variables:
        API_KEY: Default API token if not provided in constructor
        CONVERTER_URL: Default service URL if not provided in constructor

    Example:
        >>> # Using environment variables
        >>> config = APIConfig()
        >>>
        >>> # Using explicit parameters
        >>> config = APIConfig(
        ...     token='your-api-key',
        ...     url='https://api.converter.com'
        ... )
        >>> headers = config.get_header('main_header')
    """

    def __init__(self, token: str | None = None, url: str | None = None):
        """Initialize API configuration.

        Args:
            token: API authentication token. If None, reads from API_KEY environment variable.
            url: Base URL for the remote service. If None, reads from CONVERTER_URL environment variable.
        """
        self.token = token or os.environ.get("API_KEY")
        self.url = url or os.environ.get("CONVERTER_URL")
        self.headers = {
            "main_header": {
                "cache-control": "no-cache",
                "content-type": "application/json",
                "x-oc-api-key": self.token,
            },
            "cache_header": {"cache-control": "no-cache", "x-oc-api-key": self.token},
        }

    def get_header(self, header_key: str):
        """Retrieve a specific header configuration.

        Args:
            header_key: Key identifying the header set to retrieve

        Returns:
            Dictionary containing the requested headers
        """
        return self.headers[header_key]

    def set_header(self, key: str, data: dict):
        """Set or update a header configuration.

        Args:
            key: Key identifying the header set to update
            data: Dictionary containing the header configuration
        """
        self.headers[key] = data
