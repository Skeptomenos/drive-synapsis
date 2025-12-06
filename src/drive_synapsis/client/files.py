"""File management mixin for GDriveClient."""
from googleapiclient.http import MediaFileUpload
from typing import Optional, Any
import os


class FilesMixin:
    """Mixin providing file management operations."""
    
    def move_file(self, file_id: str, new_folder_id: str) -> str:
        """Move a file to a different folder.
        
        Args:
            file_id: The file ID.
            new_folder_id: Destination folder ID.
            
        Returns:
            Success message.
        """
        file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        self.drive_service.files().update(
            fileId=file_id,
            addParents=new_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        return f"Moved file to folder {new_folder_id}"

    def rename_file(self, file_id: str, new_name: str) -> str:
        """Rename a file without changing its location.
        
        Args:
            file_id: The file ID.
            new_name: New name for the file.
            
        Returns:
            Success message.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'name': new_name}
        ).execute()
        
        return f"Renamed to '{new_name}'"

    def delete_file(self, file_id: str, permanent: bool = False) -> str:
        """Delete a file. By default moves to trash.
        
        Args:
            file_id: The file ID.
            permanent: If True, permanently delete.
            
        Returns:
            Success message.
        """
        if permanent:
            self.drive_service.files().delete(fileId=file_id).execute()
            return "Permanently deleted"
        else:
            self.drive_service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()
            return "Moved to trash (recoverable via Drive UI)"

    def copy_file(self, file_id: str, new_name: str, folder_id: Optional[str] = None) -> dict[str, Any]:
        """Create a copy of a file with a new name.
        
        Args:
            file_id: The file ID.
            new_name: Name for the copy.
            folder_id: Optional destination folder.
            
        Returns:
            File metadata dictionary.
        """
        body = {'name': new_name}
        if folder_id:
            body['parents'] = [folder_id]
        
        result = self.drive_service.files().copy(
            fileId=file_id,
            body=body,
            fields='id, name, webViewLink'
        ).execute()
        
        return result

    def star_file(self, file_id: str, starred: bool = True) -> str:
        """Star or unstar a file for quick access.
        
        Args:
            file_id: The file ID.
            starred: True to star, False to unstar.
            
        Returns:
            Success message.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'starred': starred}
        ).execute()
        
        return f"File {'starred' if starred else 'unstarred'}"

    def set_file_description(self, file_id: str, description: str) -> str:
        """Set or update a file's description.
        
        Args:
            file_id: The file ID.
            description: Description text.
            
        Returns:
            Success message.
        """
        self.drive_service.files().update(
            fileId=file_id,
            body={'description': description}
        ).execute()
        
        return "Updated description"

    def upload_file(self, local_path: str, parent_id: Optional[str] = None) -> dict[str, Any]:
        """Upload any file to Drive.
        
        Args:
            local_path: Path to local file.
            parent_id: Optional parent folder ID.
            
        Returns:
            File metadata dictionary.
        """
        name = os.path.basename(local_path)
        file_metadata = {'name': name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        media = MediaFileUpload(local_path, resumable=True)
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return file

    def update_file_media(self, file_id: str, local_path: str) -> None:
        """Update the content of an existing file.
        
        Args:
            file_id: The file ID.
            local_path: Path to local file with new content.
        """
        media = MediaFileUpload(local_path, resumable=True)
        
        self.drive_service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
