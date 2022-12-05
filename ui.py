import sys
import os

from typing import Protocol, Any

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
        self.converter = None

    def run(self):
        print("RUN")
        self.view.set_status("convert")
        config = self.setup()
        print(f"CONFIG RUN: : {config = }")
        return config

    def setup(self):
        print(f"SETUP {self}")
        args = self._get_params()
        print(f"PARAMS: {args = }")
        job_config = JobConfig(*args)
        print(f"CONFIG: : {job_config = }")
        return job_config

    def _get_params(self):
        target_object = Target(
            self.view.get("target"),
            self.view.get("category")
        )
        path_to_file = self.view.get("path_to_file")
        print(f"SETUP {target_object = } {path_to_file = }")
        return target_object, path_to_file

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

    docstring = """
    -path - full/path/to/file
    -name - file_name in current directory
    -t - [target] - string of file format(default "mobi")
    -cat - [category] - category of formatting file (default "ebook")
    """

    def __init__(self, interface):
        self.interface = interface
        self.root = tk.Tk()

        self.root.title('gui')
        self.root.geometry('600x300')
        self.app = tk.Frame(self.root)
        self._config: dict[str] = {}

    def create_view(self):
        self.app.grid()

        # add buttons section
        self.convert_btn = tk.Button(self.app, text='Convert', command=self.interface_convert)
        self.convert_btn.grid(column=0, row=0)

        self.open_file_btn = tk.Button(self.app, text="Open file", command=self.open_file)
        self.open_file_btn.grid(column=1, row=0)

        self.quit_btn = tk.Button(self.app, text="Quit", command=self.root.destroy)
        self.quit_btn.grid(column=5, row=0)

        # add options section
        self.check_targer = tk.StringVar()
        tk.Checkbutton(
            self.app,
            text="taget",
            variable=self.check_targer,
            command=lambda: self.update_text(self.check_targer.get()),
        ).grid(column=0, row=2)

        j_vars = tk.Variable(value=self.JOB_VARIANTS)
        f_vars = tk.Variable(value=self.FORMAT_VARIANTS)

        self.list_box = ttk.Combobox(
            self.app,
            textvariable=j_vars,
            state="readonly",
            values=self.JOB_VARIANTS)
        self.list_box.grid(column=0, row=1, columnspan=2)
        self.list_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.set_data("category", self.list_box.get())
        )

        self.list_box2 = ttk.Combobox(
            self.app,
            textvariable=f_vars,
            state="readonly",
            values=self.FORMAT_VARIANTS)
        self.list_box2.grid(column=2, row=1)
        self.list_box2.bind(
            "<<ComboboxSelected>>",
            lambda event: self.set_data("target", self.list_box2.get())
        )

        # add status and info section
        self.result_txt = tk.Text(self.app, width=40, height=5, wrap=tk.WORD)
        self.result_txt.grid(row=11, column=0, columnspan=3)

        self.status_field = tk.Text(self.app, width=20, height=1)
        self.status_field.grid(column=2, row=0, columnspan=2)

    def set_data(self, key, value):
        self._config[key] = value

    def item_select(self, event):
        print(f"TEST: {event = }")
        msg = self.list_box.get()
        print(f"TEST: {msg = }")

    def interface_convert(self):
        print(f"{self.list_box = } {self.list_box.get() = }")
        if not (self.list_box.get() and self.list_box2.get()):
            self.update_text(self.docstring)
            return False
        self.interface.run()
        return True

    def open_file(self):
        filetypes = (
            ('book files', '*.mobi'),
            ('book files', '*.fb2'),
            ('text files', '*.txt'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir=work_dir,
            filetypes=filetypes)

        print(f"{filename = }")
        self._config["path_to_file"] = filename

        tk.messagebox.showinfo(
            title='Selected File',
            message=filename or "file not selected"
        )

    def update_text(self, message):
        self.result_txt.delete(0.0, tk.END)
        self.result_txt.insert(0.0, message)

    def set_status(self, msg):
        self.status_field.delete(0.0, tk.END)
        self.status_field.insert(0.0, msg)

    def get(self, key: str) -> Any:
        return self._config.get(key)

    def run(self):
        self.create_view()
        self.set_status("ready")
        self.root.mainloop()


def main():
    inter = ConverterInterfaceTk()
    inter.view.run()


if __name__ == '__main__':
    main()
