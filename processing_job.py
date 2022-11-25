import os
import json
import time
from typing import Tuple
from abc import abstractmethod, ABC
import requests

from utils import get_full_file_path
from config import JobConfig, ConverterConfig


class JobProcessor(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def send_job_data(self) -> str:
        """send job data for processing. Return job ID"""

    @abstractmethod
    def get_job_data(self, job_id: str) -> str:
        """get job data after processing"""

    @abstractmethod
    def convert(self) -> str:
        """converts the data to needed format. Save result"""

    @abstractmethod
    def save_file(self, path_to_save: str, *args) -> str:
        """save result and return path to result"""


class JobProcessorDummy(JobProcessor):
    def __init__(self, job_config, *args, **kwargs):
        self.job_config = job_config
        super().__init__(*args, **kwargs)

    def send_job_data(self):
        print("Data was sent")
        return "test id"

    def get_job_data(self, job_id: str):
        print("Data was got")

    def convert(self):
        print("Data was converted")

    def save_file(self, path_to_save, *args):
        print("file was saved")
        return "path/to/file"


class JobProcessorRemote(JobProcessor):
    def __init__(
            self,
            job_config: JobConfig,
            converter_config: ConverterConfig):
        self.job_config = job_config
        self.converter_config = converter_config
        self._data = None

    def send_job_data(self) -> str:
        option_data = self._set_data_options()
        server_url, work_id = self._get_job_id_from_server(
            option_data)
        url_upload = self.set_upload_url(work_id, server_url)

        with open(self.job_config.path_to_file, "rb") as file_data:
            self._send_file_to_server(url_upload, file_data)
        return work_id

    def get_job_data(self, job_id: str) -> dict:
        status = self.get_job_status(job_id)
        if error := status.get("error"):
            raise ValueError(error)
        return status.get("result")

    def convert(self):
        """
        main function create all resquests to remote server
        and save converted file to local directory
        """

        self.validate_path()
        work_id = self.send_job_data()

        uri_to_downloas_file = self.get_job_data(work_id)
        return self.save_file(self.job_config.path_to_save, uri_to_downloas_file)

    # TODO: create PATH saver class
    def save_file(self, path_to_save: str, uri_to_downloas_file: str):
        return self._save_from_url(uri_to_downloas_file, path_to_save)

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

    def _send_file_to_server(self, server_url: str, file_data: bytes) -> dict:
        """sends bytes file data to remote API"""

        response = requests.post(
            server_url,
            headers=self.converter_config.get_header("cache_header"),
            files={"file": (self.job_config.path_to_file, file_data)},
        )
        return response.json().get("completed")

    def set_upload_url(self, work_id: str, server_url: str) -> str:
        return f"{server_url}/upload-file/{work_id}"

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

    def get_job_status(self, work_id: str):
        res_status, status = False, False
        while True:
            time.sleep(3)
            res_status, status = self._get_status_convert_file(work_id)
            if status != "processing":
                break

        if status != "completed":
            return {"error": res_status.json()["status"]["info"]}
        return {"result": res_status.json()["output"][0]["uri"]}

    def validate_path(self):
        if not os.path.isfile(self.job_config.path_to_file):
            raise ValueError("invalid file path")
        return True

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
