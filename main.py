import logging

from config import APIConfig
from converter import Converter

from processors.local_processor import LocalProcessor
from processors.processor_on_docker import ProcessorOnDocker, TextRedirector
from processors.remote_processor import JobProcessorRemote

from uis.cli_ui import ConverterInterfaceCLI
from uis.tk_ui import ConverterInterfaceTk

from workers.worker import ThreadWorker

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError as err:
    msg = "Where is not package in your system."
    logger.warning(msg)
    raise ImportError(msg) from err

load_dotenv()


def main() -> None:
    interface = ConverterInterfaceTk()
    worker = ThreadWorker()
    processor = ProcessorOnDocker(TextRedirector(interface))

    converter = Converter(interface, processor, worker)
    interface.run(converter)


if __name__ == "__main__":
    main()
