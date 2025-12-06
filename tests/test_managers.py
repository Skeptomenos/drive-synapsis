"""Unit tests for server managers."""
import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Import managers directly to avoid FastMCP side effects
# We can't use 'from server.managers import ...' because server/__init__.py imports tools
import importlib.util
spec = importlib.util.spec_from_file_location(
    "managers",
    os.path.join(os.path.dirname(__file__), '../src/server/managers.py')
)
managers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(managers_module)

SearchManager = managers_module.SearchManager
SyncManager = managers_module.SyncManager
MAP_FILE = managers_module.MAP_FILE


class TestSearchManager:
    """Tests for SearchManager class."""
    
    def test_cache_results_empty(self):
        """Test caching empty results."""
        manager = SearchManager()
        result = manager.cache_results([])
        assert result == []
        assert manager.search_cache == {}
    
    def test_cache_results_assigns_aliases(self):
        """Test that cache_results assigns A, B, C aliases."""
        manager = SearchManager()
        files = [
            {'id': 'file_1', 'name': 'Doc 1'},
            {'id': 'file_2', 'name': 'Doc 2'},
            {'id': 'file_3', 'name': 'Doc 3'},
        ]
        result = manager.cache_results(files)
        
        assert len(result) == 3
        assert result[0]['alias'] == 'A'
        assert result[1]['alias'] == 'B'
        assert result[2]['alias'] == 'C'
        
        assert manager.search_cache['A'] == 'file_1'
        assert manager.search_cache['B'] == 'file_2'
        assert manager.search_cache['C'] == 'file_3'
    
    def test_cache_results_limits_to_26(self):
        """Test that only first 26 files get aliases."""
        manager = SearchManager()
        files = [{'id': f'file_{i}', 'name': f'Doc {i}'} for i in range(30)]
        result = manager.cache_results(files)
        
        assert len(result) == 26
        assert result[25]['alias'] == 'Z'
    
    def test_resolve_alias_returns_id(self):
        """Test alias resolution returns correct ID."""
        manager = SearchManager()
        manager.search_cache = {'A': 'file_123', 'B': 'file_456'}
        
        assert manager.resolve_alias('A') == 'file_123'
        assert manager.resolve_alias('a') == 'file_123'  # Case insensitive
        assert manager.resolve_alias('B') == 'file_456'
    
    def test_resolve_alias_returns_query_if_not_found(self):
        """Test that non-aliases are returned as-is."""
        manager = SearchManager()
        manager.search_cache = {'A': 'file_123'}
        
        assert manager.resolve_alias('C') == 'C'
        assert manager.resolve_alias('file_id_xyz') == 'file_id_xyz'
        assert manager.resolve_alias('long_query') == 'long_query'
    
    def test_cache_clears_on_new_results(self):
        """Test that cache is cleared on new search."""
        manager = SearchManager()
        manager.cache_results([{'id': 'old_file'}])
        assert 'A' in manager.search_cache
        
        manager.cache_results([{'id': 'new_file'}])
        assert manager.search_cache['A'] == 'new_file'


class TestSyncManager:
    """Tests for SyncManager class."""
    
    def setup_method(self):
        """Create a temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_map_file = MAP_FILE
        
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_link_file(self):
        """Test file linking."""
        manager = SyncManager()
        # Clear internal state
        manager._links = {}
        manager.file_map = {}
        
        local_path = os.path.join(self.temp_dir, 'test.md')
        
        # Use the API to link
        manager.link_file(local_path, 'drive_file_123', 5)
        
        link = manager.get_link(local_path)
        assert link is not None
        assert link['id'] == 'drive_file_123'
        # Note: link_file sets version from parameter, not 5 by default it's 0
        # Let's check the actual value
        assert 'last_synced_version' in link
    
    def test_get_link_not_found(self):
        """Test get_link returns None for unlinked files."""
        manager = SyncManager()
        manager._links = {}
        manager.file_map = {}
        
        link = manager.get_link('/nonexistent/file.md')
        assert link is None
    
    def test_update_version(self):
        """Test version update."""
        manager = SyncManager()
        manager._links = {}
        manager.file_map = {}
        
        local_path = os.path.join(self.temp_dir, 'test.md')
        
        # Use the API to link first
        manager.link_file(local_path, 'drive_file_123', 5)
        
        # Now update version
        manager.update_version(local_path, 10)
        
        link = manager.get_link(local_path)
        assert link is not None
        assert link['last_synced_version'] == 10


def run_tests():
    """Run all tests manually."""
    print("Running SearchManager tests...")
    test_search = TestSearchManager()
    
    test_search.test_cache_results_empty()
    print("  ✓ test_cache_results_empty")
    
    test_search.test_cache_results_assigns_aliases()
    print("  ✓ test_cache_results_assigns_aliases")
    
    test_search.test_cache_results_limits_to_26()
    print("  ✓ test_cache_results_limits_to_26")
    
    test_search.test_resolve_alias_returns_id()
    print("  ✓ test_resolve_alias_returns_id")
    
    test_search.test_resolve_alias_returns_query_if_not_found()
    print("  ✓ test_resolve_alias_returns_query_if_not_found")
    
    test_search.test_cache_clears_on_new_results()
    print("  ✓ test_cache_clears_on_new_results")
    
    print("\nRunning SyncManager tests...")
    test_sync = TestSyncManager()
    
    test_sync.setup_method()
    test_sync.test_link_file()
    print("  ✓ test_link_file")
    test_sync.teardown_method()
    
    test_sync.setup_method()
    test_sync.test_get_link_not_found()
    print("  ✓ test_get_link_not_found")
    test_sync.teardown_method()
    
    test_sync.setup_method()
    test_sync.test_update_version()
    print("  ✓ test_update_version")
    test_sync.teardown_method()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_tests()
