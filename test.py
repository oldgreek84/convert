import requests
import json

base_url = "https://api.cloudconvert.com/v2"
filename = "Didro_Vibrani_tvori_cd0235_387876.fb2"


def send_job():
    payload = {
        # 'token': 'your-api-key',
        "tasks": {
            # "import-my-file": {
            #   "operation": "import/url",
            #   "url": "https://my.url/file.docx"
            # },
            "convert-my-file": {"operation": "convert", "input": filename, "output_format": "mobi"},
            # "export-my-file": {
            #   "operation": "export/url",
            #   "input": "convert-my-file"
            # }
        }
    }

    r = requests.post(base_url + '/jobs', params=payload)

    print(r.status_code)
    print(r.content)

    data = r.json()
    print(data)

    return data['data']['id'], data['data']['status']


def get_status(job_id):
    # GET https://sync.api.cloudconvert.com/v2/jobs/6559c281-ed85-4728-80db-414561c631e9
    response = requests.get(base_url + '/jobs/' + job_id)

    print(response.status_code)
    print(response.content)

    data = response.json()
    print(data)

    return data['data']['status'], [ts['status'] for ts in data['data']['tasks'] if ts['operation'] == 'convert']


def main():
    job_id, status = send_job()
    gb_st, status = get_status(job_id)


if __name__ == "__main__":
    main()
