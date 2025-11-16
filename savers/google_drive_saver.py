import pathlib
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


from interfaces.saver_interface import SaverProtocol

if TYPE_CHECKING:
    import io

SCOPES = ["https://www.googleapis.com/auth/drive"]


def init_gdrive_service():
    """Initialize Google Drive API service with OAuth2 authentication.

    Sets up the Google Drive API client using OAuth2 credentials.
    Handles the complete authentication flow including token refresh
    and initial authorization if needed.

    The function looks for credentials.json and token.json in the same
    directory as this module. If token.json doesn't exist or is expired,
    it will trigger the OAuth2 flow to obtain new credentials.

    Returns:
        Authenticated Google Drive service object ready for API calls

    Raises:
        FileNotFoundError: If credentials.json is not found

    Files Required:
        credentials.json: OAuth2 client configuration from Google Console
        token.json: Stored user credentials (created automatically)
    """
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
                msg = f"credentials.json not found at {credentials_path}"
                raise FileNotFoundError(msg)

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with pathlib.Path(token_path).open("w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


class GoogleDriveSaver(SaverProtocol):
    """Google Drive cloud storage implementation of SaverProtocol.

    This saver uploads converted files to Google Drive using the Google Drive API.
    It handles OAuth2 authentication, file upload with resumable transfers,
    and provides proper error handling for cloud storage operations.

    Features:
        - OAuth2 authentication with automatic token refresh
        - Resumable file uploads for large files
        - Automatic credential management
        - Error handling for network and API issues
        - File metadata and naming control

    Requirements:
        - Google Drive API enabled in Google Cloud Console
        - credentials.json file with OAuth2 client configuration
        - Internet connection for API access
        - Appropriate Google Drive storage quota

    Attributes:
        service: Authenticated Google Drive API service instance
        source_name: Path to the file to be uploaded

    Setup Files:
        credentials.json: OAuth2 client configuration from Google Console
        token.json: User authorization token (created automatically)

    Example:
        >>> saver = GoogleDriveSaver()
        >>> saver.setup(source_name='/tmp/converted.mobi')
        >>> result = saver.save()
        >>> print(f"File uploaded: {result}")
    """

    def __init__(self):
        """Initialize Google Drive saver with API service."""
        self.service = init_gdrive_service()
        self.source_name: str | None = None
        self.source_data: io.BytesIO | None = None

    def setup(self, **kwargs):
        """Configure the Google Drive saver with source file path.

        Args:
            **kwargs: Configuration parameters including:
                source_name: Path to the file to be uploaded to Google Drive

        Raises:
            ValueError: If source_name is not provided
        """
        source_name = kwargs.get("source_name")
        if not source_name:
            msg = "source_name is required in setup"
            raise ValueError(msg)

        self.source_name = source_name

        source_data = kwargs.get("source_data")
        if not source_data:
            msg = "source_data must be provided for LocalFileSaver setup"
            raise ValueError(msg)

        self.source_data = source_data

    def save(self, *, source_name: str | None = None):
        """Upload the file to Google Drive.

        Uploads the specified file to Google Drive using the authenticated
        service. The file is uploaded with resumable transfer to handle
        large files efficiently.

        Args:
            source_name: Optional override for the source file path.
                        If None, uses the path from setup()

        Returns:
            The name of the uploaded file in Google Drive

        Raises:
            ValueError: If no source path is provided or configured
            FileNotFoundError: If the source file doesn't exist
            HttpError: If the Google Drive API request fails
        """
        filename = self.source_name
        file_metadata = {"name": filename}

        media = MediaIoBaseUpload(self.source_data, resumable=True, mimetype="text/plain")

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
    s.setup(source_name="test_file.txt")
    res = s.save()
    print(f"Uploaded file ID: {res}")
