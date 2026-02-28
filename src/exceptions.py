"""Custom exception classes for the e-book converter application.

This module defines all custom exceptions used throughout the application,
providing a centralized location for error handling and documentation.
The exceptions are organized in a hierarchy that reflects the application
architecture and allows for granular error handling.

Exception Hierarchy:
    ConverterError (base)
    ├── ConfigurationError
    │   ├── ParamsError
    │   └── APIConfigError
    ├── ProcessingError
    │   ├── ProcessorError
    │   ├── LocalProcessorError
    │   ├── DockerProcessorError
    │   └── RemoteProcessorError
    ├── StorageError
    │   ├── SaverError
    │   ├── LocalSaverError
    │   └── CloudSaverError
    ├── InterfaceError
    │   ├── UIError
    │   └── CLIError
    └── ConcurrencyError
        ├── WorkerError
        └── ThreadError

Usage:
    from exceptions import ProcessorError, ConfigurationError

    try:
        processor.convert_file(file_path)
    except ProcessorError as e:
        logger.error(f"Processing failed: {e}")
    except ConfigurationError as e:
        logger.error(f"Configuration issue: {e}")
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime

# =============================================================================
# Base Exception Classes
# =============================================================================


class ConverterError(Exception):
    """Base exception for all converter-related errors."""

    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# =============================================================================
# Configuration Related Exceptions
# =============================================================================


class ConfigurationError(ConverterError):
    """Base class for configuration-related errors.

    Raised when there are issues with application configuration,
    including command-line arguments, configuration files, API settings,
    or environment variables.
    """


class ParamsError(ConfigurationError):
    """Exception raised when parameter parsing or validation fails.

    This exception is thrown when command-line arguments, configuration parameters,
    or other input parameters are invalid, missing, or cannot be parsed correctly.
    """


class APIConfigError(ConfigurationError):
    """Exception raised when API configuration is invalid or incomplete.

    This includes issues with API keys, URLs, authentication settings,
    or other API-related configuration problems.
    """


# =============================================================================
# Processing Related Exceptions
# =============================================================================


class ProcessingError(ConverterError):
    """Base class for all processing-related errors.

    Covers errors that occur during the actual conversion process,
    regardless of the processor type (local, Docker, remote).
    """


class ProcessorError(ProcessingError):
    """General processor error for conversion operations.

    This exception is thrown when conversion processing encounters errors
    such as invalid files, processing failures, external tool errors,
    or communication issues with processing services.
    """


class LocalProcessorError(ProcessorError):
    """Exception specific to local processor operations.

    Raised when issues occur with local ebook-convert execution,
    subprocess management, or local file system operations.
    """


class DockerProcessorError(ProcessorError):
    """Exception specific to Docker processor operations.

    Raised when issues occur with Docker container management,
    image building, volume mounting, or Docker daemon communication.
    """


class RemoteProcessorError(ProcessorError):
    """Exception specific to remote processor operations.

    Raised when issues occur with remote API communication,
    network connectivity, authentication, or remote service errors.
    """


# =============================================================================
# Storage Related Exceptions
# =============================================================================


class StorageError(ConverterError):
    """Base class for storage and file saving errors.

    Covers errors related to saving converted files to various
    destinations including local filesystem and cloud storage.
    """


class SaverError(StorageError):
    """General saver error for file storage operations.

    This exception is thrown when file saving operations fail
    due to permissions, disk space, network issues, or other
    storage-related problems.
    """


class LocalSaverError(SaverError):
    """Exception specific to local file system saving operations.

    Raised when issues occur with local file operations such as
    insufficient disk space, permission errors, or file system errors.
    """


class CloudSaverError(SaverError):
    """Exception specific to cloud storage operations.

    Raised when issues occur with cloud storage services such as
    authentication failures, quota exceeded, or network connectivity problems.
    """


class GoogleDriveError(CloudSaverError):
    """Exception specific to Google Drive operations.

    Raised when issues occur with Google Drive API operations
    including authentication, file upload, or API quota issues.
    """


# =============================================================================
# Interface Related Exceptions
# =============================================================================


class InterfaceError(ConverterError):
    """Base class for user interface related errors.

    Covers errors that occur in user interface components
    including CLI, GUI, and web interfaces.
    """


class UIError(InterfaceError):
    """General user interface error.

    Raised when UI components encounter errors such as
    invalid user input, display issues, or component failures.
    """


class CLIError(InterfaceError):
    """Exception specific to command-line interface operations.

    Raised when issues occur with CLI argument parsing,
    terminal operations, or command-line specific functionality.
    """


class GUIError(InterfaceError):
    """Exception specific to graphical user interface operations.

    Raised when issues occur with GUI components, window management,
    or graphical interface specific functionality.
    """


# =============================================================================
# Concurrency Related Exceptions
# =============================================================================


class ConcurrencyError(ConverterError):
    """Base class for concurrency and threading related errors.

    Covers errors that occur in concurrent execution,
    threading operations, and worker management.
    """


class WorkerError(ConcurrencyError):
    """Exception raised when worker operations fail.

    This includes errors in worker initialization, execution,
    result retrieval, or worker lifecycle management.
    """


class ThreadError(ConcurrencyError):
    """Exception raised when threading operations fail or are in invalid state.

    Raised when thread operations encounter errors such as
    thread creation failures, synchronization issues, or invalid thread states.
    """


# =============================================================================
# Format Related Exceptions
# =============================================================================


class FormatError(ConverterError):
    """Base class for format-related errors.

    Covers errors related to file format detection, validation,
    format compatibility, and format-specific operations.
    """


class UnsupportedFormatError(FormatError):
    """Exception raised when an unsupported file format is encountered.

    Raised when the application encounters a file format that is not
    supported for conversion or when format detection fails.
    """


class FormatValidationError(FormatError):
    """Exception raised when format validation fails.

    Raised when a file claims to be a certain format but fails
    validation checks or is corrupted.
    """


# =============================================================================
# Utility Functions for Exception Handling
# =============================================================================


def create_error_context(**kwargs) -> dict:
    """Create an error context dictionary with common debugging information."""
    context = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "traceback": traceback.format_exc(),
    }
    context.update(kwargs)
    return context


def handle_exception_chain(exception: Exception) -> list[str]:
    """Extract the full exception chain as a list of message strings."""
    messages = []
    current = exception

    while current:
        messages.append(str(current))
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)

    return messages


# =============================================================================
# Exception Categories for Error Handling
# =============================================================================

RETRIABLE_EXCEPTIONS = (
    RemoteProcessorError,
    CloudSaverError,
    # Add other exceptions that should trigger retry logic
)

FATAL_EXCEPTIONS = (
    ConfigurationError,
    UnsupportedFormatError,
    # Add other exceptions that should stop processing immediately
)

USER_FRIENDLY_EXCEPTIONS = (
    ParamsError,
    UnsupportedFormatError,
    LocalSaverError,
    # Add other exceptions that should show user-friendly messages
)
