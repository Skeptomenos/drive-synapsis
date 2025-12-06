"""Custom exceptions for the Google Drive MCP server.

This module provides structured error handling with specific exception types
for different failure scenarios. All exceptions inherit from GDriveError.
"""
from typing import Optional, Any


class GDriveError(Exception):
    """Base exception for all gdrive-mcp errors.
    
    Attributes:
        message: Human-readable error description.
        file_id: Optional file ID related to the error.
    """
    
    def __init__(self, message: str, file_id: Optional[str] = None) -> None:
        self.message = message
        self.file_id = file_id
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the error message, optionally including file ID."""
        if self.file_id:
            return f"{self.message} (file: {self.file_id})"
        return self.message


class AuthenticationError(GDriveError):
    """Raised when authentication fails or token is expired."""
    pass


class FileNotFoundError(GDriveError):
    """Raised when a requested file doesn't exist or was deleted."""
    pass


class PermissionDeniedError(GDriveError):
    """Raised when access to a file is denied."""
    pass


class QuotaExceededError(GDriveError):
    """Raised when API rate limit or quota is exceeded."""
    pass


class InvalidFormatError(GDriveError):
    """Raised when an unsupported export format is requested."""
    
    def __init__(self, format_type: str, supported: list[str]) -> None:
        self.format_type = format_type
        self.supported = supported
        message = f"Unsupported format '{format_type}'. Supported: {', '.join(supported)}"
        super().__init__(message)


class SyncConflictError(GDriveError):
    """Raised when there's a version conflict during sync.
    
    Attributes:
        local_version: The version we have locally.
        remote_version: The current remote version.
    """
    
    def __init__(
        self, 
        message: str, 
        local_version: int, 
        remote_version: int,
        file_id: Optional[str] = None
    ) -> None:
        self.local_version = local_version
        self.remote_version = remote_version
        super().__init__(message, file_id)


class LinkNotFoundError(GDriveError):
    """Raised when no sync link exists for a local file."""
    
    def __init__(self, local_path: str) -> None:
        self.local_path = local_path
        super().__init__(f"No link found for '{local_path}'. Use link_local_file first.")


class LocalFileNotFoundError(GDriveError):
    """Raised when a local file doesn't exist."""
    
    def __init__(self, local_path: str) -> None:
        self.local_path = local_path
        super().__init__(f"Local file not found: {local_path}")


def handle_http_error(error: Any, file_id: Optional[str] = None) -> GDriveError:
    """Convert googleapiclient HttpError to a specific exception.
    
    Args:
        error: The HttpError from googleapiclient.
        file_id: Optional file ID for context.
        
    Returns:
        An appropriate GDriveError subclass.
    """
    try:
        status = error.resp.status
    except AttributeError:
        return GDriveError(f"API error: {str(error)}", file_id)
    
    if status == 401:
        return AuthenticationError(
            "Authentication failed. Please re-authenticate by deleting token.json and restarting.",
            file_id
        )
    elif status == 403:
        return PermissionDeniedError(
            "Access denied. Check file sharing settings or request access.",
            file_id
        )
    elif status == 404:
        return FileNotFoundError(
            "File not found. It may have been deleted or moved.",
            file_id
        )
    elif status == 429:
        return QuotaExceededError(
            "API quota exceeded. Please wait a moment and try again.",
            file_id
        )
    else:
        return GDriveError(f"API error (HTTP {status}): {str(error)}", file_id)


# Standard error message format helper
def format_error(action: str, error: Exception) -> str:
    """Format an error message consistently.
    
    Args:
        action: The action that failed (e.g., "Search", "Upload").
        error: The exception that occurred.
        
    Returns:
        Formatted error string.
    """
    if isinstance(error, GDriveError):
        return f"{action} failed: {error.message}"
    return f"{action} failed: {str(error)}"
