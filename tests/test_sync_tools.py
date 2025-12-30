"""Unit tests for sync_tools module."""

import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


class TestAutoDetectMultiTab:
    """Tests for auto-detect multi-tab feature in download_google_doc."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_client = Mock()
        self.mock_sync_manager = Mock()
        self.mock_search_manager = Mock()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_multi_tab_triggers_hybrid_sync(self):
        """When doc has 2+ tabs, should switch to hybrid sync."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_sm.get_link.return_value = {"id": "doc123", "last_synced_version": 1}

            mock_client.get_doc_structure.return_value = {
                "tabs": [
                    {
                        "tabProperties": {"tabId": "t1", "title": "Tab1"},
                        "documentTab": {"body": {"content": []}},
                    },
                    {
                        "tabProperties": {"tabId": "t2", "title": "Tab2"},
                        "documentTab": {"body": {"content": []}},
                    },
                ]
            }
            mock_client.download_doc.return_value = "# Full content"
            mock_client.extract_text_from_element.return_value = "Tab text"

            from drive_synapsis.server.sync_tools import download_google_doc

            local_path = os.path.join(self.temp_dir, "test.md")
            result = download_google_doc.fn(
                local_path, format="markdown", dry_run=False
            )

            assert "Multi-tab document detected (2 tabs)" in result
            assert "Hybrid Sync" in result

    def test_single_tab_proceeds_normally(self):
        """When doc has 1 tab, should proceed with normal download."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_sm.get_link.return_value = {"id": "doc123", "last_synced_version": 1}
            mock_sm.file_map = {}

            mock_client.get_doc_structure.return_value = {
                "tabs": [
                    {"tabProperties": {"tabId": "t1", "title": "Tab1"}},
                ]
            }
            mock_client.download_doc.return_value = "# Single tab content"
            mock_client.get_file_version.return_value = 2

            from drive_synapsis.server.sync_tools import download_google_doc

            local_path = os.path.join(self.temp_dir, "test.md")
            result = download_google_doc.fn(
                local_path, format="markdown", dry_run=False
            )

            assert "Multi-tab" not in result
            assert "Successfully downloaded" in result

    def test_api_failure_falls_back_to_normal(self):
        """When get_doc_structure fails, should fall back to normal download."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_sm.get_link.return_value = {"id": "doc123", "last_synced_version": 1}
            mock_sm.file_map = {}

            mock_client.get_doc_structure.side_effect = Exception("API Error")
            mock_client.download_doc.return_value = "# Content after fallback"
            mock_client.get_file_version.return_value = 2

            from drive_synapsis.server.sync_tools import download_google_doc

            local_path = os.path.join(self.temp_dir, "test.md")
            result = download_google_doc.fn(
                local_path, format="markdown", dry_run=False
            )

            assert "Multi-tab" not in result
            assert "Successfully downloaded" in result

    def test_non_markdown_skips_multi_tab_check(self):
        """When format is not markdown, should skip multi-tab detection."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_sm.get_link.return_value = {"id": "doc123", "last_synced_version": 1}
            mock_sm.file_map = {}

            mock_client.download_doc.return_value = "<html>content</html>"
            mock_client.get_file_version.return_value = 2

            from drive_synapsis.server.sync_tools import download_google_doc

            local_path = os.path.join(self.temp_dir, "test.html")
            result = download_google_doc.fn(local_path, format="html", dry_run=False)

            mock_client.get_doc_structure.assert_not_called()
            assert "Successfully downloaded" in result


class TestTargetDirectoryDerivation:
    """Tests for deriving target directory from local_path."""

    def test_md_extension_stripped(self):
        """'Doc.md' should become 'Doc' directory."""
        import os

        local_path = "/path/to/Document.md"
        target_dir = os.path.splitext(local_path)[0]
        assert target_dir == "/path/to/Document"

    def test_txt_extension_stripped(self):
        """'Notes.txt' should become 'Notes' directory."""
        import os

        local_path = "/path/to/Notes.txt"
        target_dir = os.path.splitext(local_path)[0]
        assert target_dir == "/path/to/Notes"

    def test_no_extension_unchanged(self):
        """Path without extension stays the same."""
        import os

        local_path = "/path/to/Document"
        target_dir = os.path.splitext(local_path)[0]
        assert target_dir == "/path/to/Document"


class TestLinkRewriting:
    """Tests for Google Drive link rewriting logic."""

    def test_drive_link_pattern_matches(self):
        """Regex should match Google Docs links in markdown."""
        import re

        pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"

        text = "[My Doc](https://docs.google.com/document/d/abc123/edit)"
        match = re.search(pattern, text)

        assert match is not None
        assert match.group(1) == "My Doc"
        assert "abc123" in match.group(2)

    def test_extracts_doc_id_from_url(self):
        """Should extract document ID from Google Docs URL."""
        url = "https://docs.google.com/document/d/1a2b3c4d5e6f/edit?usp=sharing"

        doc_id = None
        if "docs.google.com/document/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]

        assert doc_id == "1a2b3c4d5e6f"

    def test_non_drive_links_unchanged(self):
        """Non-Google links should not be modified."""
        import re

        pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"

        text = "[Example](https://example.com/page)"
        match = re.search(pattern, text)

        assert match is not None
        assert "docs.google.com" not in match.group(2)


class TestDownloadDocTabsImpl:
    """Tests for _download_doc_tabs_impl helper function."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_full_export_file(self):
        """Should create _Full_Export.md with full document content."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.download_doc.return_value = "# Full Document\n\nContent here."
            mock_client.get_doc_structure.return_value = {"tabs": []}
            mock_client.extract_text_from_element.return_value = "Plain text"

            from drive_synapsis.server.sync_tools import _download_doc_tabs_impl

            target_dir = os.path.join(self.temp_dir, "output")
            result = _download_doc_tabs_impl(target_dir, "doc123")

            full_export_path = os.path.join(target_dir, "_Full_Export.md")
            assert os.path.exists(full_export_path)

            with open(full_export_path) as f:
                content = f.read()
            assert "# Full Document" in content

    def test_creates_tab_files_for_multi_tab(self):
        """Should create individual files for each tab."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.download_doc.return_value = "# Full content"
            mock_client.get_doc_structure.return_value = {
                "tabs": [
                    {
                        "tabProperties": {"tabId": "t1", "title": "Introduction"},
                        "documentTab": {"body": {"content": []}},
                    },
                    {
                        "tabProperties": {"tabId": "t2", "title": "Chapter 1"},
                        "documentTab": {"body": {"content": []}},
                    },
                ]
            }
            mock_client.extract_text_from_element.return_value = "Tab content"

            from drive_synapsis.server.sync_tools import _download_doc_tabs_impl

            target_dir = os.path.join(self.temp_dir, "output")
            result = _download_doc_tabs_impl(target_dir, "doc123")

            assert "2 tab files" in result
            assert os.path.exists(os.path.join(target_dir, "Introduction.txt"))
            assert os.path.exists(os.path.join(target_dir, "Chapter 1.txt"))

    def test_sanitizes_tab_titles(self):
        """Should sanitize tab titles for safe filenames."""
        with (
            patch("drive_synapsis.server.sync_tools.get_client") as mock_get_client,
            patch("drive_synapsis.server.sync_tools.sync_manager") as mock_sm,
        ):
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.download_doc.return_value = "content"
            mock_client.get_doc_structure.return_value = {
                "tabs": [
                    {
                        "tabProperties": {
                            "tabId": "t1",
                            "title": "Tab/With:Special*Chars?",
                        },
                        "documentTab": {"body": {"content": []}},
                    },
                ]
            }
            mock_client.extract_text_from_element.return_value = "text"

            from drive_synapsis.server.sync_tools import _download_doc_tabs_impl

            target_dir = os.path.join(self.temp_dir, "output")
            _download_doc_tabs_impl(target_dir, "doc123")

            files = os.listdir(target_dir)
            tab_files = [f for f in files if f != "_Full_Export.md"]

            assert len(tab_files) == 1
            assert "/" not in tab_files[0]
            assert ":" not in tab_files[0]
            assert "*" not in tab_files[0]
            assert "?" not in tab_files[0]
