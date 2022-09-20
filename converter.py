#!/usr/bin/env python3

"""
The application works with remote converter API.
Converts electronic books from fb2 format to mobi by default
Needs to ser enviroment data API_KEY and CONVERTER_URL
"""

import json
import sys
import os
import time
import requests
from dotenv import load_dotenv

from utils import get_path, parse_command, save_from_url, catcher


load_dotenv()

API_KEY = os.environ.get("API_KEY")
URL = os.environ.get("CONVERTER_URL")

DOCSTRING = """
command needs:
-path - full/path/to/file
-name - file_name in current directory
-t - [target] - string of file format(default "mobi")
-cat - [category] - category of formatting file (default "ebook")
"""

HEADERS = {
    "cache-control": "no-cache",
    "content-type": "application/json",
    "x-oc-api-key": API_KEY,
}


def _set_data_options(target: str, category: str) -> str:
    """
    creates json string with parameters to converts files
    target: string e-book extension(mobi by default)
    category: string of category converter(e-book by default)
    returns string with parameters
    """
    data = {"conversion": [{"category": category, "target": target}]}
    return json.dumps(data)


def _send_job_to_server(data: str):
    """
    sends request to create remote job
    data: json string with parameters target and category
    returns response object and stirng with job id
    """

    response = requests.post(URL, headers=HEADERS, data=data)
    try:
        work_id = response.json()["id"]
        server = response.json()["server"]
        print("id: ", work_id)
        return server, work_id
    except KeyError:
        print(response.json())
        return False


def _send_file_to_server(
        work_id: str, server: str, file_path: str, file_data: bytes):
    """
    sends request to remote API with opened file object
    work_id: string with unique id from remote API
    server: string with special URL of working server
    file_path: string with path to file then needs uploads to server
    returns http response object
    """

    head = {"cache-control": "no-cache", "x-oc-api-key": API_KEY}

    url_upload = f"{server}/upload-file/{work_id}"
    response = requests.post(
        url_upload,
        headers=head,
        files={"file": (file_path, file_data)})
    completed = response.json().get("completed")
    print(f"send completed: {response.json()}")
    return completed


def _get_status_convert_file(work_id: str):
    """
    sends request to server with unique id and return response with
    status code
    """

    response = requests.get(f"{URL}/{work_id}", headers=HEADERS)

    status_code = response.json()["status"]["code"]
    print(status_code)
    return response, status_code


@catcher
def main(path_to_file, path_to_save="books", target="mobi", category="ebook"):
    """
    main function create all resquests to remote server
    and save converted file to local directory
    """

    if not os.path.isfile(path_to_file):
        raise ValueError("invalid file path")

    data = _set_data_options(target, category)
    server, work_id = _send_job_to_server(data)
    with open(path_to_file, "rb") as file:
        _send_file_to_server(work_id, server, path_to_file, file)

    res_status, status = False, False
    while True:
        time.sleep(3)
        res_status, status = _get_status_convert_file(work_id)
        if status != "processing":
            break

    if status == "completed":
        uri_to_downloas_file = res_status.json()["output"][0]["uri"]
        save_from_url(uri_to_downloas_file, path_to_save)
    elif status == "incomplete":
        print("missing information to run a job")
    elif status == "failed":
        print(res_status.json()["status"]["info"])


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(DOCSTRING)
    else:
        data_settings = parse_command()
        if data_settings.get("-path"):
            working_file_path = data_settings["-path"]
        elif data_settings.get("-name"):
            working_file_path = get_path(data_settings["-name"])
        else:
            working_file_path = sys.argv[1]

        working_target = data_settings.get("-t", "mobi")
        working_category = data_settings.get("-cat", "ebook")

        print(working_file_path, working_target, working_category)

        main(
            working_file_path, target=working_target, category=working_category)
