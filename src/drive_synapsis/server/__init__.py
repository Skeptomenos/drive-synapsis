"""Google Drive MCP Server - modular implementation.

This module initializes the MCP server and imports all tool modules
to register them with the mcp instance.
"""
from .main import mcp, get_client

# Import all tools to register them with mcp
from . import search_tools
from . import doc_tools
from . import sheet_tools
from . import file_tools
from . import sync_tools
from . import sharing_tools

__all__ = ['mcp', 'get_client']
