import argparse
import logging

from config import APIConfig
from converter import Converter

from processors.local_processor import LocalProcessor
from processors.processor_on_docker import ProcessorOnDocker, TextRedirector
from processors.remote_processor import JobProcessorRemote

from savers.local_saver import LocalFileSaver
from savers.google_drive_saver import GoogleDriveSaver

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
    interface = ConverterInterfaceCLI()
    parser = argparse.ArgumentParser(description="E-book Converter Application")
    parser.add_argument(
        "--ui",
        type=str,
        choices=["cli", "tk"],
        default="tk",
        help="Choose the user interface: 'cli' for Command-Line, 'tk' for Tkinter GUI",
    )
    args = parser.parse_args()

    if args.ui == "cli":
        interface = ConverterInterfaceCLI()
    else:
        interface = ConverterInterfaceTk()

    worker = ThreadWorker()
    processor = ProcessorOnDocker(TextRedirector(interface))
    saver = LocalFileSaver()

    converter = Converter(interface, processor, saver, worker)
    interface.run(converter)


if __name__ == "__main__":
    main()
