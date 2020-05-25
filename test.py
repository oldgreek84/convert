#!/usr/bin/env python3

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
    return path_file

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        print(get_path(file_name))
    else:
        print(get_path(__file__))
