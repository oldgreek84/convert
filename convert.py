#!/usr/bin/env python3

import os
import requests
import time
import sys

# post request to send file 
# curl -i -X POST -d '{"apikey": "_YOUR_API_KEY_", "file":"http://google.com/", "outputformat":"png"}' http://api.convertio.co/convert

# api = 24e70f6014bcb9b3ff6de4512cebbb0c
# first request:
# response = requests.post(url, json=data)
# put request:
# s = requests.put(url+f'/{id}/{file_name}/', data=open(file, 'rb'))

# file_url = '/home/nata/1/1.fb2'
# file = '/home/nata/1/1.fb2'
# file_name = '1.fb2'
# outputformat = 'mobi'
# input = 'upload'
# data = {'apikey': apikey, 'input': input, 'file': file, 'outputformat': outputformat}

apikey = '24e70f6014bcb9b3ff6de4512cebbb0c'
url = 'http://api.convertio.co/convert'

def get_path(file_name):
    # curdir = os.path.abspath(os.path.curdir)
    files = [x.name for x in os.scandir(os.path.curdir) if x.is_file()]
    if file_name in files:
        path_file = os.path.abspath(file_name)
    else:
        print(f'file not found or have incorrect name: {file_name}')
        path_file = None
    return path_file

def get_files():
    path = os.path.abspath(os.path.curdir)
    files = [x.path for x in os.scandir(path) if x.is_file()]
    return files

def settings(file_path, outputformat, input='upload'):
    data = {'apikey': apikey,
            'input': input,
            'file': file_path,
            'outputformat': outputformat}
    return data

def get_id(data):
    response = requests.post(url, json=data)
    id = response.json()['data']['id']
    print('get id: ', id)
    return id

def put_file(file_path, id):
    file_name = os.path.basename(file_path)
    send = requests.put(url + f'/{id}/{file_name}/', data=open(file_path, 'rb'))
    return send

def status(id):
    print('[file converting]')
    while True:
        print('waiting...')
        # global url
        response = requests.get(url + f'/{id}/status/')
        status = response.json()
        percent = status['data']['step_percent']
        if percent == 100: break
        time.sleep(5)
    file_url = status['data']['output']['url']
    size = status['data']['output']['size']
    print('url: ', file_url)
    print('size: ', size)
    return file_url

url1 ='https://s165.convertio.me/p/ZbC2U6DiKbqWQCZjhz6ECw/720399bd43ab4ae19677c5a63d718e6c/1.pdf'

def other_save(url, bufsize=1024):
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

def main(file_path, outputformat):
    data = settings(file_path, outputformat)
    id = get_id(data)
    put_file(file_path, id)
    file_url = status(id)
    other_save(file_url)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        file_path = sys.argv[1]
        outputformat = sys.argv[2]
        main(file_path, outputformat)
    elif len(sys.argv) == 2:
        outputformat = sys.argv[1]
        for file in get_files():
            main(file, outputformat)
    else:
        print('command needs parametrs: "/path/to/file" "outputformath" or "outputformat"')
