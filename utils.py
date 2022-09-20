#!/usr/bin/env python3
""" modul with spetials utils to works with application """

import os
import sys
from functools import wraps
from typing import Callable

import requests


def catcher(func: Callable):
    """
    decorator catch all exception in function and
    retun message with errors
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as ex:
            errors = {"status": "error", "message": ex.args[-1]}
            print(errors)
            func.errors = errors

    return wrapper


def get_value(arg: str) -> str:
    """gets and returns next argument for command line"""

    indx = sys.argv.index(arg)
    try:
        res = sys.argv[indx + 1]
    except IndexError:
        return {"error": "not found value"}
    return res


def get_path(file_name: str) -> str:
    """returns path of file if then exists or raise exception"""

    files = [x.name for x in os.scandir(os.path.curdir) if x.is_file()]
    if file_name in files:
        path_file = os.path.abspath(file_name)
    else:
        path_file = None
        raise FileNotFoundError(f"file {file_name} not found")
    return path_file


def parse_command() -> dict:
    """return dict with arguments of command line"""

    data = {}
    args = sys.argv[1:]
    while len(args) >= 2:
        data[args[0]] = args[1]
        args = args[2:]
    return data


def save_from_url(url: str, sub_dir: str = os.path.curdir) -> str:
    """saves file form remote URL to directory"""

    filename = url.split("/")[-1]
    full_path = get_full_file_path(filename, sub_dir)
    response = requests.get(url, stream=True)
    save_data_from_responce_to_dir(full_path, response)
    return full_path


def get_full_file_path(filename: str, sub_dir: str) -> str:
    """return full file path"""

    main_path = os.path.abspath(sub_dir)
    if not os.path.exists(main_path):
        os.mkdir(main_path)
    return os.path.join(main_path, filename)


def save_data_from_responce_to_dir(
    file_path: str, response: requests.Response, bufsize: int = 1024
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
