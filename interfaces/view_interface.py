"""View Protocol for MVP pattern.

This module defines the ViewProtocol - a passive view interface that works
with any UI implementation (CLI, Tk, Web, etc.). The view is responsible
only for rendering and capturing user input, with no business logic.

The Presenter (Application) handles all logic and communicates with the View
through this protocol, making it easy to swap UI implementations without
changing business logic.

The View uses the existing Config and Format system to build JobConfig,
so individual getters for file path, source/target format are not needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from src.config import JobConfig


class ViewProtocol(Protocol):
    """Passive view interface for MVP pattern.

    This protocol defines a UI-agnostic interface that works for CLI,
    Tkinter, Web, or any other UI implementation. Views implementing
    this protocol should be passive - they only render data and capture
    user input, with no business logic.

    The protocol is divided into four categories:
    1. Config: Get JobConfig built from user input
    2. Output: Methods to display information to user
    3. Events: Callbacks for user actions
    4. Lifecycle: Application flow control

    Example:
        >>> class TkView:
        ...     def get_config(self) -> JobConfig:
        ...         return self._build_config_from_ui()
        ...
        ...     def show_status(self, status: str) -> None:
        ...         self.status_label.config(text=status)

        >>> class CLIView:
        ...     def get_config(self) -> JobConfig:
        ...         return self.config  # built during setup()
        ...
        ...     def show_status(self, status: str) -> None:
        ...         print(f">>> STATUS: {status}")
    """

    # =========================================================================
    # OUTPUT: Display information to user
    # =========================================================================

    def show_status(self, status: str) -> None:
        """Display the current status.

        Args:
            status: Status message (e.g., 'Ready', 'Processing', 'Completed')
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

    # =========================================================================
    # EVENTS: Callbacks for user actions
    # =========================================================================

    def set_on_convert(self, callback: Callable[[], None]) -> None:
        """Register callback for when user triggers conversion.

        The view calls this callback when the user clicks Convert button
        (Tk) or confirms conversion (CLI).

        Args:
            callback: Function to call when conversion is triggered
        """
        ...

    # =========================================================================
    # CONFIG: Get configuration for conversion
    # =========================================================================

    def get_config(self) -> JobConfig:
        """Get the current job configuration.

        Returns the JobConfig object built from user input. This is called
        by the Application when the user triggers conversion.

        Returns:
            JobConfig object with target format and file path
        """
        ...

    # =========================================================================
    # LIFECYCLE: Application flow control
    # =========================================================================

    def run(self) -> None:
        """Start the view.

        For CLI: Runs the input prompts and triggers callback
        For Tk: Starts mainloop()
        For Web: Starts server

        This method may block (Tk mainloop) or run synchronously (CLI).
        """
        ...
