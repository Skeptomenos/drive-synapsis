"""Google Drive Client - modular implementation.

This module provides a facade that combines all client mixins into
a single GDriveClient class with the same interface as the original.
"""
from .base import GDriveClientBase
from .search import SearchMixin
from .documents import DocumentsMixin
from .sheets import SheetsMixin
from .files import FilesMixin
from .sharing import SharingMixin
from .comments import CommentsMixin


class GDriveClient(
    GDriveClientBase,
    SearchMixin,
    DocumentsMixin,
    SheetsMixin,
    FilesMixin,
    SharingMixin,
    CommentsMixin,
):
    """Full-featured Google Drive client.
    
    Combines all mixins to provide complete Google Drive, Docs, and Sheets
    functionality through a unified interface.
    """
    pass


__all__ = ['GDriveClient']
