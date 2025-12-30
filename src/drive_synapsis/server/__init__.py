"""Google Drive MCP Server - modular implementation."""

from .main import mcp, get_client

from . import search_tools
from . import doc_tools
from . import sheet_tools
from . import file_tools
from . import sync_tools
from . import sharing_tools

__all__ = ["mcp", "get_client", "main"]


def main():
    """Entry point for the Drive Synapsis MCP server."""
    mcp.run(show_banner=False)
