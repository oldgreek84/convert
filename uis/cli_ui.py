"""CLI View Implementation for MVP Pattern.

This module provides CLIView - a passive view implementation for command-line
interface. The view implements ViewProtocol and is responsible only for
rendering output and capturing user input via terminal.

All business logic is handled by the Application (Presenter) via callbacks.

Features:
    - Command-line argument parsing
    - Interactive format selection prompts
    - Confirmation before conversion
    - Status and message display to stdout
    - Error reporting with detailed messages

Example:
    >>> from uis.cli_ui import CLIView
    >>> from src.application import Application
    >>> from src.converter import Converter
    >>>
    >>> view = CLIView()
    >>> converter = Converter(view, processor, saver, worker)
    >>> app = Application(converter, view)
    >>> app.run()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from formats.service import get_format_service
from src.config import ViewSelections
from src.exceptions import ParamsError, UIError
from uis import DOCSTRING
from utils.common_utils import get_path, parse_command

if TYPE_CHECKING:
    from collections.abc import Callable


class CLIView:
    """Command-line View implementing ViewProtocol.

    Handles argument parsing, interactive format selection, and
    text-based status display. All business logic is delegated
    to the Application via the convert callback.
    """

    docstring = DOCSTRING

    def __init__(self):
        self._on_convert = None
        self._selections: ViewSelections | None = None

    def _print(self, msg: str) -> None:  # noqa: PLR6301
        if sys.__stdout__:
            sys.__stdout__.write(msg + "\n")
            sys.__stdout__.flush()

    def set_on_convert(self, callback: Callable[[], None]) -> None:
        self._on_convert = callback

    def run(self) -> None:
        self._selections = self._setup()

        # Confirm
        if input("Convert? [y/N]: ").lower() == "y" and self._on_convert:
            self._on_convert()

    def get_config(self) -> ViewSelections:
        if not self._selections:
            msg = "Config is not set up properly"
            raise UIError(msg)
        return self._selections

    def _setup(self) -> ViewSelections:
        try:
            return self._get_selections(sys.argv)
        except ParamsError as err:
            self.show_message(self.docstring)
            msg = f"There is not params to set ({err})"
            raise ParamsError(msg) from err

    def _get_selections(self, args: list) -> ViewSelections:
        if len(args) == 1:
            msg = f"Not enough params {args}"
            raise ParamsError(msg)

        params_data = parse_command()
        if params_data.get("-path"):
            working_file_path = params_data["-path"]
        elif params_data.get("-name"):
            working_file_path = get_path(params_data["-name"])
        else:
            working_file_path = sys.argv[1]

        source_format = Path(working_file_path).suffix.lstrip(".")
        format_service = get_format_service()
        format_from = format_service.get_source_format(source_format)

        available_targets = format_service.list_available_targets(format_from)
        if not available_targets:
            msg = f"No conversion targets available for {source_format}"
            raise ParamsError(msg)

        choices = {}
        self.show_message("Available conversion formats:")
        for indx, metadata in enumerate(available_targets, start=1):
            self.show_message(f"  {indx}. {metadata}")
            choices[str(indx)] = metadata

        while True:
            result_enter = input("Enter format number: ").strip()
            if result_enter in choices:
                break

            self.show_message(
                f"Invalid choice '{result_enter}'. Please enter a number from 1 to {len(choices)}"
            )

        chosen_metadata = choices[result_enter]
        self.show_message(f"Selected: {chosen_metadata.display_name}")
        target_format = chosen_metadata.name

        self.show_message(
            f"\n{'=' * 80}\nPARAMS:\
            \n\t{working_file_path = }\
            \n\t{source_format = }\
            \n\t{target_format = }\
            \n{'=' * 80}"
        )

        return ViewSelections(
            source_format=source_format,
            target_format=target_format,
            path_to_file=working_file_path,
        )

    # =========================================================================
    # OUTPUT: Display information to user (ViewProtocol)
    # =========================================================================

    def show_status(self, status: str) -> None:
        """Display status message."""
        self._print(f">>> STATUS: {status}")

    def show_message(self, message: str) -> None:
        """Display informational message."""
        self._print(f">>> INFO: {message}")

    def show_error(self, error: str) -> None:
        """Display error message."""
        self._print(f">>> ERROR: {error}")

    def show_result(self, result: str | Path) -> None:
        """Display conversion result path."""
        self._print(f">>> RESULT: {result}")

    def show_formats(self, formats: list[str]) -> None:
        """Display available formats."""
        self._print(">>> FORMATS:")
        for indx, fmt in enumerate(formats, start=1):
            self._print(f"    {indx}) {fmt}")

    def show_progress(self, progress: float) -> None:
        """Display progress (no-op for CLI)."""
