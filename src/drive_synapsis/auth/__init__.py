"""
OAuth 2.1 Authentication Package for Drive Synapsis.

This package provides a production-grade OAuth 2.1 implementation with:
- Session management with state persistence (survives server restarts)
- Multi-user support with credential store abstraction
- Non-blocking OAuth callback server
- PKCE enforcement for security
"""

from .scopes import SCOPES, DRIVE_SCOPES, DOCS_SCOPES, SHEETS_SCOPES
from .credential_store import get_credential_store, CredentialStore
from .oauth21_session_store import get_oauth21_session_store, OAuth21SessionStore
from .google_auth import (
    get_credentials,
    get_creds,
    start_auth_flow,
    handle_auth_callback,
    check_client_secrets,
    GoogleAuthenticationError,
)

__all__ = [
    # Scopes
    "SCOPES",
    "DRIVE_SCOPES",
    "DOCS_SCOPES",
    "SHEETS_SCOPES",
    # Credential Store
    "get_credential_store",
    "CredentialStore",
    # Session Store
    "get_oauth21_session_store",
    "OAuth21SessionStore",
    # Auth Functions
    "get_credentials",
    "get_creds",
    "start_auth_flow",
    "handle_auth_callback",
    "check_client_secrets",
    "GoogleAuthenticationError",
]
