import os
import json
import time
import requests
from typing import Tuple
from abc import abstractmethod, ABC
from enum import Enum, auto
import requests

from utils import get_full_file_path, catcher, coroutine
from config import JobConfig, ConverterConfig


class Status(Enum):
    OK = auto()
    ERROR = auto()
    COMPLETED = auto()

    def is_correc(self):
        return self.OK


class Worker:
    def __init__(self, job):
        self.job = job

    def get_job_status(self):
        while True:
            job = (yield)


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
    dummy_msg = None
    dummy_url = None
    dummy_response = {
        "message": dummy_msg,
        "output": None if dummy_msg != 'completed' else [{"uri": "http://uri_for_download"}],
        "status": {
            "code": dummy_msg,
            "status_code": 200,
            "info": None if dummy_msg != "error" else "it`s error message!!!"},
    }

    def __init__(self, job_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_config = job_config
        self.status_checker_job = self.get_status_cor()
        self._status = "wait"
        self._data = {}

    def send_job_data(self):
        print("------ DUMMY --: Data was sent")
        return "DUMMY <<test id>>"

    def get_job_data(self, job_id: str):
        return job_id

    def convert(self):
        """
        sen data
        get status
        if status -> "completed" -> return data
        save data
        """
        # self._convert()
        print("==============================")
        work_id = self.send_job_data()
        self._data["work_id"] = work_id
        print("==============================")
        self.check_status()
        # self.waiter = self.test_worker()
        print("==============================")
        self.check_and_save()
        print("==============================")

    def check_status(self, until_done=False):
        print("------ CHECK STATUS RUNS--- ")

        print("------ CHECK STATUS RUNS-- befor producer ")
        self.producer(self.status_checker_job, until_done)
        # self.next_producer(self.waiter)
        print("------ CHECK STATUS RUNS-- after producer ")
        return self._status

    def check_and_save(self):
        if self._status == 'completed':
            uri_to_downloas_file = "some_path"
            full_path = self.save_file(uri_to_downloas_file)

            self._data["uri_to_downloas_file"] = uri_to_downloas_file
            self._data["full_path"] = full_path
            print("------ CHECK SAVED --- ")

    def producer(self, cor, until_done=False):
        while True:
            time.sleep(3)
            cor.send(True)

            if not until_done:
                break

            print(f"----- ST: {self._status}")
            if self.is_completed():
                cor.close()
                break

    def get_some(self, cor):
        return next(cor)

    def get_job_status(self):
        # self.waiter.send(True)
        return self._status

    def is_completed(self):
        return self._status in ["completed", "error"]

    def test_worker(self):
        checker = self.check_cor()
        waiter = self.waiter_cor(checker)
        self.next_producer(waiter)
        return waiter

    def next_producer(self, cor):
        cor.send(True)

    @coroutine
    def waiter_cor(self, next_cor=None):
        while True:
            time.sleep(3)
            _ = (yield)
            status = next(next_cor)
            print(f"STATUS: {status}")
            self._status = status
            if status in ["completed", "error"]:
                next_cor.close()
                return

    @coroutine
    def check_cor(self):
        resp_status = "wait"
        try:
            while True:
                check = (yield resp_status)
                if check:
                    _, resp_status = self.get_response_status()
        except GeneratorExit:
            print("closing...")

    @coroutine
    def get_some_cor(self):
        while True:
            _, resp_status = self.get_response_status()
            _ = (yield resp_status)

    @coroutine
    def get_status_cor(self):
        try:
            while True:
                run = (yield)
                print(f"1: {run = }")
                if run:
                    res, resp_status = self.get_response_status()
                    print("------------------------------")
                    print(f"response: {res = } {resp_status = }")
                    yield res, resp_status
                    print(f"2: {run = }")
                    print("------------------------------")
                    self._status = res.json()['message']
        except GeneratorExit:
            print("closing.........")

    # def _convert(self):
    #     print("------ DUMMY --: Converter started")
    #     self.send_job_data()
    #     self._status = "sent"

    #     res = self.get_job_data(12)
    #     print(f"DUMMY: {res = }")

    #     print("------ DUMMY --: Data was converted")
    #     return self.save_file(res)

    # def get_job_status_test(self, work_id: str):
    #     res_status, status = False, False
    #     while True:
    #         time.sleep(3)
    #         res_status, status = self._get_status_convert_file(work_id)
    #         # yield res_status, status
    #         if status != "processing":
    #             break

    #     self._status = status

    #     if status != "completed":
    #         status = res_status.json()["status"]["info"]
    #         return {"error": status}
    #     return {"result": res_status.json()["output"][0]["uri"]}

    # def _get_status_convert_file(self, work_id: str):
    #     response = requests.get(
    #         f"{self.converter_config.api_url}/{work_id}",
    #         headers=self.converter_config.get_header("main_header"),
    #     )

    #     status_code = response.json()["status"]["code"]
    #     return response, status_code

    def get_response_status(self):
        res = requests.get("http://localhost:5000/", json={})
        return res, res.json()["status"]["code"]

    def save_file(self, path_to_save, *args):
        print("------ DUMMY --: file was saved")
        return "path/to/file"

    def get_processor_data(self, key):
        return self._data.get(key, False)


class JobProcessorRemote(JobProcessor):
    def __init__(
            self,
            job_config: JobConfig, *args):
        self.job_config = job_config
        self.converter_config = ConverterConfig()
        self._data = {}
        self._status = "ready"

    # @catcher
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
        self._convert()

    def _convert(self):

        self.validate_path()
        work_id = self.send_job_data()

        uri_to_downloas_file = self.get_job_data(work_id)
        full_path = self.save_file(self.job_config.path_to_save, uri_to_downloas_file)

        self._data["work_id"] = work_id
        self._data["uri_to_downloas_file"] = uri_to_downloas_file
        self._data["full_path"] = full_path

        return full_path

    def get_processor_data(self, key):
        return self._data.get(key, False)

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

    def cor_set_status(self):
        while True:
            if self._status in ["error", "completed"]:
                break
            name = (yield self._status)
            print(name)

    def processing_status(self):
        pass

    def send_status(self):
        try:
            while True:
                get = (yield self._status)
                print(get)
                if get:
                    result = self.get_job_status_test(12)
                    print(result)
        except GeneratorExit:
            print("closing...")

    def get_job_status_test(self, work_id: str):
        res_status, status = False, False
        while True:
            time.sleep(3)
            res_status, status = self._get_status_convert_file(work_id)
            # yield res_status, status
            if status != "processing":
                break

        self._status = status

        if status != "completed":
            status = res_status.json()["status"]["info"]
            return {"error": status}
        return {"result": res_status.json()["output"][0]["uri"]}

    def get_job_status(self, work_id: str):
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

    def validate_path(self):
        """validate path to file for converting"""

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
