from __future__ import annotations

import sys
import threading
import docker

from pathlib import Path
from docker.errors import ImageNotFound

try:
    from docker.errors import BuildError
except ImportError:
    BuildError = Exception

from typing import TYPE_CHECKING

from processors.local_processor import LocalProcessor
import exceptions

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

IMAGE_NAME = "ebook_converter"


def init_container(
    rebuild: bool = False,
    callback: Callable | None = None,
) -> docker.client.DockerClient:
    """Initialize Docker container for e-book conversion.

    Sets up the Docker environment for running conversion operations.
    If the required Docker image doesn't exist, it will be built automatically.
    The build process runs in a separate thread to avoid blocking the main application.

    Args:
        rebuild: Force rebuild of the Docker image even if it exists
        callback: Optional callback function called when build completes

    Returns:
        Configured Docker client ready for container operations
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
    dockerfile_path: str,
    tag: str,
    callback: Callable | None = None,
) -> None:
    """Build Docker image using the low-level Docker API.

    Creates a Docker image from the Dockerfile in the specified path.
    Provides real-time build output and calls the callback function
    upon successful completion.

    Args:
        dockerfile_path: Directory containing the Dockerfile
        tag: Tag name for the built image
        callback: Optional callback function called with DockerClient on success
    """
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

    except BuildError as e:
        print(f"Build failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def start_build(dockerfile_path: str, tag: str, callback: Callable | None = None) -> None:
    """Start Docker image build process in a separate thread.

    Initiates the Docker image build process in a background thread to avoid
    blocking the main application. The build process uses the Dockerfile in
    the specified path to create the converter image.

    Args:
        dockerfile_path: Directory containing the Dockerfile
        tag: Tag name for the built image
        callback: Optional callback function called when build completes
    """
    build_thread = threading.Thread(target=build_image, args=(dockerfile_path, tag, callback))
    build_thread.daemon = True  # Ensures the thread exits when the program closes
    build_thread.start()
    print("Build started in the background!")


class TextRedirector:
    """Text stream redirector for capturing and displaying Docker build output.

    This class redirects standard output streams to UI components, allowing
    Docker build messages and other text output to be displayed in the
    user interface instead of the console.

    Attributes:
        widget: UI component that implements display_common_info method
        tag: Stream identifier (typically "stdout" or "stderr")

    Example:
        >>> redirector = TextRedirector(ui_widget)
        >>> sys.stdout = redirector  # Redirect stdout to UI
    """

    def __init__(self, widget, tag="stdout"):
        """Initialize the text redirector.

        Args:
            widget: UI component to receive redirected text
            tag: Stream identifier for the redirected output
        """
        self.widget = widget
        self.tag = tag

    def write(self, message):
        """Write a message to the UI widget.

        Args:
            message: Text message to display in the UI
        """
        self.widget.display_common_info(message)

    # NOTE: Required for sys.stdout compatibility
    def flush(self):
        """Flush the output stream (no-op for UI compatibility)."""


# TODO: split classes to make LocalProcessor more common
#       and set it as base to other with similar logic
class ProcessorOnDocker(LocalProcessor):
    """Docker-based processor that runs conversions inside Docker containers.

    This processor extends LocalProcessor to run ebook-convert operations
    inside Docker containers, providing isolation and consistent execution
    environments. It automatically manages Docker image building, container
    lifecycle, and volume mounting for file access.

    Features:
        - Automatic Docker image building if not present
        - Volume mounting for file access
        - Container lifecycle management
        - Output redirection to UI components
        - Parallel container execution support

    Requirements:
        - Docker service running and accessible
        - Appropriate Docker permissions
        - Dockerfile present in processor directory

    Attributes:
        client: Docker client instance for container operations
        containers: Dictionary mapping job IDs to container information

    Example:
        >>> redirector = TextRedirector(ui_component)
        >>> processor = ProcessorOnDocker(redirector)
        >>> job_id = processor.send_job('book.fb2', {'target': 'mobi'})
    """

    def __init__(self, redirector=sys.stdout) -> None:
        """Initialize the Docker processor.

        Args:
            redirector: Output redirector for capturing Docker messages.
                       Defaults to sys.stdout for console output.
        """
        super().__init__()
        self.client = None
        self.containers: dict[int, tuple] = {}
        sys.stdout = redirector

    def set_docker_client(self, new_client: docker.client.DockerClient) -> None:
        """Update the Docker client instance.

        This callback method is called when the Docker image build process
        completes successfully, providing the processor with a ready-to-use
        Docker client for container operations.

        Args:
            new_client: Configured Docker client instance
        """
        self.client = new_client

    def send_job(self, filename: str, format_options: dict | None = None) -> int:
        self.client = init_container(rebuild=False, callback=self.set_docker_client)
        if format_options is None:
            format_options = {}

        # setup command params to processing job
        params = self._prepare_command(filename, format_options)
        command, file_to_save = params["command"], params["file_to_save"]

        path_to_mount = Path(filename).parents[0].absolute()
        container = self.client.containers.run(
            image=IMAGE_NAME,
            volumes=[f"{path_to_mount}:/mnt/books"],
            command=command,
            detach=True,
        )
        container_id = hash(container.id or str(container))
        self.containers[container_id] = (container, file_to_save)  # type: ignore
        return container_id

    def _prepare_command(self, filename: str, options: dict) -> dict:
        res = super()._prepare_command(filename, options)

        # prepare paths of files as current dir
        main_command_elements, other = res["command"][:3], res["command"][3:]
        main_command, path_to_file, path_to_save = main_command_elements
        path_to_save = str(Path(path_to_save).name)
        path_to_file = str(Path(path_to_file).name)

        res["command"] = [main_command, path_to_file, path_to_save, *other]
        return res

    def _get_container(self, job_id: int):  # type: ignore
        return self.containers[job_id][0]

    def get_job_status(self, job_id: int) -> Generator:
        container = self._get_container(job_id)
        if self.client:
            logs_stream = self.client.containers.get(container.id).logs(stream=True)  # type: ignore
            for line in logs_stream:
                yield line.decode("utf-8").strip()

    def get_job_result(self, job_id: int) -> str:
        """Get job data by job ID after processing and return it

        Raises:
            KeyError: If key is missed in containers dict.
        """
        try:
            container, filename = self.containers[job_id]
        except KeyError as err:
            msg = f"Container was not found [{job_id}]"
            raise KeyError(msg) from err

        container.remove()
        return self._prepare_result_bytes(filename)


if __name__ == "__main__":
    build_image(dockerfile_path="./processors", tag="my-image:latest")
