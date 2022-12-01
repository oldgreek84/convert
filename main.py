try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

from processor import (
    JobProcessorRemote,
    JobProcessorDummy,
)
from config import JobConfig
from ui import ConverterInterfaceCLI, ConverterInterfaceTk, DummyUI
from worker import Worker1, Worker2, Worker3, Worker4
from converter import Converter

load_dotenv()


def main() -> None:
    cli = DummyUI()
    worker = Worker4()
    processor = JobProcessorDummy()
    converter = Converter(cli, processor, worker)
    converter.convert()


if __name__ == "__main__":
    main()
