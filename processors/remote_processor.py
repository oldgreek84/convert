from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, TextIO

import requests

from config import APIConfig, ConverterStatus
from interfaces.processor_interface import JobProcessor
from processors import ProcessorError
from utils.common_utils import get_full_file_path, save_data_from_response_to_dir

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path, PosixPath

PROCESSOR_TIMEOUT = 3


# TODO: make JobProcessor more generic - use API Config classes for the implementation
#       possibility to use different APIs without changing of this class
class JobProcessorRemote(JobProcessor):
    """Remote processor implementation using external conversion APIs.

    This processor communicates with remote conversion services via HTTP APIs,
    allowing conversion operations to be performed on external servers. It handles
    file upload, job monitoring, and result retrieval through REST API calls.

    Features:
        - HTTP-based API communication
        - Asynchronous job monitoring with polling
        - File upload and download handling
        - Status mapping from API responses
        - Configurable timeout and retry logic

    The processor follows a typical remote job workflow:
    1. Upload file and create conversion job
    2. Poll job status until completion
    3. Download converted file result
    4. Handle errors and timeouts

    Attributes:
        api_config: Configuration for API authentication and endpoints
        _status: Current job status for completion checking

    Example:
        >>> config = APIConfig(token='api-key', url='https://api.converter.com')
        >>> processor = JobProcessorRemote(config)
        >>> job_id = processor.send_job('book.fb2', {'target': 'mobi'})
    """

    def __init__(self, api_config: APIConfig = APIConfig()) -> None:
        """Initialize the remote processor with API configuration.

        Args:
            api_config: API configuration containing authentication and endpoint details.
                       Defaults to environment-based configuration if not provided.
        """
        super().__init__()
        self.api_config = api_config
        self._status = None

    def set_status(self, status: str) -> None:
        """Update the current job status.

        Args:
            status: New status value for the current job
        """
        self._status = status

    def send_job(self, filename: str, options: dict | None = None) -> int:
        """Submit a file for remote conversion processing.

        Uploads the specified file to the remote conversion service and
        creates a new conversion job with the provided options.

        Args:
            filename: Path to the source file to be converted
            options: Dictionary containing conversion parameters

        Returns:
            Unique job identifier assigned by the remote service
        """
        if options is None:
            options = {}

        with open(filename) as f:
            return self._send_job_data(filename, f, options)

    def get_job_status(self, job_id: int) -> Generator:
        """Monitor the progress of a remote conversion job.

        Polls the remote service for job status updates until the job completes.
        Yields status information messages for UI display.

        Args:
            job_id: Unique identifier of the job to monitor

        Yields:
            Status information messages from the remote service

        Note:
            This method blocks with periodic polling intervals defined by PROCESSOR_TIMEOUT
        """
        while not self.is_completed():
            time.sleep(PROCESSOR_TIMEOUT)
            status_info = self._get_job_status(job_id)
            status = self._prepare_status(status_info["code"])
            self.set_status(status)
            yield status_info["info"]

    @staticmethod
    def _prepare_status(status_code: str) -> ConverterStatus:
        """Map remote API status codes to internal ConverterStatus enum values.

        Args:
            status_code: Status code string from the remote API

        Returns:
            Corresponding ConverterStatus enum value, defaults to FAILED for unknown codes
        """
        codes_map = {
            "ready": ConverterStatus.READY,
            "completed": ConverterStatus.COMPLETED,
            "processing": ConverterStatus.PROCESSING,
            "error": ConverterStatus.FAILED,
        }
        return codes_map.get(status_code, ConverterStatus.FAILED)

    def is_completed(self) -> bool:
        """Check if the current job has completed processing.

        Returns:
            True if the job status is COMPLETED, False otherwise
        """
        return self._status == ConverterStatus.COMPLETED

    def _send_job_data(self, path_to_file: str, file_data: TextIO, options: dict) -> int:
        """Send file and conversion options to remote API to create a job.

        Args:
            path_to_file: Path to the source file being converted
            file_data: Open file object for reading file contents
            options: Dictionary of conversion options

        Returns:
            Job ID assigned by the remote service
        """
        # get server`s options for convert
        job_id, server_url = self._get_job_id_from_server(self._set_data_options(options))
        url_upload = self._set_upload_url(job_id, server_url)

        # send file data to server
        self._send_file_to_server(url_upload, path_to_file, file_data)
        return job_id

    @staticmethod
    def _set_data_options(options: dict) -> str:
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
        """Send request to create remote job

        Args:
            options_data: json string with parameters target and category

        Returns:
            job server url and job id

        Raises:
            ProcessorError: if url of the remote processor is not set.
        """
        url = self.api_config.url
        if not url:
            msg = "API URL not configured"
            raise ProcessorError(msg)

        response = requests.post(
            url,
            headers=self.api_config.get_header("main_header"),
            data=options_data,
            timeout=PROCESSOR_TIMEOUT,
        )

        data: dict = response.json()
        return data["id"], data["server"]

    @staticmethod
    def _set_upload_url(job_id: int, server_url: str) -> str:
        """Construct the file upload URL for a specific job.

        Args:
            job_id: Unique job identifier
            server_url: Base URL of the remote server

        Returns:
            Complete upload endpoint URL
        """
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
        """Retrieve status information for a specific job.

        Args:
            job_id: Unique job identifier

        Returns:
            Status dictionary containing code and info fields
        """
        res = self._get_job_info(job_id)
        return res["status"]

    def get_job_result(self, job_id: int) -> str:
        """Retrieve the result URL for a completed conversion job.

        Args:
            job_id: Unique identifier of the completed job

        Returns:
            URL where the converted file can be downloaded
        """
        return self._get_job_result(job_id)

    def _get_job_result(self, job_id: int) -> str:
        """Extract the result URI from job information.

        Args:
            job_id: Unique job identifier

        Returns:
            URI of the converted file output
        """
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
        """Check API response for errors and raise exception if found.

        Args:
            data: Response data from the remote API

        Raises:
            ProcessorError: If the response contains error information
        """
        is_error = data["status"]["code"] == "error" or data["errors"]
        if not is_error:
            return

        msg = f"ERROR: {self._get_error_info(data)}"
        raise ProcessorError(msg)

    @staticmethod
    def _get_error_info(data: dict) -> list[str | None]:
        """Extract error information from API response.

        Args:
            data: Response data containing error details

        Returns:
            List containing error messages or status codes
        """
        return [data["errors"] or data["status"]["code"]]

    def save_file(self, path_to_result: str, path_to_save: str | Path) -> str | PosixPath | Path:
        """Save the converted file from a remote URL to local filesystem.

        Args:
            path_to_result: URL of the converted file on the remote server
            path_to_save: Local directory path where the file should be saved

        Returns:
            Full path to the saved file
        """
        return self._save_from_url(path_to_result, path_to_save)

    # TODO: check func from utils for this processing or replace it here
    @staticmethod
    def _save_from_url(url: str, sub_dir: str | Path = os.path.curdir) -> str | PosixPath | Path:
        """saves file form remote URL to directory"""
        filename = url.split("/", maxsplit=1)[-1] if url else ""
        full_path = get_full_file_path(filename, sub_dir)
        response = requests.get(url, stream=True)
        save_data_from_response_to_dir(full_path, response)
        return full_path
