"""
Shared configuration for Drive Synapsis.

This module centralizes configuration values to avoid hardcoded values
scattered throughout the codebase.
"""

import os
from typing import Optional

# Server configuration
DRIVE_SYNAPSIS_PORT = int(os.getenv("DRIVE_SYNAPSIS_PORT", "9877"))
DRIVE_SYNAPSIS_BASE_URI = os.getenv("DRIVE_SYNAPSIS_BASE_URI", "http://localhost")

# Credentials directory
CREDENTIALS_DIR = os.path.expanduser(
    os.getenv("DRIVE_SYNAPSIS_CREDENTIALS_DIR", "~/.config/drive-synapsis")
)

# Transport mode (stdio or streamable-http)
_transport_mode: str = "stdio"


def get_transport_mode() -> str:
    """Get the current transport mode."""
    return _transport_mode


def set_transport_mode(mode: str) -> None:
    """Set the current transport mode."""
    global _transport_mode
    _transport_mode = mode


def get_oauth_base_url() -> str:
    """
    Get the OAuth base URL for constructing OAuth endpoints.

    Returns:
        Base URL for OAuth endpoints (e.g., "http://localhost:9877")
    """
    external_url = os.getenv("DRIVE_SYNAPSIS_EXTERNAL_URL")
    if external_url:
        return external_url
    return f"{DRIVE_SYNAPSIS_BASE_URI}:{DRIVE_SYNAPSIS_PORT}"


def get_oauth_redirect_uri() -> str:
    """
    Get the OAuth redirect URI.

    Returns:
        The configured redirect URI for OAuth callbacks.
    """
    explicit_uri = os.getenv("DRIVE_SYNAPSIS_REDIRECT_URI")
    if explicit_uri:
        return explicit_uri
    return f"{get_oauth_base_url()}/oauth2callback"


def get_credentials_dir() -> str:
    """
    Get the credentials directory path, creating it if necessary.

    Returns:
        Path to the credentials directory.
    """
    if not os.path.exists(CREDENTIALS_DIR):
        os.makedirs(CREDENTIALS_DIR, exist_ok=True)
    return CREDENTIALS_DIR
