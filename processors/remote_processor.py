from __future__ import annotations

import json
import os
import time
from pathlib import Path, PosixPath
from typing import TextIO, Generator

import requests
from config import APIConfig
from processors import ProcessorError
from interfaces.processor_interface import JobProcessor
from utils import get_full_file_path, save_data_from_response_to_dir

PROCESSOR_TIMEOUT = 3


class JobProcessorRemote:
    """Processor use remote API for convert files."""
    def __init__(self) -> None:
        self.api_config = APIConfig()
        self._status = "ready"

    def set_status(self, status: str) -> None:
        self._status = status

    def send_job(self, filename: str, options: None | dict = None) -> int:
        """Method to send data to processing and return job ID"""
        if options is None:
            options = {}

        with open(filename) as f:
            return self._send_job_data(filename, f, options)

    def get_job_status(self, job_id: int) -> Generator:
        while not self.is_completed():
            time.sleep(PROCESSOR_TIMEOUT)
            status = self._get_job_status(job_id)
            self.set_status(status["code"])
            yield self._status, status["info"]

    def is_completed(self) -> bool:
        return self._status == "completed"

    def _send_job_data(self, path_to_file: str, file_data: TextIO, options: dict) -> int:
        # get server`s options for convert
        job_id, server_url = self._get_job_id_from_server(self._set_data_options(options))
        url_upload = self._set_upload_url(job_id, server_url)

        # send file data to server
        self._send_file_to_server(url_upload, path_to_file, file_data)
        return job_id

    def _set_data_options(self, options: dict) -> str:
        """return json-like object of converter options"""
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

    def _get_job_id_from_server(self, options_data: str) -> tuple[int, str]:
        """sends request to create remote job

        options_data: json string with parameters target and category
        return: job server url and job id
        """
        response = requests.post(
            self.api_config.url,
            headers=self.api_config.get_header("main_header"),
            data=options_data,
            timeout=PROCESSOR_TIMEOUT,
        )
        data: dict = response.json()
        return data["id"], data["server"]

    @staticmethod
    def _set_upload_url(job_id: int, server_url: str) -> str:
        return f"{server_url}/upload-file/{job_id}"

    def _send_file_to_server(self, server_url: str, path_to_file: str, file_data: TextIO) -> dict:
        """sends file data to remote API"""
        response = requests.post(
            server_url,
            headers=self.api_config.get_header("cache_header"),
            files={"file": (path_to_file, file_data)},
            timeout=PROCESSOR_TIMEOUT,
        )

        return response.json().get("completed")

    def _get_job_status(self, job_id: int) -> dict:
        res = self._get_job_info(job_id)
        return res["status"]

    def get_job_result(self, job_id: int) -> str:
        return self._get_job_result(job_id)

    def _get_job_result(self, job_id: int) -> str:
        res = self._get_job_info(job_id)
        return res["output"][0]["uri"]

    def _get_job_info(self, job_id: int) -> dict:
        """sends request to server with unique id
        and return response with status code
        """
        response = requests.get(
            f"{self.api_config.url}/{job_id}",
            headers=self.api_config.get_header("main_header"),
            timeout=PROCESSOR_TIMEOUT,
        )

        res = response.json()
        self._check_errors(res)
        return res

    def _check_errors(self, data: dict) -> None:
        is_error = data["status"]["code"] == "error" or data["errors"]
        if not is_error:
            return

        msg = f"ERROR: {self._get_error_info(data)}"
        raise ProcessorError(msg)

    @staticmethod
    def _get_error_info(data: dict) -> list[str | None]:
        return [data["errors"] or data["status"]["code"]]

    def save_file(self, path_to_result: str, path_to_save: str | Path) -> str | PosixPath | Path:
        return self._save_from_url(path_to_result, path_to_save)

    def _save_from_url(self, url: str, sub_dir: str | Path = os.path.curdir) -> str | PosixPath | Path:
        """saves file form remote URL to directory"""
        filename = url.split("/")[-1] if url else ""
        full_path = get_full_file_path(filename, sub_dir)
        response = requests.get(url, stream=True)
        save_data_from_response_to_dir(full_path, response)
        return full_path
