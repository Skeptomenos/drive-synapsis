"""
OAuth 2.1 Session Store for Drive Synapsis.

This module provides session management with OAuth state persistence
to survive server restarts during OAuth flows.
"""

import json
import logging
import os
import tempfile
from typing import Dict, Optional, Any
from threading import RLock
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field

from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_oauth_states_file_path() -> str:
    """Get the file path for persisting OAuth states."""
    env_dir = os.getenv("DRIVE_SYNAPSIS_CREDENTIALS_DIR")
    if env_dir:
        base_dir = env_dir
    else:
        home_dir = os.path.expanduser("~")
        if home_dir and home_dir != "~":
            base_dir = os.path.join(home_dir, ".drive-synapsis")
        else:
            base_dir = os.path.join(os.getcwd(), ".drive-synapsis")

    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    return os.path.join(base_dir, "oauth_states.json")


def _normalize_expiry_to_naive_utc(expiry: Optional[Any]) -> Optional[datetime]:
    """
    Convert expiry values to timezone-naive UTC datetimes for google-auth compatibility.
    """
    if expiry is None:
        return None

    if isinstance(expiry, datetime):
        if expiry.tzinfo is not None:
            try:
                return expiry.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                return expiry.replace(tzinfo=None)
        return expiry

    if isinstance(expiry, str):
        try:
            parsed = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        except ValueError:
            logger.debug("Failed to parse expiry string '%s'", expiry)
            return None
        return _normalize_expiry_to_naive_utc(parsed)

    return None


@dataclass
class SessionContext:
    """Container for session-related information."""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OAuth21SessionStore:
    """
    Session store for OAuth 2.1 authenticated sessions.

    Maintains a mapping of user emails to their OAuth credentials and
    persists OAuth states to disk to survive server restarts.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_mapping: Dict[str, str] = {}  # session_id -> user_email
        self._oauth_states: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()
        self._states_file_path = _get_oauth_states_file_path()

        # Load persisted OAuth states on initialization
        self._load_oauth_states_from_disk()

    def _cleanup_expired_oauth_states_locked(self) -> None:
        """Remove expired OAuth state entries. Caller must hold lock."""
        now = datetime.now(timezone.utc)
        expired_states = [
            state
            for state, data in self._oauth_states.items()
            if data.get("expires_at") and data["expires_at"] <= now
        ]
        for state in expired_states:
            del self._oauth_states[state]
            logger.debug("Removed expired OAuth state: %s...", state[:8])

    def _load_oauth_states_from_disk(self) -> None:
        """Load persisted OAuth states from disk on initialization."""
        try:
            if not os.path.exists(self._states_file_path):
                logger.debug("No persisted OAuth states file found")
                return

            with open(self._states_file_path, "r") as f:
                persisted_data = json.load(f)

            if not isinstance(persisted_data, dict):
                logger.warning("Invalid OAuth states file format, ignoring")
                return

            loaded_count = 0
            for state, data in persisted_data.items():
                try:
                    if "expires_at" in data and data["expires_at"]:
                        data["expires_at"] = datetime.fromisoformat(data["expires_at"])
                    if "created_at" in data and data["created_at"]:
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                    self._oauth_states[state] = data
                    loaded_count += 1
                except (ValueError, TypeError) as e:
                    logger.warning("Failed to parse OAuth state: %s", e)

            self._cleanup_expired_oauth_states_locked()
            logger.info(
                "Loaded %d OAuth states from disk (%d after cleanup)",
                loaded_count,
                len(self._oauth_states),
            )

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse OAuth states file: %s", e)
        except IOError as e:
            logger.warning("Failed to read OAuth states file: %s", e)
        except Exception as e:
            logger.error("Unexpected error loading OAuth states: %s", e)

    def _save_oauth_states_to_disk(self) -> None:
        """Persist OAuth states to disk atomically. Caller must hold lock."""
        try:
            serializable_data = {}
            for state, data in self._oauth_states.items():
                serializable_data[state] = {
                    "session_id": data.get("session_id"),
                    "expires_at": data["expires_at"].isoformat()
                    if data.get("expires_at")
                    else None,
                    "created_at": data["created_at"].isoformat()
                    if data.get("created_at")
                    else None,
                }

            target_dir = os.path.dirname(self._states_file_path)
            fd, temp_path = tempfile.mkstemp(dir=target_dir, suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(serializable_data, f, indent=2)
                os.replace(temp_path, self._states_file_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

            logger.debug("Persisted %d OAuth states to disk", len(serializable_data))

        except IOError as e:
            logger.error("Failed to persist OAuth states to disk: %s", e)
        except Exception as e:
            logger.error("Unexpected error persisting OAuth states: %s", e)

    def store_oauth_state(
        self,
        state: str,
        session_id: Optional[str] = None,
        expires_in_seconds: int = 600,
    ) -> None:
        """
        Persist an OAuth state value for later validation.

        States are stored both in memory and on disk to survive server restarts.
        """
        if not state:
            raise ValueError("OAuth state must be provided")
        if expires_in_seconds < 0:
            raise ValueError("expires_in_seconds must be non-negative")

        with self._lock:
            self._cleanup_expired_oauth_states_locked()
            now = datetime.now(timezone.utc)
            expiry = now + timedelta(seconds=expires_in_seconds)
            self._oauth_states[state] = {
                "session_id": session_id,
                "expires_at": expiry,
                "created_at": now,
            }

            self._save_oauth_states_to_disk()

            logger.debug(
                "Stored OAuth state %s... (expires at %s)",
                state[:8],
                expiry.isoformat(),
            )

    def validate_and_consume_oauth_state(
        self,
        state: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate that a state value exists and consume it.

        Args:
            state: The OAuth state returned by Google.
            session_id: Optional session identifier that initiated the flow.

        Returns:
            Metadata associated with the state.

        Raises:
            ValueError: If the state is missing, expired, or does not match.
        """
        if not state:
            raise ValueError("Missing OAuth state parameter")

        with self._lock:
            self._cleanup_expired_oauth_states_locked()
            state_info = self._oauth_states.get(state)

            if not state_info:
                logger.error("OAuth callback received unknown or expired state")
                raise ValueError("Invalid or expired OAuth state parameter")

            bound_session = state_info.get("session_id")
            if bound_session and session_id and bound_session != session_id:
                del self._oauth_states[state]
                self._save_oauth_states_to_disk()
                logger.error(
                    "OAuth state session mismatch (expected %s, got %s)",
                    bound_session,
                    session_id,
                )
                raise ValueError("OAuth state does not match the initiating session")

            # State is valid - consume it to prevent reuse
            del self._oauth_states[state]
            self._save_oauth_states_to_disk()
            logger.debug("Validated OAuth state %s...", state[:8])
            return state_info

    def store_session(
        self,
        user_email: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_uri: str = "https://oauth2.googleapis.com/token",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scopes: Optional[list] = None,
        expiry: Optional[Any] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Store OAuth 2.1 session information.

        Args:
            user_email: User's email address
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            token_uri: Token endpoint URI
            client_id: OAuth client ID
            client_secret: OAuth client secret
            scopes: List of granted scopes
            expiry: Token expiry time
            session_id: Session ID to map to this user
        """
        with self._lock:
            normalized_expiry = _normalize_expiry_to_naive_utc(expiry)
            session_info = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_uri": token_uri,
                "client_id": client_id,
                "client_secret": client_secret,
                "scopes": scopes or [],
                "expiry": normalized_expiry,
                "session_id": session_id,
            }

            self._sessions[user_email] = session_info

            if session_id:
                self._session_mapping[session_id] = user_email
                logger.info(
                    f"Stored OAuth session for {user_email} (session: {session_id})"
                )
            else:
                logger.info(f"Stored OAuth session for {user_email}")

    def get_credentials(self, user_email: str) -> Optional[Credentials]:
        """
        Get Google credentials for a user from OAuth session.

        Args:
            user_email: User's email address

        Returns:
            Google Credentials object or None
        """
        with self._lock:
            session_info = self._sessions.get(user_email)
            if not session_info:
                logger.debug(f"No OAuth session found for {user_email}")
                return None

            try:
                credentials = Credentials(
                    token=session_info["access_token"],
                    refresh_token=session_info.get("refresh_token"),
                    token_uri=session_info["token_uri"],
                    client_id=session_info.get("client_id"),
                    client_secret=session_info.get("client_secret"),
                    scopes=session_info.get("scopes", []),
                    expiry=session_info.get("expiry"),
                )

                logger.debug(f"Retrieved OAuth credentials for {user_email}")
                return credentials

            except Exception as e:
                logger.error(f"Failed to create credentials for {user_email}: {e}")
                return None

    def get_credentials_by_session(self, session_id: str) -> Optional[Credentials]:
        """
        Get Google credentials using session ID.

        Args:
            session_id: Session ID

        Returns:
            Google Credentials object or None
        """
        with self._lock:
            user_email = self._session_mapping.get(session_id)
            if not user_email:
                logger.debug(f"No user mapping found for session {session_id}")
                return None

            return self.get_credentials(user_email)

    def get_user_by_session(self, session_id: str) -> Optional[str]:
        """Get user email by session ID."""
        with self._lock:
            return self._session_mapping.get(session_id)

    def remove_session(self, user_email: str) -> None:
        """Remove session for a user."""
        with self._lock:
            if user_email in self._sessions:
                session_info = self._sessions.get(user_email, {})
                session_id = session_info.get("session_id")

                del self._sessions[user_email]

                if session_id and session_id in self._session_mapping:
                    del self._session_mapping[session_id]

                logger.info(f"Removed OAuth session for {user_email}")

    def has_session(self, user_email: str) -> bool:
        """Check if a user has an active session."""
        with self._lock:
            return user_email in self._sessions

    def get_single_user_email(self) -> Optional[str]:
        """Return the sole authenticated user email when exactly one session exists."""
        with self._lock:
            if len(self._sessions) == 1:
                return next(iter(self._sessions))
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        with self._lock:
            return {
                "total_sessions": len(self._sessions),
                "users": list(self._sessions.keys()),
                "session_mappings": len(self._session_mapping),
                "pending_oauth_states": len(self._oauth_states),
            }


# Global instance
_global_store: Optional[OAuth21SessionStore] = None


def get_oauth21_session_store() -> OAuth21SessionStore:
    """Get the global OAuth 2.1 session store."""
    global _global_store
    if _global_store is None:
        _global_store = OAuth21SessionStore()
    return _global_store
