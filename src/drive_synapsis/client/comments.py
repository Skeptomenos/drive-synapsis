"""Comment operations mixin for GDriveClient."""
from typing import Optional, Any


class CommentsMixin:
    """Mixin providing comment-related operations."""
    
    def get_file_comments(self, file_id: str) -> list[dict[str, Any]]:
        """Fetch all comments for a file.
        
        Args:
            file_id: The file ID.
            
        Returns:
            List of comment objects with content, author, and context.
        """
        comments = []
        page_token = None
        
        while True:
            response = self.drive_service.comments().list(
                fileId=file_id,
                fields='comments(id, content, author(displayName), quotedFileContent, replies(content, author(displayName))), nextPageToken',
                pageSize=100,
                pageToken=page_token
            ).execute()
            
            comments.extend(response.get('comments', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
                
        return comments

    def create_comment(self, file_id: str, content: str, quoted_text: Optional[str] = None) -> str:
        """Create a new comment on a file.
        
        Args:
            file_id: The file ID.
            content: The comment text.
            quoted_text: Optional text to anchor the comment to.
            
        Returns:
            Success message with comment ID.
        """
        try:
            comment_body = {'content': content}
            
            if quoted_text:
                comment_body['quotedFileContent'] = {'value': quoted_text}
                
            result = self.drive_service.comments().create(
                fileId=file_id,
                body=comment_body,
                fields='id'
            ).execute()
            
            return f"Comment created. ID: {result.get('id')}"
        except Exception as e:
            return f"Error creating comment: {str(e)}"

    def reply_to_comment(self, file_id: str, comment_id: str, content: str) -> str:
        """Reply to an existing comment.
        
        Args:
            file_id: The file ID.
            comment_id: The comment ID to reply to.
            content: The reply text.
            
        Returns:
            Success message with reply ID.
        """
        try:
            result = self.drive_service.replies().create(
                fileId=file_id,
                commentId=comment_id,
                body={'content': content},
                fields='id'
            ).execute()
            
            return f"Reply created. ID: {result.get('id')}"
        except Exception as e:
            return f"Error creating reply: {str(e)}"
