from __future__ import annotations

import tkinter as tk
import tkinter.filedialog as fd
from tkinter import scrolledtext
from tkinter import ttk

from pathlib import Path
from typing import Any

from uis import DOCSTRING
from config import JobConfig as Config, Target

work_dir = Path(__file__)


# TODO: add button on interface to upload results
class ConverterInterfaceTk:
    """User interface with WM is written by TK python library.
    Has simple user interface.
    """

    def __init__(self) -> None:
        self.converter: Any = None
        self.view = TkView(self)

    def run(self, converter) -> None:
        self.converter = converter
        self.view.run()

    def setup(self) -> Config:
        args = self._get_params()
        return Config(*args)

    def convert(self, config: Config) -> None:
        self.converter.convert(config)

    def _get_params(self) -> tuple[Target, Any]:
        target_object = Target(self.view.get_param("target"), self.view.get_param("category"))
        path_to_file = self.view.get_param("path_to_file")
        return target_object, path_to_file

    def display_job_status(self, status: str) -> None:
        self.view.set_status(status)

    def display_common_info(self, message: str, status: str | None = None) -> None:
        if status is not None:
            self.display_job_status(status)
        self.view.add_text_message(message)

    def display_job_result(self, result: Path | str) -> None:
        self.view.add_text_message(result)
        self.view.show_message(result)

    def display_job_id(self, job_id: str) -> None:
        self.view.update_text_message(job_id)

    def display_error(self, error: str) -> None:
        self.display_job_status("error")
        self.view.add_text_message(error)
        self.view.show_message(error)


# TODO: improve design of view
class TkView:
    job_variants = ("ebook", "video")
    format_variants = ("mobi", "pdf")
    docstring = DOCSTRING

    def __init__(self, interface: ConverterInterfaceTk) -> None:
        self.interface = interface
        self.root = tk.Tk()

        self.root.title("gui")
        self.root.geometry("600x300")
        self.app = tk.Frame(self.root)
        self._config: dict[str, Any] = {}

    def create_view(self) -> None:
        self.app.grid(padx=10, pady=10)

        # Add FIRST row of elements
        # add field to choose a file
        self.file_field = tk.Text(self.app, width=20, height=1)
        self.file_field.grid(column=1, row=0)

        # add buttons section
        self.open_file_btn = tk.Button(self.app, text="Open file", command=self.open_file)
        self.open_file_btn.grid(column=0, row=0)

        self.convert_btn = tk.Button(self.app, text="Convert", command=self.interface_convert)
        self.convert_btn.grid(column=2, row=0)

        self.quit_btn = tk.Button(self.app, text="Quit", command=self.root.destroy)
        self.quit_btn.grid(column=3, row=0)

        # Add SECOND row of elements
        # add status field
        self.label_status = tk.Label(self.app, text="Status:")
        self.label_status.grid(column=0, row=1)
        self.status_field = tk.Text(self.app, width=20, height=1)
        self.status_field.grid(column=1, row=1, columnspan=3)

        # ADD THIRD row of elements
        # add options section
        self.list_box_value = tk.Variable(value=self.job_variants)
        self.list_box2_value = tk.Variable(value=self.format_variants)

        self.list_box = ttk.Combobox(
            self.app, textvariable=self.list_box_value, state="readonly", values=self.job_variants
        )
        self.list_box.current(0)
        self.list_box.grid(column=0, row=3, columnspan=2)
        self.list_box.bind(
            "<<ComboboxSelected>>", lambda event: self.set_data("category", self.list_box.get())
        )
        self.set_data("category", self.list_box.get())

        self.list_box2 = ttk.Combobox(
            self.app,
            textvariable=self.list_box2_value,
            state="readonly",
            values=self.format_variants,
        )
        self.list_box2.current(0)
        self.list_box2.grid(column=2, row=3)
        self.list_box2.bind(
            "<<ComboboxSelected>>", lambda event: self.set_data("target", self.list_box2.get())
        )
        self.set_data("target", self.list_box2.get())

        # ADD LAST row of elements
        # add result area to show common info
        self.result_txt = scrolledtext.ScrolledText(
            self.app, width=60, heigh=10, font=("Times New Roman", 12)
        )
        self.result_txt.grid(row=11, column=0, columnspan=4)

    def set_data(self, key: Any, value: Any) -> None:
        self._config[key] = value

    def interface_convert(self) -> bool:
        """Run convert processing in UI"""
        if not (self.list_box.get() and self.list_box2.get()):
            self.update_text_message(self.docstring)
            return False
        config = self.interface.setup()
        self.interface.convert(config)
        return True

    def open_file(self) -> None:
        filetypes = (("book files", "*.fb2"), ("text files", "*.txt"), ("All files", "*.*"))

        filename = fd.askopenfilename(title="Open a file", initialdir=work_dir, filetypes=filetypes)

        self._config["path_to_file"] = filename

        self.file_field.insert(0.0, filename)

    def add_text_message(self, message: str | Path) -> None:
        if not isinstance(message, str):
            return

        self.result_txt.insert(tk.END, message.strip() + "\n")

    def update_text_message(self, message: str) -> None:
        """Clear old message from text area and write new one"""
        self.result_txt.delete(0.0, tk.END)
        self.result_txt.insert(0.0, message)

    def set_status(self, msg: str) -> None:
        """Show new status in status field"""
        self.status_field.delete(0.0, tk.END)
        self.status_field.insert(0.0, msg)

    def get_param(self, key: str) -> Any:
        return self._config.get(key)

    def show_message(self, message) -> None:
        """Show message in popup window"""
        tk.messagebox.showinfo(title="Info", message=message)

    def run(self) -> None:
        self.create_view()
        self.set_status("ready")
        self.root.mainloop()
