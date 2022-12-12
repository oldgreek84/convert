import os
import json

from abc import abstractmethod, ABC
from pathlib import Path
from typing import Tuple, Any, Optional, Union

import requests

from utils import get_full_file_path, coroutine
from config import APIConfig


class ProcessorError(Exception):
    """common except type for errors"""


class JobProcessor(ABC):
    def __init__(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def is_completed(self) -> bool:
        """return True if job is completed"""

    @abstractmethod
    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        """send job data for processing. Return job ID"""

    @abstractmethod
    def get_job_status(self, job_id: str) -> Any:
        """return job status by job ID"""

    @abstractmethod
    def get_job_result(self, job_id: str) -> Optional[Union[Path, str]]:
        """get job data by job ID after processing and return it"""

    @abstractmethod
    def save_file(
            self,
            path_to_result: Optional[Union[str, Path]],
            path_to_save: Optional[Union[str, Path]]) -> str:
        """save job result after processing and return path to file"""


class JobProcessorRemote(JobProcessor):
    # TODO: refacotor to remove self._status, self._result
    # and replace its to return value
    # we want replacing some details
    def __init__(self) -> None:
        self.api_config = APIConfig()
        self._status = "ready"
        self._result = None

    def is_completed(self) -> bool:
        return self._status == "completed"

    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        # get server`s options for convert
        work_id, server_url = self._get_job_id_from_server(
            self._set_data_options(options))
        url_upload = self._set_upload_url(work_id, server_url)

        # send file data to server
        self._send_file_to_server(url_upload, path_to_file, file_data)
        return work_id

    def _set_data_options(self, options: dict) -> str:
        """return jsonify convert options"""

        data = {
            "conversion": [
                {
                    "category": options.pop("category", None),
                    "target": options.pop("target", None),
                    **options,
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
            self.api_config.url,
            headers=self.api_config.get_header("main_header"),
            data=data
        )
        data = response.json()
        return data["id"], data["server"]

    def _set_upload_url(self, work_id: str, server_url: str) -> str:
        return f"{server_url}/upload-file/{work_id}"

    def _send_file_to_server(
            self, server_url: str, path_to_file: str, file_data: bytes) -> dict:
        """sends bytes file data to remote API"""

        response = requests.post(
            server_url,
            headers=self.api_config.get_header("cache_header"),
            files={"file": (path_to_file, file_data)},
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
            f"{self.api_config.url}/{work_id}",
            headers=self.api_config.get_header("main_header"),
        )

        res = response.json()
        self._check_errors(res)
        return res

    def _check_errors(self, data: dict) -> None:
        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            raise ProcessorError(f"ERROR: {self._get_error_info(data)}")

    def _get_error_info(self, data: dict) -> Optional[Union[str, None]]:
        return [data["errors"] or data["status"]["code"]]

    # TODO: create SAVER class
    def save_file(
            self,
            path_to_result: Optional[Union[str, Path]],
            path_to_save: Optional[Union[str, Path]]) -> str:
        return self._save_from_url(path_to_result, path_to_save)

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
