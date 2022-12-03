import sys
import os

from typing import Protocol

import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk


from utils import parse_command, get_path, ParamsError
from config import Target, JobConfig
from processor import JobProcessor

work_dir = os.path.abspath(__file__)


class UIProtocol(Protocol):
    def setup(self, processor: JobProcessor, *args, **kwargs) -> bool:
        raise NotImplementedError

    def display_job_status(self, status):
        raise NotImplementedError

    def display_job_result(self, result):
        raise NotImplementedError

    def display_job_id(self, job_id):
        raise NotImplementedError

    def display_errors(self, errors: list):
        raise NotImplementedError


class DummyUI:
    def __init__(self, processor, converter, worker=None):
        self.processor = processor
        self.converter = converter
        self.worker = worker

    def run(self):
        pass

    def setup(self, processor: JobProcessor) -> bool:
        print(f"DUMMY UI: setup {processor}")
        return True

    def display_job_status(self, status):
        print(f"DUMMY UI: display status {status}")

    def display_job_result(self, result):
        print(f"DUMMY UI: display result {result}")

    def display_job_id(self, job_id):
        print(f"DUMMY UI: display ID {job_id}")

    def display_errors(self, errors: list):
        for error in errors:
            print(f"DUMMY UI: ERROR: {error}")


def yes_no(message="run [N/y] ?"):
    res = input(message)
    if res.lower() == "y":
        return True
    return False


class ConverterInterfaceCLI:
    docstring = """
>>> INTERFACE command needs:
    -path - full/path/to/file
    -name - file_name in current directory
    -t - [target] - string of file format(default "mobi")
    -cat - [category] - category of formatting file (default "ebook")
    """

    def run(self, processor: JobProcessor):
        return self.setup(processor) and yes_no()

    def display_job_status(self, status):
        print(f">>> INTERFACE STATUS: {status}")

    def display_job_result(self, result):
        print(f">>> INTERFACE RESULT: {result}")

    def display_job_id(self, job_id):
        print(f">>> INTERFACE JOB ID: {job_id}")

    def display_errors(self, errors: list):
        self.display_job_status("error")
        for error in errors:
            print(f">>> INTERFACE ERROR: {error}")

    def setup(self, processor: JobProcessor):
        try:
            args = self._get_params(sys.argv)
        except ParamsError:
            print(self.docstring)
            return False

        job_config = JobConfig(*args)
        processor.job_config = JobConfig(*args)
        print(f"TEST INTERFACE: {processor.job_config = }")
        return job_config

    def _get_params(self, args: tuple) -> tuple:
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

        target_object = Target(working_target, working_category)
        print(
            ">>> INTERFACE (Params):\n",
            f"{working_file_path = }\n",
            f"{working_target = }\n",
            f"{working_category = }\n",
            f"{target_object = }\n"
        )
        return target_object, working_file_path


class ConverterInterfaceTk:
    def __init__(self):
        self.view = TkView(self)
        self.view.run()

    def convert(self):
        # self.view.run()
        print(f"RUN CONVERT {self}")

    def setup(self, processor: JobProcessor):
        pass

    def display_job_status(self, status):
        raise NotImplementedError

    def display_job_result(self, result):
        raise NotImplementedError

    def display_job_id(self, job_id):
        raise NotImplementedError

    def display_errors(self, errors: list):
        raise NotImplementedError


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
        self.interface.convert()

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


def main():
    inter = ConverterInterfaceTk()
    inter.view.run()


if __name__ == '__main__':
    main()
