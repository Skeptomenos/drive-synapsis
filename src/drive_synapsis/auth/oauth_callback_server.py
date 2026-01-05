"""
OAuth Callback Server for Drive Synapsis.

In stdio mode, starts a minimal HTTP server for OAuth callbacks.
This allows non-blocking OAuth flows where the user authenticates in browser.
"""

import asyncio
import logging
import threading
import time
import socket
from typing import Optional, Tuple

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from .scopes import get_scopes
from .oauth21_session_store import get_oauth21_session_store
from .oauth_config import get_oauth_redirect_uri, get_oauth_config

logger = logging.getLogger(__name__)


def _create_success_html(user_email: str) -> str:
    """Create a success HTML page after OAuth completion."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 400px;
            }}
            .success-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            .email {{
                color: #667eea;
                font-weight: bold;
            }}
            p {{
                color: #666;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">&#10004;</div>
            <h1>Authentication Successful!</h1>
            <p>You have successfully authenticated as:</p>
            <p class="email">{user_email}</p>
            <p>You can close this window and return to your application.</p>
        </div>
    </body>
    </html>
    """


def _create_error_html(error_message: str) -> str:
    """Create an error HTML page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Failed</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 400px;
            }}
            .error-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            .error-message {{
                color: #ee5a5a;
                background: #fff5f5;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">&#10060;</div>
            <h1>Authentication Failed</h1>
            <div class="error-message">{error_message}</div>
            <p>Please try again or contact support if the issue persists.</p>
        </div>
    </body>
    </html>
    """


class MinimalOAuthServer:
    """
    Minimal HTTP server for OAuth callbacks in stdio mode.
    Only starts when needed and runs in a background thread.
    """

    def __init__(self, port: int = 8000, base_uri: str = "http://localhost") -> None:
        self.port = port
        self.base_uri = base_uri
        self.app = FastAPI()
        self.server: Optional[uvicorn.Server] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False

        self._setup_callback_route()

    def _setup_callback_route(self) -> None:
        """Setup the OAuth callback route."""

        @self.app.get("/oauth2callback")
        async def oauth_callback(request: Request) -> HTMLResponse:
            """Handle OAuth callback from Google."""
            from .google_auth import handle_auth_callback

            state = request.query_params.get("state")
            code = request.query_params.get("code")
            error = request.query_params.get("error")

            if error:
                error_message = f"Google returned an error: {error}"
                logger.error(error_message)
                return HTMLResponse(
                    content=_create_error_html(error_message), status_code=400
                )

            if not code:
                error_message = "No authorization code received from Google"
                logger.error(error_message)
                return HTMLResponse(
                    content=_create_error_html(error_message), status_code=400
                )

            try:
                logger.info(f"OAuth callback: Received code (state: {state})")

                redirect_uri = get_oauth_redirect_uri()
                user_email, credentials = handle_auth_callback(
                    scopes=get_scopes(),
                    authorization_response=str(request.url),
                    redirect_uri=redirect_uri,
                    session_id=None,
                )

                logger.info(f"OAuth callback: Successfully authenticated {user_email}")
                return HTMLResponse(content=_create_success_html(user_email))

            except Exception as e:
                error_message = f"Error processing OAuth callback: {str(e)}"
                logger.error(error_message, exc_info=True)
                return HTMLResponse(
                    content=_create_error_html(error_message), status_code=500
                )

    def start(self) -> Tuple[bool, str]:
        """
        Start the minimal OAuth server.

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if self.is_running:
            logger.info("Minimal OAuth server is already running")
            return True, ""

        # Parse hostname from base_uri
        try:
            from urllib.parse import urlparse

            parsed_uri = urlparse(self.base_uri)
            hostname = parsed_uri.hostname or "localhost"
        except Exception:
            hostname = "localhost"

        # Check if port is available
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((hostname, self.port))
        except OSError:
            error_msg = f"Port {self.port} is already in use"
            logger.error(error_msg)
            return False, error_msg

        def run_server() -> None:
            """Run the server in a separate thread."""
            try:
                config = uvicorn.Config(
                    self.app,
                    host=hostname,
                    port=self.port,
                    log_level="warning",
                    access_log=False,
                )
                self.server = uvicorn.Server(config)
                asyncio.run(self.server.serve())
            except Exception as e:
                logger.error(f"Minimal OAuth server error: {e}", exc_info=True)
                self.is_running = False

        # Start server in background thread
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Wait for server to start
        max_wait = 3.0
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex((hostname, self.port))
                    if result == 0:
                        self.is_running = True
                        logger.info(
                            f"Minimal OAuth server started on {hostname}:{self.port}"
                        )
                        return True, ""
            except Exception:
                pass
            time.sleep(0.1)

        error_msg = f"Failed to start OAuth server on {hostname}:{self.port}"
        logger.error(error_msg)
        return False, error_msg

    def stop(self) -> None:
        """Stop the minimal OAuth server."""
        if not self.is_running:
            return

        try:
            if self.server and hasattr(self.server, "should_exit"):
                self.server.should_exit = True

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=3.0)

            self.is_running = False
            logger.info("Minimal OAuth server stopped")

        except Exception as e:
            logger.error(f"Error stopping OAuth server: {e}", exc_info=True)


# Global instance for stdio mode
_minimal_oauth_server: Optional[MinimalOAuthServer] = None


def ensure_oauth_callback_available(
    transport_mode: str = "stdio", port: int = 8000, base_uri: str = "http://localhost"
) -> Tuple[bool, str]:
    """
    Ensure OAuth callback endpoint is available.

    For stdio mode: Starts a minimal server if needed.

    Args:
        transport_mode: "stdio" or "streamable-http"
        port: Port number (default 8000)
        base_uri: Base URI (default "http://localhost")

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    global _minimal_oauth_server

    if transport_mode == "streamable-http":
        # In streamable-http mode, assume main server handles callbacks
        logger.debug("Using existing server for OAuth callbacks")
        return True, ""

    elif transport_mode == "stdio":
        if _minimal_oauth_server is None:
            logger.info(f"Creating minimal OAuth server on {base_uri}:{port}")
            _minimal_oauth_server = MinimalOAuthServer(port, base_uri)

        if not _minimal_oauth_server.is_running:
            logger.info("Starting minimal OAuth server for stdio mode")
            return _minimal_oauth_server.start()
        else:
            logger.info("Minimal OAuth server is already running")
            return True, ""

    else:
        error_msg = f"Unknown transport mode: {transport_mode}"
        logger.error(error_msg)
        return False, error_msg


def cleanup_oauth_callback_server() -> None:
    """Clean up the minimal OAuth server if it was started."""
    global _minimal_oauth_server
    if _minimal_oauth_server:
        _minimal_oauth_server.stop()
        _minimal_oauth_server = None
