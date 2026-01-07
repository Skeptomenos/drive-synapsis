"""
Credential Store for Drive Synapsis.

This module provides a standardized interface for credential storage and retrieval,
using local JSON files for persistence.
"""

import os
import json
import logging
import base64
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class CredentialStore(ABC):
    """Abstract base class for credential storage."""

    @abstractmethod
    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials for a user by email."""
        pass

    @abstractmethod
    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials for a user."""
        pass

    @abstractmethod
    def delete_credential(self, user_email: str) -> bool:
        """Delete credentials for a user."""
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        """List all users with stored credentials."""
        pass


class LocalDirectoryCredentialStore(CredentialStore):
    """Credential store that uses local JSON files for storage."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """
        Initialize the local credential store.

        Args:
            base_dir: Base directory for credential files. If None, uses
                     ~/.config/drive-synapsis/credentials
        """
        if base_dir is None:
            env_dir = os.getenv("DRIVE_SYNAPSIS_CREDENTIALS_DIR")
            if env_dir:
                base_dir = os.path.join(env_dir, "credentials")
            else:
                home_dir = os.path.expanduser("~")
                base_dir = os.path.join(
                    home_dir, ".config", "drive-synapsis", "credentials"
                )

        self.base_dir = base_dir
        self._ensure_dir_exists()
        logger.info(f"LocalDirectoryCredentialStore initialized: {base_dir}")

    def _ensure_dir_exists(self) -> None:
        """Ensure the credentials directory exists."""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"Created credentials directory: {self.base_dir}")

    def _email_to_filename(self, user_email: str) -> str:
        """
        Convert email to a safe filename using URL-safe base64 encoding.

        This ensures the transformation is reversible for any email address,
        including those with underscores (e.g., john_doe@example.com).
        """
        encoded = base64.urlsafe_b64encode(user_email.encode("utf-8")).decode("ascii")
        # Remove padding for cleaner filenames
        return encoded.rstrip("=")

    def _filename_to_email(self, filename: str) -> str:
        """
        Convert a filename back to the original email address.

        Reverses the URL-safe base64 encoding from _email_to_filename.
        """
        # Add back padding if needed
        padding = 4 - (len(filename) % 4)
        if padding != 4:
            filename += "=" * padding
        return base64.urlsafe_b64decode(filename.encode("ascii")).decode("utf-8")

    def _get_credential_path(self, user_email: str) -> str:
        """Get the file path for a user's credentials."""
        self._ensure_dir_exists()
        safe_email = self._email_to_filename(user_email)
        return os.path.join(self.base_dir, f"{safe_email}.json")

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from local JSON file."""
        creds_path = self._get_credential_path(user_email)

        if not os.path.exists(creds_path):
            logger.debug(f"No credential file found for {user_email}")
            return None

        try:
            with open(creds_path, "r") as f:
                creds_data = json.load(f)

            # Parse expiry if present
            expiry = None
            if creds_data.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                    # Ensure timezone-naive datetime for Google auth library
                    if expiry.tzinfo is not None:
                        expiry = expiry.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry for {user_email}: {e}")

            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes"),
                expiry=expiry,
            )

            logger.debug(f"Loaded credentials for {user_email}")
            return credentials

        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading credentials for {user_email}: {e}")
            return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to local JSON file."""
        creds_path = self._get_credential_path(user_email)

        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else None,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        try:
            with open(creds_path, "w") as f:
                json.dump(creds_data, f, indent=2)
            logger.info(f"Stored credentials for {user_email}")
            return True
        except IOError as e:
            logger.error(f"Error storing credentials for {user_email}: {e}")
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credential file for a user."""
        creds_path = self._get_credential_path(user_email)

        try:
            if os.path.exists(creds_path):
                os.remove(creds_path)
                logger.info(f"Deleted credentials for {user_email}")
            return True
        except IOError as e:
            logger.error(f"Error deleting credentials for {user_email}: {e}")
            return False

    def list_users(self) -> List[str]:
        """List all users with credential files."""
        if not os.path.exists(self.base_dir):
            return []

        users = []
        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith(".json"):
                    encoded_part = filename[:-5]
                    try:
                        user_email = self._filename_to_email(encoded_part)
                        users.append(user_email)
                    except (ValueError, UnicodeDecodeError) as e:
                        logger.warning(
                            f"Could not decode credential file {filename}: {e}"
                        )
            logger.debug(f"Found {len(users)} users with credentials")
        except OSError as e:
            logger.error(f"Error listing credential files: {e}")

        return sorted(users)


# Global credential store instance
_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """Get the global credential store instance."""
    global _credential_store

    if _credential_store is None:
        _credential_store = LocalDirectoryCredentialStore()
        logger.info(f"Initialized credential store: {type(_credential_store).__name__}")

    return _credential_store


def set_credential_store(store: CredentialStore) -> None:
    """Set the global credential store instance."""
    global _credential_store
    _credential_store = store
    logger.info(f"Set credential store: {type(store).__name__}")
