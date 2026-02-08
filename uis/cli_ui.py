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
from src.config import JobConfig
from src.exceptions import ParamsError, UIError
from uis import DOCSTRING
from utils.common_utils import get_path, parse_command

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.config import JobConfig as Config


class CLIView:
    """Command-line View implementing ViewProtocol.

    This class provides a text-based passive view for the e-book converter.
    It handles command-line argument parsing, user prompts, and text-based
    status display. All business logic is delegated to the Application
    via the convert callback.

    The view follows the MVP pattern:
    - Captures user input (file path, format selection)
    - Displays output (status, messages, errors)
    - Triggers conversion via registered callback

    Attributes:
        docstring: Help text for command-line usage
        config: Current JobConfig after setup

    Example:
        >>> view = CLIView()
        >>> view.set_on_convert(lambda: converter.convert(view.get_config()))
        >>> view.run()
    """

    docstring = DOCSTRING

    def __init__(self):
        self._on_convert = None
        self.config = None

    def _print(self, msg: str) -> None:
        """Print message to stdout with proper handling.

        Args:
            msg: Message to print to the console
        """
        if sys.__stdout__:
            sys.__stdout__.write(msg + "\n")
            sys.__stdout__.flush()

    def set_on_convert(self, callback: Callable[[], None]) -> None:
        self._on_convert = callback

    def run(self) -> None:
        config = self.setup()
        self.config = config

        # Confirm
        if input("Convert? [y/N]: ").lower() == "y" and self._on_convert:
            self._on_convert()

    def get_config(self):
        if not self.config:
            raise UIError("Config is not set up properly")
        return self.config

    def setup(self) -> Config:
        try:
            args = self._get_params(sys.argv)
        except ParamsError as err:
            self.show_message(self.docstring)
            msg = f"There is not params to set ({err})"
            raise ParamsError(msg) from err

        return JobConfig(*args)

    def _get_params(self, args: list) -> tuple:
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

        format_from_name = Path(working_file_path).suffix.lstrip(".")
        format_service = get_format_service()
        format_from = format_service.get_source_format(format_from_name)

        available_targets = format_service.list_available_targets(format_from)
        if not available_targets:
            raise ParamsError(f"No conversion targets available for {format_from_name}")

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

        format_to_name = choices[result_enter].name
        format_to = format_service.get_target_format(format_to_name, **params_data)
        format_service.validate_conversion(format_from_name, format_to_name)

        target_object = format_service.create_target_object(format_to.name, **params_data)
        working_target = target_object.target
        working_category = target_object.category

        msg = f"\n{'=' * 80}\nPARAMS:\
                \n\t{working_file_path = }\
                \n\t{working_target = }\
                \n\t{working_category = }\
                \n\t{target_object = }\
                \n{'=' * 80}"
        self.show_message(msg)
        return target_object, working_file_path

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
