"""Sharing and permissions mixin for GDriveClient."""
from typing import Any


class SharingMixin:
    """Mixin providing sharing and permission operations."""
    
    def share_file(self, file_id: str, email: str, role: str = 'reader') -> str:
        """Share a file with a user via email.
        
        Args:
            file_id: The file ID.
            email: Email address of the user.
            role: 'reader', 'writer', or 'commenter'.
            
        Returns:
            Success message.
        """
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        
        self.drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        return f"Shared with {email} as {role}"

    def make_file_public(self, file_id: str) -> str:
        """Make a file publicly accessible.
        
        Args:
            file_id: The file ID.
            
        Returns:
            Message with public link.
        """
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        self.drive_service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        file_meta = self.drive_service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return f"Public link: {file_meta.get('webViewLink')}"

    def revoke_access(self, file_id: str, email: str) -> str:
        """Remove a user's access to a file.
        
        Args:
            file_id: The file ID.
            email: Email address of the user.
            
        Returns:
            Success or not found message.
        """
        permissions = self.drive_service.permissions().list(
            fileId=file_id,
            fields='permissions(id, emailAddress)'
        ).execute()
        
        for perm in permissions.get('permissions', []):
            if perm.get('emailAddress') == email:
                self.drive_service.permissions().delete(
                    fileId=file_id,
                    permissionId=perm['id']
                ).execute()
                return f"Revoked access for {email}"
        
        return f"No permission found for {email}"

    def list_permissions(self, file_id: str) -> list[dict[str, Any]]:
        """List all users who have access to a file.
        
        Args:
            file_id: The file ID.
            
        Returns:
            List of permission dictionaries.
        """
        result = self.drive_service.permissions().list(
            fileId=file_id,
            fields='permissions(id, emailAddress, role, type)'
        ).execute()
        
        return result.get('permissions', [])
