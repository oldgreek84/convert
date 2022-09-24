import os
import json
import time
from typing import Protocol, Tuple
from dataclasses import dataclass
import requests

from utils import get_full_file_path


@dataclass
class Target:
    target: str = "mobi"
    category: str = "ebook"


@dataclass
class JobConfig:
    target: Target
    path_to_file: str
    path_to_save: str


class JobProcessor(Protocol):
    def send_job_data(self):
        """send job data for processing"""

    def get_job_data(self):
        """get job data after processing"""


class ConverterConfig:
    """Docstring for UrlConverter:."""

    def __init__(self, api_key: str, api_url: str):
        """TODO: to be defined."""
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "main_header": {
                "cache-control": "no-cache",
                "content-type": "application/json",
                "x-oc-api-key": self.api_key,
            },
            "cache_header": {
                "cache-control": "no-cache", "x-oc-api-key": self.api_key},
        }

    def get_header(self, header_key: str):
        return self.headers[header_key]

    def set_header(self, key: str, data: dict):
        self.headers[key] = data


class JobProcessorRemote:
    def __init__(
            self, job_config: JobConfig,
            target: Target, converter_config: ConverterConfig):
        self.job_config = job_config
        self.target = target
        self.converter_config = converter_config

    def send_job_data(self) -> str:
        option_data = self._set_data_options()
        server_url, work_id = self._get_job_id_from_server(
            option_data)
        url_upload = self.set_upload_url(work_id, server_url)

        with open(self.job_config.path_to_file, "rb") as file_data:
            self._send_file_to_server(url_upload, file_data)
        return work_id

    def _set_data_options(self) -> str:
        """return jsonify convert options"""
        data = {
            "conversion": [
                {"category": self.target.category, "target": self.target.target}
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

    def convert(self):
        """
        main function create all resquests to remote server
        and save converted file to local directory
        """

        self.validate_path()
        work_id = self.send_job_data()

        uri_to_downloas_file = self.get_job_data(work_id)
        self.save_from_url(uri_to_downloas_file, self.job_config.path_to_save)

    def get_job_data(self, work_id: str) -> dict:
        status = self.get_job_status(work_id)
        if error := status.get("error"):
            raise ValueError(error)
        return status.get("result")

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

    def save_from_url(self, url: str, sub_dir: str = os.path.curdir) -> str:
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
