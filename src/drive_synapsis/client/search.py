"""Search operations mixin for GDriveClient."""
from typing import Optional, Any
from utils.constants import DEFAULT_SNIPPET_LENGTH, DEFAULT_MAX_WORKERS, GOOGLE_MIME_TYPES
import concurrent.futures


class SearchMixin:
    """Mixin providing search-related operations."""
    
    def search_files(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for files using Drive Query Language.
        
        Args:
            query: Search string to match against file names and content.
            limit: Maximum number of results to return.
            
        Returns:
            List of file metadata dictionaries.
        """
        drive_query = f"(name contains '{query}' or fullText contains '{query}') and trashed = false"
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, parents)"
        ).execute()
        
        return results.get('files', [])

    def search_files_advanced(
        self,
        query: str,
        file_type: Optional[str] = None,
        modified_after: Optional[str] = None,
        owner: str = 'me',
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Advanced search with filters.
        
        Args:
            query: Search query.
            file_type: 'doc', 'sheet', 'folder', 'pdf', etc.
            modified_after: ISO date string (e.g. '2024-01-01').
            owner: 'me' or 'anyone'.
            limit: Max results.
            
        Returns:
            List of file metadata dictionaries.
        """
        query_parts = [f"(name contains '{query}' or fullText contains '{query}')"]
        query_parts.append("trashed = false")
        
        if file_type:
            mime_map = {
                'doc': 'application/vnd.google-apps.document',
                'sheet': 'application/vnd.google-apps.spreadsheet',
                'folder': 'application/vnd.google-apps.folder',
                'pdf': 'application/pdf',
                'image': 'image/',
            }
            if file_type in mime_map:
                mime = mime_map[file_type]
                if file_type == 'image':
                    query_parts.append(f"mimeType contains '{mime}'")
                else:
                    query_parts.append(f"mimeType = '{mime}'")
        
        if modified_after:
            query_parts.append(f"modifiedTime > '{modified_after}T00:00:00'")
        
        if owner == 'me':
            query_parts.append("'me' in owners")
        
        drive_query = ' and '.join(query_parts)
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, parents)"
        ).execute()
        
        return results.get('files', [])

    def search_in_folder(self, folder_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search for files within a specific folder.
        
        Args:
            folder_id: The folder ID.
            query: Search query.
            limit: Maximum results.
            
        Returns:
            List of file metadata dictionaries.
        """
        drive_query = f"'{folder_id}' in parents and (name contains '{query}' or fullText contains '{query}') and trashed = false"
        
        results = self.drive_service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="files(id, name, mimeType, webViewLink)"
        ).execute()
        
        return results.get('files', [])

    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """Find a folder ID by exact name match.
        
        Args:
            folder_name: The folder name to search for.
            
        Returns:
            The folder ID or None if not found.
        """
        drive_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive_service.files().list(q=drive_query, fields="files(id)").execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def list_folder_contents(self, folder_id: str) -> list[dict[str, Any]]:
        """List all children of a folder (non-recursive).
        
        Args:
            folder_id: The folder ID.
            
        Returns:
            List of file metadata dictionaries.
        """
        drive_query = f"'{folder_id}' in parents and trashed = false"
        all_files = []
        page_token = None
        
        while True:
            results = self.drive_service.files().list(
                q=drive_query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token
            ).execute()
            all_files.extend(results.get('files', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
        return all_files

    def get_file_snippet(self, file_id: str, length: int = DEFAULT_SNIPPET_LENGTH) -> str:
        """Get a short snippet of the file content.
        
        Args:
            file_id: The file ID.
            length: Maximum snippet length.
            
        Returns:
            Truncated content string.
        """
        try:
            content = self.read_file(file_id)
            if content.startswith("# File:"):
                parts = content.split('\n\n', 1)
                if len(parts) > 1:
                    content = parts[1]
            
            snippet = content[:length].replace('\n', ' ').strip()
            if len(content) > length:
                snippet += "..."
            return snippet
        except Exception:
            return ""

    def batch_get_snippets(self, files: list, max_workers: int = DEFAULT_MAX_WORKERS) -> dict[str, str]:
        """Fetch snippets for multiple files in parallel.
        
        Args:
            files: List of file dictionaries with 'id' key.
            max_workers: Number of parallel workers.
            
        Returns:
            Dict mapping file_id to snippet.
        """
        snippets = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(self.get_file_snippet, f['id']): f['id'] 
                for f in files
            }
            
            for future in concurrent.futures.as_completed(future_to_id):
                file_id = future_to_id[future]
                try:
                    snippets[file_id] = future.result()
                except Exception:
                    snippets[file_id] = ""
                    
        return snippets
