"""MCP Server initialization and entry point."""

from fastmcp import FastMCP
from ..client import GDriveClient
from typing import Optional

# Initialize MCP Server
mcp = FastMCP("Drive Synapsis")

# Global client, initialized lazily
_client: Optional[GDriveClient] = None


def get_client() -> GDriveClient:
    """Get or create the global GDriveClient instance.

    Returns:
        The authenticated GDriveClient instance.

    Raises:
        Exception: If authentication fails.
    """
    global _client
    if not _client:
        _client = GDriveClient()
    return _client


@mcp.resource("gdrive://{file_id}")
def read_gdrive_resource(file_id: str) -> str:
    """Read a Google Drive file as a resource."""
    from .doc_tools import read_google_drive_file

    return read_google_drive_file(file_id=file_id)
