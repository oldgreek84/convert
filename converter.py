import os
import json
import time

from typing import Tuple, Generator, Any, Protocol
from enum import Enum, auto

import requests

from utils import get_full_file_path
from config import JobConfig, ConverterConfig
from worker import WorkerProtocol, Worker4
from processor import JobProcessor, JobProcessorDummy
from ui import UIProtocol, DummyUI


class Converter:
    def __init__(
            self,
            ui: UIProtocol,
            processor: JobProcessor,
            worker: WorkerProtocol = None):
        self.ui = ui
        self.processor = processor
        self.worker = worker
        self._data = {}

    def convert(self):
        """converts the data to needed format. Save result"""

        self.worker.execute(self._convert)

    def _convert(self):
        self.ui.setup()

        # send file to processor
        job_id = self.send_job()

        # check processing result and get it path
        try:
            result = self.get_job(job_id)
        except ValueError as err:
            self.ui.display_job_status("error")
            self.ui.display_errors([str(err)])
            return False

        # save result file
        self.save(result)
        return result

    def send_job(self) -> str:
        """send job data for processing. Return job ID"""

        self.ui.display_job_status("ready")
        return self.processor.send_job_data()

    def get_job(self, job_id) -> str:
        """ get result job from processor"""

        while True:
            time.sleep(3)
            status = self.processor.get_job_status()
            result = self.processor.get_job_result(job_id)
            self.ui.display_job_status(status)
            if self.processor.is_completed():
                break
        return result

    def save(self, file_path):
        path = self.processor.save_file(file_path)
        self.ui.display_job_result(path)


def main() -> None:
    cli = DummyUI()
    worker = Worker4()
    processor = JobProcessorDummy()
    converter = Converter(cli, processor, worker)
    converter.convert()


if __name__ == '__main__':
    main()
