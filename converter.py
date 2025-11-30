from __future__ import annotations

import traceback
import sys
import os
import io
import json

from functools import partial
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any

from config import ConverterStatus
from config import JobConfig as Config

from exceptions import ConverterError, handle_exception_chain, create_error_context


if TYPE_CHECKING:
    from collections.abc import Callable

    from interfaces.processor_interface import JobProcessor
    from interfaces.saver_interface import SaverProtocol
    from interfaces.ui_interface import UIProtocol
    from interfaces.worker_interface import Worker
    from config import Target


# TODO: implement functionality to add different converter formats
# TODO: implement saver class to replace logic of saving results with different sources
# TODO: maybe make save the result private and return as result the bytes instead of link to file
# because each processor can have different type of result link. Example:
# /home/doc/projects/convert/Mystetstvo_liubovi.fb2.mobi
# https://www16.online-convert.com/dl/web7/download-file/8d8cd6a8-eb1d-4171-afa3-ee447036fbf0/Mystetstvo_liubovi.mobi
class Converter:
    """Main orchestrator class that coordinates e-book conversion operations.

    The Converter class implements the core business logic for converting e-book files
    from one format to another. It follows the dependency injection pattern, accepting
    pluggable components for user interface, processing, saving, and concurrency.

    This class coordinates the entire conversion workflow:
    1. Validates configuration and file paths
    2. Sends conversion jobs to processors
    3. Monitors processing status and displays updates
    4. Retrieves and saves conversion results
    5. Handles errors and status notifications

    The class supports multiple processor types (local, Docker, remote), various
    user interfaces (CLI, GUI, web), different savers (local filesystem, cloud),
    and optional concurrent execution via workers.

    Attributes:
        interface: User interface implementation for displaying status and results
        processor: Processing implementation for handling conversion operations
        saver: Storage implementation for saving converted files
        worker: Optional worker for concurrent execution
        config: Current job configuration
        status: Current conversion status

    Example:
        >>> from converter import Converter
        >>> from processors.local_processor import LocalProcessor
        >>> from uis.cli_ui import ConverterInterfaceCLI
        >>> from savers.local_saver import LocalFileSaver
        >>>
        >>> converter = Converter(
        ...     interface=ConverterInterfaceCLI(),
        ...     processor=LocalProcessor(),
        ...     saver=LocalFileSaver()
        ... )
        >>> converter.convert(job_config)
    """

    def __init__(
        self,
        interface: UIProtocol,
        processor: JobProcessor,
        saver: SaverProtocol,
        worker: Worker | None = None,
    ) -> None:
        self.interface = interface
        self.processor = processor
        self.saver = saver
        self.worker = worker
        self.config: Any[None, Config] = None
        self.set_status(ConverterStatus.READY)

    def get_status(self) -> str:
        """Return current status of processor."""
        return self.status

    def set_status(self, status: ConverterStatus) -> None:
        self.status = status
        self.interface.display_job_status(self.status)

    def convert(self, config: Config) -> None:
        """Run processing the data to needed format."""
        self.set_status(ConverterStatus.PROCESSING)
        self.set_config(config)

        run_process = self.setup_converter_executor()
        run_process()

    def set_config(self, config: Config) -> None:
        """Set converter configuration."""
        self.config = config

    def setup_converter_executor(self) -> Callable:
        """Return Callable object to processing main flow."""
        executor = self._convert
        if self.worker:
            executor = partial(self.worker.execute, self._convert)
            self.worker.set_error_handler(self.error_handler)
        return executor

    def _convert(self) -> None:
        # validate config
        print(f"----- 1:")
        self.validate_config()

        print(f"----- 2:")
        # send file to processor
        job_id = self.send_job()
        print(f"----- 3: {job_id}")

        # check processing result and get it path
        result_file_name, source_data = self.get_result(job_id)
        print(f"----- 4: {result_file_name} {source_data}")

        # save result file
        if result_file_name:
            self.save(result_file_name, source_data)

        print(f"----- 5:")
        self.set_status(ConverterStatus.COMPLETED)

    def prepare_params(self, options) -> Target:
        return self.processor.prepare_params(options)

    def validate_config(self) -> None:
        """Run different type of covert validation.

        Raises:
            ConverterError: in case of issues with converting.
        """
        if not self.config or not self.config.get_config():
            error_msg = "Converter`s config was not set"
            raise ConverterError(error_msg)

    @staticmethod
    def validate_path(path_to_file: str) -> bool:
        """Validate path to file for converting.

        Args:
            path_to_file: sting path to open file.

        Returns:
            return True if all is right.

        Raises:
            ConverterError: raise error if path is not valid.
        """
        if not Path(path_to_file).is_file():
            msg = f"Invalid file path: {path_to_file}"
            raise ConverterError(msg)
        return True

    def get_file_path(self) -> str:
        """Return string path to target (file need to be converted)."""
        return self.config.path_to_file

    def get_job_options(self) -> dict:
        """Return the structure with main convert params."""
        return self.config.get_config()

    def send_job(self) -> int:
        """Send job data to processor. Return job ID"""
        # setup converter options
        path_to_file = self.get_file_path()
        print(f"----- send_job: {path_to_file=}")
        self.validate_path(path_to_file)
        options = self.get_job_options()

        # send main data to processing
        job_id = self.processor.send_job(path_to_file, options)

        # show job ID on interface
        self.interface.display_common_info(f"Job ID: {job_id}")

        return job_id

    def get_result(self, job_id: int) -> tuple(str, io.BytesIO):
        """Get job result from processor. Return path to converted file
        and bytes data in stream"""
        # check processing results as status to show info in user interface
        # NOTE: need to implement processing as generator to stream processor status
        processor_info = self.processor.get_job_status(job_id)
        for message in processor_info:
            self.interface.display_common_info(message, status=ConverterStatus.PROCESSING)

        # after end of processing data return the result as bytes data or Path to save file
        # NOTE: need to check different types of results
        #       (some processors returns path to save, other bytes)
        return self.processor.get_job_result(job_id)

    def error_handler(self, error: Exception) -> None:
        """Send error from converter to user interface."""
        if int(os.getenv('DEBUG')):
            error = create_error_context(error=error)

        self.set_status(ConverterStatus.FAILED)
        self.interface.display_error(f"Converter got an error: {error}", ConverterStatus.FAILED)

    def save(self, source_name: str, source_data: io.BytesIO) -> str | Path | PosixPath:
        """Save result of processing.

        This method now follows the open-closed principle by:
        1. Using the saver's setup method to configure saver-specific parameters
        2. Each saver implementation handles its own required parameters via setup()
        3. No need to modify this method when adding new saver types
        """
        # Setup saver with source path and destination from config
        self.saver.setup(
            source_name=source_name,
            source_data=source_data,
            destination_path=self.config.path_to_save,
        )
        result = self.saver.save()
        self.interface.display_job_result(result)
        return result
