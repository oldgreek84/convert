"""Tkinter View Implementation for MVP Pattern.

This module provides TkView - a passive view implementation using Tkinter
with ttkbootstrap for modern styling. The view implements ViewProtocol
and is responsible only for rendering UI and capturing user input.

All business logic is handled by the Application (Presenter) via callbacks.
Thread-safe UI updates are ensured using the @tk_thread_safe decorator
which wraps methods with tkthread.call_nosync().

Features:
    - Modern dark theme with ttkbootstrap (darkly theme)
    - File browser integration with format filtering
    - Format selection dropdowns with smart defaults
    - Progress bar and status display with color coding
    - Scrollable message area for logs
    - Thread-safe UI updates for background worker support

Example:
    >>> from uis.tk_ui import TkView
    >>> from src.application import Application
    >>> from src.converter import Converter
    >>>
    >>> view = TkView()
    >>> converter = Converter(view, processor, saver, worker)
    >>> app = Application(converter, view)
    >>> app.run()
"""

from __future__ import annotations

import functools

import tkthread

# NOTE: Patch tkinter to allow thread-safe method calls
tkthread.patch()

import tkinter as tk
import tkinter.filedialog as fd
from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox

from src.config import JobConfig as Config
from src.config import Target

if TYPE_CHECKING:
    from collections.abc import Callable

work_dir = Path(__file__)

# Type variables for generic decorator
P = ParamSpec("P")
T = TypeVar("T")


def tk_thread_safe[**P, T](func: Callable[P, T]) -> Callable[P, None]:
    """Decorator to make Tkinter methods thread-safe.

    Wraps the method to execute via tkthread.call_nosync(), ensuring
    the UI update runs on the main Tk thread even when called from
    a background thread (e.g., ThreadWorker).

    Usage:
        @tk_thread_safe
        def show_status(self, status: str) -> None:
            self.status_label.config(text=status)
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        tkthread.call_nosync(lambda: func(*args, **kwargs))

    return wrapper


CONVERTER_FORMATS_MAPPING = {
    "pdf": ["mobi"],
    "mobi": ["fb2", "txt", "epub"],
    "fb2": ["mobi", "txt", "epub"],
    "ebook": ["mobi", "fb2", "epub", "txt"],
}


class TkView:
    """Passive View implementing ViewProtocol with ttkbootstrap styling.

    This view is purely passive - it only renders UI and captures user input.
    All business logic is handled by the Presenter via callbacks.

    Features:
        - Modern dark theme with ttkbootstrap (darkly theme)
        - File browser integration
        - Format selection dropdowns with smart defaults
        - Progress bar and status display
        - Scrollable message area
        - Thread-safe UI updates via tkthread
    """

    def __init__(self) -> None:
        self.root = ttkb.Window(title="E-book Converter", themename="darkly")
        self.root.geometry("800x550")
        self._on_convert: Callable[[], None] | None = None
        self._create_widgets()
        self.config = None

    def _create_widgets(self) -> None:
        """Create all UI widgets with proper styling."""
        # === HEADER SECTION ===
        header_label = ttkb.Label(
            self.root,
            text="E-book Converter",
            font=("Helvetica", 18, "bold"),
            bootstyle="inverse-primary",  # type: ignore[call-arg]
        )
        header_label.pack(pady=(20, 5), fill=tk.X)

        instruction_label = ttkb.Label(
            self.root,
            text="Select a file and target format to convert",
            font=("Helvetica", 10),
        )
        instruction_label.pack(pady=(0, 15))

        # === FORMAT SELECTION SECTION ===
        format_frame = ttkb.Frame(self.root)
        format_frame.pack(pady=10)

        # From format label and combobox
        from_label = ttkb.Label(format_frame, text="From:", font=("Helvetica", 10))
        from_label.grid(row=0, column=0, padx=(0, 5))

        self.selection_from = ttkb.Combobox(
            format_frame,
            bootstyle="info",  # type: ignore[call-arg]
            values=["fb2", "txt", "epub", "pdf", "mobi"],
            width=12,
        )
        self.selection_from.grid(row=0, column=1, padx=10)
        self.selection_from.current(0)
        self.selection_from.bind("<<ComboboxSelected>>", self._on_source_format_change)

        # Arrow label
        arrow_label = ttkb.Label(format_frame, text=">>>", font=("Helvetica", 12, "bold"))
        arrow_label.grid(row=0, column=2, padx=10)

        # To format label and combobox
        to_label = ttkb.Label(format_frame, text="To:", font=("Helvetica", 10))
        to_label.grid(row=0, column=3, padx=(0, 5))

        self.selection_to = ttkb.Combobox(
            format_frame,
            bootstyle="info",  # type: ignore[call-arg]
            values=["mobi", "pdf", "epub", "fb2"],
            width=12,
        )
        self.selection_to.grid(row=0, column=4, padx=10)
        self.selection_to.current(0)
        self.selection_to.bind("<<ComboboxSelected>>", self._on_target_format_change)

        # === FILE SELECTION SECTION ===
        file_frame = ttkb.Frame(self.root)
        file_frame.pack(pady=15, padx=20, fill=tk.X)

        # Open file button
        self.open_btn = ttkb.Button(
            file_frame,
            text="Open File",
            bootstyle="info",  # type: ignore[call-arg]
            command=self._open_file,
            width=12,
        )
        self.open_btn.pack(side=tk.LEFT, padx=(0, 10))

        # File path entry
        self.file_entry = ttkb.Entry(file_frame, font=("Helvetica", 10))
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.file_entry.bind("<Button-1>", lambda e: self._open_file())

        # Convert button
        self.convert_btn = ttkb.Button(
            file_frame,
            text="Convert",
            bootstyle="success",  # type: ignore[call-arg]
            command=self._on_convert_click,
            width=12,
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Quit button
        self.quit_btn = ttkb.Button(
            file_frame,
            text="Quit",
            bootstyle="danger-outline",  # type: ignore[call-arg]
            command=self.root.destroy,
            width=8,
        )
        self.quit_btn.pack(side=tk.LEFT)

        # === STATUS SECTION ===
        status_frame = ttkb.Frame(self.root)
        status_frame.pack(pady=15, padx=20, fill=tk.X)

        # Progress bar
        self.progress_bar = ttkb.Progressbar(
            status_frame,
            bootstyle="success-striped",  # type: ignore[call-arg]
            length=400,
            mode="indeterminate",
        )
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 15))

        # Status label
        status_label_text = ttkb.Label(status_frame, text="Status:", font=("Helvetica", 10))
        status_label_text.pack(side=tk.LEFT, padx=(0, 5))

        self.status_label = ttkb.Label(
            status_frame,
            text="Ready",
            font=("Helvetica", 10, "bold"),
            bootstyle="success",  # type: ignore[call-arg]
            width=15,
        )
        self.status_label.pack(side=tk.LEFT)

        # === MESSAGE AREA SECTION ===
        message_frame = ttkb.LabelFrame(self.root, text="Messages", bootstyle="info")  # type: ignore[call-arg]
        message_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttkb.Scrollbar(message_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text area for messages
        self.message_text = tk.Text(
            message_frame,
            height=12,
            font=("Consolas", 9),
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff",
            yscrollcommand=scrollbar.set,
        )
        self.message_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.message_text.yview)

        # === FOOTER ===
        footer_label = ttkb.Label(
            self.root,
            text="E-book Converter v1.0",
            font=("Helvetica", 8),
            bootstyle="secondary",  # type: ignore[call-arg]
        )
        footer_label.pack(pady=(5, 10))

    def _on_source_format_change(self, event) -> None:
        """Update target format options when source format changes."""
        current = self.selection_from.get()
        targets = CONVERTER_FORMATS_MAPPING.get(current, ["mobi"])
        self.selection_to.config(values=targets)
        if targets:
            self.selection_to.set(targets[0])

    def _on_target_format_change(self, event) -> None:
        """Update source format when target changes (optional auto-select)."""

    def _open_file(self) -> None:
        """Open file dialog and set file path."""
        filetypes = (
            ("E-book files", f"*.{self.selection_from.get()}"),
            ("All e-books", "*.fb2 *.epub *.mobi *.pdf *.txt"),
            ("All files", "*.*"),
        )
        filename = fd.askopenfilename(
            title="Select an e-book file",
            initialdir=Path.home(),
            filetypes=filetypes,
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            # Auto-detect source format from file
            ext = Path(filename).suffix.lstrip(".")
            if ext in ["fb2", "txt", "epub", "pdf", "mobi"]:
                self.selection_from.set(ext)
                self._on_source_format_change(None)

    def _on_convert_click(self) -> None:
        """Handle convert button click - delegates to presenter callback."""
        if self._on_convert:
            self._on_convert()

    def _get_file_path(self) -> str:
        """Get the selected file path from entry widget."""
        return self.file_entry.get().strip()

    def _get_target_format(self) -> str:
        """Get the target format from combobox."""
        return self.selection_to.get()

    # =========================================================================
    # OUTPUT: Display information to user (ViewProtocol)
    # All methods decorated with @tk_thread_safe for thread-safe UI updates
    # =========================================================================

    @tk_thread_safe
    def show_status(self, status: str) -> None:
        """Update status label with appropriate styling (thread-safe)."""
        self.status_label.config(text=status)
        # Update style based on status
        style_map = {
            "ready": "success",
            "processing": "warning",
            "completed": "success",
            "failed": "danger",
        }
        style = style_map.get(status.lower(), "info")
        self.status_label.config(bootstyle=style)  # type: ignore[call-arg]

    @tk_thread_safe
    def show_message(self, message: str) -> None:
        """Add a message to the message area (thread-safe)."""
        self.message_text.insert(tk.END, message.strip() + "\n")
        self.message_text.see(tk.END)

    @tk_thread_safe
    def show_error(self, error: str) -> None:
        """Show error in popup dialog (thread-safe)."""
        self.progress_bar.stop()
        Messagebox.show_error(title="Conversion Error", message=error)

    @tk_thread_safe
    def show_result(self, result: str | Path) -> None:
        """Show success result and offer to save file (thread-safe)."""
        self.progress_bar.stop()
        self._show_message_sync(f"Conversion complete: {result}")

        # Read the converted file and offer save dialog
        try:
            with open(result, "rb") as f:
                content = f.read()
            self._download_result(Path(result).name, content)
        except Exception as e:
            Messagebox.show_error(title="Error", message=f"Failed to read result: {e}")

    def _show_message_sync(self, message: str) -> None:
        """Add message without thread wrapper (for internal use from main thread)."""
        self.message_text.insert(tk.END, message.strip() + "\n")
        self.message_text.see(tk.END)

    @tk_thread_safe
    def show_formats(self, formats: list[str]) -> None:
        """Update available target formats (thread-safe)."""
        self.selection_to.config(values=formats)
        if formats:
            self.selection_to.set(formats[0])

    @tk_thread_safe
    def show_progress(self, progress: float) -> None:
        """Update progress bar (thread-safe)."""
        if progress < 0:
            # Indeterminate mode
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start()
        elif progress >= 1.0:
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate", value=100)
        else:
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate", value=int(progress * 100))

    def _download_result(self, filename: str, content: bytes) -> None:
        """Show save dialog for converted file (called from main thread via @tk_thread_safe)."""
        file_path = fd.asksaveasfilename(
            initialfile=filename,
            initialdir=Path.home(),
            defaultextension=f".{self.selection_to.get()}",
            filetypes=[
                ("E-book files", f"*.{self.selection_to.get()}"),
                ("All Files", "*.*"),
            ],
            title="Save Converted E-book",
        )

        if not file_path:
            return

        try:
            with open(file_path, "wb") as f:
                f.write(content)
            Messagebox.show_info(title="Success", message=f"File saved: {file_path}")
        except Exception as e:
            Messagebox.show_error(title="Error", message=f"Failed to save: {e}")

    # =========================================================================
    # EVENTS: Callbacks for user actions (ViewProtocol)
    # =========================================================================

    def get_config(self) -> Config:
        args = self._get_params()
        self.config = Config(*args)
        return self.config

    def _get_params(self) -> tuple[Target, Any]:
        target_object = Target(self._get_target_format(), "ebook")
        path_to_file = self._get_file_path()
        return target_object, path_to_file

    def set_on_convert(self, callback: Callable[[], None]) -> None:
        """Register callback for convert button."""
        self._on_convert = callback

    # =========================================================================
    # LIFECYCLE (ViewProtocol)
    # =========================================================================

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()
