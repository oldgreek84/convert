"""Common test fixtures and mock implementations for testing.

This module provides dummy/mock implementations of various interfaces
that can be used across different test modules.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Optional, Union

import requests

from src.exceptions import ProcessorError
from src.config import JobConfig


class DummyWorker:
    """Mock worker for testing that implements the Worker protocol."""

    def __init__(self):
        self._completed = False
        self._result = None
        self._error_handler = None

    def execute(self, func, *args, **kwargs) -> None:
        """Execute function synchronously for testing."""
        try:
            self._result = func(*args, **kwargs)
            self._completed = True
        except Exception as e:
            if self._error_handler:
                self._error_handler(e)
            self._completed = True

    def is_completed(self) -> bool:
        return self._completed

    def get_result(self) -> Any:
        return self._result

    def set_error_handler(self, handler) -> None:
        self._error_handler = handler


class DummyUI:
    """Mock UI for testing that implements ViewProtocol."""

    def __init__(self):
        self.config = None
        self._on_convert = None
        self.messages = []
        self.errors = []
        self.statuses = []
        self.results = []

    def set_on_convert(self, callback) -> None:
        self._on_convert = callback

    def run(self) -> None:
        pass

    def get_config(self) -> JobConfig:
        return self.config

    def setup(self) -> JobConfig:
        return self.config

    def show_status(self, status: str) -> None:
        self.statuses.append(status)

    def show_message(self, message: str) -> None:
        self.messages.append(message)

    def show_error(self, error: str) -> None:
        self.errors.append(error)

    def show_result(self, result) -> None:
        self.results.append(result)

    def show_formats(self, formats: list[str]) -> None:
        pass

    def show_progress(self, progress: float) -> None:
        pass


class DummySaver:
    """Mock saver for testing that implements SaverProtocol."""

    def __init__(self):
        self.source_name = None
        self.source_data = None
        self.destination_path = None

    def setup(self, **kwargs) -> None:
        self.source_name = kwargs.get("source_name")
        self.source_data = kwargs.get("source_data")
        self.destination_path = kwargs.get("destination_path")

    def save(self, source_path: str | None = None) -> str:
        return f"{self.destination_path}/{self.source_name}"


class DummyJobProcessor:
    """Mock processor for testing that implements JobProcessor protocol."""

    def __init__(self):
        self._completed = False
        self._job_id = "test_job_id"
        self._result_data = io.BytesIO(b"test data")

    def is_completed(self) -> bool:
        return self._completed

    def send_job(self, path_to_file: str, options: dict) -> str:
        return self._job_id

    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        return self._job_id

    def get_job_status(self, job_id: str) -> list[str]:
        self._completed = True
        return ["Processing...", "Completed"]

    def get_job_result(self, job_id: str) -> tuple[str, io.BytesIO]:
        return ("result.mobi", self._result_data)

    def prepare_params(self, options):
        return options

    def save_file(
        self, path_to_result: Optional[Union[str, Path]], path_to_save: Optional[Union[str, Path]]
    ) -> str:
        return f"{path_to_save}/{path_to_result}"


class LocalTestJobProcessor:
    """Test processor that actually makes HTTP requests (for integration tests)."""

    dummy_msg = None
    dummy_url = "http://localhost:5000"
    dummy_response = {
        "message": dummy_msg,
        "output": None if dummy_msg != "completed" else [{"uri": "http://uri_for_download"}],
        "status": {
            "code": dummy_msg,
            "status_code": 200,
            "info": None if dummy_msg != "error" else "it`s error message!!!",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = "ready"
        self._data: dict = {}
        self._result = None

    def is_completed(self) -> bool:
        return self._status == "completed"

    def send_job_data(self, path_to_file: str, file_data: bytes, options: dict) -> str:
        res = requests.post(f"{self.dummy_url}", json={"conversion": options})
        work_id = res.json()["id"]
        self._data["id"] = work_id

        res = requests.post(
            f"{self.dummy_url}/test-server/upload-file/test_ID", files={"file": file_data}
        )
        return work_id

    def get_job_status(self, job_id: str) -> str:
        if not self.is_completed():
            self._status = self._get_job_status(job_id)
        return self._status

    def _get_job_status(self, job_id: str = "test_ID") -> str:
        res = self._get_converted_file_status_data(job_id)
        return res["status"]["code"]

    def get_job_result(self, job_id: str):
        if self.is_completed():
            self._result = self._get_job_result(job_id)
        return self._result

    def _get_job_result(self, job_id: str = "test_ID"):
        res = self._get_converted_file_status_data(job_id)
        return res["info"][0]["uri"]

    def _get_converted_file_status_data(self, job_id: str) -> dict:
        response = requests.get(f"{self.dummy_url}/{job_id}")
        res = response.json()
        self._check_errors(res)
        return res

    def _check_errors(self, data: dict) -> None:
        is_error = data["status"]["code"] == "error" or data["errors"]
        if is_error:
            raise ProcessorError(f"ERROR: {self._get_error_info(data)}")

    def _get_error_info(self, data: dict) -> list:
        return [data["errors"] or data["status"]["code"]]

    def save_file(
        self, path_to_result: Optional[Union[str, Path]], path_to_save: Optional[Union[str, Path]]
    ) -> str:
        full_path = f"path/to/{path_to_save}"
        self._data["full_path"] = full_path
        return full_path
