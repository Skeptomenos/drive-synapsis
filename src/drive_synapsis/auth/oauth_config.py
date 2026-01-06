"""
OAuth Configuration Management for Drive Synapsis.

This module centralizes OAuth-related configuration to eliminate hardcoded values.
Supports OAuth 2.1 with PKCE enforcement.
"""

import os
from typing import List, Optional, Dict, Any


class OAuthConfig:
    """
    Centralized OAuth configuration management.

    Provides a single source of truth for all OAuth-related configuration values.
    """

    def __init__(self) -> None:
        # Base server configuration
        self.base_uri = os.getenv("DRIVE_SYNAPSIS_BASE_URI", "http://localhost")
        self.port = int(os.getenv("DRIVE_SYNAPSIS_PORT", "9877"))
        self.base_url = f"{self.base_uri}:{self.port}"

        # External URL for reverse proxy scenarios
        self.external_url = os.getenv("DRIVE_SYNAPSIS_EXTERNAL_URL")

        # Credentials directory
        self.credentials_dir = os.path.expanduser(
            os.getenv("DRIVE_SYNAPSIS_CREDENTIALS_DIR", "~/.drive-synapsis")
        )

        # OAuth client configuration (from environment or client_secret.json)
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

        # Client secrets file path
        self.client_secrets_path = os.path.join(
            self.credentials_dir, "client_secret.json"
        )

        # OAuth 2.1 settings - PKCE is always required
        self.pkce_required = True
        self.supported_code_challenge_methods = ["S256"]

        # Transport mode (will be set at runtime)
        self._transport_mode = "stdio"

        # Redirect URI configuration
        self.redirect_uri = self._get_redirect_uri()

    def _get_redirect_uri(self) -> str:
        """Get the OAuth redirect URI."""
        explicit_uri = os.getenv("DRIVE_SYNAPSIS_REDIRECT_URI")
        if explicit_uri:
            return explicit_uri
        return f"{self.get_oauth_base_url()}/oauth2callback"

    def get_oauth_base_url(self) -> str:
        """
        Get OAuth base URL for constructing OAuth endpoints.

        Uses DRIVE_SYNAPSIS_EXTERNAL_URL if set (for reverse proxy scenarios),
        otherwise falls back to constructed base_url with port.
        """
        if self.external_url:
            return self.external_url
        return self.base_url

    def get_redirect_uris(self) -> List[str]:
        """Get all valid OAuth redirect URIs."""
        uris = [self.redirect_uri]

        # Custom redirect URIs from environment
        custom_uris = os.getenv("DRIVE_SYNAPSIS_CUSTOM_REDIRECT_URIS")
        if custom_uris:
            uris.extend([uri.strip() for uri in custom_uris.split(",")])

        return list(dict.fromkeys(uris))

    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        # Either environment variables or client_secret.json must exist
        if self.client_id and self.client_secret:
            return True
        return os.path.exists(self.client_secrets_path)

    def set_transport_mode(self, mode: str) -> None:
        """Set the current transport mode."""
        self._transport_mode = mode

    def get_transport_mode(self) -> str:
        """Get the current transport mode."""
        return self._transport_mode

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get a summary of the current OAuth configuration (excluding secrets)."""
        return {
            "base_url": self.base_url,
            "external_url": self.external_url,
            "effective_oauth_url": self.get_oauth_base_url(),
            "redirect_uri": self.redirect_uri,
            "credentials_dir": self.credentials_dir,
            "client_configured": self.is_configured(),
            "pkce_required": self.pkce_required,
            "transport_mode": self._transport_mode,
        }


# Global configuration instance
_oauth_config: Optional[OAuthConfig] = None


def get_oauth_config() -> OAuthConfig:
    """Get the global OAuth configuration instance."""
    global _oauth_config
    if _oauth_config is None:
        _oauth_config = OAuthConfig()
    return _oauth_config


def reload_oauth_config() -> OAuthConfig:
    """Reload the OAuth configuration from environment variables."""
    global _oauth_config
    _oauth_config = OAuthConfig()
    return _oauth_config


# Convenience functions
def get_oauth_base_url() -> str:
    """Get OAuth base URL."""
    return get_oauth_config().get_oauth_base_url()


def get_oauth_redirect_uri() -> str:
    """Get the primary OAuth redirect URI."""
    return get_oauth_config().redirect_uri


def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured."""
    return get_oauth_config().is_configured()


def get_credentials_dir() -> str:
    """Get the credentials directory path."""
    config = get_oauth_config()
    if not os.path.exists(config.credentials_dir):
        os.makedirs(config.credentials_dir, exist_ok=True)
    return config.credentials_dir
