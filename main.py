from dotenv import load_dotenv

from processing_job import (
    JobProcessorRemote,
    JobProcessorDummy,
)
from interfaces import ConverterInterfaceCLI, ConverterInterfaceTk

load_dotenv()


def main():
    # job_config = JobConfig(target, path_to_file)
    # job_processor = JobProcessorRemote(job_config)

    converter = ConverterInterfaceCLI(JobProcessorDummy)
    # converter = ConverterInterfaceTk(JobProcessorDummy)
    converter.run()


if __name__ == "__main__":
    main()
