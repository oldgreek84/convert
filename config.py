import os
from dataclasses import dataclass


@dataclass
class Target:
    target: str = "mobi"
    category: str = "ebook"


@dataclass
class JobConfig:
    target: Target
    path_to_file: str
    path_to_save: str = "books"


class ConverterConfig:
    """Docstring for UrlConverter:."""

    def __init__(self, api_key: str = None, api_url: str = None):
        """TODO: to be defined."""
        self.api_key = api_key or os.environ.get("API_KEY")
        self.api_url = api_url or os.environ.get("CONVERTER_URL")
        self.headers = {
            "main_header": {
                "cache-control": "no-cache",
                "content-type": "application/json",
                "x-oc-api-key": self.api_key,
            },
            "cache_header": {
                "cache-control": "no-cache", "x-oc-api-key": self.api_key},
        }

    def get_header(self, header_key: str):
        return self.headers[header_key]

    def set_header(self, key: str, data: dict):
        self.headers[key] = data
