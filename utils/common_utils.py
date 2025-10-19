from __future__ import annotations

import os
import sys
from functools import wraps
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from collections.abc import Callable


def coroutine(func: Callable):
    """Decorator for automatically initializing coroutine generators.

    This decorator automatically calls send(None) on generator functions
    to advance them to their first yield point, making them ready to
    receive values. This is useful for implementing coroutine-based
    processing pipelines.

    Args:
        func: Generator function to be initialized as a coroutine

    Returns:
        Wrapped function that returns a primed coroutine

    Example:
        >>> @coroutine
        ... def consumer():
        ...     while True:
        ...         value = yield
        ...         print(f"Received: {value}")
        >>> c = consumer()  # Already primed and ready
        >>> c.send("hello")  # Can send immediately
    """

    def wrap(*args, **kwargs):
        gen = func(*args, **kwargs)
        gen.send(None)
        return gen

    return wrap


def catcher(error_list: list | None = None):
    """Decorator for catching and collecting exceptions in functions.

    This decorator wraps functions to catch all exceptions and store
    error information in a structured format. Useful for batch operations
    where you want to collect all errors rather than stopping on the first one.

    Args:
        error_list: Optional list to collect error dictionaries

    Returns:
        Decorator function that catches exceptions and logs them

    Example:
        >>> errors = []
        >>> @catcher(errors)
        ... def risky_operation():
        ...     raise ValueError("Something went wrong")
        >>> risky_operation()
        >>> print(errors)  # [{"status": "error", "message": "Something went wrong"}]
    """
    if error_list is None:
        error_list = []

    def catcher_wrap(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as ex:
                errors = {"status": "error", "message": str(ex)}
                # Store errors in wrapper function instead of original function
                wrapper.errors = errors  # type: ignore[attr-defined]
                error_list.append(errors)

        return wrapper

    return catcher_wrap


def get_value(arg: str) -> str | bool | None:
    """Get the value of a command-line argument.

    Searches sys.argv for the specified argument and returns the value
    that follows it. Useful for parsing command-line options.

    Args:
        arg: Command-line argument to search for (e.g., '--input')

    Returns:
        The value following the argument, False if no value found, or None if not present
    """
    indx = sys.argv.index(arg)
    try:
        res = sys.argv[indx + 1]
    except IndexError:
        return False
    return res


def get_path(file_name: str) -> str:
    """Resolve and return the absolute path of a file.

    Converts a filename to its absolute path representation using
    pathlib.Path.resolve(). Useful for ensuring consistent path
    handling across different operating systems.

    Args:
        file_name: Name or path of the file to resolve

    Returns:
        Absolute path string for the file

    Note:
        This function does not check if the file exists
    """
    return str(Path(file_name).resolve())


def parse_command() -> dict:
    """Parse command-line arguments into a dictionary.

    Parses sys.argv to extract flag-value pairs and returns them
    as a dictionary. Only processes arguments that start with
    '-' or '--' as flags.

    Returns:
        Dictionary mapping command-line flags to their values

    Example:
        For command: python script.py --input file.txt -t mobi
        Returns: {'--input': 'file.txt', '-t': 'mobi'}
    """
    data = {}
    args = sys.argv[1:]
    while len(args) >= 2:
        # do not add values without param flag
        if not args[0].startswith(("-", "--")):
            args = args[1:]
            continue

        data[args[0]] = args[1]
        args = args[2:]
    return data


def save_from_url(url: str, sub_dir: str = os.path.curdir) -> str | Path | PosixPath:
    """Download and save a file from a remote URL to a local directory.

    Downloads a file from the specified URL and saves it to the given
    directory. The filename is extracted from the URL path.

    Args:
        url: HTTP/HTTPS URL of the file to download
        sub_dir: Directory to save the file in (defaults to current directory)

    Returns:
        Path to the saved file
    """
    filename = url.split("/", maxsplit=1)[0]
    full_path = get_full_file_path(filename, sub_dir)
    response = requests.get(url, stream=True)
    save_data_from_response_to_dir(full_path, response)
    return full_path


def get_full_file_path(filename: str, sub_dir: str | Path) -> str | Path | PosixPath:
    """Construct the full path for a file in a directory, creating the directory if needed.

    Combines a filename with a directory path and ensures the directory exists.
    If the directory doesn't exist, it will be created.

    Args:
        filename: Name of the file
        sub_dir: Directory path where the file should be located

    Returns:
        Complete path to the file (directory + filename)

    Side Effects:
        Creates the directory if it doesn't exist
    """
    main_path = Path(sub_dir).resolve()
    if not main_path.exists():
        main_path.mkdir()
    return main_path / filename


def save_data_from_response_to_dir(
    file_path: str | Path, response: requests.Response, bufsize: int = 1024
) -> None:
    """Save data from an HTTP response to a file using streaming.

    Streams the response content to a file in chunks to handle large
    files efficiently without loading everything into memory.

    Args:
        file_path: Path where the file should be saved
        response: HTTP response object containing the file data
        bufsize: Buffer size for reading chunks (default: 1024 bytes)
    """
    with Path(file_path).open("wb") as opened_file:
        opened_file.writelines(response.iter_content(bufsize))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file_name = sys.argv[1]
        print(get_path(test_file_name))
    else:
        print(get_path(__file__))

    resp = requests.get("http://www.google.com")
    save_data_from_response_to_dir(get_full_file_path("some.txt", "book"), resp)
