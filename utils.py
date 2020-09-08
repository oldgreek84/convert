#!/usr/bin/env python3
''' modul with spetials utils to works with application '''

import os
import sys
import requests

from functools import wraps
import traceback


test_id = '1d3a0ff8-2ba0-497b-8be0-0a509be94adb'
server ='https://www13.online-convert.com/dl/web8'
path = '/home/doc/oskar_i_rojeva_pani.fb2'


def catcher(func):
    '''
    decorator catch all exception in funtion and
    retun message with errors
    '''

    wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            return {'status': 'error',
                    'message': e.args}
    return wrapper


def get_value(arg):
    ''' gets and returns next argument for command line '''

    indx = sys.argv.index(arg)
    try:
        res = sys.argv[indx+1]
    except IndexError:
        print('not found value')
    return res


def get_path(file_name):
    ''' returns path of file if then exists or raise exception '''

    files = [x.name for x in os.scandir(os.path.curdir) if x.is_file()]
    if file_name in files:
        path_file = os.path.abspath(file_name)
    else:
        print(f'incorect name: {file_name}')
        path_file = None
        raise FileNotFoundError(f'file {file_name} not found')
    return path_file


def parse_command():
    ''' return dict with arguments of command line '''

    data = {}
    args = sys.argv[1:]
    while len(args) >= 2:
        data[args[0]] = args[1]
        args = args[2:]
    return data


def save_from_url(url, bufsize=1024):
    ''' saves file form remote URL to current working directory '''

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
        test_file_name = sys.argv[1]
        print(get_path(test_file_name))
    else:
        print(get_path(__file__))
