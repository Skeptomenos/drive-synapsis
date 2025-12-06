"""Server managers for search caching and file synchronization.

This module provides typed data structures and managers for:
- SearchManager: Caches search results with aliases (A, B, C...)
- SyncManager: Tracks links between local files and Google Drive
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json
import os


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CachedFile:
    """A file cached from search results.
    
    Attributes:
        id: The Google Drive file ID.
        name: The file name.
        alias: Single-letter alias (A-Z) for quick reference.
        mime_type: The MIME type of the file.
        snippet: Preview text from the file content.
        score: Relevance score (0-100).
    """
    id: str
    name: str
    alias: str
    mime_type: str = ""
    snippet: str = ""
    score: int = 0


@dataclass
class SyncLink:
    """Link between a local file and a Google Drive file.
    
    Attributes:
        file_id: The Google Drive file ID.
        last_synced_version: The version number at last sync.
    """
    file_id: str
    last_synced_version: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.file_id,
            'last_synced_version': self.last_synced_version
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SyncLink':
        """Create from dictionary (loaded from JSON)."""
        return cls(
            file_id=data.get('id', ''),
            last_synced_version=data.get('last_synced_version', 0)
        )


# ============================================================================
# Search Manager
# ============================================================================

class SearchManager:
    """Manages search result caching and alias resolution.
    
    Assigns single-letter aliases (A-Z) to search results for quick reference
    in subsequent commands.
    """
    
    def __init__(self) -> None:
        self._cache: dict[str, CachedFile] = {}  # Maps 'A' -> CachedFile
        # Keep search_cache for backward compatibility
        self.search_cache: dict[str, str] = {}  # Maps 'A' -> file_id

    def cache_results(self, files: list[dict]) -> list[dict]:
        """Cache search results and assign aliases (A, B, C...).
        
        Args:
            files: List of file metadata dictionaries.
            
        Returns:
            List of files with 'alias' key added (max 26).
        """
        self._cache.clear()
        self.search_cache.clear()
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ranked_results = []
        
        for i, file in enumerate(files):
            if i < len(letters):
                alias = letters[i]
                
                # Create typed cache entry
                cached = CachedFile(
                    id=file['id'],
                    name=file.get('name', 'Untitled'),
                    alias=alias,
                    mime_type=file.get('mimeType', ''),
                    snippet=file.get('snippet', ''),
                    score=file.get('score', 0)
                )
                self._cache[alias] = cached
                
                # Maintain backward compatibility
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
    
    def get_cached_file(self, alias: str) -> Optional[CachedFile]:
        """Get the full cached file info by alias.
        
        Args:
            alias: Single letter alias (A-Z).
            
        Returns:
            CachedFile or None if not found.
        """
        return self._cache.get(alias.upper())


# ============================================================================
# Sync Manager
# ============================================================================

MAP_FILE = "gdrive_map.json"


class SyncManager:
    """Manages local file to Google Drive ID mappings for synchronization.
    
    Persists links to gdrive_map.json for cross-session persistence.
    """
    
    def __init__(self, map_file: str = MAP_FILE) -> None:
        self._map_file = map_file
        self._links: dict[str, SyncLink] = {}  # abs_path -> SyncLink
        # Keep file_map for backward compatibility
        self.file_map: dict[str, dict] = {}
        self._load_map()
    
    def _load_map(self) -> None:
        """Load the file map from disk."""
        if os.path.exists(self._map_file):
            with open(self._map_file, 'r') as f:
                data = json.load(f)
                for path, info in data.items():
                    self._links[path] = SyncLink.from_dict(info)
                    self.file_map[path] = info  # backward compat
        else:
            self._links = {}
            self.file_map = {}
    
    def _save_map(self) -> None:
        """Save the file map to disk."""
        # Sync _links to file_map for backward compatibility
        self.file_map = {path: link.to_dict() for path, link in self._links.items()}
        with open(self._map_file, 'w') as f:
            json.dump(self.file_map, f, indent=2)
    
    def link_file(self, local_path: str, file_id: str, version: int = 0) -> str:
        """Link a local file to a Google Drive file ID.
        
        Args:
            local_path: Path to the local file.
            file_id: Google Drive file ID.
            version: Initial synced version (default 0).
            
        Returns:
            Success message.
        """
        abs_path = os.path.abspath(local_path)
        link = SyncLink(file_id=file_id, last_synced_version=version)
        self._links[abs_path] = link
        self.file_map[abs_path] = link.to_dict()  # backward compat
        self._save_map()
        return f"Linked {local_path} -> {file_id}"
    
    def get_link(self, local_path: str) -> Optional[dict]:
        """Get the Drive link info for a local file.
        
        Args:
            local_path: Path to the local file.
            
        Returns:
            Link info dict or None (backward compatible format).
        """
        abs_path = os.path.abspath(local_path)
        # Check typed _links first
        link = self._links.get(abs_path)
        if link:
            return link.to_dict()
        # Fallback to file_map for backward compatibility
        return self.file_map.get(abs_path)
    
    def get_sync_link(self, local_path: str) -> Optional[SyncLink]:
        """Get the typed SyncLink for a local file.
        
        Args:
            local_path: Path to the local file.
            
        Returns:
            SyncLink or None.
        """
        abs_path = os.path.abspath(local_path)
        return self._links.get(abs_path)
    
    def update_version(self, local_path: str, version: int) -> None:
        """Update the last synced version for a file.
        
        Args:
            local_path: Path to the local file.
            version: New version number.
        """
        abs_path = os.path.abspath(local_path)
        # Update typed _links if present
        if abs_path in self._links:
            self._links[abs_path].last_synced_version = version
        # Always update file_map for backward compat
        if abs_path in self.file_map:
            self.file_map[abs_path]['last_synced_version'] = version
            self._save_map()
    
    def unlink_file(self, local_path: str) -> bool:
        """Remove a sync link.
        
        Args:
            local_path: Path to the local file.
            
        Returns:
            True if link was removed, False if not found.
        """
        abs_path = os.path.abspath(local_path)
        if abs_path in self._links:
            del self._links[abs_path]
            del self.file_map[abs_path]
            self._save_map()
            return True
        return False


# ============================================================================
# Global manager instances
# ============================================================================

search_manager = SearchManager()
sync_manager = SyncManager()
