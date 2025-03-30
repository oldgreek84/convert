from __future__ import annotations

import subprocess
from pathlib import Path, PosixPath
from typing import Generator, Union
from config import ConverterStatus

from processors import ProcessorError


class LocalProcessor:
    """Job processor which user local installed application called "ebook-convert"
    to convert via OTHER CLI app"""

    def __init__(self) -> None:
        self._status = ConverterStatus.READY
        self.processes: dict[int, tuple] = {}

    def _get_process(self, job_id: int) -> subprocess.Popen:
        return self.processes[job_id][0]

    def is_completed(self) -> bool:
        """return True if job is completed"""
        return self._status == ConverterStatus.COMPLETED

    def send_job(self, filename: str, options: None | dict = None) -> int:
        if options is None:
            options = {}

        # setup command params to processing job
        params = self._prepare_command(filename, options)
        command, file_to_save = params["command"], params["file_to_save"]

        try:
            # if send errors to pipe we will have traceback data in process
            # can use it in debug mode
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
        except Exception as ex:
            raise ProcessorError(f"Error in send: {ex}") from ex

        self.processes[process.pid] = (process, file_to_save)
        return process.pid

    def _prepare_command(self, filename: str, options: dict) -> dict:
        """Prepare list with string command to user inner application"""
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
        return list(options.keys())

    def get_job_status(self, job_id: int) -> Generator:
        """return job status by job ID"""
        process = self._get_process(job_id)
        yield from self._get_job_status(process)

    def _get_job_status(self, process: subprocess.Popen) -> Generator:
        while True:
            line = process.stdout.readline() if process.stdout is not None else None
            if not line:
                self.set_status(ConverterStatus.COMPLETED)
                break
            yield self._status, line.decode().strip()

    def get_job_result(self, job_id: int) -> str:
        """get job data by job ID after processing and return it"""
        try:
            process, result = self.processes[job_id]
        except KeyError as err:
            raise ProcessorError("Processor did not find") from err

        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise ProcessorError(f"ERROR IN RESULTS {process.stderr or ''}")
        return result

    def save_file(
        self, path_to_result: str, path_to_save: str | Path
    ) -> str | Path | PosixPath:
        """save job result after processing and return path to file"""
        return self._resolve_path(path_to_result, path_to_save)

    @staticmethod
    def _resolve_path(
        path_to_result: str, destination_dir: str | Path
    ) -> str | Path | PosixPath:
        """Return exists path by destination path in system"""
        source_path = Path(path_to_result)
        destenation_path = Path(destination_dir)
        destenation_path.mkdir(parents=True, exist_ok=True)
        new_file_path = destenation_path / source_path.name
        source_path.rename(new_file_path)
        return new_file_path
