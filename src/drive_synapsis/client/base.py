"""Base client with Google API service initialization."""
from googleapiclient.discovery import build
from ..auth import get_creds
from typing import Any


class GDriveClientBase:
    """Base class with Google API services."""
    
    def __init__(self) -> None:
        """Initialize the client with authenticated Google API services."""
        self.creds = get_creds()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
    
    def get_file_version(self, file_id: str) -> int:
        """Get the current version of the file from Drive metadata.
        
        Args:
            file_id: The file ID.
            
        Returns:
            The version number as an integer.
        """
        file_meta = self.drive_service.files().get(
            fileId=file_id, fields="version"
        ).execute()
        return int(file_meta.get('version', 0))
    
    def get_file_metadata(self, file_id: str) -> dict[str, Any]:
        """Get comprehensive metadata about a file.
        
        Args:
            file_id: The file ID.
            
        Returns:
            Dictionary with file metadata.
        """
        return self.drive_service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, createdTime, modifiedTime, owners, parents, starred, trashed, webViewLink'
        ).execute()
