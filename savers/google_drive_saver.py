import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from interfaces.saver_interface import SaverProtocol
import pathlib

SCOPES = ["https://www.googleapis.com/auth/drive"]


def init_gdrive_service():
    current_dir = pathlib.Path(pathlib.Path(__file__).resolve()).parent
    token_path = current_dir / "token.json"
    credentials_path = current_dir / "credentials.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


class GoogleDriveSaver(SaverProtocol):
    def __init__(self):
        self.service = init_gdrive_service()
        self.source_path = None

    def setup(self, **kwargs):
        source_path = kwargs.get("source_path")
        if not source_path:
            raise ValueError("source_path is required in setup")
        self.source_path = source_path

    def save(self):
        source_path = self.source_path

        if not source_path:
            raise ValueError(
                "No source_path provided. Call setup() first or pass source_path to save()"
            )

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        filename = os.path.basename(source_path)
        file_metadata = {"name": filename}

        media = MediaFileUpload(source_path, resumable=True)

        try:
            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id,name")
                .execute()
            )

            print(f"File: {file.get('name')} uploaded successfully. File ID: {file.get('id')}")
            return file.get("name")

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise


if __name__ == "__main__":
    s = GoogleDriveSaver()
    s.setup(source_path="test_file.txt")
    res = s.save()
    print(f"Uploaded file ID: {res}")
