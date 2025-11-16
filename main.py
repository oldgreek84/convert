"""E-book Converter Application - Main Entry Point

This module serves as the main entry point for the e-book converter application.
It provides command-line interface for selecting different UI modes and configures
the default components for the conversion system.

The application supports multiple user interfaces:
- CLI: Command-line interface for terminal usage
- TK: Tkinter-based graphical user interface (default)

Default Configuration:
- Processor: ProcessorOnDocker (Docker-based conversion)
- Saver: LocalFileSaver (saves to local filesystem)
- Worker: ThreadWorker (threaded execution)

Usage:
    python main.py --ui cli    # Use command-line interface
    python main.py --ui tk     # Use graphical interface (default)
    python main.py             # Use graphical interface (default)

The module automatically loads all available formats and initializes the
converter with appropriate components based on the selected interface.
"""

import argparse
import logging
import formats
import os

from config import APIConfig
from converter import Converter

from processors.local_processor import LocalProcessor
from processors.processor_on_docker import ProcessorOnDocker, TextRedirector
from processors.remote_processor import GenericRemoteProcessor, ApiServiceCur

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

# Load all format modules
formats.load_formats()

# Access the registry
print("Available formats:", list(formats.registry.keys()))


def main() -> None:
    """Main application entry point.

    Parses command-line arguments to determine the user interface type,
    initializes the converter with appropriate components, and starts
    the selected interface.

    The function sets up:
    - Argument parsing for UI selection
    - Component initialization (processor, saver, worker)
    - Converter instantiation with dependency injection
    - Interface startup

    Command-line Arguments:
        --ui {cli,tk}: User interface type (default: tk)
    """
    # parser = argparse.ArgumentParser(description="E-book Converter Application")
    # parser.add_argument(
    #     "--ui",
    #     type=str,
    #     choices=["cli", "tk"],
    #     default="tk",
    #     help="Choose the user interface: 'cli' for Command-Line, 'tk' for Tkinter GUI",
    # )
    # args = parser.parse_args()
    #
    # if args.ui == "cli":
    #     interface = ConverterInterfaceCLI()
    # else:
    #     interface = ConverterInterfaceTk()

    # Step 1: setup interface
    interface = ConverterInterfaceCLI()

    # Step 2: setup main processor
    processor = ProcessorOnDocker(TextRedirector(interface))
    # processor = GenericRemoteProcessor(ApiServiceCur())

    # Step 3: setup saver
    saver = LocalFileSaver()

    # Step 4: setup Converter with required params and non-blocking worker
    worker = ThreadWorker()
    converter = Converter(interface, processor, saver, worker)  # type: ignore[arg-type]

    # Step 5: run converter with interface
    interface.run(converter)


if __name__ == "__main__":
    main()
