"""Search-related MCP tools."""
from .main import mcp, get_client
from .managers import search_manager
from ..utils.constants import (
    SCORE_TITLE_MATCH,
    SCORE_CONTENT_MATCH,
    SCORE_TYPE_BOOST,
    MAX_SCORE,
)
from ..utils.errors import handle_http_error, format_error, GDriveError

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception  # Fallback for testing


@mcp.tool()
def search_google_drive(query: str, limit: int = 10) -> str:
    """
    Search for files in Google Drive.
    Args:
        query: The search query (e.g. "Project Plan", "budget").
        limit: Max number of results (default 10).
    Returns:
        Formatted list of files (Alias: Title - Summary).
    """
    try:
        files = get_client().search_files(query, limit)
        
        if not files:
            return "No files found."
            
        snippets_map = get_client().batch_get_snippets(files)
        
        scored_results = []
        for file in files:
            score = 0
            name = file.get('name', '')
            snippet = snippets_map.get(file['id'], '')
            mime_type = file.get('mimeType', '')
            
            if query.lower() in name.lower():
                score += SCORE_TITLE_MATCH
                
            if query.lower() in snippet.lower():
                score += SCORE_CONTENT_MATCH
                
            if 'google-apps.document' in mime_type or 'google-apps.spreadsheet' in mime_type:
                score += SCORE_TYPE_BOOST
                
            score = min(score, MAX_SCORE)
            
            file['score'] = score
            file['snippet'] = snippet
            scored_results.append(file)
            
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        active_files = search_manager.cache_results(scored_results)
        
        output = []
        for file in active_files:
            alias = file['alias']
            name = file.get('name', 'Untitled')
            snippet = file.get('snippet', '')
            score = file.get('score', 0)
            
            output.append(f"{alias}: {name} (Confidence: {score}%)\n   {snippet}")
            
        return "\n\n".join(output)

    except HttpError as e:
        return format_error("Search", handle_http_error(e))
    except GDriveError as e:
        return format_error("Search", e)
    except Exception as e:
        return f"Search failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def search_google_drive_advanced(
    query: str,
    file_type: str = None,
    modified_after: str = None,
    owner: str = 'me',
    limit: int = 10
) -> str:
    """
    Advanced search with filters for file type, modification date, and owner.
    Args:
        query: Search query.
        file_type: Filter by type - 'doc', 'sheet', 'folder', 'pdf', 'image'.
        modified_after: Only files modified after this date (YYYY-MM-DD).
        owner: 'me' (your files) or 'anyone' (all accessible files).
        limit: Maximum number of results (default 10).
    """
    try:
        results = get_client().search_files_advanced(
            query, file_type, modified_after, owner, limit
        )
        
        if not results:
            return "No files found matching criteria."
        
        search_manager.cache_results(results)
        
        output = [f"Found {len(results)} files:"]
        for idx, file in enumerate(results):
            alias = file.get('alias', chr(65 + idx))
            output.append(f"  [{alias}] {file['name']} ({file.get('mimeType', 'unknown')})")
        
        return "\n".join(output)
    except HttpError as e:
        return format_error("Search", handle_http_error(e))
    except GDriveError as e:
        return format_error("Search", e)
    except Exception as e:
        return f"Search failed: Unexpected error ({type(e).__name__}: {e})"


@mcp.tool()
def search_folder(folder_id: str, query: str, limit: int = 10) -> str:
    """
    Search for files within a specific folder.
    Args:
        folder_id: The ID of the folder or its search alias.
        query: Search query.
        limit: Maximum number of results.
    """
    try:
        real_id = search_manager.resolve_alias(folder_id)
        results = get_client().search_in_folder(real_id, query, limit)
        
        if not results:
            return "No files found in folder."
        
        search_manager.cache_results(results)
        
        output = [f"Found {len(results)} files in folder:"]
        for idx, file in enumerate(results):
            alias = file.get('alias', chr(65 + idx))
            output.append(f"  [{alias}] {file['name']} ({file.get('mimeType', 'unknown')})")
        
        return "\n".join(output)
    except HttpError as e:
        return format_error("Folder search", handle_http_error(e, folder_id))
    except GDriveError as e:
        return format_error("Folder search", e)
    except Exception as e:
        return f"Folder search failed: Unexpected error ({type(e).__name__}: {e})"
