import sys
import os

from typing import Protocol, Any, Optional, Union
from pathlib import Path

import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk


from utils import parse_command, get_path, ParamsError
from config import Target, JobConfig
from processor import JobProcessor

# TODO: refactoring resolve circular import by factory
# from converter import Converter

work_dir = os.path.abspath(__file__)


class UIProtocol(Protocol):
    def run(self, converter) -> None:
        raise NotImplementedError

    def setup(self) -> JobConfig:
        raise NotImplementedError

    def convert(self) -> None:
        raise NotImplementedError

    def display_message(self, message: str) -> None:
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
    def __init__(self):
        self.converter = None

    def run(self, converter) -> None:
        print(f"DUMMY UI: RUN {converter}")

    def setup(self) -> JobConfig:
        print("DUMMY UI: SETUP")

    def convert(self) -> None:
        print("DUMMY UI: CONVERT")

    def display_job_status(self, status):
        print(f"DUMMY UI: display status {status}")

    def display_job_result(self, result):
        print(f"DUMMY UI: display result {result}")

    def display_job_id(self, job_id):
        print(f"DUMMY UI: display ID {job_id}")

    def display_errors(self, errors: list):
        for error in errors:
            print(f"DUMMY UI: ERROR: {error}")


def yes_no(message="Do you want to run convert[N/y]?: "):
    res = input(message)
    if res.lower() == "y":
        return True
    return False


class ConverterInterfaceCLI:
    docstring = """
    command needs:
    -path - full/path/to/file
    -name - file_name in current directory
    -t - [target] - string of file format(default "mobi")
    -cat - [category] - category of formatting file (default "ebook")
    """

    def __init__(self):
        self.converter = None

    def convert(self) -> None:
        self.converter.convert()

    def run(self, converter) -> None:
        self.converter = converter
        try:
            config = self.setup()
            self.converter.set_config(config)
        except Exception as ex:
            self.display_errors([f"Something wrong with config {config}", f"{ex}"])

        if yes_no():
            self.convert()

    def setup(self) -> JobConfig:
        try:
            args = self._get_params(sys.argv)
        except ParamsError:
            self.display_message(self.docstring)
            return False

        return JobConfig(*args)

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

        msg = f"\n{'=' * 80}\nPARAMS:\n\
            {working_file_path = }\n\
            {working_target = }\n\
            {working_category = }\n\
            {target_object = }\n\
            {'=' * 80}"
        self.display_message(msg)
        return target_object, working_file_path

    def display_message(self, message: str) -> None:
        print(f" INTERFACE MESSAGE: {message}")

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


class ConverterInterfaceTk:
    def __init__(self) -> None:
        self.converter = None
        self.view = TkView(self)

    def run(self, converter) -> None:
        self.converter = converter
        self.view.run()

    def setup(self) -> JobConfig:
        args = self._get_params()
        return JobConfig(*args)

    def convert(self) -> None:
        self.converter.set_config(self.setup())
        self.converter.convert()

    def _get_params(self) -> tuple[Target, Path]:
        target_object = Target(
            self.view.get("target"),
            self.view.get("category")
        )
        path_to_file = self.view.get("path_to_file")
        return target_object, path_to_file

    def display_job_status(self, status: str) -> None:
        self.view.set_status(status)

    def display_job_result(self, result: Optional[Union[Path, str]]) -> None:
        self.view.update_text(result)
        self.view.show_message(result)

    def display_job_id(self, job_id: str) -> None:
        self.view.update_text(job_id)

    def display_errors(self, errors: list) -> None:
        errors = "\n".join(errors)
        self.view.update_text(errors)
        self.view.show_message(errors)


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
        self.open_file_btn.grid(column=0, row=2)

        self.quit_btn = tk.Button(self.app, text="Quit", command=self.root.destroy)
        self.quit_btn.grid(column=5, row=0)

        # add options section
        self.check_targer = tk.StringVar()
        tk.Checkbutton(
            self.app,
            text="taget",
            variable=self.check_targer,
            command=lambda: self.update_text(self.check_targer.get()),
        ).grid(column=0, row=3)

        j_vars = tk.Variable(value=self.JOB_VARIANTS)
        f_vars = tk.Variable(value=self.FORMAT_VARIANTS)

        self.list_box = ttk.Combobox(
            self.app,
            textvariable=j_vars,
            state="readonly",
            values=("ebook", "video"),
        )
        self.list_box.current(1)
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
        self.list_box2.current(1)
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

        self.file_field = tk.Text(self.app, width=20, height=1)
        self.file_field.grid(column=1, row=2, columnspan=3)

    def set_data(self, key, value):
        self._config[key] = value

    def interface_convert(self):
        if not (self.list_box.get() and self.list_box2.get()):
            self.update_text(self.docstring)
            return False
        self.interface.convert()
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

        self._config["path_to_file"] = filename

        self.file_field.insert(0.0, filename)

    def update_text(self, message):
        self.result_txt.delete(0.0, tk.END)
        self.result_txt.insert(0.0, message)

    def set_status(self, msg):
        self.status_field.delete(0.0, tk.END)
        self.status_field.insert(0.0, msg)

    def get(self, key: str) -> Any:
        return self._config.get(key)

    def show_message(self, message):
        tk.messagebox.showinfo(title="Info", message=message)

    def run(self):
        self.create_view()
        self.set_status("ready")
        self.root.mainloop()


def main():
    inter = ConverterInterfaceTk()
    inter.view.run()


if __name__ == '__main__':
    main()
