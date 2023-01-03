from typing import Optional, Union, Any
from pathlib import Path

import requests

from processor import JobProcessor, ProcessorError
from config import JobConfig


class DummyWorker:
    def execute(self) -> None:
        pass

    def set_error_handler(self, error: Exception) -> None:
        pass


class DummyUI:
    def __init__(self):
        self.converter = None

    def run(self, converter) -> None:
        print(f"DUMMY UI: RUN {converter}")

    def setup(self) -> JobConfig:
        print("DUMMY UI: SETUP")

    def convert(self) -> None:
        print("DUMMY UI: CONVERT")

    def display_job_status(self, status):
        print(f"DUMMY UI: display status {status}")

    def display_job_result(self, result):
        print(f"DUMMY UI: display result {result}")

    def display_job_id(self, job_id):
        print(f"DUMMY UI: display ID {job_id}")

    def display_errors(self, errors: list):
        for error in errors:
            print(f"DUMMY UI: ERROR: {error}")


class DummyJobProcessor(JobProcessor):
    def is_completed(self) -> bool:
        """return True if job is completed"""

    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        """send job data for processing. Return job ID"""

    def get_job_status(self, job_id: str) -> Any:
        """return job status by job ID"""

    def get_job_result(self, job_id: str) -> Optional[Union[Path, str]]:
        """get job data by job ID after processing and return it"""

    def save_file(
            self,
            path_to_result: Optional[Union[str, Path]],
            path_to_save: Optional[Union[str, Path]]) -> str:
        """save job result after processing and return path to file"""


class LocalTestJobProcessor(JobProcessor):
    dummy_msg = None
    dummy_url = "http://localhost:5000"
    dummy_response = {
        "message": dummy_msg,
        "output": None if dummy_msg != 'completed' else [{"uri": "http://uri_for_download"}],
        "status": {
            "code": dummy_msg,
            "status_code": 200,
            "info": None if dummy_msg != "error" else "it`s error message!!!"},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = "ready"
        self._data = {}
        self._result = None

    def is_completed(self) -> bool:
        return self._status == "completed"

    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        # send pramas to server
        print("--- PROCESSOR: Job was sent")
        print(f"--- PROCESSOR: PARAMS:  {path_to_file = } {options = }")
        res = requests.post(f"{self.dummy_url}", json={"conversion": options})
        work_id = res.json()["id"]
        self._data["id"] = work_id

        # send data to server
        print("--- PROCESSOR: Data was sent")
        res = requests.post(
            f"{self.dummy_url}/test-server/upload-file/test_ID",
            files={"file": file_data})
        print(f"TEST DUMMY: {res.json()['completed'] = }")
        return work_id

    def get_job_status(self, job_id: str) -> str:
        if not self.is_completed():
            self._status = self._get_job_status(job_id)
        return self._status

    def _get_job_status(self, job_id: str = "test_ID") -> dict:
        res = self._get_converted_file_status_data(job_id)
        status = res["status"]["code"]

        print(f"TEST : {status = }")
        return status

    def get_job_result(self, job_id):
        if self.is_completed():
            self._result = self._get_job_result(job_id)
        return self._result

    def _get_job_result(self, job_id: str = "test_ID"):
        res = self._get_converted_file_status_data(job_id)

        result = res["info"][0]["uri"]

        print(f"TEST : {result = }")
        return result

    def _get_converted_file_status_data(self, job_id: str):
        response = requests.get(
            f"{self.dummy_url}/{job_id}",
        )

        print(f"TEST:  {response.text = }")
        res = response.json()
        print(f"TEST: {res = }")
        self._check_errors(res)
        return res

    def _check_errors(self, data: dict):
        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            raise ProcessorError(f"ERROR: {self._get_error_info(data)}")

    def _get_error_info(self, data: dict):
        return [data["errors"] or data["status"]["code"]]

    def save_file(
            self,
            path_to_result: Optional[Union[str, Path]],
            path_to_save: Optional[Union[str, Path]]) -> str:
        print(f"--- DUMMY --: file {path_to_result} was saved")
        full_path = f"path/to/{path_to_save}"
        self._data["full_path"] = full_path
        return full_path
