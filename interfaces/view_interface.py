"""View Protocols for MVP pattern with Interface Segregation.

This module defines segregated view interfaces following the Interface
Segregation Principle (ISP). Instead of one fat ViewProtocol with 9 methods,
we split into focused protocols:

Protocol Hierarchy:
-------------------
    ConverterOutputProtocol (4 methods)
        show_status(), show_message(), show_error(), show_result()

    AppViewProtocol (3 methods)
        run(), get_config(), set_on_convert()

    PresenterViewProtocol = ConverterOutputProtocol + AppViewProtocol
        Used by AppPresenter (7 methods total)

    ViewProtocol = PresenterViewProtocol + UI extras
        Used by UI implementations (9 methods total)

Usage:
------
    - AppPresenter uses PresenterViewProtocol (only what it needs)
    - TkView, CLIView implement ViewProtocol (full interface)
    - Converter has no view dependency (uses EventEmitter)

Example:
    >>> class AppPresenter:
    ...     def __init__(self, view: PresenterViewProtocol, converter: Converter):
    ...         self.view = view
    ...         converter.events.on("status", view.show_status)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

from src.config import ViewSelections


@runtime_checkable
class ConverterOutputProtocol(Protocol):
    """Protocol for receiving converter output/events.

    This minimal interface defines what the Converter needs to communicate
    its progress. Application subscribes these methods to Converter events.

    These 4 methods map directly to Converter's event emissions:
    - 'status' event -> show_status()
    - 'message' event -> show_message()
    - 'error' event -> show_error()
    - 'result' event -> show_result()

    Example:
        >>> converter.events.on('status', view.show_status)
        >>> converter.events.on('message', view.show_message)
    """

    def show_status(self, status: str) -> None:
        """Display the current conversion status.

        Args:
            status: Status string (e.g., 'ready', 'processing', 'completed', 'failed')
        """
        ...

    def show_message(self, message: str) -> None:
        """Display an informational message.

        Args:
            message: Message to display to user
        """
        ...

    def show_error(self, error: str) -> None:
        """Display an error message.

        Args:
            error: Error message to display
        """
        ...

    def show_result(self, result: str | Path) -> None:
        """Display the conversion result.

        Args:
            result: Path or description of the converted file
        """
        ...


@runtime_checkable
class AppViewProtocol(Protocol):
    """Protocol for Application-View interaction.

    This interface defines what the Application (Presenter) needs from
    the View for lifecycle control and user input handling.

    Methods:
    - run(): Start the view (mainloop or linear flow)
    - get_config(): Get user's conversion configuration
    - set_on_convert(): Register callback for conversion trigger
    """

    def run(self) -> None:
        """Start the view.

        For CLI: Runs the input prompts and triggers callback
        For Tk: Starts mainloop()
        For Web: Starts server

        This method may block (Tk mainloop) or run synchronously (CLI).
        """
        ...

    def get_config(self) -> ViewSelections:
        """Get raw user selections for conversion.

        Returns primitive data only — the presenter builds domain objects.

        Returns:
            ViewSelections with source format, target format, and file path
        """
        ...

    def set_on_convert(self, callback: Callable[[], None]) -> None:
        """Register callback for when user triggers conversion.

        The view calls this callback when the user clicks Convert button
        (Tk) or confirms conversion (CLI).

        Args:
            callback: Function to call when conversion is triggered
        """
        ...


@runtime_checkable
class PresenterViewProtocol(ConverterOutputProtocol, AppViewProtocol, Protocol):
    """Minimal view interface required by AppPresenter.

    Combines the two segregated protocols that AppPresenter actually needs:
    - AppViewProtocol: run(), get_config(), set_on_convert()
    - ConverterOutputProtocol: show_status(), show_message(), show_error(), show_result()

    This is the Interface Segregation principle in action - AppPresenter
    depends on exactly what it needs, nothing more.
    """


@runtime_checkable
class ViewProtocol(PresenterViewProtocol, Protocol):
    """Full view interface for UI implementations.

    This protocol extends PresenterViewProtocol with additional display
    methods that are UI-specific but not needed by AppPresenter.

    UI implementations (TkView, CLIView) should implement this full protocol.
    AppPresenter should use PresenterViewProtocol instead.

    Additional methods:
    - show_formats(): Display available conversion formats
    - show_progress(): Update progress bar/indicator
    """

    def show_formats(self, formats: list[str]) -> None:
        """Display available target formats.

        Args:
            formats: List of available format names
        """
        ...

    def show_progress(self, progress: float) -> None:
        """Update progress indication.

        Args:
            progress: Progress value (0.0 to 1.0), or -1 for indeterminate
        """
        ...
