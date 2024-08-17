from __future__ import annotations

import sys
from pathlib import Path

from config import JobConfig, Target
from converter import Converter
from interfaces import Config
from uis import DOCSTRING, InterfaceError
from utils import ParamsError, get_path, parse_command


def yes_no(message="Do you want to run convert[N/y]?: "):
    return input(message).lower() in {"y", "yes"}


class ConverterInterfaceCLI:
    """Command line interface for converter to use in terminal."""

    docstring = DOCSTRING

    def __init__(self) -> None:
        self.converter: None | Converter = None

    def convert(self, config: Config) -> None:
        if not config:
            msg = "There is not config of converter."
            raise InterfaceError(msg)
        if self.converter is None:
            msg = "Converter is not initilazed"
            raise InterfaceError(msg)
        self.converter.convert(config)

    def run(self, converter) -> None:
        self.converter = converter
        try:
            config = self.setup()
            if yes_no():
                self.convert(config)
        except Exception as ex:
            self.display_error(f"Something wrong: {ex}")

    def setup(self) -> Config:
        try:
            args = self._get_params(sys.argv)
        except ParamsError as err:
            self.display_common_info(self.docstring)
            msg = "There is not params to set"
            raise ParamsError(msg) from err

        return JobConfig(*args)

    def _get_params(self, args: list) -> tuple:
        if len(args) == 1:
            msg = f"Not enough params {args}"
            raise ParamsError(msg)

        data_settings = parse_command()
        if data_settings.get("-path"):
            working_file_path = data_settings["-path"]
        elif data_settings.get("-name"):
            working_file_path = get_path(data_settings["-name"])
        else:
            working_file_path = sys.argv[1]

        working_target = data_settings.get("-t", "mobi")
        working_category = data_settings.get("-cat", "ebook")

        target_object = Target(working_target, working_category)

        msg = f"\n{'=' * 80}\nPARAMS:\
                \n\t{working_file_path = }\
                \n\t{working_target = }\
                \n\t{working_category = }\
                \n\t{target_object = }\
                \n{'=' * 80}"
        self.display_common_info(msg)
        return target_object, working_file_path

    def display_common_info(self, message: str, status: str | None = None) -> None:
        msg = ">>> INTERFACE"
        if status is not None:
            msg += f" [STATUS: {status}] \t|"
        msg += f" INFO: {message}"
        print(msg)

    def display_job_status(self, status: str) -> None:
        print(f">>> INTERFACE STATUS: {status}")

    def display_job_result(self, result: Path | str) -> None:
        print(f">>> INTERFACE RESULT: {result}")

    def display_job_id(self, job_id: str) -> None:
        print(f">>> INTERFACE JOB ID: {job_id}")

    def display_error(self, error: str) -> None:
        self.display_job_status("error")
        print(f">>> INTERFACE ERROR: {error}")
