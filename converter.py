import sys
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
        self._data = {}

    def start(self):
        # TODO: redesign start method and work with UI
        if config := self.ui.run(self.processor):
            self.convert()

    def convert(self) -> bool:
        """converts the data to needed format. Save result"""

        try:
            worker_executor = partial(self.worker.execute, self._convert)
            executor = worker_executor if self.worker else self._convert
            executor()
        except Exception as ex:
            self.ui.display_errors([f"some error {ex = }"])
            print(traceback.print_exc())

    def _convert(self):
        # send file to processor
        job_id = self.send_job()

        # check processing result and get it path
        result = self.get_job(job_id)

        # save result file
        if result:
            self.save(result)

    def send_job(self) -> str:
        """send job data for processing. Return job ID"""

        job_id = self.processor.send_job_data()
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

        result = self.processor.get_job_result(job_id)
        return result

    def save(self, file_path: Optional[Union[Path, str]]) -> None:
        path = self.processor.save_file(file_path)
        self.ui.display_job_result(path)


def main():
    pass


if __name__ == '__main__':
    main()
