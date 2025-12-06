"""File management MCP tools."""
from .main import mcp, get_client
from .managers import search_manager, sync_manager
from utils.errors import (
    handle_http_error, format_error, GDriveError, 
    LocalFileNotFoundError
)
import json
import os

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception


@mcp.tool()
def upload_file(local_path: str, folder_id: str = None) -> str:
    """
    Upload any file (binary or text) to Google Drive.
    Args:
        local_path: Path to the local file.
        folder_id: Optional ID of the parent folder in Drive.
    """
    try:
        if not os.path.exists(local_path):
            raise LocalFileNotFoundError(local_path)
             
        file = get_client().upload_file(local_path, folder_id)
        sync_manager.link_file(local_path, file['id'])
        
        return f"Successfully uploaded {local_path}. ID: {file['id']}"
    except LocalFileNotFoundError as e:
        return format_error("Upload", e)
    except HttpError as e:
        return format_error("Upload", handle_http_error(e))
    except GDriveError as e:
        return format_error("Upload", e)
    except Exception as e:
        return f"Upload failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def move_file(file_id: str, folder_id: str) -> str:
    """
    Move a file to a different folder.
    Args:
        file_id: The ID of the file or its search alias.
        folder_id: The ID of the destination folder or its search alias.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        real_folder = search_manager.resolve_alias(folder_id)
        return get_client().move_file(real_id, real_folder)
    except HttpError as e:
        return format_error("Move file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Move file", e)
    except Exception as e:
        return f"Move file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def rename_file(file_id: str, new_name: str) -> str:
    """
    Rename a file without changing its location.
    Args:
        file_id: The ID of the file or its search alias.
        new_name: The new name for the file.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().rename_file(real_id, new_name)
    except HttpError as e:
        return format_error("Rename file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Rename file", e)
    except Exception as e:
        return f"Rename file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def delete_file(file_id: str, permanent: bool = False) -> str:
    """
    Delete a file (default: move to trash).
    Args:
        file_id: The ID of the file or its search alias.
        permanent: If True, permanently delete (cannot be recovered).
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().delete_file(real_id, permanent)
    except HttpError as e:
        return format_error("Delete file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Delete file", e)
    except Exception as e:
        return f"Delete file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def copy_file(file_id: str, new_name: str, folder_id: str = None) -> str:
    """
    Create a copy of a file.
    Args:
        file_id: The ID of the file or its search alias.
        new_name: Name for the copy.
        folder_id: Optional destination folder ID.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        real_folder = search_manager.resolve_alias(folder_id) if folder_id else None
        result = get_client().copy_file(real_id, new_name, real_folder)
        return f"Created copy '{result['name']}' with ID: {result['id']}"
    except HttpError as e:
        return format_error("Copy file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Copy file", e)
    except Exception as e:
        return f"Copy file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def get_file_info(file_id: str) -> str:
    """
    Get detailed information about a file.
    Args:
        file_id: The ID of the file or its search alias.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        meta = get_client().get_file_metadata(real_id)
        
        output = [
            f"Name: {meta.get('name')}",
            f"Type: {meta.get('mimeType')}",
            f"Size: {meta.get('size', 'N/A')} bytes",
            f"Created: {meta.get('createdTime')}",
            f"Modified: {meta.get('modifiedTime')}",
            f"Starred: {meta.get('starred')}",
            f"Trashed: {meta.get('trashed')}",
            f"Link: {meta.get('webViewLink')}"
        ]
        
        return "\n".join(output)
    except HttpError as e:
        return format_error("Get file info", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Get file info", e)
    except Exception as e:
        return f"Get file info failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def star_file(file_id: str, starred: bool = True) -> str:
    """
    Star or unstar a file for quick access.
    Args:
        file_id: The ID of the file or its search alias.
        starred: True to star, False to unstar.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().star_file(real_id, starred)
    except HttpError as e:
        return format_error("Star file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Star file", e)
    except Exception as e:
        return f"Star file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def set_doc_description(file_id: str, description: str) -> str:
    """
    Set or update a file's description metadata.
    Useful for adding context or notes.
    Args:
        file_id: The ID of the file or its search alias.
        description: The description text.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().set_file_description(real_id, description)
    except HttpError as e:
        return format_error("Set description", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Set description", e)
    except Exception as e:
        return f"Set description failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def bulk_delete_files(file_ids: str, permanent: bool = False) -> str:
    """
    Delete multiple files at once.
    Args:
        file_ids: JSON array of file IDs, e.g. '["id1", "id2", "id3"]'
        permanent: If True, permanently delete (cannot recover).
    """
    try:
        ids = json.loads(file_ids)
        success = 0
        errors = []
        
        for fid in ids:
            try:
                real_id = search_manager.resolve_alias(fid)
                get_client().delete_file(real_id, permanent)
                success += 1
            except HttpError as e:
                err = handle_http_error(e, fid)
                errors.append(f"{fid}: {err.message}")
            except Exception as e:
                errors.append(f"{fid}: {str(e)}")
        
        result = f"Deleted {success}/{len(ids)} files."
        if errors:
            result += f"\nErrors:\n" + "\n".join(errors)
        return result
    except json.JSONDecodeError:
        return "Bulk delete failed: Invalid JSON array format."
    except Exception as e:
        return f"Bulk delete failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def bulk_move_files(file_ids: str, folder_id: str) -> str:
    """
    Move multiple files to a folder.
    Args:
        file_ids: JSON array of file IDs.
        folder_id: Destination folder ID or alias.
    """
    try:
        ids = json.loads(file_ids)
        real_folder = search_manager.resolve_alias(folder_id)
        success = 0
        errors = []
        
        for fid in ids:
            try:
                real_id = search_manager.resolve_alias(fid)
                get_client().move_file(real_id, real_folder)
                success += 1
            except HttpError as e:
                err = handle_http_error(e, fid)
                errors.append(f"{fid}: {err.message}")
            except Exception as e:
                errors.append(f"{fid}: {str(e)}")
        
        result = f"Moved {success}/{len(ids)} files."
        if errors:
            result += f"\nErrors:\n" + "\n".join(errors)
        return result
    except json.JSONDecodeError:
        return "Bulk move failed: Invalid JSON array format."
    except Exception as e:
        return f"Bulk move failed: Unexpected error ({type(e).__name__}: {e})"
