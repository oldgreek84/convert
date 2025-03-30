from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum


class ParamsError(Exception):
    """Common error class for parsing params"""


class ConverterStatus(StrEnum):
    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"



@dataclass
class Target:
    target: str
    category: str
    options: dict = field(default_factory=dict)


@dataclass
class JobConfig:
    target: Target
    path_to_file: str
    path_to_save: str = "books"

    @property
    def job_target(self):
        return self.target.target

    @property
    def job_category(self):
        return self.target.category

    @property
    def job_options(self):
        return self.target.options

    def get_config(self) -> dict:
        return {
            "category": self.job_category,
            "target": self.job_target,
            "options": self.job_options,
        }


class APIConfig:
    """Class provides params to setup remote API."""
    def __init__(self, token: str | None = None, url: str | None = None):
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

    def get_header(self, header_key: str):
        return self.headers[header_key]

    def set_header(self, key: str, data: dict):
        self.headers[key] = data
