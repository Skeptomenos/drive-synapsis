"""Backward compatibility wrapper for GDriveClient.

This module re-exports GDriveClient from the new modular client/ package
to maintain backward compatibility with existing imports.

Usage:
    from gdrive_client import GDriveClient  # Still works!
"""
from client import GDriveClient

__all__ = ['GDriveClient']
