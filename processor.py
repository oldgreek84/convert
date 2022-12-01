import os
import json
import time

from abc import abstractmethod, ABC
from typing import Tuple, Generator, Any
from enum import Enum, auto

import requests

from utils import get_full_file_path
from config import JobConfig, ConverterConfig
from worker import WorkerProtocol, Worker4


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
    def get_job_status(self) -> Any:
        """return job status"""

    @abstractmethod
    def send_job_data(self) -> str:
        """send job data for processing. Return job ID"""

    @abstractmethod
    def get_job_result(self, job_id: str) -> str:
        """get job data after processing and return it"""

    @abstractmethod
    def save_file(self, path_for_save: str) -> str:
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

    def is_completed(self) -> bool:
        return self._status in ["completed", "error"]

    def get_job_status(self) -> str:
        return self._status

    def send_job_data(self) -> str:
        print("--- PROCESSOR: Data was sent")
        res = requests.get(f"{self.dummy_url}/for_send/")
        work_id = res.json()["work_id"]
        self._data["work_id"] = work_id
        return work_id

    def get_job_result(self, job_id: str) -> dict:
        status = self._get_job_status(job_id)
        if error := status.get("error"):
            raise ValueError(error)
        result = status.get("result")
        self._data["uri_to_downloas_file"] = result
        return result

    def _get_job_status(self, job_id):
        res = requests.get("http://localhost:5000/", json={"job_id": job_id})
        result, status = res, res.json()["status"]["code"]

        self._status = status

        if status != "completed":
            return {"error": result.json()["status"]["info"]}
        return {"result": result.json()["output"][0]["uri"]}

    def prepare_result(self, raw_data: requests.Response):
        res = None
        try:
            data = raw_data.json()
            res = data["status"]["info"] or data["output"][0]["uri"]
        except Exception as ex:
            print(f"--- PROCESSOR ERROR: {ex = }")
        return res

    def save_file(self, path_to_file="path/to/file"):
        print(f"--- DUMMY --: file {path_to_file} was saved")
        full_path = "path/to/saved"
        self._data["full_path"] = full_path
        return full_path


class JobProcessorRemote(JobProcessor):
    def __init__(self, job_config: JobConfig, woker: WorkerProtocol):
        self.job_config = job_config
        self.converter_config = ConverterConfig()
        self._data = {}
        self._status = "ready"

    # def convert(self):
    #     """
    #     main function create all resquests to remote server
    #     and save converted file to local directory
    #     """
    #     self._convert()

    # def _convert(self):

    #     self.validate_path()
    #     work_id = self.send_job_data()

    #     uri_to_downloas_file = self.get_job_result(work_id)
    #     full_path = self.save_file(self.job_config.path_to_save, uri_to_downloas_file)

    #     self._data["work_id"] = work_id
    #     self._data["uri_to_downloas_file"] = uri_to_downloas_file
    #     self._data["full_path"] = full_path

    #     return full_path

    def validate_path(self):
        """validate path to file for converting"""

        if not os.path.isfile(self.job_config.path_to_file):
            raise ValueError("invalid file path")
        return True

    def send_job_data(self) -> str:
        # get server`s options for convert
        option_data = self._set_data_options()
        server_url, work_id = self._get_job_id_from_server(
            option_data)
        url_upload = self._set_upload_url(work_id, server_url)

        # send file data to server
        with open(self.job_config.path_to_file, "rb") as file_data:
            res = self._send_file_to_server(url_upload, file_data)
            print(f"REMOTE: {res = }")
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
        work_id = response.json()["id"]
        server = response.json()["server"]
        return server, work_id

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

    def get_job_result(self, job_id: str) -> dict:
        status = self._get_job_status(job_id)
        if error := status.get("error"):
            raise ValueError(error)
        return status.get("result")

    def _get_job_status(self, work_id: str) -> dict:
        res_status, status = False, False
        while True:
            time.sleep(3)
            res_status, status = self._get_status_convert_file(work_id)
            if status != "processing":
                break

        self._status = status

        if status != "completed":
            return {"error": res_status.json()["status"]["info"]}
        return {"result": res_status.json()["output"][0]["uri"]}

    def _get_status_convert_file(self, work_id: str) -> Tuple[requests.Response, str]:
        """sends request to server with unique id
        and return response with status code
        """

        response = requests.get(
            f"{self.converter_config.api_url}/{work_id}",
            headers=self.converter_config.get_header("main_header"),
        )

        status_code = response.json()["status"]["code"]
        return response, status_code

    # TODO: create PATH saver class
    def save_file(self, path_to_save, uri_to_downloas_file):
        return self._save_from_url(uri_to_downloas_file, path_to_save)

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


class ApiProcessor:
    def __init__(self, file_data: bytes, job_config: dict):
        self.converter_config = ConverterConfig()
        self.job_config = job_config
        self.file_data = file_data

    # def send_job_data(self) -> str:
    #     option_data = self._set_data_options()
    #     server_url, work_id = self._get_job_id_from_server(
    #         option_data)
    #     url_upload = self.set_upload_url(work_id, server_url)

    #     with open(self.job_config.path_to_file, "rb") as file_data:
    #         self._send_file_to_server(url_upload, file_data)
    #     return work_id

    def _set_data_options(self) -> str:
        """return jsonify convert options"""
        data = {
            "conversion": [
                {
                    "category": self.job_config["category"],
                    "target": self.job_config["target"]
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
        work_id = response.json()["id"]
        server = response.json()["server"]
        return server, work_id

    def _send_file_to_server(self, server_url: str, file_data: bytes) -> dict:
        """sends bytes file data to remote API"""

        response = requests.post(
            server_url,
            headers=self.converter_config.get_header("cache_header"),
            files={"file": (self.job_config["path_to_file"], file_data)},
        )
        return response.json().get("completed")

    def set_upload_url(self, work_id: str, server_url: str) -> str:
        return f"{server_url}/upload-file/{work_id}"

    def get_job_result(self, work_id: str):
        res_status, status = self._get_status_convert_file(work_id)

        if status != "completed":
            return {"error": res_status.json()["status"]["info"]}
        return {"result": res_status.json()["output"][0]["uri"]}

    def _get_status_convert_file(self, work_id: str):
        """sends request to server with unique id
        and return response with status code
        """

        response = requests.get(
            f"{self.converter_config.api_url}/{work_id}",
            headers=self.converter_config.get_header("main_header"),
        )

        status_code = response.json()["status"]["code"]
        return response, status_code


if __name__ == '__main__':
    test = JobProcessorDummy(JobConfig, worker=Worker4())
