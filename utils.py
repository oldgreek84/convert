#!/usr/bin/env python3

import requests
import sys
import os

def get_path(file_name):
    # curdir = os.path.abspath(os.path.curdir)
    files = [x.name for x in os.scandir(os.path.curdir) if x.is_file()]
    if file_name in files:
        path_file = os.path.abspath(file_name)
    else:
        print(f'incorect name: {file_name}')
        path_file = None
        raise FileNotFoundError(f'file {file_name} not found')
    return path_file

def parse_command():
    data = {}
    args = sys.argv[1:]
    while len(args) >= 2:
        data[args[0]] = args[1]
        args = args[2:]
    return data

def save_from_url(url, bufsize=1024):
    path = os.path.abspath(os.path.curdir)
    filename = url.split('/')[-1]
    file_path = os.path.join(path, filename)
    response = requests.get(url, stream=True)
    with open(file_path, 'wb') as f:
        print('writing file...')
        for path in response.iter_content(bufsize):
            if path:
                f.write(path)
    print('[ end writing ]')
    print(f'[file save to {file_path}]')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        print(get_path(file_name))
    else:
        print(get_path(__file__))
