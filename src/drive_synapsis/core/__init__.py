"""
Core utilities package for Drive Synapsis.

This package provides shared configuration and context management.
"""

from .config import (
    DRIVE_SYNAPSIS_PORT,
    DRIVE_SYNAPSIS_BASE_URI,
    get_oauth_base_url,
    get_oauth_redirect_uri,
    get_transport_mode,
    set_transport_mode,
)
from .context import (
    get_session_id,
    set_session_id,
)

__all__ = [
    # Config
    "DRIVE_SYNAPSIS_PORT",
    "DRIVE_SYNAPSIS_BASE_URI",
    "get_oauth_base_url",
    "get_oauth_redirect_uri",
    "get_transport_mode",
    "set_transport_mode",
    # Context
    "get_session_id",
    "set_session_id",
]
