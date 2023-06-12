#!/usr/bin/env python3
"""module with spetials utils to works with application"""

import os
import pathlib
import sys
from collections.abc import Callable
from functools import wraps

import requests


class ParamsError(Exception):
    """common error class for parsing params"""


def coroutine(func):
    """decorator for auto init coroutine generator"""

    def wrap(*args, **kwargs):
        gen = func(*args, **kwargs)
        gen.send(None)
        return gen

    return wrap


def catcher(error_list=None):
    """decorator catch all exception in function and
    return message with errors
    """

    def catcher_wrap(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as ex:
                errors = {"status": "error", "message": str(ex)}
                func.errors = errors
                error_list.append(errors)

        return wrapper

    return catcher_wrap


def get_value(arg: str) -> str | bool | None:
    """gets and returns next argument for command line"""
    indx = sys.argv.index(arg)
    try:
        res = sys.argv[indx + 1]
    except IndexError:
        return False
    return res


def get_path(file_name: str) -> str:
    """returns path of file if then exists or raise exception"""
    return str(pathlib.Path(file_name).resolve())


def parse_command() -> dict:
    """return dict with arguments of command line"""
    data = {}
    args = sys.argv[1:]
    while len(args) >= 2:
        data[args[0]] = args[1]
        args = args[2:]
    return data


def save_from_url(url: str, sub_dir: str = os.path.curdir) -> pathlib.Path:
    """saves file form remote URL to directory"""
    filename = url.split("/")[-1]
    full_path = get_full_file_path(filename, sub_dir)
    response = requests.get(url, stream=True)
    save_data_from_responce_to_dir(full_path, response)
    return full_path


def get_full_file_path(filename: str, sub_dir: str) -> pathlib.Path:
    """return full file path"""
    main_path = pathlib.Path(sub_dir).resolve()
    if not main_path.exists():
        main_path.mkdir()
    return main_path / filename


def save_data_from_responce_to_dir(
    file_path: pathlib.Path, response: requests.Response, bufsize: int = 1024
):
    """save file from response object to dir"""
    with open(file_path, "wb") as opened_file:
        for part in response.iter_content(bufsize):
            opened_file.write(part)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_file_name = sys.argv[1]
        print(get_path(test_file_name))
    else:
        print(get_path(__file__))

    resp = requests.get("http://www.google.com")
    save_data_from_responce_to_dir(get_full_file_path("some.txt", "book"), resp)
