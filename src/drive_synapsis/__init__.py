"""Drive Synapsis - Google Drive MCP Server Package.

This package provides an MCP (Model Context Protocol) server for Google Drive
integration, allowing AI assistants to search, read, and write Google Drive files.
"""
from .client import GDriveClient
from .auth import get_creds

__version__ = "0.2.0"
__all__ = ["GDriveClient", "get_creds"]
