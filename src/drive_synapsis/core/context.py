"""
Context variables for Drive Synapsis.

This module provides request-scoped context variables for session management.
"""

import contextvars
from typing import Optional

# Context variable to hold the current session ID
_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "session_id", default=None
)


def get_session_id() -> Optional[str]:
    """
    Get the current session ID from context.

    Returns:
        The current session ID or None if not set.
    """
    return _session_id.get()


def set_session_id(session_id: Optional[str]) -> None:
    """
    Set the current session ID in context.

    Args:
        session_id: The session ID to set, or None to clear.
    """
    _session_id.set(session_id)
