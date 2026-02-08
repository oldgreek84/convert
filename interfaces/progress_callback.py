"""Progress Callback Protocol for Converter.

This module defines the ProgressCallback protocol - an interface for
receiving progress updates during conversion operations. This decouples
the Converter from any specific UI implementation.

The Converter accepts an optional ProgressCallback and calls its methods
during processing. The Presenter implements this protocol and forwards
updates to the View.

Example:
    >>> class ConverterPresenter(ProgressCallback):
    ...     def on_status(self, status: str) -> None:
    ...         self.view.show_status(status)
    ...
    ...     def on_progress(self, percent: float) -> None:
    ...         self.view.show_progress(percent)
    ...
    >>> converter.convert(config, progress=presenter)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class ProgressCallback(Protocol):
    """Protocol for receiving conversion progress updates.

    This protocol defines callbacks that the Converter calls during
    processing. Implementations (typically the Presenter) receive these
    updates and forward them to the appropriate View.

    The protocol is designed to be:
    - Optional: Converter works without a callback (headless/batch mode)
    - Decoupled: Converter doesn't know about UI
    - Flexible: Same callback works for CLI, Tk, Web, logging, etc.

    Methods are called in this typical order:
    1. on_status("Processing") - conversion started
    2. on_message("Sending job...") - informational updates
    3. on_progress(0.25) - progress updates (if available)
    4. on_progress(0.50) - more progress
    5. on_complete(path) OR on_error(error) - final result

    Example:
        >>> class LoggingCallback:
        ...     def on_status(self, status: str) -> None:
        ...         logger.info(f"Status: {status}")
        ...
        ...     def on_error(self, error: str) -> None:
        ...         logger.error(f"Failed: {error}")
    """

    def on_status(self, status: str) -> None:
        """Called when conversion status changes.

        Args:
            status: New status (e.g., 'ready', 'processing', 'completed', 'failed')
        """
        ...

    def on_progress(self, percent: float) -> None:
        """Called when progress is updated.

        Args:
            percent: Progress from 0.0 to 1.0, or -1.0 for indeterminate
        """
        ...

    def on_message(self, message: str) -> None:
        """Called for informational messages during processing.

        Args:
            message: Informational message about current operation
        """
        ...

    def on_complete(self, result: str | Path) -> None:
        """Called when conversion completes successfully.

        Args:
            result: Path to the converted file or result identifier
        """
        ...

    def on_error(self, error: str) -> None:
        """Called when conversion fails.

        Args:
            error: Error message describing the failure
        """
        ...


class NullProgressCallback:
    """Null object implementation of ProgressCallback.

    Use this when no progress reporting is needed (headless/batch mode).
    All methods are no-ops, avoiding None checks in Converter.

    Example:
        >>> callback = progress or NullProgressCallback()
        >>> callback.on_status("Processing")  # Safe, does nothing
    """

    def on_status(self, status: str) -> None:
        """No-op implementation."""
        pass

    def on_progress(self, percent: float) -> None:
        """No-op implementation."""
        pass

    def on_message(self, message: str) -> None:
        """No-op implementation."""
        pass

    def on_complete(self, result: str | Path) -> None:
        """No-op implementation."""
        pass

    def on_error(self, error: str) -> None:
        """No-op implementation."""
        pass
