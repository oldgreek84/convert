import os
import json
import time

from abc import abstractmethod, ABC
from pathlib import Path
from typing import Tuple, Any, Optional, Union
from enum import Enum, auto

import requests

from utils import get_full_file_path, coroutine
from config import ConverterConfig


class ProcessorError(Exception):
    """common except type for errors"""


class Status(Enum):
    OK = auto()
    ERROR = auto()
    COMPLETED = auto()

    def is_correc(self):
        return self.OK


class JobProcessor(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_completed(self) -> bool:
        """return True if job is completed"""

    @abstractmethod
    def send_job_data(self) -> str:
        """send job data for processing. Return job ID"""

    @abstractmethod
    def get_job_status(self, job_id: str) -> Any:
        """return job status"""

    @abstractmethod
    def get_job_result(self, job_id: str) -> Optional[Union[Path, str]]:
        """get job data after processing and return it"""

    @abstractmethod
    def save_file(self, path_to_result: Optional[Union[str, Path]]) -> str:
        """save job result after processing and return path to file"""


class JobProcessorDummy(JobProcessor):
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
        self.errors = []

    def is_completed(self) -> bool:
        return self._status == "completed"

    def send_job_data(self) -> str:
        # TODO: set config
        # send pramas to server
        job_config = {}
        print("--- PROCESSOR: Job was sent")
        res = requests.post(f"{self.dummy_url}", json={"conversion": job_config})
        work_id = res.json()["id"]
        self._data["id"] = work_id

        # send data to server
        print("--- PROCESSOR: Data was sent")
        data = b""
        res = requests.post(
            f"{self.dummy_url}/test-server/upload-file/test_ID", files={"file": data})
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

    def save_file(self, path_to_result: Optional[Union[str, Path]] = "path/to/file") -> str:
        print(f"--- DUMMY --: file {path_to_result} was saved")
        full_path = "path/to/saved"
        self._data["full_path"] = full_path
        return full_path


class JobProcessorRemote(JobProcessor):
    # TODO: should improve converter config
    def __init__(self):
        self.job_config = None
        self.converter_config = ConverterConfig()
        self._status = "ready"
        self._result = None

    def is_completed(self) -> bool:
        return self._status == "completed"

    def validate_path(self):
        """validate path to file for converting"""

        if not os.path.isfile(self.job_config.path_to_file):
            raise ValueError("invalid file path")
        return True

    def send_job_data(self) -> str:
        self.validate_path()

        # get server`s options for convert
        work_id, server_url = self._get_job_id_from_server(
            self._set_data_options())
        url_upload = self._set_upload_url(work_id, server_url)

        # send file data to server
        with open(self.job_config.path_to_file, "rb") as file_data:
            self._send_file_to_server(url_upload, file_data)
        return work_id

    def _set_data_options(self) -> str:
        """return jsonify convert options"""

        data = {
            "conversion": [
                {
                    "category": self.job_config.target.category,
                    "target": self.job_config.target.target
                }
            ]
        }
        return json.dumps(data)

    def _get_job_id_from_server(self, data: str) -> Tuple[str, str]:
        """
        sends request to create remote job
        data: json string with parameters target and category
        return: job server url and job id
        """

        response = requests.post(
            self.converter_config.api_url,
            headers=self.converter_config.get_header("main_header"),
            data=data
        )
        data = response.json()
        return data["id"], data["server"]

    def _set_upload_url(self, work_id: str, server_url: str) -> str:
        return f"{server_url}/upload-file/{work_id}"

    def _send_file_to_server(self, server_url: str, file_data: bytes) -> dict:
        """sends bytes file data to remote API"""

        response = requests.post(
            server_url,
            headers=self.converter_config.get_header("cache_header"),
            files={"file": (self.job_config.path_to_file, file_data)},
        )

        return response.json().get("completed")

    def get_job_status(self, job_id: str) -> str:
        if not self.is_completed():
            self._status = self._get_job_status(job_id)
        return self._status

    def _get_job_status(self, work_id: str) -> dict:
        res = self._get_job_info(work_id)
        return res["status"]["code"]

    def get_job_result(self, job_id: str) -> Optional[Union[Path, str]]:
        if self.is_completed():
            self._result = self._get_job_result(job_id)
        return self._result

    def _get_job_result(self, job_id: str) -> Optional[Union[Path, str]]:
        res = self._get_job_info(job_id)
        return res["output"][0]["uri"]

    def _get_job_info(self, work_id: str) -> dict:
        """sends request to server with unique id
        and return response with status code
        """

        response = requests.get(
            f"{self.converter_config.api_url}/{work_id}",
            headers=self.converter_config.get_header("main_header"),
        )

        res = response.json()
        self._check_errors(res)
        return res

    def _check_errors(self, data: dict):
        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            raise ProcessorError(f"ERROR: {self._get_error_info(data)}")

    def _get_error_info(self, data: dict):
        return [data["errors"] or data["status"]["code"]]

    def prepare_result(self, data: dict) -> str:
        """
        remote api response
        {
            "status": {"code": "str", "info": "str"},
            "errors": [],
            "info": [],
        }
        """
        try:
            res = data.json()
        except Exception:
            return False, "error"

        status_code = res["status"]["code"]
        result = res['info'][0]["uri"] if res['info'] else res['status']['info']
        return result, status_code

    # TODO: create SAVER class
    def save_file(self, path_to_result: Optional[Union[str, Path]]) -> str:
        return self._save_from_url(path_to_result, self.job_config.path_to_save)

    def _save_from_url(self, url: str, sub_dir: str = os.path.curdir) -> str:
        """saves file form remote URL to directory"""

        filename = url.split("/")[-1]
        full_path = get_full_file_path(filename, sub_dir)
        response = requests.get(url, stream=True)
        self.save_data_from_response_to_dir(full_path, response)
        return full_path

    def save_data_from_response_to_dir(
        self, file_path: str, response: requests.Response, bufsize: int = 1024
    ):
        """save file from response object to dir"""

        with open(file_path, "wb") as opened_file:
            for part in response.iter_content(bufsize):
                opened_file.write(part)


@coroutine
def main_loop():
    try:
        while True:
            res = (yield)
            print(res)
    except GeneratorExit:
        print("closing...")


def main():
    test = JobProcessorDummy()
    job_id = test.send_job_data()
    print(f"MAIN: {job_id = }")

    while not test.is_completed():
        time.sleep(3)
        try:
            status = test.get_job_status(job_id)
            print(f"MAIN: {status = }")
            print(f"MAIN: {test.is_completed() = }")
        except ProcessorError as pe_ex:
            print(f"MAIN: ERROR {pe_ex}")
            return False

    result = test.get_job_result(job_id)
    print(f"MAIN: {result = }")


if __name__ == '__main__':
    main()
