"""Centralized constants for Google Drive MCP server."""

# MIME Types - Google Apps
GOOGLE_MIME_TYPES = {
    'doc': 'application/vnd.google-apps.document',
    'sheet': 'application/vnd.google-apps.spreadsheet',
    'folder': 'application/vnd.google-apps.folder',
    'presentation': 'application/vnd.google-apps.presentation',
    'form': 'application/vnd.google-apps.form',
    'pdf': 'application/pdf',
    'image': 'image/',  # Prefix match
}

# MIME Types - Export Formats
EXPORT_MIME_TYPES = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'html': 'text/html',
    'markdown': 'text/markdown',
    'rtf': 'application/rtf',
    'odt': 'application/vnd.oasis.opendocument.text',
    'csv': 'text/csv',
    'json': 'application/json',
}

# Default Values
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_SNIPPET_LENGTH = 200
DEFAULT_COMMENT_PAGE_SIZE = 100
DEFAULT_MAX_WORKERS = 5
DEFAULT_SHEET_RANGE = "A1:Z1000"

# Scoring Weights (for search ranking)
SCORE_TITLE_MATCH = 50
SCORE_CONTENT_MATCH = 30
SCORE_TYPE_BOOST = 10
MAX_SCORE = 100

# Access Roles
ROLE_READER = 'reader'
ROLE_WRITER = 'writer'
ROLE_COMMENTER = 'commenter'

# Permission Types
PERM_TYPE_USER = 'user'
PERM_TYPE_ANYONE = 'anyone'
