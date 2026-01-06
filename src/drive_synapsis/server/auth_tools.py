"""Authentication MCP tools for Drive Synapsis."""

import logging

from .main import mcp
from ..auth import start_auth_flow, check_client_secrets
from ..auth.oauth_callback_server import start_oauth_callback_server

logger = logging.getLogger(__name__)


@mcp.tool()
def start_google_auth(service_name: str = "Google Drive") -> str:
    """
    Manually initiate Google OAuth authentication flow.

    NOTE: This tool should typically NOT be called directly. The authentication system
    automatically handles credential checks and prompts for authentication when needed.
    Only use this tool if:
    1. You need to re-authenticate with different credentials
    2. You want to proactively authenticate before using other tools
    3. The automatic authentication flow failed and you need to retry

    In most cases, simply try calling a Drive Synapsis tool - it will
    automatically handle authentication if required.

    Args:
        service_name: Display name for the service (default: "Google Drive")

    Returns:
        Authentication URL and instructions, or error message.
    """
    error_message = check_client_secrets()
    if error_message:
        return f"**Authentication Error:** {error_message}"

    try:
        success, error_msg, redirect_uri = start_oauth_callback_server()

        if not success:
            return f"**Error:** OAuth callback server unavailable: {error_msg}"

        auth_message = start_auth_flow(
            user_google_email=None,
            service_name=service_name,
            redirect_uri=redirect_uri,
        )
        return auth_message

    except Exception as e:
        logger.error(f"Failed to start Google authentication flow: {e}", exc_info=True)
        return f"**Error:** An unexpected error occurred: {e}"
