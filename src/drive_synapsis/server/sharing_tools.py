"""Sharing and permission MCP tools."""
from .main import mcp, get_client
from .managers import search_manager
from ..utils.errors import handle_http_error, format_error, GDriveError
import json

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception


@mcp.tool()
def share_file_with_user(file_id: str, email: str, role: str = 'reader') -> str:
    """
    Share a file with a specific user.
    Args:
        file_id: The ID of the file or its search alias.
        email: Email address of the user to share with.
        role: Access level - 'reader' (view only), 'writer' (edit), or 'commenter'.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().share_file(real_id, email, role)
    except HttpError as e:
        return format_error("Share file", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Share file", e)
    except Exception as e:
        return f"Share file failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def make_file_public(file_id: str) -> str:
    """
    Make a file publicly accessible (anyone with link can view).
    Returns a shareable link.
    Args:
        file_id: The ID of the file or its search alias.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().make_file_public(real_id)
    except HttpError as e:
        return format_error("Make public", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Make public", e)
    except Exception as e:
        return f"Make public failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def revoke_file_access(file_id: str, email: str) -> str:
    """
    Remove a user's access to a file.
    Args:
        file_id: The ID of the file or its search alias.
        email: Email address of the user whose access to revoke.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().revoke_access(real_id, email)
    except HttpError as e:
        return format_error("Revoke access", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("Revoke access", e)
    except Exception as e:
        return f"Revoke access failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def list_file_permissions(file_id: str) -> str:
    """
    List all users who have access to a file.
    Args:
        file_id: The ID of the file or its search alias.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        permissions = get_client().list_permissions(real_id)
        
        if not permissions:
            return "No permissions found (file may be private)."
        
        output = ["File Permissions:"]
        for perm in permissions:
            email = perm.get('emailAddress', perm.get('type', 'Unknown'))
            role = perm.get('role', 'unknown')
            perm_type = perm.get('type', 'unknown')
            
            if perm_type == 'anyone':
                output.append(f"  - Anyone with link: {role}")
            else:
                output.append(f"  - {email}: {role}")
        
        return "\n".join(output)
    except HttpError as e:
        return format_error("List permissions", handle_http_error(e, file_id))
    except GDriveError as e:
        return format_error("List permissions", e)
    except Exception as e:
        return f"List permissions failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def bulk_share_files(file_ids: str, email: str, role: str = 'reader') -> str:
    """
    Share multiple files with a user.
    Args:
        file_ids: JSON array of file IDs.
        email: Email to share with.
        role: 'reader', 'writer', or 'commenter'.
    """
    try:
        ids = json.loads(file_ids)
        success = 0
        errors = []
        
        for fid in ids:
            try:
                real_id = search_manager.resolve_alias(fid)
                get_client().share_file(real_id, email, role)
                success += 1
            except HttpError as e:
                err = handle_http_error(e, fid)
                errors.append(f"{fid}: {err.message}")
            except Exception as e:
                errors.append(f"{fid}: {str(e)}")
        
        result = f"Shared {success}/{len(ids)} files with {email} as {role}."
        if errors:
            result += f"\nErrors:\n" + "\n".join(errors)
        return result
    except json.JSONDecodeError:
        return "Bulk share failed: Invalid JSON array format."
    except Exception as e:
        return f"Bulk share failed: Unexpected error ({type(e).__name__}: {e})"
