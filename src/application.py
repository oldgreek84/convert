"""Application Controller for MVP Pattern.

This module provides the Application class that acts as the orchestrator
between the View (UI) and the Converter (Model). It implements the
callback-based approach that works with both synchronous (CLI) and
event-driven (Tk) user interfaces.

The Application breaks the bidirectional dependency between UI and Converter
by acting as a mediator, registering callbacks with the View and delegating
conversion requests to the Converter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interfaces.view_interface import ViewProtocol
    from src.converter import Converter


class Application:
    """Application controller that orchestrates View and Converter.

    This class implements the MVP (Model-View-Presenter) pattern where:
    - View: Passive UI (TkView, CLIView) - only renders and captures input
    - Presenter: This Application class - handles logic and coordination
    - Model: Converter - business logic for e-book conversion

    The Application:
    1. Registers a convert callback with the View
    2. Starts the View (which may block for event loop)
    3. When View triggers conversion, the callback executes converter.convert()

    This pattern allows:
    - CLI: Linear flow (setup -> confirm -> convert)
    - Tk: Event-driven flow (mainloop with button callback)

    Attributes:
        converter: The Converter instance for processing conversions
        view: The View instance for user interaction

    Example:
        >>> view = TkView()  # or CLIView()
        >>> converter = Converter(view, processor, saver, worker)
        >>> app = Application(converter, view)
        >>> app.run()
    """

    def __init__(self, converter: Converter, view: ViewProtocol) -> None:
        """Initialize the application with converter and view.

        Args:
            converter: The Converter instance for e-book conversion
            view: The View instance implementing ViewProtocol
        """
        self.converter = converter
        self.view = view
        self.view.set_on_convert(self._handle_convert)

    def run(self) -> None:
        """Start the application.

        Starts the View which handles user interaction. For CLI, this runs
        synchronously. For Tk, this enters the mainloop and blocks until
        the window is closed.
        """
        self.view.run()

    def _handle_convert(self) -> None:
        """Handle conversion request from View.

        This callback is invoked by the View when the user triggers
        conversion (e.g., clicks Convert button or confirms in CLI).
        It retrieves the configuration from the View and delegates
        to the Converter.
        """
        self.converter.convert(self.view.get_config())
