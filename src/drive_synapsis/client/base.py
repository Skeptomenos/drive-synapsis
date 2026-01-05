"""Base client with Google API service initialization."""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import Any, Optional

from ..auth.google_auth import get_creds, get_credentials, GoogleAuthenticationError


class GDriveClientBase:
    """Base class with Google API services."""

    def __init__(self, credentials: Optional[Credentials] = None) -> None:
        if credentials:
            self.creds = credentials
        else:
            self.creds = get_credentials()
            if not self.creds:
                self.creds = get_creds()

        self.drive_service = build("drive", "v3", credentials=self.creds)
        self.docs_service = build("docs", "v1", credentials=self.creds)
        self.sheets_service = build("sheets", "v4", credentials=self.creds)

    def get_file_version(self, file_id: str) -> int:
        file_meta = (
            self.drive_service.files().get(fileId=file_id, fields="version").execute()
        )
        return int(file_meta.get("version", 0))

    def get_file_metadata(self, file_id: str) -> dict[str, Any]:
        return (
            self.drive_service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, owners, parents, starred, trashed, webViewLink",
            )
            .execute()
        )
