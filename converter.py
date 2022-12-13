import os
import time

from pathlib import Path
from typing import Optional, Union, Callable
from functools import partial

from worker import WorkerProtocol
from processor import JobProcessor
from ui import UIProtocol
from config import JobConfig


class ConvertError(Exception):
    """own converter error"""


class Converter:
    def __init__(
            self,
            ui: UIProtocol,
            processor: JobProcessor,
            worker: WorkerProtocol = None) -> None:
        self.ui = ui
        self.processor = processor
        self.worker = worker
        self.config: JobConfig = None

    def set_config(self, config: JobConfig) -> None:
        self.config = config

    def convert(self) -> None:
        """converts the data to needed format. Save converted file"""

        # TODO: processing error handler if worker was not setted
        try:
            executor = self.set_converter_executor()
            executor()
        except Exception as ex:
            self.ui.display_errors([f"Converter had an error: {ex}"])

    def set_converter_executor(self) -> Callable:
        executor = self._convert
        if self.worker:
            executor = partial(self.worker.execute, self._convert)
            self.worker.set_error_handler(self.error_handler)
        return executor

    def _convert(self) -> None:
        # validate config
        self.validate_config()

        # send file to processor
        job_id = self.send_job()

        # check processing result and get it path
        result = self.get_job(job_id)

        # save result file
        if result:
            self.save(result, self.config.path_to_save)

    def validate_config(self) -> None:
        if not self.config or not self.config.get_config():
            raise ConvertError("Converter`s config was not set")

    def validate_path(self, path_to_file: str) -> bool:
        """validate path to file for converting"""

        if not os.path.isfile(path_to_file):
            raise ValueError("Invalid file path")
        return True

    def get_file_path(self) -> str:
        return self.config.path_to_file

    # TODO: implement functionality to add different converter formats
    def get_job_options(self) -> dict:
        return self.config.get_config()

    def send_job(self) -> str:
        """send job data to processor. Return job ID"""

        path_to_file = self.get_file_path()
        self.validate_path(path_to_file)

        options = self.get_job_options()
        print(f"TEST: {options = }")

        with open(path_to_file, "rb") as file_data:
            job_id = self.processor.send_job_data(path_to_file, file_data, options)

        self.ui.display_job_id(job_id)
        self.ui.display_job_status(self.processor.get_job_status(job_id))
        return job_id

    def get_job(self, job_id: str) -> Optional[Union[Path, str]]:
        """ get job result from processor. Return path to converted file"""

        while not self.processor.is_completed():
            time.sleep(3)
            status = self.processor.get_job_status(job_id)
            self.ui.display_job_status(status)

        return self.processor.get_job_result(job_id)

    def error_handler(self, error: Exception) -> None:
        self.ui.display_errors([str(error)])

    # TODO: maybe replace saver to converter
    def save(
            self, file_path: Optional[Union[Path, str]],
            path_to_save: Optional[Union[Path, str]]) -> Path:
        path = self.processor.save_file(file_path, path_to_save)
        self.ui.display_job_result(path)
        return path
