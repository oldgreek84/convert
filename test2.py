import json
import sys
import os
import requests
import time
from convert import other_save, get_path

api_key = 'c6978d7a29f5d34b0cb9597f322528d6'
url ='https://api2.online-convert.com/jobs'

###############
# test data:
headers = {
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'x-oc-api-key': api_key
    }
data_test = '{\n"conversion": [{\n"category": "ebook",\n"target": "mobi"\n}]\n}'
data_test1 = {'conversion': [{'category': 'ebook', 'target': 'mobi'}]}
###############

def set_data(target, category):
    data = {'conversion': [{'category': category, 'target': target}]}
    return json.dumps(data)

def send_job(data, api_key=api_key):
    headers = {
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'x-oc-api-key': api_key
        }

    response = requests.post(url, headers=headers, data=data)
    id = response.json()['id']
    print('id: ', id)
    # server = response.json()['server']
    return response

def send_file(id, server, file_path, api_key=api_key):
    headers = {
        'cache-control': 'no-cache',
        'x-oc-api-key': api_key
    }

    files = {
        'file': (file_path, open(file_path, 'rb'))
    }
    url_upload = f'{server}/upload-file/{id}'
    response = requests.post(url_upload, headers=headers, files=files)
    completed = response.json()['completed']
    if completed: print('file send completed')
    return response

def get_status(id):
    headers = {
        'cache-control': 'no-cache',
        'x-oc-api-key': api_key 
    }
    response = requests.get(url+f'/{id}', headers=headers)
    status_code = response.json()['status']['code']
    print(status_code)
    # uri  = response.json()['output'][0]['uri']
    return response

def main(file_path, target="mobi", category="ebook", api_key=api_key):
    data = set_data(target, category) 
    res_send = send_job(data, api_key)
    id = res_send.json()['id']
    server = res_send.json()['server']
    res_put = send_file(id, server, file_path)
    while True:
        res_st = get_status(id)
        status = res_st.json()['status']['code']
        if status == 'completed': break
        time.sleep(3)
    uri = res_st.json()['output'][0]['uri']
    other_save(uri)

def get_value(arg):
    indx = sys.argv.index(arg)
    try:
        res = sys.argv[indx+1]
    except IndexError:
        print('not found value')
    return res


if __name__ == "__main__":
    if '-path' in sys.argv:
        file_path = get_value('-path')
    elif '-name' in sys.argv:
        file_path = get_path(get_value('-name'))
    else:
        file_path = sys.argv[1]
    target=sys.argv[-1]
    main(file_path, target)



