import sys
import os
import time

from abc import ABC, abstractmethod
from typing import Protocol

import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk


from utils import parse_command, get_path, ParamsError
from config import Target, JobConfig
from processing_job import JobProcessor

work_dir = os.path.abspath(__file__)


class UI(Protocol):
    def setup(self) -> None:
        raise NotImplementedError

    def run(self) -> None:
        raise NotImplementedError


class ConverterInterface(ABC):
    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def run(self):
        pass


class ConverterInterfaceCLI(ConverterInterface):
    docstring = """
    command needs:
    -path - full/path/to/file
    -name - file_name in current directory
    -t - [target] - string of file format(default "mobi")
    -cat - [category] - category of formatting file (default "ebook")
    """

    def __init__(self, processor):
        self.processor = processor

    def setup(self):
        args = self._get_params(sys.argv)
        self.processor.job_config(*args)

    def run(self):
        try:
            self.setup()
        except ParamsError:
            print(self.docstring)

        if not self.processor:
            return False

        self._run()
        return True

    def _run(self):
        print(">>> INTERFACE: start FIRST convert --------------------------")
        self.processor.convert()

        work_id = self.processor.get_processor_data("work_id")
        print("File was sent. Please wait...")
        print(f"Work ID: {work_id}")

        print(">>> INTERFACE: START status loop ----------------------------")
        self._get_status()
        print(">>> INTERFACE: END status loop ------------------------------")

        result_path = self.processor.get_processor_data("uri_to_downloas_file")
        print(f"Result path: {result_path}")

        full_path = self.processor.get_processor_data("result")
        print(f"File was saved to: {full_path}")

        print(">>> INTERFACE: END ------------------------------------------")
        return full_path

    def _get_status(self):
        while not self.processor.is_completed():
            time.sleep(3)
            status = self.processor.get_job_status()
            print(f">>> INTERFACE: {status = } {self.processor.is_completed() = } ")
            print(f">>> INTERFACE: {status = } {self.processor.worker.get_result() = } ")
            print(f">>> INTERFACE: {status = } {self.processor.worker.is_completed() = } ")

    def _get_params(self, args):
        if len(args) == 1:
            raise ParamsError

        data_settings = parse_command()
        if data_settings.get("-path"):
            working_file_path = data_settings["-path"]
        elif data_settings.get("-name"):
            working_file_path = get_path(data_settings["-name"])
        else:
            working_file_path = sys.argv[1]

        working_target = data_settings.get("-t", "mobi")
        working_category = data_settings.get("-cat", "ebook")

        print(f">>> INTERFACE (Params):\n {working_file_path}\n{working_target}\n{working_category}")
        target_object = Target(working_target, working_category)
        return target_object, working_file_path


class ConverterInterfaceTk(ConverterInterface):
    def __init__(self, job):
        self.job = job
        self.view = TkView(self)

    def run(self):
        self.view.run()

    def convert(self):
        print("Convert")
        self.job.convert()

    def setup(self):
        pass


class TkView:
    JOB_VARIANTS = ("ebook", "video")
    FORMAT_VARIANTS = ("mobi", "pdf")

    def __init__(self, interface):
        self.interface = interface
        self.root = tk.Tk()

        self.root.title('gui')
        self.root.geometry('600x300')
        self.app = tk.Frame(self.root)

    def create_view(self):
        self.app.grid()

        butn = tk.Button(self.app, text='Convert', command=self.interface_convert)
        butn.grid()

        butn2 = tk.Button(self.app, text="Open file", command=self.open_file)
        butn2.grid()

        quit_btn = tk.Button(self.root, text="Quit", command=self.root.destroy)
        quit_btn.grid()

        j_vars = tk.Variable(value=self.JOB_VARIANTS)
        f_vars = tk.Variable(value=self.FORMAT_VARIANTS)

        self.list_box = ttk.Combobox(
            self.root,
            textvariable=j_vars,
            state="readonly",
            values=self.JOB_VARIANTS)
        self.list_box.grid()
        self.list_box.bind("<<ComboboxSelected>>", self.item_select)

        self.list_box2 = ttk.Combobox(
            self.root,
            textvariable=f_vars,
            state="readonly",
            values=self.FORMAT_VARIANTS)
        self.list_box2.grid()
        self.list_box2.bind("<<ComboboxSelected>>", self.item_select(self.list_box2))

    def item_select(self, event):
        print(event)
        msg = self.list_box.get()
        print(msg)

    def interface_convert(self):
        self.interface.convert(self.interface)

    def open_file(self):
        filetypes = (
            ('text files', '*.txt'),
            ('book files', '*.mobi'),
            ('book files', '*.fb2'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir=work_dir,
            filetypes=filetypes)

        print(filename)

        tk.messagebox.showinfo(
            title='Selected File',
            message=filename or "file not selected"
        )

    def run(self):
        self.create_view()
        self.root.mainloop()
