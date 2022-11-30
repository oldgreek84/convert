from dotenv import load_dotenv

from processing_job import (
    JobProcessorRemote,
    JobProcessorDummy,
)
from config import JobConfig
from ui import ConverterInterfaceCLI, ConverterInterfaceTk
from worker import Worker1, Worker2, Worker3, Worker4

load_dotenv()


def main():
    worker = Worker4()
    job = JobProcessorDummy(job_config=JobConfig, worker=worker)
    converter = ConverterInterfaceCLI(job)
    converter.run()


if __name__ == "__main__":
    main()
