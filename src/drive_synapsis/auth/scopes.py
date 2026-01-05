"""
Google OAuth Scopes for Drive Synapsis.

This module defines the OAuth scopes required for Google Drive, Docs, and Sheets access.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Base OAuth scopes required for user identification
USERINFO_EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
USERINFO_PROFILE_SCOPE = "https://www.googleapis.com/auth/userinfo.profile"
OPENID_SCOPE = "openid"

BASE_SCOPES = [USERINFO_EMAIL_SCOPE, USERINFO_PROFILE_SCOPE, OPENID_SCOPE]

# Google Drive scopes
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"

DRIVE_SCOPES = [DRIVE_SCOPE, DRIVE_READONLY_SCOPE, DRIVE_FILE_SCOPE]

# Google Docs scopes
DOCS_READONLY_SCOPE = "https://www.googleapis.com/auth/documents.readonly"
DOCS_WRITE_SCOPE = "https://www.googleapis.com/auth/documents"

DOCS_SCOPES = [DOCS_READONLY_SCOPE, DOCS_WRITE_SCOPE]

# Google Sheets scopes
SHEETS_READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
SHEETS_WRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"

SHEETS_SCOPES = [SHEETS_READONLY_SCOPE, SHEETS_WRITE_SCOPE]

# Combined scopes for Drive Synapsis
# We use the full access scopes for simplicity
SCOPES = [
    DRIVE_SCOPE,  # Full Drive access
    DOCS_WRITE_SCOPE,  # Full Docs access
    SHEETS_WRITE_SCOPE,  # Full Sheets access
] + BASE_SCOPES


def get_scopes() -> List[str]:
    """
    Get the list of OAuth scopes required for Drive Synapsis.

    Returns:
        List of unique OAuth scopes.
    """
    return list(set(SCOPES))


def get_minimal_scopes() -> List[str]:
    """
    Get minimal scopes for read-only access.

    Returns:
        List of read-only OAuth scopes.
    """
    return [
        DRIVE_READONLY_SCOPE,
        DOCS_READONLY_SCOPE,
        SHEETS_READONLY_SCOPE,
    ] + BASE_SCOPES
