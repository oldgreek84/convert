import os
import time
import traceback

from pathlib import Path
from typing import Optional, Union
from functools import partial

from worker import WorkerProtocol
from processor import JobProcessor, ProcessorError
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

    def convert(self) -> bool:
        """converts the data to needed format. Save result"""

        try:
            worker_executor = partial(self.worker.execute, self._convert)
            executor = worker_executor if self.worker else self._convert
            self.worker.set_error_handler(self.error_handler)
            executor()
        except Exception as ex:
            self.ui.display_errors([f"some error {ex = }"])

    def _convert(self):
        # send file to processor
        job_id = self.send_job()

        # check processing result and get it path
        result = self.get_job(job_id)

        # save result file
        if result:
            self.save(result)

    def validate_path(self, path_to_file: str):
        """validate path to file for converting"""

        if not os.path.isfile(path_to_file):
            raise ValueError("invalid file path")
        return True

    def get_file_path(self):
        return self.config.path_to_file

    def get_job_options(self):
        return {
            "category": self.config.job_category,
            "target": self.config.job_target,
            "options": {},
        }

    def send_job(self) -> str:
        """send job data for processing. Return job ID"""

        path_to_file = self.get_file_path()
        self.validate_path(path_to_file)

        options = self.get_job_options()

        with open(path_to_file, "rb") as file_data:
            job_id = self.processor.send_job_data(path_to_file, file_data, options)

        self.ui.display_job_status(self.processor.get_job_status(job_id))
        self.ui.display_job_id(job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[Union[Path, str]]:
        """ get result job from processor"""

        while not self.processor.is_completed():
            time.sleep(3)
            try:
                status = self.processor.get_job_status(job_id)
                self.ui.display_job_status(status)
            except ProcessorError as ex_pe:
                error = f"MAIN: ERROR {ex_pe}"
                self.ui.display_errors([error])
                return False

        return self.processor.get_job_result(job_id)

    def error_handler(self, error):
        self.ui.display_errors([str(error)])

    def save(self, file_path: Optional[Union[Path, str]]) -> None:
        path = self.processor.save_file(file_path, self.config.path_to_save)
        self.ui.display_job_result(path)


def main():
    pass


if __name__ == '__main__':
    main()
