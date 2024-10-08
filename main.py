import logging

from converter import Converter

from processors.remote_processor import JobProcessorRemote
from processors.local_processor import LocalProcessor
from processors.processor_on_docker import ProcessorOnDocker

from uis.cli_ui import ConverterInterfaceCLI
from uis.tk_ui import ConverterInterfaceTk

from worker import ThreadWorker

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError as err:
    logger.warning("dotenv module is not installed in your system")
    msg = "Whrer is not package in your system."
    raise ImportError(msg) from err

load_dotenv()


def main() -> None:
    interface = ConverterInterfaceCLI()
    # interface = ConverterInterfaceTk()

    worker = ThreadWorker()

    # processor = JobProcessorRemote()
    # processor = LocalProcessor()
    processor = ProcessorOnDocker()

    converter = Converter(interface, processor, worker)
    interface.run(converter)


if __name__ == "__main__":
    main()
