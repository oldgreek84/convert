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
    python main.py             # Use graphical interface (default)

The module automatically loads all available formats and initializes the
converter with appropriate components based on the selected interface.
"""

import logging

import formats
from processors.processor_on_docker import ProcessorOnDocker, TextRedirector
from savers.local_saver import LocalFileSaver
from src.application import AppPresenter
from src.converter import Converter

# from uis.cli_ui import CLIView
from uis.tk_ui import TkView
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
print("Available formats:", [f.name for f in formats.registry.get_all()])


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
    """
    # Step 1: setup interface
    # user_interface = CLIView()
    user_interface = TkView()

    # Step 2: setup main processor
    processor = ProcessorOnDocker(TextRedirector(user_interface))
    # processor = GenericRemoteProcessor(ApiServiceCur())

    # Step 3: setup saver
    saver = LocalFileSaver()
    # saver = GoogleDriveSaver()

    # Step 4: setup Converter with required params and non-blocking worker
    worker = ThreadWorker()
    converter = Converter(processor, saver, worker)  # type: ignore[arg-type]

    # Step 5: run processing with presenter
    presenter = AppPresenter(converter, user_interface)
    presenter.run()


if __name__ == "__main__":
    main()
