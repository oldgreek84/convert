from __future__ import annotations

import io
import json
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TextIO

import requests

from interfaces.processor_interface import JobProcessor
from processors import ProcessorError
from src.config import ConverterStatus
from src.exceptions import APIConfigError

if TYPE_CHECKING:
    from collections.abc import Generator

PROCESSOR_TIMEOUT = 3
SUCCESS_CODE = 200


@dataclass
class ApiStatus:
    status_code: int
    info: dict
    job_id: int | str
    status: ConverterStatus


class GenericAPIServiceInterface:
    def get_options(self, key):
        raise NotImplementedError

    def send_job(self, path_to_file, file_data: TextIO, options: dict):
        raise NotImplementedError

    def get_job_status(self, job_id):
        raise NotImplementedError

    def get_job_result(self, job_id):
        raise NotImplementedError

    def prepare_result(self, result):
        raise NotImplementedError


# TODO: add api registry
class ApiServiceCur(GenericAPIServiceInterface):
    def __init__(self, token=None, url=None):
        self.status_options = {"timeout": PROCESSOR_TIMEOUT}
        self.token = token or os.environ.get("API_KEY")
        self.url = url or os.environ.get("CONVERTER_URL")
        self.headers = {
            "main_header": {
                "cache-control": "no-cache",
                "content-type": "application/json",
                "x-oc-api-key": self.token,
            },
            "cache_header": {"cache-control": "no-cache", "x-oc-api-key": self.token},
        }

    @property
    def timeout(self):
        return self.get_options("timeout")

    def get_options(self, key):
        if self.status_options.get(key):
            return self.status_options[key]

        return getattr(self, key, None)

    def get_header(self, key):
        return self.headers.get(key, {})

    def send_job(self, path_to_file: str, file_data: TextIO, options: dict):
        data = {
            "conversion": [
                {
                    "category": options.pop("category", None),
                    "target": options.pop("target", None),
                    **options,
                }
            ]
        }

        response = requests.post(
            self.url,
            headers=self.get_header("main_header"),
            data=json.dumps(data),
            timeout=PROCESSOR_TIMEOUT,
        )

        data: dict = response.json()
        job_id, server_url = data["id"], data["server"]
        upload_url = f"{server_url}/upload-file/{job_id}"

        response = requests.post(
            upload_url,
            headers=self.get_header("cache_header"),
            files={"file": (path_to_file, file_data)},
            timeout=PROCESSOR_TIMEOUT,
        )

        return job_id

    def get_job_status(self, job_id):
        response = requests.get(
            f"{self.url}/{job_id}",
            headers=self.get_header("main_header"),
            timeout=PROCESSOR_TIMEOUT,
        )

        data = response.json()

        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            msg = f"ERROR: {self._get_error_info(data)}"
            raise ProcessorError(msg)

        codes_map = {
            "ready": ConverterStatus.READY,
            "completed": ConverterStatus.COMPLETED,
            "processing": ConverterStatus.PROCESSING,
            "error": ConverterStatus.FAILED,
        }
        con_status = codes_map.get(data["status"]["code"], ConverterStatus.FAILED)
        self._status = con_status
        return ApiStatus(response.status_code, data["status"]["info"], job_id, con_status)

    def get_job_result(self, job_id):
        response = requests.get(
            f"{self.url}/{job_id}",
            headers=self.get_header("main_header"),
            timeout=PROCESSOR_TIMEOUT,
        )

        data = response.json()
        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            msg = f"ERROR: {self._get_error_info(data)}"
            raise ProcessorError(msg)

        return data["output"][0]["uri"]

    def prepare_result(self, result):
        url = result
        filename = url.split("/")[-1] if url else ""
        try:
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            return filename, io.BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None, None


class ApiAdapter:
    def __init__(self, service: GenericAPIServiceInterface):
        self._service = service
        self.max_retrises = 3

    def setup(self, **kwargs) -> None:
        pass

    def prepare_options(self, format_options: dict) -> dict:
        return dict(format_options)

    def send_job(self, file_name: str, file_data: io.IOBase, options: dict) -> int | str:
        return self._service.send_job(file_name, file_data, options)

    def get_options(self, key: Any, default: Any | None = None) -> Any:
        try:
            return self._service.get_options(key)
        except KeyError:
            return default

    def get_status(self, job_id: int | str) -> ApiStatus:
        return self._service.get_job_status(job_id)

    def get_job_result(self, job_id: int | str) -> tuple(str, io.BytesIO):
        result = self._service.get_job_result(job_id)
        return self._service.prepare_result(result)


# TODO: make options maybe as dataclass or separated class of format
# because in this case options is a params to convert
class GenericRemoteProcessor(JobProcessor):
    def __init__(self, service, init=False):
        self.api_adapter = ApiAdapter(service)
        self._status = ConverterStatus.READY

        if init:
            self.setup()

    def setup(self):
        if not self.api_adapter:
            msg = "API service is not setup."
            raise APIConfigError(msg)

        self.api_adapter.setup()

    def send_job(self, filename: str, format_options: dict | None = None) -> int:
        if format_options is None:
            format_options = {}

        options = self.api_adapter.prepare_options(format_options)

        with open(filename) as file_obj:
            return self.api_adapter.send_job(filename, file_obj, options)

    def get_job_status(self, job_id: int) -> Generator:
        result = None
        while not self.is_completed(result):
            time.sleep(self.api_adapter.get_options("timeout"))
            result: ApiStatus = self.api_adapter.get_status(job_id)
            self.set_status(result.status)
            yield result.info

    def get_job_result(self, job_id: int) -> tuple(str, io.BytesIO):
        return self.api_adapter.get_job_result(job_id)

    def set_status(self, status: ConverterStatus) -> None:
        self._status = status

    def is_completed(self, api_result: ApiStatus | None = None) -> bool:
        if api_result is None:
            return False

        requests_result = api_result.status_code
        return api_result.status == ConverterStatus.COMPLETED and requests_result == SUCCESS_CODE
