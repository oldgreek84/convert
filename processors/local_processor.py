from __future__ import annotations

import io
import subprocess
from typing import TYPE_CHECKING

from interfaces.processor_interface import JobProcessor
from processors import ProcessorError

if TYPE_CHECKING:
    from collections.abc import Generator


class LocalProcessor(JobProcessor):
    """Local processor implementation using the ebook-convert command-line tool.

    This processor executes conversion operations by invoking the locally installed
    'ebook-convert' utility through subprocess calls. It manages multiple concurrent
    conversion jobs and provides real-time status monitoring through process output.

    The processor handles the complete lifecycle of local conversions:
    - Command preparation with appropriate arguments
    - Process execution and management
    - Output streaming for status updates
    - Result file handling and path resolution

    Requirements:
        - ebook-convert tool must be installed and available in PATH
        - Appropriate permissions for file access and subprocess execution
        - Sufficient disk space for temporary and output files

    Attributes:
        processes: Dictionary mapping job IDs to (process, output_file) tuples

    Example:
        >>> processor = LocalProcessor()
        >>> job_id = processor.send_job('book.fb2', {'target': 'mobi', 'category': 'ebook'})
        >>> for status in processor.get_job_status(job_id):
        ...     print(f"Status: {status}")
        >>> result_path = processor.get_job_result(job_id)
    """

    def __init__(self) -> None:
        super().__init__()
        self.processes: dict[int, tuple] = {}

    def _get_process(self, job_id: int) -> subprocess.Popen:
        """Retrieve the subprocess for a given job ID.

        Args:
            job_id: Unique identifier for the conversion job

        Returns:
            The subprocess.Popen object for the specified job

        Raises:
            KeyError: If the job ID is not found in active processes
        """
        return self.processes[job_id][0]

    def send_job(self, filename: str, format_options: dict | None = None) -> int:
        if format_options is None:
            format_options = {}

        # setup command params to processing job
        params = self._prepare_command(filename, format_options)
        command, file_to_save = params["command"], params["file_to_save"]

        try:
            # if send errors to pipe we will have traceback data in process
            # can use it in debug mode
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
        except Exception as ex:
            msg = f"Error in send: {ex}"
            raise ProcessorError(msg) from ex

        self.processes[process.pid] = (process, file_to_save)
        return process.pid

    def _prepare_command(self, filename: str, options: dict) -> dict:
        """Prepare the ebook-convert command with appropriate arguments.

        Constructs the command line arguments for the ebook-convert tool,
        including the source file, target file, and conversion options.

        Args:
            filename: Path to the source file to convert
            options: Dictionary containing target format and conversion options

        Returns:
            Dictionary with 'command' (list of command arguments) and
            'file_to_save' (output file path)
        """
        command = ["ebook-convert", filename]

        processing_target = options["target"]
        file_to_save = f"{filename}.{processing_target}"

        other_options = self._prepare_other_options(options["options"])
        command.extend([file_to_save, *other_options])
        return {
            "file_to_save": file_to_save,
            "command": command,
        }

    @staticmethod
    def _prepare_other_options(options: dict) -> list:
        """Convert options dictionary to command line arguments.

        Args:
            options: Dictionary of conversion options

        Returns:
            List of command line option strings
        """
        return list(options.keys())

    def get_job_status(self, job_id: int) -> Generator:
        """Monitor the progress of a conversion job.

        Args:
            job_id: Unique identifier for the conversion job

        Yields:
            Status messages from the conversion process
        """
        process = self._get_process(job_id)
        yield from self._get_job_status(process)

    def _get_job_status(self, process: subprocess.Popen) -> Generator:
        """Generate status updates from process output.

        Args:
            process: The subprocess to monitor

        Yields:
            Decoded status messages from the process output
        """
        if process.stdout:
            output = process.stdout.read()
            if output:
                for line in output:
                    yield line.decode().strip()

    def get_job_result(self, job_id: int) -> str:
        """Retrieve the result of a completed conversion job.

        Args:
            job_id: Unique identifier for the conversion job

        Returns:
            Path to the converted file

        Raises:
            ProcessorError: If job not found or conversion failed
        """
        try:
            process, filename = self.processes[job_id]
        except KeyError as err:
            msg = "Processor did not find"
            raise ProcessorError(msg) from err

        if process.stdout:
            process.stdout.close()

        return_code = process.wait()

        if return_code != 0:
            msg = f"ERROR IN RESULTS {process.stderr or ''}"
            raise ProcessorError(msg)

        return self._prepare_result_bytes(filename)

    def _prepare_result_bytes(self, filename):
        with open(filename, 'rb') as source_data:
            return filename, io.BytesIO(source_data.read())
