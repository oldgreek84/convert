from __future__ import annotations
from ui import JobConfig, Path


class WebUI:
    def run(self, converter) -> None:
        print(f"test UI: {self}")

    def setup(self) -> JobConfig | bool:
        print(f"test UI: {self}")

    def convert(self, config: JobConfig) -> None:
        print(f"test UI: {self}")

    def display_message(self, message: str) -> None:
        print(f"test UI: {self}")

    def display_job_status(self, status: str) -> None:
        print(f"test UI: {self}")

    def display_job_result(self, result: Path | str) -> None:
        print(f"test UI: {self}")

    def display_job_id(self, job_id: str) -> None:
        print(f"test UI: {self}")

    def display_error(self, error: str) -> None:
        print(f"test UI: {self}")
