try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

from processor import JobProcessorRemote
from ui import ConverterInterfaceCLI, ConverterInterfaceTk
from worker import ThreadWorker
from converter import Converter

load_dotenv()


def main() -> None:
    interface = ConverterInterfaceCLI()
    worker = ThreadWorker()
    processor = JobProcessorRemote()
    converter = Converter(interface, processor, worker)
    interface.run(converter)


if __name__ == "__main__":
    main()
