"""
Core Google OAuth Logic for Drive Synapsis.

This module provides the main OAuth 2.1 authentication flow with PKCE support.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple, Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .scopes import SCOPES, get_scopes
from .oauth21_session_store import get_oauth21_session_store
from .credential_store import get_credential_store
from .oauth_config import get_oauth_config, get_oauth_redirect_uri, get_credentials_dir

logger = logging.getLogger(__name__)


class GoogleAuthenticationError(Exception):
    """Exception raised when Google authentication is required or fails."""

    def __init__(self, message: str, auth_url: Optional[str] = None):
        super().__init__(message)
        self.auth_url = auth_url


def load_client_secrets_from_env() -> Optional[Dict[str, Any]]:
    """
    Load client secrets from environment variables.

    Returns:
        Client secrets configuration dict or None if not set.
    """
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    if client_id and client_secret:
        config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }
        logger.info("Loaded OAuth credentials from environment variables")
        return config

    return None


def load_client_secrets(client_secrets_path: str) -> Dict[str, Any]:
    """
    Load client secrets from environment variables or file.

    Args:
        client_secrets_path: Path to client secrets JSON file (fallback)

    Returns:
        Client secrets configuration dict

    Raises:
        ValueError: If client secrets have invalid format
        IOError: If file cannot be read and no environment variables set
    """
    # Try environment variables first
    env_config = load_client_secrets_from_env()
    if env_config:
        return env_config["web"]

    # Fall back to file
    try:
        with open(client_secrets_path, "r") as f:
            client_config = json.load(f)

        if "web" in client_config:
            logger.info(f"Loaded OAuth credentials from {client_secrets_path}")
            return client_config["web"]
        elif "installed" in client_config:
            logger.info(f"Loaded OAuth credentials from {client_secrets_path}")
            return client_config["installed"]
        else:
            raise ValueError("Invalid client secrets file format")

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error loading client secrets from {client_secrets_path}: {e}")
        raise


def check_client_secrets() -> Optional[str]:
    """
    Check if OAuth client secrets are available.

    Returns:
        Error message if secrets not found, None otherwise.
    """
    config = get_oauth_config()

    env_config = load_client_secrets_from_env()
    if env_config:
        return None

    if os.path.exists(config.client_secrets_path):
        return None

    return (
        f"OAuth client credentials not found. Please either:\n"
        f"1. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables\n"
        f"2. Place client_secret.json in {config.client_secrets_path}"
    )


def create_oauth_flow(
    scopes: List[str], redirect_uri: str, state: Optional[str] = None
) -> Flow:
    """
    Create an OAuth flow with PKCE enabled.

    Args:
        scopes: List of OAuth scopes
        redirect_uri: OAuth redirect URI
        state: Optional state parameter

    Returns:
        Configured OAuth Flow object
    """
    config = get_oauth_config()

    # Try environment variables first
    env_config = load_client_secrets_from_env()
    if env_config:
        flow = Flow.from_client_config(
            env_config,
            scopes=scopes,
            redirect_uri=redirect_uri,
            state=state,
            autogenerate_code_verifier=True,  # PKCE enabled
        )
        logger.debug("Created OAuth flow from environment variables with PKCE")
        return flow

    # Fall back to file
    if not os.path.exists(config.client_secrets_path):
        raise FileNotFoundError(
            f"OAuth client secrets not found at {config.client_secrets_path}"
        )

    flow = Flow.from_client_secrets_file(
        config.client_secrets_path,
        scopes=scopes,
        redirect_uri=redirect_uri,
        state=state,
        autogenerate_code_verifier=True,  # PKCE enabled
    )
    logger.debug(f"Created OAuth flow from {config.client_secrets_path} with PKCE")
    return flow


def start_auth_flow(
    user_google_email: Optional[str] = None,
    service_name: str = "Google Drive",
    redirect_uri: Optional[str] = None,
) -> str:
    """
    Initiate the Google OAuth flow and return an actionable message.

    Args:
        user_google_email: Optional user's email (for display)
        service_name: Name of the service requiring auth
        redirect_uri: OAuth redirect URI

    Returns:
        Formatted string with auth URL and instructions

    Raises:
        Exception: If OAuth flow cannot be initiated
    """
    if redirect_uri is None:
        redirect_uri = get_oauth_redirect_uri()

    user_display = (
        f"{service_name} for '{user_google_email}'"
        if user_google_email
        else service_name
    )

    logger.info(f"Initiating auth for {user_display}")

    try:
        # Allow HTTP for localhost in development
        if "OAUTHLIB_INSECURE_TRANSPORT" not in os.environ and (
            "localhost" in redirect_uri or "127.0.0.1" in redirect_uri
        ):
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        # Generate state for CSRF protection
        oauth_state = os.urandom(16).hex()

        flow = create_oauth_flow(
            scopes=get_scopes(),
            redirect_uri=redirect_uri,
            state=oauth_state,
        )

        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

        # Store state and code_verifier for validation during callback
        store = get_oauth21_session_store()
        code_verifier = getattr(flow, "code_verifier", None)
        store.store_oauth_state(
            oauth_state, session_id=None, code_verifier=code_verifier
        )

        logger.info(f"Auth flow started. State: {oauth_state[:8]}...")

        message_lines = [
            f"**ACTION REQUIRED: Google Authentication Needed for {user_display}**\n",
            f"To proceed, authorize this application for {service_name} access.",
            "",
            "**Click this link to authenticate:**",
            f"[Authorize {service_name} Access]({auth_url})",
            "",
            "**Full URL (LLM: always print this for the user):**",
            f"```\n{auth_url}\n```",
            "",
            "**Instructions:**",
            "1. Click the link above and complete authorization in your browser",
            "2. After successful authorization, the browser will show a success message",
            "3. Return here and retry your original command",
        ]

        return "\n".join(message_lines)

    except FileNotFoundError as e:
        error_text = f"OAuth client credentials not found: {e}"
        logger.error(error_text)
        raise Exception(error_text)
    except Exception as e:
        error_text = f"Could not initiate authentication: {str(e)}"
        logger.error(error_text, exc_info=True)
        raise Exception(error_text)


def handle_auth_callback(
    scopes: List[str],
    authorization_response: str,
    redirect_uri: str,
    session_id: Optional[str] = None,
) -> Tuple[str, Any]:
    """
    Handle the OAuth callback from Google.

    Args:
        scopes: List of OAuth scopes
        authorization_response: Full callback URL from Google
        redirect_uri: OAuth redirect URI
        session_id: Optional session ID

    Returns:
        Tuple of (user_email, credentials)

    Raises:
        ValueError: If state is invalid or missing
    """
    try:
        # Allow HTTP for localhost
        if "OAUTHLIB_INSECURE_TRANSPORT" not in os.environ:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        # Validate OAuth state
        from urllib.parse import urlparse, parse_qs

        store = get_oauth21_session_store()
        parsed_response = urlparse(authorization_response)
        state_values = parse_qs(parsed_response.query).get("state")
        state = state_values[0] if state_values else None

        if not state:
            raise ValueError("Missing OAuth state parameter")

        state_info = store.validate_and_consume_oauth_state(
            state, session_id=session_id
        )
        logger.debug(f"Validated OAuth state {state[:8]}...")

        code_verifier = state_info.get("code_verifier")
        if not code_verifier:
            raise ValueError("Missing code verifier - PKCE flow incomplete")

        flow = create_oauth_flow(scopes=scopes, redirect_uri=redirect_uri, state=state)
        flow.code_verifier = code_verifier
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        logger.info("Successfully exchanged authorization code for tokens")

        # Get user info
        user_info = get_user_info(credentials)  # type: ignore[arg-type]
        if not user_info or "email" not in user_info:
            raise ValueError("Failed to get user email from Google")

        user_email = user_info["email"]
        logger.info(f"Authenticated user: {user_email}")

        # Store credentials
        credential_store = get_credential_store()
        credential_store.store_credential(user_email, credentials)  # type: ignore[arg-type]

        # Store in session store
        token = getattr(credentials, "token", None)
        refresh_token = getattr(credentials, "refresh_token", None)
        token_uri = (
            getattr(credentials, "token_uri", None)
            or "https://oauth2.googleapis.com/token"
        )
        client_id = getattr(credentials, "client_id", None)
        client_secret = getattr(credentials, "client_secret", None)
        cred_scopes = getattr(credentials, "scopes", None)
        expiry = getattr(credentials, "expiry", None)

        if token:
            store.store_session(
                user_email=user_email,
                access_token=token,
                refresh_token=refresh_token,
                token_uri=token_uri,
                client_id=client_id,
                client_secret=client_secret,
                scopes=list(cred_scopes) if cred_scopes else None,
                expiry=expiry,
                session_id=session_id,
            )

        return user_email, credentials

    except Exception as e:
        logger.error(f"Error handling auth callback: {e}")
        raise


def get_user_info(credentials: Credentials) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile information.

    Args:
        credentials: Valid Google credentials

    Returns:
        User info dict or None
    """
    if not credentials or not credentials.valid:
        logger.error("Cannot get user info: Invalid credentials")
        return None

    try:
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        logger.info(f"Fetched user info: {user_info.get('email')}")
        return user_info
    except HttpError as e:
        logger.error(f"HttpError fetching user info: {e.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        return None


def get_credentials(
    user_email: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Optional[Credentials]:
    """
    Get stored credentials, refreshing if necessary.

    Args:
        user_email: User's email address
        required_scopes: Required OAuth scopes
        session_id: Optional session ID

    Returns:
        Valid Credentials object or None
    """
    if required_scopes is None:
        required_scopes = SCOPES

    store = get_oauth21_session_store()
    credential_store = get_credential_store()
    credentials: Optional[Credentials] = None

    # Try session store first
    if session_id:
        credentials = store.get_credentials_by_session(session_id)
        if credentials:
            logger.debug(f"Found credentials for session {session_id}")

    # Try by user email
    if not credentials and user_email:
        credentials = store.get_credentials(user_email)
        if not credentials:
            # Try file-based credential store
            credentials = credential_store.get_credential(user_email)

    # Try single user mode (in-memory session store)
    if not credentials:
        single_user = store.get_single_user_email()
        if single_user:
            credentials = store.get_credentials(single_user)
            if not credentials:
                credentials = credential_store.get_credential(single_user)
            if credentials:
                user_email = single_user

    # Try single user mode (file-based credential store)
    # This handles the case where server restarts and in-memory sessions are empty
    if not credentials:
        stored_users = credential_store.list_users()
        if len(stored_users) == 1:
            single_user = stored_users[0]
            credentials = credential_store.get_credential(single_user)
            if credentials:
                user_email = single_user
                logger.info(f"Loaded credentials for single stored user: {single_user}")

    if not credentials:
        logger.info("No credentials found")
        return None

    # Check scopes
    if credentials.scopes:
        if not all(scope in credentials.scopes for scope in required_scopes):
            logger.warning("Credentials lack required scopes")
            return None

    # Check validity and refresh if needed
    if credentials.valid:
        return credentials

    if credentials.expired and credentials.refresh_token:
        logger.info("Credentials expired, attempting refresh")
        try:
            credentials.refresh(Request())
            logger.info("Credentials refreshed successfully")

            # Update stored credentials
            if user_email:
                credential_store.store_credential(user_email, credentials)
                store.store_session(
                    user_email=user_email,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_uri=credentials.token_uri
                    or "https://oauth2.googleapis.com/token",
                    client_id=credentials.client_id,
                    client_secret=credentials.client_secret,
                    scopes=list(credentials.scopes) if credentials.scopes else None,
                    expiry=credentials.expiry,
                    session_id=session_id,
                )

            return credentials

        except RefreshError as e:
            logger.warning(f"Token refresh failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            return None

    logger.warning("Credentials invalid and cannot be refreshed")
    return None


def get_credentials_or_auth_url(
    user_email: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Tuple[Optional[Credentials], Optional[str]]:
    """
    Get credentials or return auth URL if authentication needed.

    Args:
        user_email: User's email address
        required_scopes: Required OAuth scopes
        session_id: Optional session ID

    Returns:
        Tuple of (credentials, auth_message) - one will be None
    """
    credentials = get_credentials(
        user_email=user_email,
        required_scopes=required_scopes,
        session_id=session_id,
    )

    if credentials and credentials.valid:
        return credentials, None

    from .oauth_callback_server import start_oauth_callback_server

    success, error_msg, redirect_uri = start_oauth_callback_server()

    if not success:
        raise GoogleAuthenticationError(
            f"Cannot initiate OAuth flow - callback server unavailable: {error_msg}"
        )

    auth_message = start_auth_flow(
        user_google_email=user_email,
        service_name="Drive Synapsis",
        redirect_uri=redirect_uri,
    )

    return None, auth_message


# Legacy compatibility function
def get_creds() -> Any:
    """
    Legacy function for backward compatibility.

    Returns:
        Credentials object

    Raises:
        GoogleAuthenticationError: If authentication is required
    """
    credentials = get_credentials()

    if credentials and credentials.valid:
        return credentials

    # Try to get from file-based store (legacy token.json)
    config = get_oauth_config()
    legacy_token_path = os.path.join(config.credentials_dir, "token.json")

    if os.path.exists(legacy_token_path):
        try:
            credentials = Credentials.from_authorized_user_file(
                legacy_token_path, SCOPES
            )

            if credentials and credentials.valid:
                return credentials

            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Save refreshed credentials
                with open(legacy_token_path, "w") as token:
                    token.write(credentials.to_json())
                return credentials

        except Exception as e:
            logger.warning(f"Failed to load legacy token: {e}")

    from google_auth_oauthlib.flow import InstalledAppFlow

    config = get_oauth_config()

    if os.path.exists(config.client_secrets_path):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.client_secrets_path, SCOPES
            )
            credentials = flow.run_local_server(port=0)

            with open(legacy_token_path, "w") as token:
                token.write(credentials.to_json())

            return credentials
        except (OSError, IOError, ConnectionError) as e:
            logger.error(f"Network/IO error during auth flow: {e}")
            raise GoogleAuthenticationError(
                f"Authentication failed due to network error: {e}"
            )
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Blocking auth flow failed: {e}")

    auth_message = start_auth_flow(service_name="Drive Synapsis")
    raise GoogleAuthenticationError(auth_message)
