import os
import sys

from abc import ABC, abstractmethod

from dotenv import load_dotenv

from utils import parse_command, get_path
from config import Target
from processing_job import (
    JobProcessor,
    JobProcessorRemote,
    JobProcessorDummy,
    JobConfig,
    ConverterConfig,
)

load_dotenv()

DOCSTRING = """
command needs:
-path - full/path/to/file
-name - file_name in current directory
-t - [target] - string of file format(default "mobi")
-cat - [category] - category of formatting file (default "ebook")
"""


class ConverterInterface(ABC):
    @abstractmethod
    def send_job(self):
        pass

    @abstractmethod
    def get_job(self, work_id: str):
        pass

    @abstractmethod
    def convert(self):
        pass


class ConverterInterfaceCLI:
    def __init__(self, job_processor: JobProcessor):
        self.job_processor = job_processor

    def convert(self):
        work_id = self.job_processor.send_job_data()
        print("file was sent")
        print(f"work ID: {work_id}")
        result_path = self.job_processor.get_job_data(work_id)
        print(result_path)
        full_path = self.job_processor.convert()
        print(f"file was saved to: {full_path}")


def main(path_to_file, path_to_save, target):
    url = os.environ.get("CONVERTER_URL")
    api_key = os.environ.get("API_KEY")
    print(f"Target: {target}")
    converter_config = ConverterConfig(api_key, url)
    job_config = JobConfig(target, path_to_file, path_to_save)
    job_processor = JobProcessorRemote(job_config, converter_config)
    converter_cli = ConverterInterfaceCLI(job_processor)
    converter_cli.convert()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(DOCSTRING)
    else:
        data_settings = parse_command()
        if data_settings.get("-path"):
            working_file_path = data_settings["-path"]
        elif data_settings.get("-name"):
            working_file_path = get_path(data_settings["-name"])
        else:
            working_file_path = sys.argv[1]

        working_target = data_settings.get("-t", "mobi")
        working_category = data_settings.get("-cat", "ebook")

        print(working_file_path, working_target, working_category)
        target_object = Target(working_target, working_category)

        main(working_file_path, path_to_save="books", target=target_object)
