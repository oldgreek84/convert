from __future__ import annotations

import tkthread

# NOTE: allow to call methods in another tk thread
tkthread.patch()

import tkinter as tk
import tkinter.filedialog as fd
from pathlib import Path
from typing import TYPE_CHECKING, Any

import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox

from config import ConverterStatus, Target
from config import JobConfig as Config

if TYPE_CHECKING:
    from converter import Converter

work_dir = Path(__file__)

CONVERTER_FORMATS_MAPPING = {
    "pdf": ["mobi"],
    "mobi": ["fb2", "txt", "epub"],
    "fb2": ["mobi", "txt", "epub"],
    "ebook": ["mobi", "fb2", "epub", "txt"],
}


class ConverterInterfaceTk:
    """Tkinter-based graphical user interface for the e-book converter.

    This class provides a modern, user-friendly GUI for the converter using
    the Tkinter library with ttkbootstrap for enhanced styling. It offers
    intuitive file selection, format configuration, and real-time progress
    monitoring through a graphical interface.

    Features:
        - Modern dark theme with ttkbootstrap
        - File browser integration for easy file selection
        - Dropdown menus for format selection with smart defaults
        - Real-time progress bar and status updates
        - Threaded execution to prevent UI freezing
        - Error dialogs and success notifications
        - Save-as dialog for converted files
        - Format compatibility validation

    Components:
        - File selection area with browse button
        - Format selection dropdowns (from/to)
        - Convert button with progress indication
        - Status display and message area
        - Progress bar for conversion monitoring

    The interface uses the Model-View pattern where this class acts as
    the controller and TkView handles the actual UI rendering and events.

    Attributes:
        view: TkView instance handling the UI rendering
        converter: Reference to the converter instance
        config: Current job configuration

    Example:
        >>> interface = ConverterInterfaceTk()
        >>> converter = Converter(interface, processor, saver)
        >>> interface.run(converter)
    """

    def __init__(self) -> None:
        self.view: TkView = TkView(self)
        self.view.create_view()

    def run(self, converter: Converter) -> None:
        self.converter = converter
        self.view.run()

    def setup(self) -> Config:
        args = self._get_params()
        self.config = Config(*args)
        return self.config

    def convert(self, config: Config) -> None:
        self.converter.convert(config)

    def _get_params(self) -> tuple[Target, Any]:
        target_object = Target(self.view.get_param("target"), self.view.get_param("category"))
        path_to_file = self.view.get_param("path_to_file")
        return target_object, path_to_file

    def get_config(self):
        return self.config

    def display_job_status(self, status: ConverterStatus) -> None:
        self.view.set_status(status)

    def display_common_info(self, message: str, status: ConverterStatus | None = None) -> None:
        if status is not None:
            self.display_job_status(status)
        self.view.add_text_message(message)

    def display_job_result(self, result: Path | str) -> None:
        self.view.add_text_message(result)
        with open(result, "rb") as file:
            tkthread.call_nosync(self.view.processing_result, result, file.read())

    def display_job_id(self, job_id: str) -> None:
        self.view.update_text_message(job_id)

    def display_error(self, error: str, status: ConverterStatus) -> None:
        self.display_job_status(status)
        tkthread.call_nosync(self.view.show_message, error, "show_error")
        self.view.processing_error(error)


class TkView:
    """View component handling the actual Tkinter UI rendering and events.

    This class is responsible for creating and managing all the visual
    components of the Tkinter interface, handling user interactions,
    and updating the display based on application state changes.

    The view implements a modern dark-themed interface using ttkbootstrap
    with organized sections for different functionality areas.

    UI Layout:
        - Header: Title and instructions
        - Format Selection: From/To format dropdowns with smart defaults  
        - File Operations: File browser, path display, convert button
        - Status Section: Progress bar and status text field
        - Results Area: Scrollable text area for messages and results

    Features:
        - Responsive layout with proper spacing
        - Format compatibility checking and auto-selection
        - Real-time progress indication
        - Error and success message dialogs
        - File save dialog integration
        - Thread-safe UI updates

    Attributes:
        interface: Reference to the parent interface controller
        root: Main window widget using ttkbootstrap theming
        _config: Internal configuration state storage
        Various UI components: frames, buttons, text fields, etc.
    """

    def __init__(self, interface: ConverterInterfaceTk) -> None:
        """Initialize the view with the parent interface.

        Args:
            interface: Parent ConverterInterfaceTk instance for callbacks
        """
        self.interface = interface
        self.root = ttkb.Window(title="Simple Converter", themename="darkly")
        self.root.geometry("800x550")
        self._config: dict[str, Any] = {}

    def create_view(self) -> None:
        # get window params
        screen_width = self.root.winfo_width()

        # add label
        label_title = ttkb.Label(self.root, text="Please, choose file and format to convert")
        label_title.pack(pady=10)

        # SET SECTION ONE
        # options to set converter direction
        self.frame2 = ttkb.Frame(self.root)
        self.frame2.pack(pady=10)

        options = {"from": ["fb2", "txt", "epub", "pdf"], "to": ["mobi", "fb2"]}

        self.selection_from = ttkb.Combobox(self.frame2, bootstyle="info", values=options["from"])  # type: ignore[call-arg]
        self.selection_from.grid(column=1, row=0, padx=10)
        self.selection_from.current(0)
        self.selection_from.bind("<<ComboboxSelected>>", self.bind_convert_direction_from)

        self.selection_to = ttkb.Combobox(self.frame2, bootstyle="info", values=options["to"])  # type: ignore[call-arg]
        self.selection_to.grid(column=2, row=0, padx=10)
        self.selection_to.current(0)
        self.selection_to.bind("<<ComboboxSelected>>", self.bind_convert_direction_to)

        # SET SECTION TWO
        # add buttons
        self.frame1 = ttkb.Frame(self.root)
        self.frame1.pack(pady=10)

        button_open_file = ttkb.Button(  # type: ignore[call-arg]
                                       self.frame1, text="Open File", bootstyle="info", command=self.open_file  # type: ignore[call-arg]
                                       )
        button_open_file.grid(row=0, column=1, padx=10)

        # add field to show/select file to convert
        self.file_field = tk.Text(self.frame1, width=20, height=1)
        self.file_field.grid(column=2, row=0, padx=10)
        self.file_field.bind("<Button-1>", lambda event: self.open_file())

        button_convert = ttkb.Button(  # type: ignore[call-arg]
                                     self.frame1,
                                     text="Convert",
                                     bootstyle="success, outline",  # type: ignore[call-arg]
                                     command=self.interface_convert,
                                     )
        button_convert.grid(row=0, column=3, padx=10)

        button_quit = ttkb.Button(  # type: ignore[call-arg]
                                  self.frame1, text="Quit", bootstyle="danger", command=self.root.destroy  # type: ignore[call-arg]
                                  )
        button_quit.grid(row=0, column=4, padx=10)

        # SET SECTION FOUR
        # add status field
        self.frame3 = ttkb.Frame(self.root)
        self.frame3.pack(pady=10)

        self.status_field = ttkb.Text(self.frame3, width=20, height=1)
        self.status_field.grid(column=2, row=0, padx=10)

        # set progress bar
        self.progress_bar = ttkb.Progressbar(self.frame3, length=360)
        self.progress_bar.grid(column=1, row=0, padx=10)

        # SET SECTION FIFE
        # set text area
        self.result_txt = ttkb.Text(self.root, width=screen_width, height=100)
        self.result_txt.pack(pady=10, padx=10, fill=tk.X)

    def bind_convert_direction_from(self, event):
        current_val = self.selection_from.get()
        default = "mobi"
        list_of_possible = CONVERTER_FORMATS_MAPPING.get(current_val, [default])
        self.selection_to.set(list_of_possible[0])

    def bind_convert_direction_to(self, event):
        current_val = self.selection_to.get()
        default = "fb2"
        list_of_possible = CONVERTER_FORMATS_MAPPING.get(current_val, [default])
        self.selection_from.set(list_of_possible[0])

    def bind_convert_direction(self, event, direction="mobi"):
        current_val = self.selection_to.get()
        list_of_possible = CONVERTER_FORMATS_MAPPING.get(current_val, [direction])
        self.selection_from.set(list_of_possible[0])

    def bind_open_file_tap(self, event):
        self.open_file()

    def set_config(self):
        self.set_data("path_to_file", self.file_field.get("0.0", "end").strip("\n"))
        self.set_data("category", "ebook")
        self.set_data("target", self.selection_to.get())

    def set_data(self, key: Any, value: Any) -> None:
        self._config[key] = value

    def interface_convert(self) -> bool:
        """Run convert processing in UI"""
        self.update_text_message("")
        self.set_config()
        config = self.interface.setup()
        self.progress_bar.start()
        self.interface.convert(config)
        return True

    def processing_error(self, error: str) -> None:
        self.add_text_message(error)
        self.progress_bar.stop()

    def processing_result(self, result: Path, content: bytes):
        self.progress_bar.stop()
        self.download_result(result.name, content)

    def open_file(self) -> None:
        self.file_field.delete(0.0, "end")
        filetypes = (("Ebook files", f"*.{self.selection_from.get()}"), ("All files", "*.*"))
        filename = fd.askopenfilename(title="Open a file", initialdir=work_dir, filetypes=filetypes)
        self.file_field.insert(0.0, filename)

    def download_result(self, filename: str, converted_file_content: bytes) -> None:
        file_path = fd.asksaveasfilename(
            initialfile=filename,
            initialdir=".",
            defaultextension=f".{self.selection_to.get()}",
            filetypes=[("Ebook files", f"*.{self.selection_to.get()}"), ("All Files", "*.*")],
            title="Save Converted eBook",
        )

        if not file_path:
            return

        try:
            with open(file_path, "wb") as file:
                file.write(converted_file_content)
            self.show_message(f"File saved: {file_path}")
        except Exception as exc:
            self.show_message(f"Failed to save file: {exc}", "show_error")

    def add_text_message(self, message: str | Path) -> None:
        if not isinstance(message, str):
            return

        self.result_txt.insert(tk.END, message.strip() + "\n")
        self.result_txt.see(tk.END)

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

    def show_message(self, message: str, message_type="show_info") -> None:
        """Show message in popup window"""
        dialog_window = getattr(Messagebox, message_type)
        dialog_window(title="Converter Info", message=message)

    def run(self) -> None:
        self.root.mainloop()
