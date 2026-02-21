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
    - Adjustable font size (saved between sessions)

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
from uis.settings import get_font_size, set_font_size

if TYPE_CHECKING:
    from collections.abc import Callable

work_dir = Path(__file__)

# Font size presets - actual font sizes in points
FONT_SIZE_PRESETS = {
    "Small": 8,
    "Medium": 10,
    "Large": 16,
    "Extra Large": 20,
}

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

# TODO: make Tk View use format domain for choose available formats
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
        - Adjustable font size with persistence
    """

    def __init__(self) -> None:
        self.root = ttkb.Window(title="E-book Converter", themename="darkly")

        # Load user font size preference
        self._font_size_name = get_font_size()
        self._font_size = FONT_SIZE_PRESETS.get(self._font_size_name, 8)

        # List to track all widgets that need font updates
        self._font_widgets: list = []

        # Set window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = max(900, int(screen_width * 0.5))
        window_height = max(700, int(screen_height * 0.6))
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(800, 600)

        # Configure root grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)  # Message area row expands

        self._on_convert: Callable[[], None] | None = None
        self._create_widgets()
        self.config = None

    def _get_font(self, bold: bool = False, scale: float = 1.0) -> tuple[str, int, str]:
        """Get font tuple with current size.

        Uses 'DejaVu Sans' which is available on most Linux systems
        and correctly respects font size settings.
        """
        size = int(self._font_size * scale)
        weight = "bold" if bold else "normal"
        return ("DejaVu Sans", size, weight)

    def _get_mono_font(self, scale: float = 1.0) -> tuple[str, int]:
        """Get monospace font tuple with current size."""
        size = int(self._font_size * scale)
        return ("DejaVu Sans Mono", size)

    def _register_widget(self, widget) -> None:
        """Register a widget for font updates."""
        self._font_widgets.append(widget)

    def _configure_styles(self) -> None:
        """Configure ttk styles for buttons, labelframes, and combobox dropdowns.

        This method is called on init and when font size changes to update
        all themed widget styles that don't support direct font configuration.
        """
        style = ttkb.Style()

        # Button styles
        style.configure("TButton", font=self._get_font())
        style.configure("info.TButton", font=self._get_font())
        style.configure("success.TButton", font=self._get_font())
        style.configure("danger.Outline.TButton", font=self._get_font())

        # LabelFrame title styles
        style.configure("TLabelframe.Label", font=self._get_font())
        style.configure("info.TLabelframe.Label", font=self._get_font())
        style.configure("secondary.TLabelframe.Label", font=self._get_font())

        # Combobox dropdown (Listbox) font via option database
        self.root.option_add("*TCombobox*Listbox.font", self._get_font())

    def _apply_fonts_to_all(self) -> None:
        """Apply current font size to all registered widgets and styles."""
        # Update individual widgets
        for widget in self._font_widgets:
            try:
                if isinstance(widget, tk.Text):
                    widget.configure(font=self._get_mono_font())
                else:
                    widget.configure(font=self._get_font())
            except tk.TclError:
                pass  # Widget may have been destroyed

        # Update ttk styles
        self._configure_styles()

    def _create_widgets(self) -> None:  # noqa: PLR0914, PLR0915
        """Create all UI widgets with proper styling."""
        pad = 15

        # Configure ttk styles before creating widgets
        self._configure_styles()

        # === HEADER SECTION (row 0) ===
        header_frame = ttkb.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(20, 5))

        header_label = ttkb.Label(
            header_frame,
            text="E-book Converter",
            bootstyle="inverse-primary",  # type: ignore[call-arg]
        )
        header_label.configure(font=self._get_font(bold=True, scale=1.8))
        header_label.pack(fill=tk.X)
        self._register_widget(header_label)

        instruction_label = ttkb.Label(
            header_frame,
            text="Select a file and target format to convert",
        )
        instruction_label.configure(font=self._get_font(scale=1.1))
        instruction_label.pack(pady=(5, 10))
        self._register_widget(instruction_label)

        # === FORMAT SELECTION SECTION (row 1) ===
        format_frame = ttkb.Frame(self.root)
        format_frame.grid(row=1, column=0, pady=pad)

        # From format label and combobox
        from_label = ttkb.Label(format_frame, text="From:")
        from_label.configure(font=self._get_font())
        from_label.grid(row=0, column=0, padx=(0, 8))
        self._register_widget(from_label)

        self.selection_from = ttkb.Combobox(
            format_frame,
            bootstyle="info",  # type: ignore[call-arg]
            values=["fb2", "txt", "epub", "pdf", "mobi"],
            width=14,
        )
        self.selection_from.configure(font=self._get_font())
        self.selection_from.grid(row=0, column=1, padx=10)
        self.selection_from.current(0)
        self.selection_from.bind("<<ComboboxSelected>>", self._on_source_format_change)
        self._register_widget(self.selection_from)

        # Arrow label
        arrow_label = ttkb.Label(format_frame, text=">>>")
        arrow_label.configure(font=self._get_font(bold=True, scale=1.2))
        arrow_label.grid(row=0, column=2, padx=15)
        self._register_widget(arrow_label)

        # To format label and combobox
        to_label = ttkb.Label(format_frame, text="To:")
        to_label.configure(font=self._get_font())
        to_label.grid(row=0, column=3, padx=(0, 8))
        self._register_widget(to_label)

        self.selection_to = ttkb.Combobox(
            format_frame,
            bootstyle="info",  # type: ignore[call-arg]
            values=["mobi", "pdf", "epub", "fb2"],
            width=14,
        )
        self.selection_to.configure(font=self._get_font())
        self.selection_to.grid(row=0, column=4, padx=10)
        self.selection_to.current(0)
        self.selection_to.bind("<<ComboboxSelected>>", self._on_target_format_change)
        self._register_widget(self.selection_to)

        # === FILE SELECTION SECTION (row 2) ===
        file_frame = ttkb.Frame(self.root)
        file_frame.grid(row=2, column=0, pady=pad, padx=25, sticky="ew")
        file_frame.columnconfigure(1, weight=1)  # Entry expands

        # Open file button
        self.open_btn = ttkb.Button(
            file_frame,
            text="Open File",
            bootstyle="info",  # type: ignore[call-arg]
            command=self._open_file,
            width=14,
        )
        self.open_btn.grid(row=0, column=0, padx=(0, 12))

        # File path entry
        self.file_entry = ttkb.Entry(file_frame)
        self.file_entry.configure(font=self._get_font())
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        self.file_entry.bind("<Button-1>", lambda _e: self._open_file())
        self._register_widget(self.file_entry)

        # Convert button
        self.convert_btn = ttkb.Button(
            file_frame,
            text="Convert",
            bootstyle="success",  # type: ignore[call-arg]
            command=self._on_convert_click,
            width=14,
        )
        self.convert_btn.grid(row=0, column=2, padx=(0, 12))

        # Quit button
        self.quit_btn = ttkb.Button(
            file_frame,
            text="Quit",
            bootstyle="danger-outline",  # type: ignore[call-arg]
            command=self.root.destroy,
            width=10,
        )
        self.quit_btn.grid(row=0, column=3)

        # === STATUS SECTION (row 3) ===
        status_frame = ttkb.Frame(self.root)
        status_frame.grid(row=3, column=0, pady=pad, padx=25, sticky="ew")
        status_frame.columnconfigure(0, weight=1)  # Progress bar expands

        # Progress bar
        self.progress_bar = ttkb.Progressbar(
            status_frame,
            bootstyle="success-striped",  # type: ignore[call-arg]
            mode="indeterminate",
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 20))

        # Status label container
        status_container = ttkb.Frame(status_frame)
        status_container.grid(row=0, column=1)

        status_label_text = ttkb.Label(status_container, text="Status:")
        status_label_text.configure(font=self._get_font())
        status_label_text.pack(side=tk.LEFT, padx=(0, 8))
        self._register_widget(status_label_text)

        self.status_label = ttkb.Label(
            status_container,
            text="Ready",
            bootstyle="success",  # type: ignore[call-arg]
            width=12,
        )
        self.status_label.configure(font=self._get_font(bold=True))
        self.status_label.pack(side=tk.LEFT)
        self._register_widget(self.status_label)

        # === MESSAGE AREA SECTION (row 4 - expands) ===
        message_frame = ttkb.LabelFrame(
            self.root,
            text=" Messages ",
            bootstyle="info",  # type: ignore[call-arg]
        )
        message_frame.grid(row=4, column=0, pady=10, padx=25, sticky="nsew")
        message_frame.columnconfigure(0, weight=1)
        message_frame.rowconfigure(0, weight=1)

        # Text area with scrollbar
        text_container = ttkb.Frame(message_frame)
        text_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        # Scrollbar
        scrollbar = ttkb.Scrollbar(text_container)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Text area for messages
        self.message_text = tk.Text(
            text_container,
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff",
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
        )
        self.message_text.configure(font=self._get_mono_font())
        self.message_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.message_text.yview)
        self._register_widget(self.message_text)

        # === FOOTER (row 5) ===
        footer_label = ttkb.Label(
            self.root,
            text="E-book Converter v1.0",
            bootstyle="secondary",  # type: ignore[call-arg]
        )
        footer_label.configure(font=self._get_font(scale=0.8))
        footer_label.grid(row=5, column=0, pady=(5, 8))
        self._register_widget(footer_label)

        # === SETTINGS SECTION (row 6) ===
        settings_frame = ttkb.LabelFrame(
            self.root,
            text=" Settings ",
            bootstyle="secondary",  # type: ignore[call-arg]
        )
        settings_frame.grid(row=6, column=0, pady=(0, 15), padx=25, sticky="ew")

        # Font size selector
        font_size_label = ttkb.Label(settings_frame, text="Font Size:")
        font_size_label.configure(font=self._get_font())
        font_size_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)
        self._register_widget(font_size_label)

        self.font_size_combo = ttkb.Combobox(
            settings_frame,
            bootstyle="secondary",  # type: ignore[call-arg]
            values=list(FONT_SIZE_PRESETS.keys()),
            width=12,
            state="readonly",
        )
        self.font_size_combo.configure(font=self._get_font())
        self.font_size_combo.pack(side=tk.LEFT, pady=10)
        self.font_size_combo.set(self._font_size_name)
        self.font_size_combo.bind("<<ComboboxSelected>>", self._on_font_size_change)
        self._register_widget(self.font_size_combo)

        # Info label
        self.font_size_info = ttkb.Label(
            settings_frame,
            text="",
            bootstyle="warning",  # type: ignore[call-arg]
        )
        self.font_size_info.configure(font=self._get_font(scale=0.9))
        self.font_size_info.pack(side=tk.LEFT, padx=(15, 10), pady=10)
        self._register_widget(self.font_size_info)

    def _on_source_format_change(self, event) -> None:  # noqa: ARG002
        """Update target format options when source format changes."""
        current = self.selection_from.get()
        targets = CONVERTER_FORMATS_MAPPING.get(current, ["mobi"])
        self.selection_to.config(values=targets)
        if targets:
            self.selection_to.set(targets[0])

    def _on_target_format_change(self, event) -> None:
        """Update source format when target changes (optional auto-select)."""

    def _on_font_size_change(self, event) -> None:  # noqa: ARG002
        """Handle font size change - saves preference and applies immediately."""
        new_size_name = self.font_size_combo.get()
        if new_size_name != self._font_size_name:
            # Save preference
            set_font_size(new_size_name)
            self._font_size_name = new_size_name
            self._font_size = FONT_SIZE_PRESETS.get(new_size_name, 8)

            # Apply to all widgets immediately
            self._apply_fonts_to_all()

            # Also update header with larger scale
            # (handled by _apply_fonts_to_all since we registered with scale info)
            self.font_size_info.config(text="Font size updated!")

            # Clear the info message after 2 seconds
            self.root.after(2000, lambda: self.font_size_info.config(text=""))

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
