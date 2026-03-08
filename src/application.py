"""Presenter layer for MVP Pattern.

This module provides the AppPresenter class that acts as the Presenter
in the MVP (Model-View-Presenter) pattern.

Architecture (Two-Layer Orchestration):
---------------------------------------
    ┌─────────────────────────────────────────────────────────┐
    │                    AppPresenter                         │
    │              (Presentation Layer Orchestrator)          │
    │            Coordinates: View <-> Converter              │
    ├─────────────────────────────────────────────────────────┤
    │                      Converter                          │
    │               (Business Layer Orchestrator)             │
    │         Coordinates: Processor -> Saver -> Worker       │
    └─────────────────────────────────────────────────────────┘

The AppPresenter:
1. Owns the View reference (View is only held here, not in Converter)
2. Subscribes to Converter events and forwards them to View
3. Registers callbacks with View and delegates to Converter

This design follows Interface Segregation Principle:
- Converter has no UI knowledge, only emits events
- AppPresenter bridges events to View methods
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from formats.service import get_format_service
from src.config import JobConfig, ViewSelections

if TYPE_CHECKING:
    from interfaces.view_interface import PresenterViewProtocol
    from src.converter import Converter


class AppPresenter:
    """Presentation layer orchestrator implementing MVP Presenter role.

    This class sits between the View (UI) and the Converter (business logic),
    enabling complete decoupling:
    - View only knows how to render and capture user input
    - Converter only knows how to convert files (no UI knowledge)
    - AppPresenter bridges them via event subscription

    Two-Layer Orchestration Pattern:
    - AppPresenter: Presentation layer - coordinates View and Converter
    - Converter: Business layer - coordinates Processor, Saver, Worker

    Event Flow:
        User action -> View -> AppPresenter -> Converter
        Converter emits -> AppPresenter forwards -> View displays

    Interface Segregation:
        AppPresenter uses PresenterViewProtocol which combines only what it needs:
        - From AppViewProtocol: run(), get_config(), set_on_convert()
        - From ConverterOutputProtocol: show_status(), show_message(), show_error(), show_result()

    Attributes:
        converter: Business layer orchestrator for conversion operations.
        view: Passive View implementation for user interaction.

    Example:
        >>> view = TkView()
        >>> converter = Converter(processor, saver, worker)
        >>> presenter = AppPresenter(converter, view)
        >>> presenter.run()
    """

    def __init__(self, converter: Converter, view: PresenterViewProtocol) -> None:
        """Initialize presenter with converter and view.

        Args:
            converter: Business layer orchestrator for e-book conversion.
            view: View implementing PresenterViewProtocol.
        """
        self.converter = converter
        self.view = view

        # Register view callback for conversion trigger
        self.view.set_on_convert(self._handle_convert)

        # Subscribe to converter events and forward to view
        self._subscribe_to_converter_events()

    def _subscribe_to_converter_events(self) -> None:
        """Subscribe view methods to converter events.

        Bridges Converter events to View display methods:
        - 'status' -> View.show_status()
        - 'message' -> View.show_message()
        - 'error' -> View.show_error()
        - 'result' -> View.show_result()
        """
        self.converter.events.on("status", self.view.show_status)
        self.converter.events.on("message", self.view.show_message)
        self.converter.events.on("error", self.view.show_error)
        self.converter.events.on("result", self.view.show_result)

    def run(self) -> None:
        """Start the application by running the view.

        For CLI views, this runs synchronously until completion.
        For GUI views (Tk), this enters the mainloop and blocks
        until the window is closed.
        """
        self.view.run()

    def _handle_convert(self) -> None:
        """Handle conversion request from View.

        Retrieves selections from View, builds JobConfig, and delegates
        to Converter.
        """
        try:
            selections = self.view.get_config()
            config = self._build_config(selections)
        except Exception as ex:
            self.converter.error_handler(ex)
            return

        self.converter.convert(config)

    def _build_config(self, selections: ViewSelections) -> JobConfig:
        """Build JobConfig from raw view selections using FormatService."""
        format_service = get_format_service()
        return JobConfig(
            fmt_from=format_service.get_source_format(selections.source_format),
            fmt_to=format_service.get_target_format(selections.target_format),
            target=format_service.create_target_object(selections.target_format),
            path_to_file=selections.path_to_file,
        )


# Backward compatibility alias
Application = AppPresenter
