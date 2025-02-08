from __future__ import annotations

import docker

from typing import Generator
from pathlib import Path

from processors.local_processor import LocalProcessor

IMAGE_NAME = "ebook_converter"


# TODO: send prints to stdout/interface
def init_container(rebuild: bool = False) -> docker.client.DockerClient:
    client = docker.from_env()
    image = client.images.get(IMAGE_NAME)
    if not image or rebuild:
        path_to_dockerfile = Path(__file__).parents[0]
        _, logs = client.images.build(path=str(path_to_dockerfile), tag=IMAGE_NAME)
        for log in logs:
            print(log)

    return client


# TODO: split classes to make LocalProcessor more common
#       and set it as base to other with similar logic
class ProcessorOnDocker(LocalProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.client = init_container()
        self.containers: dict[int, tuple] = {}

    def get_status(self) -> str:
        return self._status

    def send_job(self, filename: str, options: None | dict = None) -> int:
        if options is None:
            options = {}

        # setup command params to processing job
        params = self._prepare_command(filename, options)
        command, file_to_save = params["command"], params["file_to_save"]

        path_to_mount = Path(filename).parents[0].absolute()
        container = self.client.containers.run(
            image=IMAGE_NAME,
            volumes=[f"{path_to_mount}:/mnt/books"],
            command=command,
            detach=True,
        )
        self.containers[container.id] = (container, file_to_save)
        return container.id

    def _prepare_command(self, filename: str, options: dict) -> dict:
        res = super()._prepare_command(filename, options)

        # prepare paths of files as current dir
        main_command_elements, other = res["command"][:3], res["command"][3:]
        main_command, path_to_file, path_to_save = main_command_elements
        path_to_save = str(Path(path_to_save).name)
        path_to_file = str(Path(path_to_file).name)

        res["command"] = [main_command, path_to_file, path_to_save, *other]
        return res

    def _get_container(self, job_id: int) -> docker.models.containers.Container:
        return self.containers[job_id][0]

    def get_job_status(self, job_id: int) -> Generator:
        container = self._get_container(job_id)
        logs_stream = self.client.containers.get(container.id).logs(stream=True)
        try:
            while True:
                line = next(logs_stream).decode('utf-8').strip()
                yield self._status, line
        except StopIteration:
            pass

    def set_status(self, status: str) -> None:
        self._status = status

    def get_job_result(self, job_id: int) -> str:
        """get job data by job ID after processing and return it"""
        try:
            container, result = self.containers[job_id]
        except KeyError as err:
            raise KeyError("Processor did not find") from err

        container.remove()
        return result
