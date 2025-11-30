from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from config import ConverterStatus, JobConfig
from exceptions import ParamsError
from formats.service import format_service
from uis import DOCSTRING, InterfaceError
from utils.common_utils import get_path, parse_command

if TYPE_CHECKING:

    from converter import Converter
    from interfaces.ui_interface import Config


def yes_no(message="Do you want to run convert[N/y]?: "):
    """Prompt user for yes/no confirmation.

    Args:
        message: Prompt message to display to the user

    Returns:
        True if user responds with 'y' or 'yes', False otherwise
    """
    return input(message).lower() in {"y", "yes"}


class ConverterInterfaceCLI:
    """Command-line interface implementation for the e-book converter.

    This class provides a text-based interface for interacting with the
    converter through the terminal or command prompt. It handles command-line
    argument parsing, user prompts, and text-based status display.

    Features:
        - Command-line argument parsing
        - Interactive user prompts for confirmation
        - Real-time status updates in the terminal
        - Error message display
        - File path validation and resolution
        - Format and category configuration

    The CLI interface supports various usage modes:
        - Direct command-line execution with arguments
        - Interactive mode with user prompts
        - Status monitoring with real-time updates
        - Error reporting with detailed messages

    Attributes:
        converter: Reference to the converter instance for operations
        docstring: Help text for command-line usage

    Example:
        >>> interface = ConverterInterfaceCLI()
        >>> converter = Converter(interface, processor, saver)
        >>> interface.run(converter)
    """

    docstring = DOCSTRING

    def __init__(self) -> None:
        self.converter: Converter | None = None

    def _print(self, msg: str) -> None:
        """Print message to stdout with proper handling.

        Args:
            msg: Message to print to the console
        """
        if sys.__stdout__:
            sys.__stdout__.write(msg + "\n")
            sys.__stdout__.flush()

    def convert(self, config: Config) -> None:
        """Initiate conversion process with user feedback.

        Validates the configuration and converter state before starting
        the conversion process. Displays appropriate error messages
        if validation fails.

        Args:
            config: Complete job configuration for the conversion

        Raises:
            InterfaceError: If converter is not initialized or config is invalid
        """
        msg = ""
        if not config:
            msg = "There is not config of converter."

        if self.converter is None:
            msg = "Converter is not initilazed"

        if msg:
            raise InterfaceError(msg)

        self.converter.convert(config)

    def run(self, converter) -> None:
        self.converter = converter
        config = self.setup()
        if yes_no():
            self.convert(config)

    def setup(self) -> Config:
        try:
            args = self._get_params(sys.argv)
        except ParamsError as err:
            self.display_common_info(self.docstring)
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

        format_from_name = Path(working_file_path).suffix.lstrip('.')
        format_from = format_service.get_source_format(format_from_name)

        available_targets = format_service.list_available_targets(format_from)
        if not available_targets:
            raise ParamsError(f"No conversion targets available for {format_from_name}")

        choices = {}
        self.display_common_info("Available conversion formats:")
        for indx, metadata in enumerate(available_targets, start=1):
            self.display_common_info(f"  {indx}. {metadata}")
            choices[str(indx)] = metadata

        while True:
            result_enter = input('Enter format number: ').strip()
            if result_enter in choices:
                break

            self.display_common_info(f"Invalid choice '{result_enter}'. Please enter a number from 1 to {len(choices)}")

        chosen_metadata = choices[result_enter]
        self.display_common_info(f"Selected: {chosen_metadata.display_name}")

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
        self.display_common_info(msg)
        return target_object, working_file_path

    def display_common_info(self, message: str, status: ConverterStatus | None = None) -> None:
        msg = ">>> INTERFACE"
        if status is not None:
            msg += f" [STATUS: {status}] \t|"
        msg += f" INFO: {message}"
        self._print(msg)

    def display_job_status(self, status: ConverterStatus) -> None:
        self._print(f">>> INTERFACE STATUS: {status}")

    def display_job_result(self, result: Path | str) -> None:
        self._print(f">>> INTERFACE RESULT: {result}")

    def display_job_id(self, job_id: str) -> None:
        self._print(f">>> INTERFACE JOB ID: {job_id}")

    def display_error(self, error: str, status: ConverterStatus) -> None:
        self.display_job_status(status)
        self._print(f">>> INTERFACE ERROR: {error}")
