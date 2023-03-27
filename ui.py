import os
import sys
import tkinter as tk
import tkinter.filedialog as fd
from pathlib import Path
from tkinter import ttk
from typing import Any, Optional, Protocol, Union, runtime_checkable

from config import JobConfig, Target
from utils import ParamsError, get_path, parse_command

# TODO: refactoring resolve circular import by factory
# from converter import Converter

work_dir = os.path.abspath(__file__)


@runtime_checkable
class UIProtocol(Protocol):
    def run(self, converter) -> None:
        raise NotImplementedError

    def setup(self) -> JobConfig:
        raise NotImplementedError

    def convert(self, config: JobConfig) -> None:
        raise NotImplementedError

    def display_message(self, message: str) -> None:
        raise NotImplementedError

    def display_job_status(self, status) -> None:
        raise NotImplementedError

    def display_job_result(self, result) -> None:
        raise NotImplementedError

    def display_job_id(self, job_id) -> None:
        raise NotImplementedError

    def display_error(self, error: str) -> None:
        raise NotImplementedError


def yes_no(message="Do you want to run convert[N/y]?: "):
    return input(message).lower() == 'y'


class ConverterInterfaceCLI:
    docstring = """
    command needs:
    -path - full/path/to/file
    -name - file_name in current directory
    -t - [target] - string of file format(default "mobi")
    -cat - [category] - category of formatting file (default "ebook")
    """

    def __init__(self) -> None:
        self.converter = None

    def convert(self, config: JobConfig) -> None:
        self.converter.convert(config)

    def run(self, converter) -> None:
        self.converter = converter
        try:
            config = self.setup()
        except Exception as ex:
            self.display_error(f"Something wrong: {ex}")
            config = None

        if yes_no():
            self.convert(config)

    def setup(self) -> Optional[Union[JobConfig, bool]]:
        try:
            args = self._get_params(sys.argv)
        except ParamsError:
            self.display_message(self.docstring)
            return False

        return JobConfig(*args)

    def _get_params(self, args: list) -> tuple:
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

        msg = f"\n{'=' * 80}\nPARAMS:\
                \n\t{working_file_path = }\
                \n\t{working_target = }\
                \n\t{working_category = }\
                \n\t{target_object = }\
                \n{'=' * 80}"
        self.display_message(msg)
        return target_object, working_file_path

    def display_message(self, message: str) -> None:
        print(f">>> INTERFACE MESSAGE: {message}")

    def display_job_status(self, status):
        print(f">>> INTERFACE STATUS: {status}")

    def display_job_result(self, result):
        print(f">>> INTERFACE RESULT: {result}")

    def display_job_id(self, job_id):
        print(f">>> INTERFACE JOB ID: {job_id}")

    def display_error(self, error: str):
        self.display_job_status("error")
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
        self.converter.convert(self.setup())

    def _get_params(self) -> tuple[Target, Path]:
        target_object = Target(
            self.view.get_param("target"),
            self.view.get_param("category")
        )
        path_to_file = self.view.get_param("path_to_file")
        return target_object, path_to_file

    def display_job_status(self, status: str) -> None:
        self.view.set_status(status)

    def display_job_result(self, result: Optional[Union[Path, str]]) -> None:
        self.view.update_text(result)
        self.view.show_message(result)

    def display_job_id(self, job_id: str) -> None:
        self.view.update_text(job_id)

    def display_error(self, error: str) -> None:
        self.display_job_status("error")
        self.view.update_text(error)
        self.view.show_message(error)


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
        self.list_box_value = tk.Variable(value=self.JOB_VARIANTS)
        self.list_box2_value = tk.Variable(value=self.FORMAT_VARIANTS)

        self.list_box = ttk.Combobox(
            self.app,
            textvariable=self.list_box_value,
            state="readonly",
            values=self.JOB_VARIANTS
        )
        self.list_box.current(0)
        self.list_box.grid(column=0, row=1, columnspan=2)
        self.list_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.set_data("category", self.list_box.get())
        )
        self.set_data("category", self.list_box.get())

        self.list_box2 = ttk.Combobox(
            self.app,
            textvariable=self.list_box2_value,
            state="readonly",
            values=self.FORMAT_VARIANTS)
        self.list_box2.current(0)
        self.list_box2.grid(column=2, row=1)
        self.list_box2.bind(
            "<<ComboboxSelected>>",
            lambda event: self.set_data("target", self.list_box2.get())
        )
        self.set_data("target", self.list_box2.get())

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

    def get_param(self, key: str) -> Any:
        return self._config.get(key)

    def show_message(self, message):
        tk.messagebox.showinfo(title="Info", message=message)

    def run(self):
        self.create_view()
        self.set_status("ready")
        self.root.mainloop()


def main():
    interface = ConverterInterfaceTk()
    interface.view.run()


if __name__ == '__main__':
    main()
