'''
The application works with remote converter API.
Converts electronic books from fb2 format to mobi by default
Needs to ser enviroment data API_KEY and CONVERTER_URL
'''
import json
import sys
import os
import time
import requests

from utils import get_path, parse_command, save_from_url, catcher


API_KEY = os.environ.get('API_KEY') or 'c6978d7a29f5d34b0cb9597f322528d6'
URL = os.environ.get('CONVERTER_URL') or 'https://api2.online-convert.com/jobs'

DOCSTRING = """
command needs:
-path - full/path/to/file
or
-name - file_name in current directory
and
-t - [target] - string of file format(default "mobi")
-cat - [category] - category of formatting file (default "ebook")
"""

# test data:

HEADERS = {
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'x-oc-api-key': API_KEY
    }
DATA_TEST = '{\n"conversion":\
        [{\n"category": "ebook",\n"target": "mobi"\n}]\n}'
DATA_TEST1 = {'conversion': [{'category': 'ebook', 'target': 'mobi'}]}


def _set_data_options(target: str, category: str) -> str:
    '''
    creates json string with parameters to converts files
    target: string e-book extension(mobi by default)
    category: string of category converter(e-book by default)
    returns string with parameters
    '''

    data = {'conversion': [{'category': category, 'target': target}]}
    return json.dumps(data)


def _send_job_to_server(data: str):
    '''
    sends request to create remote job
    data: json string with parameters target and category
    returns response object and stirng with job id
    '''

    response = requests.post(URL, headers=HEADERS, data=data)
    try:
        work_id = response.json()['id']
        server = response.json()['server']
    except KeyError:
        print(response.json())
    else:
        print('id: ', work_id)
        # print('server: ', server) if needs more information
        return server, work_id


def _send_file_to_server(work_id: str, server: str, file_path: str):
    '''
    sends request to remote API with opened file object
    work_id: string with unique id from remote API
    server: string with special URL of working server
    file_path: string with path to file then needs uploads to server
    returns http response object
    '''

    head = {
        'cache-control': 'no-cache',
        'x-oc-api-key': API_KEY
        }

    try:
        files = {'file': (file_path, open(file_path, 'rb'))}
    except FileNotFoundError:
        print('file not found')
    else:
        url_upload = f'{server}/upload-file/{work_id}'
        response = requests.post(url_upload, headers=head, files=files)
        completed = response.json().get('completed')
        if completed:
            print('file send completed')
        else:
            print(response.json())


def _get_status_convert_file(work_id: str):
    '''
    sends requet to server with unique id and return response with
    status code
    '''

    response = requests.get(URL+f'/{work_id}', headers=HEADERS)

    status_code = response.json()['status']['code']
    print(status_code)
    return response, status_code


@catcher
def main(file_path, target="mobi", category="ebook"):
    '''
    main function create all resquests to remote server
    and save converted file to local directory
    '''

    if not os.path.isfile(file_path):
        raise ValueError('invalid file path')
    data = _set_data_options(target, category)
    server, work_id = _send_job_to_server(data)
    _send_file_to_server(work_id, server, file_path)
    while True:
        time.sleep(3)
        res_status, status = _get_status_convert_file(work_id)
        if status == 'completed':
            uri_to_downloas_file = res_status.json()['output'][0]['uri']
            save_from_url(uri_to_downloas_file)
            break
        elif status == 'incomplete':
            print('missing information to run a job')
            break
        elif status == 'failed':
            print(res_status.json()['status']['info'])
            break


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(DOCSTRING)
    else:
        data_settings = parse_command()
        if data_settings.get('-path'):
            working_file_path = data_settings['-path']
        elif data_settings.get('-name'):
            working_file_path = get_path(data_settings['-name'])
        else:
            working_file_path = sys.argv[1]
        working_target = data_settings.get('-t', 'mobi')
        working_category = data_settings.get('-cat', 'ebook')
        print(working_file_path, working_target, working_category)
        main(working_file_path, working_target, working_category)
