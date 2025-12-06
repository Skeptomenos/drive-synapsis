from fastmcp import FastMCP
from .client import GDriveClient
import traceback
import json
import os
import io
import csv
import re
import difflib
from collections import deque
from typing import Optional
from .utils.constants import (
    DEFAULT_SEARCH_LIMIT,
    SCORE_TITLE_MATCH,
    SCORE_CONTENT_MATCH,
    SCORE_TYPE_BOOST,
    MAX_SCORE,
)

# Initialize MCP Server
mcp = FastMCP("Drive Synapsis")

# Global client, initialized lazily or on startup
client: Optional[GDriveClient] = None


def get_client() -> GDriveClient:
    """Get or create the global GDriveClient instance.
    
    Returns:
        The authenticated GDriveClient instance.
        
    Raises:
        Exception: If authentication fails.
    """
    global client
    if not client:
        try:
            client = GDriveClient()
        except Exception as e:
            raise e
    return client


class SearchManager:
    """Manages search result caching and alias resolution."""
    
    def __init__(self) -> None:
        self.search_cache: dict[str, str] = {}  # Maps 'A' -> file_id

    def cache_results(self, files: list[dict]) -> list[dict]:
        """Cache search results and assign aliases (A, B, C...).
        
        Args:
            files: List of file metadata dictionaries.
            
        Returns:
            List of files with 'alias' key added.
        """
        self.search_cache.clear()
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ranked_results = []
        
        for i, file in enumerate(files):
            if i < len(letters):
                alias = letters[i]
                self.search_cache[alias] = file['id']
                file['alias'] = alias
                ranked_results.append(file)
                
        return ranked_results

    def resolve_alias(self, query: str) -> str:
        """Resolve a single-letter alias to a file_id.
        
        Args:
            query: Either a single letter alias or file ID.
            
        Returns:
            The resolved file_id or the original query.
        """
        if len(query) == 1 and query.upper() in self.search_cache:
            return self.search_cache[query.upper()]
        return query

search_manager = SearchManager()


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
        # 1. Search (Limit defaults to 10 for reasonable speed)
        files = get_client().search_files(query, limit)
        
        if not files:
            return "No files found."
            
        # 2. Fetch Snippets in Parallel (Need meaningful content for scoring)
        snippets_map = get_client().batch_get_snippets(files)
        
        # 3. Calculate Scores
        scored_results = []
        for file in files:
            score = 0
            name = file.get('name', '')
            snippet = snippets_map.get(file['id'], '')
            mime_type = file.get('mimeType', '')
            
            # Feature 1: Title Match (High Confidence)
            if query.lower() in name.lower():
                score += SCORE_TITLE_MATCH
                
            # Feature 2: Content Match
            if query.lower() in snippet.lower():
                score += SCORE_CONTENT_MATCH
                
            # Feature 3: Type Boost (Docs/Sheets are usually what users want)
            if 'google-apps.document' in mime_type or 'google-apps.spreadsheet' in mime_type:
                score += SCORE_TYPE_BOOST
                
            # Normalize to max score
            score = min(score, MAX_SCORE)
            
            # Store for sorting
            file['score'] = score
            file['snippet'] = snippet
            scored_results.append(file)
            
        # 4. Sort by Score (Descending)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
            
        # 5. Cache & Assign Aliases (Top N)
        active_files = search_manager.cache_results(scored_results)
        
        # 6. Format Output
        output = []
        for file in active_files:
            alias = file['alias']
            name = file.get('name', 'Untitled')
            snippet = file.get('snippet', '')
            score = file.get('score', 0)
            
            output.append(f"{alias}: {name} (Confidence: {score}%)\n   {snippet}")
            
        return "\n\n".join(output)

    except Exception as e:
        return f"Error searching: {e}"

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
        
        # Cache results and assign aliases
        search_manager.cache_results(results)
        
        # Format output
        output = [f"Found {len(results)} files:"]
        for idx, file in enumerate(results):
            alias = file.get('alias', chr(65 + idx))
            output.append(f"  [{alias}] {file['name']} ({file.get('mimeType', 'unknown')})")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error searching: {e}"

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
        real_folder_id = search_manager.resolve_alias(folder_id)
        results = get_client().search_in_folder(real_folder_id, query, limit)
        
        if not results:
            return "No files found in folder."
        
        # Cache results and assign aliases
        search_manager.cache_results(results)
        
        # Format output
        output = [f"Found {len(results)} files in folder:"]
        for idx, file in enumerate(results):
            alias = file.get('alias', chr(65 + idx))
            output.append(f"  [{alias}] {file['name']}")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error searching folder: {e}"






@mcp.tool()
def create_google_doc(title: str, content: str) -> str:
    """
    Create a new Google Doc with the given title and text content.
    Args:
        title: The name of the new document.
        content: The initial text content.
    """
    try:
        return get_client().create_doc(title, content)
    except Exception as e:
        return f"Error creating doc: {str(e)}"

@mcp.resource("gdrive://{file_id}")
def read_gdrive_resource(file_id: str) -> str:
    """
    Read a Google Drive file as a resource.
    """
    return read_google_drive_file(file_id)

import json
import os

MAP_FILE = "gdrive_map.json"

class SyncManager:
    def __init__(self):
        self._load_map()

    def _load_map(self):
        if os.path.exists(MAP_FILE):
            with open(MAP_FILE, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def _save_map(self):
        with open(MAP_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def link_file(self, local_path: str, file_id: str):
        # Initial link. We don't know the version yet, so we'll set it to 0 or fetch it.
        # Ideally we fetch it now to be safe.
        version = get_client().get_file_version(file_id)
        self.data[local_path] = {
            "id": file_id,
            "last_synced_version": version
        }
        self._save_map()
        return f"Linked {local_path} to {file_id} (Version {version})"

    def get_link(self, local_path: str):
        return self.data.get(local_path)

    def update_version(self, local_path: str, version: int):
        if local_path in self.data:
            self.data[local_path]["last_synced_version"] = version
            self._save_map()

sync_manager = SyncManager()

@mcp.tool()
def link_local_file(local_path: str, file_id: str) -> str:
    """
    Link a local file to a Google Drive file ID for synchronization.
    Args:
        local_path: The relative path to the local file (e.g. "docs/notes.md").
        file_id: The Google Drive file ID or its search alias (e.g. "A").
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return sync_manager.link_file(local_path, real_id)
    except Exception as e:
        return f"Error linking file: {str(e)}"


@mcp.tool()
def update_google_doc(local_path: str, force: bool = False, dry_run: bool = True) -> str:
    """
    Upload content from a local file to its linked Google Doc.
    SAFETY: Defaults to dry_run=True. Usage must explicitly set dry_run=False to apply changes.
    Args:
        local_path: Path to the local file.
        force: If True, overwrite even if the remote file has changed since last sync.
        dry_run: If True (default), return a diff of changes instead of updating. Set to False to apply.
    """
    try:
        link = sync_manager.get_link(local_path)
        if not link:
            return f"Error: No link found for {local_path}. Use link_local_file first."
        
        file_id = link['id']
        known_version = link.get('last_synced_version', 0)
        
        # Check remote version
        current_remote_version = get_client().get_file_version(file_id)
        
        if not force and not dry_run and current_remote_version > known_version:
            return (f"CONFLICT: Remote file (v{current_remote_version}) is newer than "
                    f"last synced (v{known_version}). Use force=True to overwrite.")
        
        # Read local content
        if not os.path.exists(local_path):
             return f"Error: Local file {local_path} not found."
             
        with open(local_path, 'r') as f:
            content = f.read()
            
        if dry_run:
            # Fetch remote content for comparison
            # We assume markdown for comparison if we are uploading markdown
            remote_content = get_client().download_doc(file_id, 'markdown')
            
            diff = difflib.unified_diff(
                remote_content.splitlines(),
                content.splitlines(),
                fromfile=f'Remote (v{current_remote_version})',
                tofile='Local (Proposed)',
                lineterm=''
            )
            diff_text = "\n".join(diff)
            if not diff_text:
                return "No changes detected."
            return f"DRY RUN (No changes made):\n\n```diff\n{diff_text}\n```"

        # Check for Tab-Aware ID (Created by hybrid download)
        # Format: "FileID:TabID"
        is_tab_update = ":" in file_id
        
        if is_tab_update:
            real_file_id, tab_id = file_id.split(":", 1)
            # Perform Plain Text Tab Update
            get_client().update_tab_content(real_file_id, tab_id, content)
             
            # Update Link Version
            new_version = get_client().get_file_version(real_file_id)
            sync_manager.update_version(local_path, new_version)
            return f"Successfully updated Tab in Google Doc (new version: {new_version})"
        
        # --- Normal Doc Update ---
        
        # Safety Check: Multi-Tab Protection
        doc_struct = get_client().get_doc_structure(file_id)
        tabs = doc_struct.get('tabs', [])
        if len(tabs) > 1 and not force:
             return (f"BLOCKED: Target document has {len(tabs)} tabs. "
                     "Updating it with this file will OVERWRITE all tabs. "
                     "Use force=True to proceed, or edit the individual Tab text files.")

        # Reverse Smart Links
        # Replace [Label](../rel/path) -> [Label](https://docs.google.com/document/d/ID)
        # Regex: \((?:\.\./|./)([^)]+)\)  -- Look for relative paths in ()
        def link_replacer(match):
            rel_path = match.group(1) 
            # Resolve to abs path
            base_dir = os.path.dirname(os.path.abspath(local_path))
            abs_target = os.path.normpath(os.path.join(base_dir, rel_path))
            
            # Find in sync map
            # This is slow, O(N). But N is small.
            for lpath, data in sync_manager.data.items():
                if os.path.abspath(lpath) == abs_target:
                    fid = data['id']
                    # Strip Tab ID if present in the link (we usually link to the main doc)
                    if ":" in fid: fid = fid.split(":")[0]
                    return f"(https://docs.google.com/document/d/{fid})"
            return match.group(0) # No match
            
        # Pattern: matches (.../foo.md) or (./foo.md)
        # Note: Markdown links are [text](link).
        pattern = r'\(((?:\.\.|[\w\s-]+)/[\w\s-]+\.[a-zA-Z0-9]+)\)'
        content = re.sub(pattern, link_replacer, content)

        # Perform Update
        get_client().update_doc(file_id, content)
        
        # Update State (Remote version likely incremented)
        new_version = get_client().get_file_version(file_id)
        sync_manager.update_version(local_path, new_version)
        
        return f"Successfully updated Google Doc (new version: {new_version})"
        
    except Exception as e:
        # traceback.print_exc() # Useful for debugging but maybe not via stdio
        return f"Error updating doc: {str(e)}"

@mcp.tool()
def read_google_drive_file(name: str, id: str = None) -> str:
    """
    Read the content of a file from Google Drive to SHOW it to the user.
    Use this ONLY when the user asks to "show", "read", or "display" the file content.
    Do NOT use this if the user asks to "download", "save", or "create" a local file.
    Args:
        name: Name of the file to read.
        id: Optional ID. If not provided, searches by name.
    """
    try:
        # If an ID is provided, use it directly after resolving alias
        if id:
            real_id = search_manager.resolve_alias(id)
            return get_client().read_file(real_id)
        # If only a name is provided, search for the file
        else:
            # The search_manager.search_files function should return a list of matches.
            # We'll take the first one for simplicity, or require a more specific query.
            # For now, let's assume search_manager.resolve_alias can handle names if no ID is given.
            # This might require an update to search_manager.resolve_alias or a new search function.
            # Assuming search_manager.resolve_alias can handle names for now.
            real_id = search_manager.resolve_alias(name)
            return get_client().read_file(real_id)
    except Exception as e:
        return f"Error reading file: {str(e)}"

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
             return f"Error: Local file {local_path} not found."
             
        file = get_client().upload_file(local_path, folder_id)
        
        # Auto-link
        sync_manager.link_file(local_path, file['id'])
        
        return f"Successfully uploaded {local_path}. ID: {file['id']}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"

@mcp.tool()
def create_sheet(title: str, data: str) -> str:
    """
    Create a Google Sheet with initial data.
    Args:
        title: Title of the Sheet.
        data: CSV string or list of lists (as JSON string).
    """
    try:
        
        # Parse data
        if data.strip().startswith('['):
            # Assume JSON list of lists
            values = json.loads(data)
        else:
            # Assume CSV
            f = io.StringIO(data)
            reader = csv.reader(f)
            values = list(reader)
            
        return get_client().create_sheet(title, values)
    except Exception as e:
        return f"Error creating sheet: {str(e)}"

@mcp.tool()
def move_file(file_id: str, folder_id: str) -> str:
    """
    Move a file to a different folder.
    Args:
        file_id: The ID of the file or its search alias.
        folder_id: The ID of the destination folder or its search alias.
    """
    try:
        real_file_id = search_manager.resolve_alias(file_id)
        real_folder_id = search_manager.resolve_alias(folder_id)
        return get_client().move_file(real_file_id, real_folder_id)
    except Exception as e:
        return f"Error moving file: {str(e)}"

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
    except Exception as e:
        return f"Error renaming file: {str(e)}"

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
    except Exception as e:
        return f"Error deleting file: {str(e)}"

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
        return f"Copied to '{new_name}' (ID: {result['id']})"
    except Exception as e:
        return f"Error copying file: {str(e)}"

@mcp.tool()
def get_file_info(file_id: str) -> str:
    """
    Get detailed information about a file.
    Args:
        file_id: The ID of the file or its search alias.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        metadata = get_client().get_file_metadata(real_id)
        
        # Format as readable string
        output = [
            f"Name: {metadata.get('name')}",
            f"Type: {metadata.get('mimeType')}",
            f"Size: {metadata.get('size', 'N/A')} bytes",
            f"Created: {metadata.get('createdTime')}",
            f"Modified: {metadata.get('modifiedTime')}",
            f"Starred: {metadata.get('starred', False)}",
            f"Link: {metadata.get('webViewLink')}"
        ]
        return "\n".join(output)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

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
    except Exception as e:
        return f"Error starring file: {str(e)}"

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
    except Exception as e:
        return f"Error sharing file: {str(e)}"

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
    except Exception as e:
        return f"Error making file public: {str(e)}"

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
    except Exception as e:
        return f"Error revoking access: {str(e)}"

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
        
        # Format as readable list
        output = ["File Permissions:"]
        for perm in permissions:
            perm_type = perm.get('type', 'user')
            email = perm.get('emailAddress', 'anyone')
            role = perm.get('role', 'reader')
            output.append(f"  - {email} ({role}, {perm_type})")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error listing permissions: {str(e)}"

@mcp.tool()
def replace_doc_text(file_id: str, find: str, replace: str, match_case: bool = False) -> str:
    """
    Find and replace text in a Google Doc.
    Useful for bulk updates like changing "TODO" to "DONE".
    Args:
        file_id: The ID of the doc or its search alias.
        find: Text to find.
        replace: Text to replace with.
        match_case: If True, search is case-sensitive.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().replace_text_in_doc(real_id, find, replace, match_case)
    except Exception as e:
        return f"Error replacing text: {str(e)}"

@mcp.tool()
def insert_doc_table(file_id: str, rows: int, cols: int, index: int = 1) -> str:
    """
    Insert a table into a Google Doc.
    Args:
        file_id: The ID of the doc or its search alias.
        rows: Number of rows.
        cols: Number of columns.
        index: Position to insert (1 = start of document).
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().insert_table(real_id, rows, cols, index)
    except Exception as e:
        return f"Error inserting table: {str(e)}"

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
    except Exception as e:
        return f"Error setting description: {str(e)}"


@mcp.tool()
def update_sheet_cell(spreadsheet_id: str, range_name: str, value: str) -> str:
    """
    Update a specific cell or range in a Google Sheet.
    Args:
        spreadsheet_id: The ID of the sheet or its search alias (e.g. "A").
        range_name: The A1 notation range (e.g. "B2", "Sheet1!A1:B2").
        value: The value to write. To write a formula, start with '='.
               To write multiple values to a range, provide a JSON list of lists as the string.
               Example: '[[1, 2], [3, 4]]'
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        
        # Check if value is a JSON structure for multi-cell update
        values = [[value]] # Default to single cell
        if value.strip().startswith('[') and range_name.count(':') > 0:
             try:
                 parsed = json.loads(value)
                 if isinstance(parsed, list):
                     values = parsed
             except:
                 pass # Treat as string
                 
        return get_client().update_sheet_values(real_id, range_name, values)
    except Exception as e:
        return f"Error updating sheet: {str(e)}"

@mcp.tool()
def read_sheet_range(spreadsheet_id: str, range_name: str) -> str:
    """
    Read a specific range of cells from a Google Sheet.
    Returns the data as a formatted string or JSON.
    Args:
        spreadsheet_id: The ID of the sheet or its search alias (e.g. "A").
        range_name: The A1 notation range (e.g. "Sheet1!A1:C10").
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        values = get_client().read_sheet_values(real_id, range_name)
        
        if not values:
            return "No data found in range."
            
        # Format as Markdown Table for readability
        output = []
        # Calculate max width for each column for alignment (simple)
        # Or just use JSON?
        # Let's return JSON for precision if it's data data.
        # But if the user asks to "Read", markdown is better.
        
        # Table Header
        header = values[0]
        output.append("| " + " | ".join(map(str, header)) + " |")
        output.append("| " + " | ".join(['---'] * len(header)) + " |")
        
        for row in values[1:]:
             # Pad row
             row_data = [str(x) for x in row]
             while len(row_data) < len(header): row_data.append('')
             output.append("| " + " | ".join(row_data) + " |")
             
        return "\n".join(output) + f"\n\n(Raw JSON: `{json.dumps(values)}`)"
        
    except Exception as e:
        return f"Error reading range: {str(e)}"

@mcp.tool()
def append_to_sheet(spreadsheet_id: str, range_name: str, values: str) -> str:
    """
    Append rows to a Google Sheet without overwriting existing data.
    Preserves formulas and references.
    Args:
        spreadsheet_id: The sheet ID or alias.
        range_name: Range like "Sheet1!A1" (start of where to append).
        values: JSON list of lists, e.g. '[["A", "B"], ["C", "D"]]'
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        parsed_values = json.loads(values)
        return get_client().append_sheet_rows(real_id, range_name, parsed_values)
    except Exception as e:
        return f"Error appending to sheet: {str(e)}"

@mcp.tool()
def add_sheet_tab(spreadsheet_id: str, tab_name: str) -> str:
    """
    Add a new tab to an existing spreadsheet.
    Does not modify existing tabs, preserving all formulas and data.
    Args:
        spreadsheet_id: The sheet ID or alias.
        tab_name: Name for the new tab.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().add_sheet_tab(real_id, tab_name)
    except Exception as e:
        return f"Error adding tab: {str(e)}"

@mcp.tool()
def format_sheet_cells(spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, bold: bool = False, background_color: str = None) -> str:
    """
    Format cells in a Google Sheet (bold text, background color).
    Args:
        spreadsheet_id: The sheet ID or alias.
        sheet_id: The specific tab/sheet ID (use 0 for first tab).
        start_row, end_row: Row range (0-indexed).
        start_col, end_col: Column range (0-indexed, A=0, B=1, etc).
        bold: Make text bold.
        background_color: Hex color like '#FF0000'.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().format_sheet_range(real_id, sheet_id, start_row, end_row, start_col, end_col, bold, background_color)
    except Exception as e:
        return f"Error formatting: {str(e)}"

@mcp.tool()
def protect_sheet_cells(spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int, description: str = 'Protected') -> str:
    """
    Protect a range of cells from editing.
    Args:
        spreadsheet_id: The sheet ID or alias.
        sheet_id: The tab ID (0 for first tab).
        start_row, end_row, start_col, end_col: Range (0-indexed).
        description: Reason for protection.
    """
    try:
        real_id = search_manager.resolve_alias(spreadsheet_id)
        return get_client().protect_sheet_range(real_id, sheet_id, start_row, end_row, start_col, end_col, description)
    except Exception as e:
        return f"Error protecting: {str(e)}"

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
        
        for file_id in ids:
            try:
                real_id = search_manager.resolve_alias(file_id)
                get_client().delete_file(real_id, permanent)
                success += 1
            except Exception as e:
                errors.append(f"{file_id}: {str(e)[:30]}")
        
        result = f"Deleted {success}/{len(ids)} files"
        if errors:
            result += f"\nErrors: {', '.join(errors[:5])}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

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
        
        for file_id in ids:
            try:
                real_id = search_manager.resolve_alias(file_id)
                get_client().move_file(real_id, real_folder)
                success += 1
            except Exception as e:
                errors.append(f"{file_id}: {str(e)[:30]}")
        
        result = f"Moved {success}/{len(ids)} files"
        if errors:
            result += f"\nErrors: {', '.join(errors[:5])}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

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
        
        for file_id in ids:
            try:
                real_id = search_manager.resolve_alias(file_id)
                get_client().share_file(real_id, email, role)
                success += 1
            except Exception as e:
                errors.append(f"{file_id}: {str(e)[:30]}")
        
        result = f"Shared {success}/{len(ids)} files with {email}"
        if errors:
            result += f"\nErrors: {', '.join(errors[:5])}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_document_outline(file_id: str) -> str:
    """
    Get the table of contents / outline of a Google Doc.
    Extracts all headings (H1-H6) to help navigate large documents.
    Use this before reading the full document to understand its structure.
    Args:
        file_id: The ID of the document or its search alias (e.g. "A").
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        outline = get_client().get_document_outline(real_id)
        
        if not outline:
            return "No headings found in document."
        
        # Format as hierarchical outline
        output = ["# Document Outline\n"]
        for item in outline:
            level = item['level']
            text = item['text']
            indent = "  " * (level - 1)
            output.append(f"{indent}{level}. {text}")
            
        return "\n".join(output)
        
    except Exception as e:
        return f"Error getting outline: {str(e)}"

@mcp.tool()
def read_document_section(file_id: str, section_number: int) -> str:
    """
    Read a specific section of a Google Doc by section number.
    First call get_document_outline to see the sections, then use this to read one.
    Args:
        file_id: The ID of the document or its search alias (e.g. "A").
        section_number: The section number (1-based) from the outline.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        outline = get_client().get_document_outline(real_id)
        
        if not outline or section_number < 1 or section_number > len(outline):
            return f"Invalid section number. Document has {len(outline)} sections."
        
        # Get the section bounds
        section = outline[section_number - 1]
        start_index = section['startIndex']
        
        # End index is either the start of the next section or document end
        if section_number < len(outline):
            end_index = outline[section_number]['startIndex']
        else:
            # Read to the end of the document
            # We'll use a large number as a proxy
            end_index = start_index + 100000
        
        content = get_client().read_document_section(real_id, start_index, end_index)
        return f"# {section['text']}\n\n{content}"
        
    except Exception as e:
        return f"Error reading section: {str(e)}"

@mcp.tool()
def post_comment(file_id: str, comment_text: str, quoted_text: str = None) -> str:
    """
    Post a comment on a Google Drive file (Doc, Sheet, etc.).
    Useful for collaboration workflows where AI needs to flag issues or ask questions.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        comment_text: The text of the comment.
        quoted_text: Optional text from the document to anchor the comment to.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().create_comment(real_id, comment_text, quoted_text)
    except Exception as e:
        return f"Error posting comment: {str(e)}"

@mcp.tool()
def reply_to_comment(file_id: str, comment_id: str, reply_text: str) -> str:
    """
    Reply to an existing comment on a Google Drive file.
    First use download_google_doc with include_comments=True to see comment IDs.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        comment_id: The ID of the comment to reply to.
        reply_text: The text of the reply.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().reply_to_comment(real_id, comment_id, reply_text)
    except Exception as e:
        return f"Error replying to comment: {str(e)}"

@mcp.tool()
def upload_folder(local_path: str, parent_folder_id: str = None) -> str:
    """
    Recursively upload a local folder to Google Drive using BFS traversal.
    More robust than recursion - handles deep trees and reports errors gracefully.
    """
    try:
        if not os.path.exists(local_path) or not os.path.isdir(local_path):
            return f"Error: {local_path} is not a directory."
        
        # Create root folder
        dir_name = os.path.basename(os.path.normpath(local_path))
        folder_metadata = {
            'name': dir_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        root_folder = get_client().drive_service.files().create(
            body=folder_metadata, fields='id').execute()
        root_folder_id = root_folder.get('id')
        
        # Track folder mappings: local_path -> drive_id
        folder_map = {local_path: root_folder_id}
        
        # BFS Queue: (local_path, drive_parent_id)
        queue = deque([(local_path, root_folder_id)])
        uploaded_count = 0
        errors = []
        
        while queue:
            current_local, current_drive_parent = queue.popleft()
            
            try:
                items = os.listdir(current_local)
            except PermissionError:
                errors.append(f"Permission denied: {current_local}")
                continue
            
            for item in items:
                # Skip system files
                if item in ['.DS_Store', '.gitignore', '__pycache__']:
                    continue
                
                item_path = os.path.join(current_local, item)
                
                if os.path.isfile(item_path):
                    # Upload file
                    try:
                        get_client().upload_file(item_path, current_drive_parent)
                        uploaded_count += 1
                    except Exception as e:
                        errors.append(f"Failed to upload {item}: {str(e)[:50]}")
                        
                elif os.path.isdir(item_path):
                    # Create subfolder and queue it
                    try:
                        meta = {
                            'name': item,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [current_drive_parent]
                        }
                        sub_folder = get_client().drive_service.files().create(
                            body=meta, fields='id').execute()
                        folder_map[item_path] = sub_folder.get('id')
                        queue.append((item_path, sub_folder.get('id')))
                    except Exception as e:
                        errors.append(f"Failed to create folder {item}: {str(e)[:50]}")
        
        # Report results
        result = f"✅ Uploaded {uploaded_count} files to '{dir_name}'"
        if errors:
            result += f"\n\n⚠️ Errors ({len(errors)}): \n" + "\n".join(errors[:10])
            if len(errors) > 10:
                result += f"\n... and {len(errors) - 10} more errors"
        return result
        
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def append_to_google_doc(file_id: str, content: str) -> str:
    """
    Append text to the end of a Google Doc.
    Useful for maintaining logs, journals, or meeting notes.
    Args:
        file_id: The ID of the file or its search alias (e.g. "A").
        content: The text to append.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        return get_client().append_text_to_doc(real_id, content)
    except Exception as e:
        return f"Error appending to doc: {str(e)}"

@mcp.tool()
def create_doc_from_template(template_id: str, new_title: str, replacements: str) -> str:
    """
    Create a new Google Doc by copying a template and replacing placeholders.
    Args:
        template_id: The ID of the template file or its search alias (e.g. "A").
        new_title: The title for the new document.
        replacements: A JSON string of replacements, e.g. '{"{{name}}": "Alice", "{{date}}": "2023-01-01"}'.
    """
    try:
        real_id = search_manager.resolve_alias(template_id)
        replacements_dict = json.loads(replacements)
        return get_client().create_from_template(real_id, new_title, replacements_dict)
    except Exception as e:
        return f"Error creating from template: {str(e)}"

@mcp.tool()
def download_google_doc(local_path: str, format: str = 'markdown', include_comments: bool = False, rewrite_links: bool = True, dry_run: bool = True) -> str:
    """
    Download content from a linked Google Doc and SAVE it to a local file.
    SAFETY: Defaults to dry_run=True. Usage must explicitly set dry_run=False to apply changes.
    Args:
        local_path: Path to the local file.
        format: The format to download (markdown, pdf, docx, html, json, csv, xlsx). Default: markdown.
        include_comments: If True, fetches comments and saves them to {local_path}.comments.json.
        rewrite_links: If True (and format=markdown), attempts to rewrite Google Drive links to relative local paths.
        dry_run: If True (default), return a diff of changes (for text/markdown) or a preview message. Set False to save.
    """
    try:
        link = sync_manager.get_link(local_path)
        if not link:
            return f"Error: No link found for {local_path}. Use link_local_file first."
        
        file_id = link['id']
        
        # Auto-Detect Multi-Tab Documents (Hybrid Sync Enforcer)
        # If the user asks for a simple markdown download, but the doc has tabs, 
        # we explicitly switch to 'download_doc_tabs' to preserve structure.
        if format == 'markdown':
            try:
                struct = get_client().get_doc_structure(file_id)
                tabs = struct.get('tabs', [])
                if len(tabs) > 1:
                    # Switch to Hybrid Sync
                    # Logic: local_path "Doc.md" -> Directory "Doc"
                    target_dir = os.path.splitext(local_path)[0]
                    return (f"NOTE: Multi-tab document detected ({len(tabs)} tabs). "
                            f"Automatically switched to Hybrid Sync.\n"
                            f"{download_doc_tabs(target_dir, file_id)}")
            except Exception as e:
                # If structure fetch fails, fall back to standard download
                print(f"Warning: Failed to check tab structure: {e}")

        # Download content
        content = get_client().download_doc(file_id, format)
        
        # Smart Link Rewriting
        rewritten_count = 0
        if rewrite_links and format == 'markdown' and isinstance(content, str):
            # Regex to find drive links: https://docs.google.com/document/d/FILE_ID/...
            # We want to match the whole URL in a markdown link: [Text](URL)
            # Simplified: Look for the File ID pattern in the content.
            # Pattern: matches /d/([a-zA-Z0-9-_]+)
            
            def replace_callback(match):
                nonlocal rewritten_count
                full_match = match.group(0) # The full URL
                doc_id = match.group(1)     # The ID
                
                # Check if this ID is in our sync map
                # Need reverse lookup: ID -> Local Path
                target_local_path = None
                for path, data in sync_manager.data.items():
                    if data['id'] == doc_id:
                        target_local_path = path
                        break
                
                if target_local_path:
                    # Calculate relative path
                    # From: directory of current local_path
                    # To: target_local_path
                    start_dir = os.path.dirname(os.path.abspath(local_path))
                    target_abs_path = os.path.abspath(target_local_path)
                    rel_path = os.path.relpath(target_abs_path, start_dir)
                    rewritten_count += 1
                    return rel_path
                
                return full_match # Return original if not found

            pattern = r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)[^)]*'
            content = re.sub(pattern, replace_callback, content)

        # --- Dry Run / Diff Logic ---
        if dry_run:
            if os.path.exists(local_path):
                # Calculate Diff if text
                if format in ['markdown', 'html', 'csv', 'json', 'txt'] and isinstance(content, str):
                    try:
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_content = f.read()
                        
                        diff = difflib.unified_diff(
                            local_content.splitlines(),
                            content.splitlines(),
                            fromfile=f'Local: {local_path}',
                            tofile=f'Remote: {file_id}',
                            lineterm=''
                        )
                        diff_text = '\n'.join(diff)
                        if not diff_text:
                            return f"Dry Run: No changes detected for {local_path}."
                        return f"Dry Run: Changes detected for {local_path}:\n{diff_text}"
                    except Exception as e:
                        return f"Dry Run: Could not diff content ({e}). Content length: {len(content)}"
                else:
                    return f"Dry Run: Binary/Other content would allow overwrite of {local_path}."
            else:
                return f"Dry Run: New file would be created at {local_path}."

        # Write to local
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        
        mode = 'wb' if isinstance(content, bytes) else 'w'
        encoding = None if isinstance(content, bytes) else 'utf-8'
        
        with open(local_path, mode, encoding=encoding) as f:
            f.write(content)

        # Handle Comments
        comment_msg = ""
        if include_comments:
            comments = get_client().get_file_comments(file_id)
            if comments:
                comments_path = local_path + ".comments.json"
                with open(comments_path, 'w', encoding='utf-8') as f:
                    json.dump(comments, f, indent=2)
                comment_msg = f" Extracted {len(comments)} comments."

        link_msg = ""
        if rewritten_count > 0:
            link_msg = f" Rewrote {rewritten_count} links."
            
        # Update State
        # Note: Version tracking is tricky for non-native formats as they don't map 1-to-1 to Drive versions perfectly
        # but we'll track the source drive version.
        current_version = get_client().get_file_version(file_id)
        sync_manager.update_version(local_path, current_version)
        
        return f"Successfully downloaded to {local_path} (Format: {format}, v{current_version}).{comment_msg}{link_msg}"
        
    except Exception as e:
        return f"Error downloading doc: {str(e)}"


@mcp.tool()
def mirror_drive_folder(local_parent_dir: str, folder_query: str, recursive: bool = True) -> str:
    """
    Recursively download a Google Drive folder to a local directory.
    Maintains directory structure and links downloaded files for future sync.
    Args:
        local_parent_dir: The local directory to download into. Created if missing.
        folder_query: The Name or ID of the Drive folder.
        recursive: Whether to download subfolders.
    """
    try:
        # Resolve Folder ID (Simple Logic: Try name match, then assume ID)
        folder_id = get_client().get_folder_id(folder_query)
        if not folder_id:
             # Fallback: assume it works as an ID if it looks like one
             if len(folder_query) > 10:
                 folder_id = folder_query
             else:
                 return f"Error: Folder '{folder_query}' not found."
             
        # Helper for recursion
        def _process_folder(f_id, current_local_path):
            os.makedirs(current_local_path, exist_ok=True)
            files = get_client().list_folder_contents(f_id)
            
            summary_log = []
            
            for file in files:
                name = file['name']
                mime = file['mimeType']
                fid = file['id']
                
                # Sanitize filename
                # Use a simple regex or whitelist to avoid OS issues
                safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in " ._-()"]).strip()
                if not safe_name:
                    safe_name = "untitled_file"

                if mime == 'application/vnd.google-apps.folder':
                    if recursive:
                        log = _process_folder(fid, os.path.join(current_local_path, safe_name))
                        summary_log.extend(log)
                elif 'google-apps.document' in mime or 'google-apps.spreadsheet' in mime:
                    # Determine extension
                    ext = ".md" if 'google-apps.document' in mime else ".csv"
                    local_file_path = os.path.join(current_local_path, safe_name + ext)
                    
                    # Download
                    try:
                        format_type = 'markdown' if 'google-apps.document' in mime else 'csv'
                        content = get_client().download_doc(fid, format_type)
                        
                        # Write
                        mode = 'wb' if isinstance(content, bytes) else 'w'
                        encoding = None if isinstance(content, bytes) else 'utf-8'
                        with open(local_file_path, mode, encoding=encoding) as f:
                            f.write(content)
                            
                        # Link
                        # Note: This creates a linear link map.
                        # Ideally, we should also track that this folder is "Mirrored" to handle deletions later,
                        # but for this iteration, individual file linking is sufficient for "Download & Sync".
                        sync_manager.link_file(local_file_path, fid)
                        summary_log.append(f"Downloaded: {local_file_path}")
                    except Exception as e:
                        summary_log.append(f"Failed to download {name}: {e}")
            
            return summary_log

        logs = _process_folder(folder_id, local_parent_dir)
        total_files = len(logs)
        
        return f"Mirror Complete for folder '{folder_query}'. Downloaded {total_files} files.\nTop results:\n" + "\n".join(logs[:5])

    except Exception as e:
        return f"Error mirroring folder: {str(e)}"


@mcp.tool()
def download_doc_tabs(local_dir: str, file_id: str) -> str:
    """
    Download a Google Doc using "Hybrid Split-Sync".
    Creates a folder containing:
    1. _Full_Export.md: The entire doc as Markdown (High Fidelity).
    2. [TabName].md: Raw text content of each individual tab.
    Args:
        local_dir: Local directory to save files into.
        file_id: The Google Drive file ID.
    """
    try:
        real_id = search_manager.resolve_alias(file_id)
        os.makedirs(local_dir, exist_ok=True)
        
        # 1. Full Export
        full_content = get_client().download_doc(real_id, 'markdown')
        with open(os.path.join(local_dir, "_Full_Export.md"), 'w') as f:
            f.write(full_content)
            
        # 2. Extract Tabs
        doc_structure = get_client().get_doc_structure(real_id)
        tabs = doc_structure.get('tabs', [])
        
        # If no tabs field, check if it's a single-tab legacy doc which just has 'body'
        # The API unifies this usually, but let's be safe.
        # Actually, for the new Tabs API, even single docs have a default tab.
        # But if 'tabs' is missing, fallback to using body as 'Main'.
        
        extracted_count = 0
        
        if not tabs:
             # Fallback for simple doc
             body = doc_structure.get('body').get('content', [])
             text = get_client().extract_text_from_element(body)
             with open(os.path.join(local_dir, "Main.txt"), 'w') as f:
                 f.write(text)
             extracted_count = 1
        else:
            for tab in tabs:
                tab_props = tab.get('tabProperties', {})
                title = tab_props.get('title', 'Untitled Tab')
                # Sanitize title
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in " ._-"]).strip()
                
                # Content is in 'documentTab' -> 'body'
                doc_tab = tab.get('documentTab', {})
                body = doc_tab.get('body', {}).get('content', [])
                
                text = get_client().extract_text_from_element(body)
                
                with open(os.path.join(local_dir, f"{safe_title}.txt"), 'w') as f:
                    f.write(text)
                
                # Register Tab Link
                tab_id = tab_props.get('tabId')
                if tab_id:
                     tab_file = os.path.join(local_dir, f"{safe_title}.txt")
                     sync_manager.link_file(tab_file, f"{real_id}:{tab_id}")
                     
                extracted_count += 1
                
        # Update Link (Map the FOLDER to the Doc ID for reference)
        # We might not be able to use standard 'update_doc' on this folder, but it marks the location.
        sync_manager.link_file(local_dir, real_id)
        # Also link _Full_Export.md explicitly
        sync_manager.link_file(os.path.join(local_dir, "_Full_Export.md"), real_id)
        
        return f"Hybrid Sync Complete in '{local_dir}'. Saved _Full_Export.md and {extracted_count} tab files."

    except Exception as e:
        return f"Error downloading tabs: {str(e)}"


def main():
    """Entry point for the Drive Synapsis MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
