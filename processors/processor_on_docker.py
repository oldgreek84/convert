from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Generator

import docker
from docker.errors import ImageNotFound

from processors.local_processor import LocalProcessor

IMAGE_NAME = "ebook_converter"


def init_container(
    rebuild: bool = False, callback: Callable | None = None,
) -> docker.client.DockerClient:
    """Run docker container with converter application.
    If docker image is not exist in system it will build the new one.
    Return docker client.
    """
    client = docker.from_env()

    # try to get prebuild image
    image = False
    try:
        image = client.images.get(IMAGE_NAME)
    except ImageNotFound as err:
        print(err)
        rebuild = True

    # rebuild image in separated thread
    if not image or rebuild:
        start_build(str(Path(__file__).parents[0]), IMAGE_NAME, callback)

    return client


def build_image(
    dockerfile_path: str, tag: str, callback: Callable | None = None,
) -> None:
    """Build docker image via low-level api."""
    client = docker.APIClient()
    print(f"Building image: {tag} from {Path(dockerfile_path).resolve()}")

    try:
        response = client.build(path=dockerfile_path, tag=tag, rm=True, decode=True)
        for chunk in response:
            if "stream" in chunk:
                print(chunk["stream"], end="")

        print(f"\nBuild completed: {tag}")

        if callback is not None:
            callback(docker.from_env())

    except docker.errors.BuildError as e:
        print(f"Build failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def start_build(dockerfile_path: str, tag: str, callback: Callable) -> None:
    """Start build processing in separated thread"""
    build_thread = threading.Thread(
        target=build_image, args=(dockerfile_path, tag, callback)
    )
    build_thread.daemon = True  # Ensures the thread exits when the program closes
    build_thread.start()
    print("Build started in the background!")


# TODO: send processing of container init to UI
# TODO: split classes to make LocalProcessor more common
#       and set it as base to other with similar logic
class ProcessorOnDocker(LocalProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.client = init_container(
            rebuild=False, callback=self.set_docker_client)
        self.containers: dict[int, tuple] = {}

    def set_docker_client(self, new_client: docker.client.DockerClient) -> None:
        """Called when the build is done to update the client."""
        self.client = new_client

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
                line = next(logs_stream).decode("utf-8").strip()
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


if __name__ == "__main__":
    build_image(dockerfile_path="./processors", tag="my-image:latest")
