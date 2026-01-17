# Service Account Authentication Implementation Plan

> **Goal**: Enable zero-friction Google Workspace access for all company employees via domain-wide delegation, eliminating the need for individual OAuth flows or client secret distribution.

## Executive Summary

Replace the current BYOK (Bring Your Own Keys) OAuth model with a centralized Service Account authentication flow. Users simply configure their email address — the service account impersonates them for all Google API calls, respecting their individual permissions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Company Infrastructure                          │
│                                                                         │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────────┐    │
│  │ Employee's   │───▶│  MCP Server      │───▶│  Google Workspace  │    │
│  │ AI Client    │    │  (local install) │    │  APIs              │    │
│  │              │    │                  │    │                    │    │
│  │ - Claude     │    │  Auth Mode:      │    │  - Drive           │    │
│  │ - Gemini CLI │    │  Service Account │    │  - Docs            │    │
│  │ - OpenCode   │    │  + Impersonation │    │  - Sheets          │    │
│  └──────────────┘    └──────────────────┘    │  - Gmail           │    │
│         │                    │               │  - Calendar        │    │
│         │                    │               └────────────────────┘    │
│         │                    │                        ▲                │
│         │                    │                        │                │
│         ▼                    ▼                        │                │
│  ┌──────────────┐    ┌──────────────────┐            │                │
│  │ User Email   │    │ Service Account  │────────────┘                │
│  │ Config       │    │ Key (secured)    │  Impersonates user          │
│  │              │    │                  │  subject=user@company.com   │
│  └──────────────┘    └──────────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Security Model

| Aspect | Behavior |
|--------|----------|
| **Data Access** | User only sees their own files, emails, calendars |
| **Permissions** | User's normal Google Workspace permissions apply |
| **Audit Trail** | Actions logged as the impersonated user |
| **Domain Lock** | Only `@yourcompany.com` emails accepted |

---

## Phase 1: GCP & Google Admin Setup

**Owner**: Platform/IT Admin  
**Duration**: 1-2 hours

### 1.1 Create Service Account

```bash
# In your company's GCP project
gcloud iam service-accounts create workspace-mcp \
    --display-name="Workspace MCP Server" \
    --description="Service account for MCP server domain-wide delegation"

# Note the email: workspace-mcp@PROJECT_ID.iam.gserviceaccount.com
```

### 1.2 Create & Download Key

```bash
gcloud iam service-accounts keys create workspace-mcp-key.json \
    --iam-account=workspace-mcp@PROJECT_ID.iam.gserviceaccount.com
```

> **Security**: Store this key in Google Secret Manager or your company vault. Never commit to git.

### 1.3 Enable Domain-Wide Delegation

1. Go to [Google Admin Console](https://admin.google.com) → Security → API Controls → Domain-wide Delegation
2. Click "Add new"
3. Enter the Service Account's **Client ID** (from GCP Console → Service Account details)
4. Add OAuth Scopes:

```
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.compose
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/tasks
https://www.googleapis.com/auth/chat.messages
https://www.googleapis.com/auth/forms.body
https://www.googleapis.com/auth/presentations
```

### 1.4 Enable Required APIs

Ensure these APIs are enabled in your GCP project:
- Google Drive API
- Google Docs API
- Google Sheets API
- Gmail API
- Google Calendar API
- Google Tasks API
- Google Chat API
- Google Forms API
- Google Slides API

---

## Phase 2: Auth Module Implementation

**Owner**: Developer  
**Duration**: 2-3 days

### 2.1 New File: `auth/service_account_auth.py`

```python
"""
Service Account Authentication with Domain-Wide Delegation.

Enables zero-friction authentication by impersonating users via a
centrally-managed service account with domain-wide delegation.
"""

import json
import logging
import os
from typing import Optional, Dict, Any

from google.oauth2 import service_account
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Required scopes for full Workspace access
SERVICE_ACCOUNT_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/presentations",
]


class ServiceAccountAuthError(Exception):
    """Raised when service account authentication fails."""
    pass


class ServiceAccountAuth:
    """
    Manages service account authentication with domain-wide delegation.
    
    This class handles:
    - Loading service account credentials from file or environment
    - Impersonating users within the allowed domain
    - Caching credentials per user for performance
    """
    
    def __init__(
        self,
        key_path: Optional[str] = None,
        key_json: Optional[str] = None,
        allowed_domain: Optional[str] = None,
        scopes: Optional[list] = None,
    ):
        """
        Initialize service account authentication.
        
        Args:
            key_path: Path to service account JSON key file
            key_json: JSON string of service account key (alternative to file)
            allowed_domain: Domain to restrict impersonation (e.g., "yourcompany.com")
            scopes: OAuth scopes to request (defaults to full Workspace access)
        """
        self.key_info = self._load_key(key_path, key_json)
        self.allowed_domain = allowed_domain or os.getenv("ALLOWED_DOMAIN")
        self.scopes = scopes or SERVICE_ACCOUNT_SCOPES
        self._credentials_cache: Dict[str, Credentials] = {}
        
        logger.info(
            f"ServiceAccountAuth initialized. "
            f"Service account: {self.key_info.get('client_email')}. "
            f"Allowed domain: {self.allowed_domain or 'any'}"
        )
    
    def _load_key(
        self, 
        key_path: Optional[str], 
        key_json: Optional[str]
    ) -> Dict[str, Any]:
        """Load service account key from file, JSON string, or environment."""
        
        # Priority 1: Explicit JSON string
        if key_json:
            logger.debug("Loading service account key from JSON string")
            return json.loads(key_json)
        
        # Priority 2: Explicit file path
        if key_path and os.path.exists(key_path):
            logger.debug(f"Loading service account key from {key_path}")
            with open(key_path, "r") as f:
                return json.load(f)
        
        # Priority 3: Environment variable (JSON string)
        env_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_JSON")
        if env_key:
            logger.debug("Loading service account key from GOOGLE_SERVICE_ACCOUNT_KEY_JSON")
            return json.loads(env_key)
        
        # Priority 4: Environment variable (file path)
        env_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
        if env_path and os.path.exists(env_path):
            logger.debug(f"Loading service account key from {env_path}")
            with open(env_path, "r") as f:
                return json.load(f)
        
        # Priority 5: Default path
        default_path = os.path.expanduser("~/.config/workspace-mcp/service-account.json")
        if os.path.exists(default_path):
            logger.debug(f"Loading service account key from default path {default_path}")
            with open(default_path, "r") as f:
                return json.load(f)
        
        raise ServiceAccountAuthError(
            "No service account key found. Provide via:\n"
            "  - GOOGLE_SERVICE_ACCOUNT_KEY_JSON environment variable\n"
            "  - GOOGLE_SERVICE_ACCOUNT_KEY_PATH environment variable\n"
            "  - ~/.config/workspace-mcp/service-account.json file"
        )
    
    def _validate_email(self, user_email: str) -> None:
        """Validate that the email is from the allowed domain."""
        if not user_email:
            raise ServiceAccountAuthError("User email is required for impersonation")
        
        if self.allowed_domain:
            if not user_email.endswith(f"@{self.allowed_domain}"):
                raise ServiceAccountAuthError(
                    f"Email {user_email} is not from allowed domain @{self.allowed_domain}"
                )
        
        # Basic email format validation
        if "@" not in user_email or "." not in user_email.split("@")[1]:
            raise ServiceAccountAuthError(f"Invalid email format: {user_email}")
    
    def get_credentials(self, user_email: str) -> Credentials:
        """
        Get credentials for impersonating the specified user.
        
        Args:
            user_email: Email of the user to impersonate
            
        Returns:
            Google credentials object for the impersonated user
            
        Raises:
            ServiceAccountAuthError: If email validation fails or auth fails
        """
        self._validate_email(user_email)
        
        # Check cache
        if user_email in self._credentials_cache:
            creds = self._credentials_cache[user_email]
            if creds.valid:
                logger.debug(f"Using cached credentials for {user_email}")
                return creds
            elif creds.expired:
                logger.debug(f"Refreshing expired credentials for {user_email}")
                creds.refresh(Request())
                return creds
        
        # Create new credentials with impersonation
        logger.info(f"Creating new credentials for {user_email}")
        
        try:
            credentials = service_account.Credentials.from_service_account_info(
                self.key_info,
                scopes=self.scopes,
                subject=user_email,  # This is the impersonation target
            )
            
            # Cache for future use
            self._credentials_cache[user_email] = credentials
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to create credentials for {user_email}: {e}")
            raise ServiceAccountAuthError(
                f"Failed to authenticate as {user_email}: {e}"
            )
    
    def clear_cache(self, user_email: Optional[str] = None) -> None:
        """Clear cached credentials."""
        if user_email:
            self._credentials_cache.pop(user_email, None)
        else:
            self._credentials_cache.clear()


# Global instance
_service_account_auth: Optional[ServiceAccountAuth] = None


def get_service_account_auth() -> ServiceAccountAuth:
    """Get or create the global ServiceAccountAuth instance."""
    global _service_account_auth
    
    if _service_account_auth is None:
        _service_account_auth = ServiceAccountAuth()
    
    return _service_account_auth


def get_impersonated_credentials(user_email: str) -> Credentials:
    """
    Convenience function to get credentials for a user.
    
    Args:
        user_email: Email of the user to impersonate
        
    Returns:
        Google credentials object
    """
    return get_service_account_auth().get_credentials(user_email)


def is_service_account_mode() -> bool:
    """Check if service account mode is enabled."""
    return os.getenv("USE_SERVICE_ACCOUNT", "").lower() in ("true", "1", "yes")
```

### 2.2 Update: `auth/google_auth.py`

Add service account support to the existing auth module:

```python
# Add to imports
from .service_account_auth import (
    is_service_account_mode,
    get_impersonated_credentials,
    ServiceAccountAuthError,
)

# Modify get_credentials function
def get_credentials(
    user_email: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Optional[Credentials]:
    """
    Get credentials for Google API access.
    
    Supports two modes:
    1. Service Account Mode: Impersonates user via domain-wide delegation
    2. OAuth Mode: Uses stored OAuth tokens (original behavior)
    """
    
    # Service Account Mode
    if is_service_account_mode():
        if not user_email:
            logger.error("Service account mode requires user_email")
            return None
        
        try:
            return get_impersonated_credentials(user_email)
        except ServiceAccountAuthError as e:
            logger.error(f"Service account auth failed: {e}")
            return None
    
    # OAuth Mode (existing implementation)
    # ... rest of existing code ...
```

### 2.3 Update: `auth/__init__.py`

Export new functions:

```python
from .service_account_auth import (
    ServiceAccountAuth,
    ServiceAccountAuthError,
    get_service_account_auth,
    get_impersonated_credentials,
    is_service_account_mode,
)
```

---

## Phase 3: Configuration & Environment

**Owner**: Developer  
**Duration**: 0.5 days

### 3.1 New Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `USE_SERVICE_ACCOUNT` | Yes | Set to `true` to enable service account mode |
| `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` | One of these | Path to service account JSON key |
| `GOOGLE_SERVICE_ACCOUNT_KEY_JSON` | One of these | JSON string of service account key |
| `ALLOWED_DOMAIN` | Recommended | Restrict to company domain (e.g., `yourcompany.com`) |
| `USER_GOOGLE_EMAIL` | Optional | Default user email if not specified per-request |

### 3.2 Example `.env` File

```bash
# Service Account Mode
USE_SERVICE_ACCOUNT=true
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=/path/to/service-account.json
ALLOWED_DOMAIN=yourcompany.com

# Optional: Default user (can be overridden per-tool)
USER_GOOGLE_EMAIL=default.user@yourcompany.com
```

### 3.3 MCP Client Configuration

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "workspace": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/workspace-mcp", "main.py"],
      "env": {
        "USE_SERVICE_ACCOUNT": "true",
        "GOOGLE_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account.json",
        "ALLOWED_DOMAIN": "yourcompany.com",
        "USER_GOOGLE_EMAIL": "alice@yourcompany.com"
      }
    }
  }
}
```

**Gemini CLI** (`~/.gemini/settings.json`):

```json
{
  "mcpServers": {
    "workspace": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/workspace-mcp", "main.py"],
      "env": {
        "USE_SERVICE_ACCOUNT": "true",
        "GOOGLE_SERVICE_ACCOUNT_KEY_PATH": "/path/to/service-account.json",
        "ALLOWED_DOMAIN": "yourcompany.com",
        "USER_GOOGLE_EMAIL": "bob@yourcompany.com"
      }
    }
  }
}
```

---

## Phase 4: Service Key Distribution

**Owner**: Platform/Security Team  
**Duration**: 1 day

### Option A: Google Secret Manager (Recommended)

```python
# Fetch key at runtime from Secret Manager
from google.cloud import secretmanager

def fetch_service_account_key() -> dict:
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/PROJECT_ID/secrets/workspace-mcp-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return json.loads(response.payload.data.decode("UTF-8"))
```

**Pros**: Centralized, audited, rotatable  
**Cons**: Requires GCP auth for the fetch itself (chicken-egg)

### Option B: Internal Package with Encrypted Key

```bash
# Encrypt key with SOPS or age
sops --encrypt service-account.json > service-account.enc.json

# Decrypt at runtime (requires SOPS key access)
sops --decrypt service-account.enc.json > /tmp/service-account.json
```

### Option C: Shared Internal Location

For internal-only use, store in:
- Internal Google Drive (shared with all employees)
- Internal documentation site
- Company vault (1Password Teams, HashiCorp Vault)

Employees download once and place at `~/.config/workspace-mcp/service-account.json`

---

## Phase 5: Testing & Validation

**Owner**: Developer  
**Duration**: 1 day

### 5.1 Unit Tests

```python
# tests/test_service_account_auth.py

import pytest
from auth.service_account_auth import (
    ServiceAccountAuth,
    ServiceAccountAuthError,
)


class TestServiceAccountAuth:
    
    def test_validates_allowed_domain(self):
        auth = ServiceAccountAuth(
            key_json='{"type": "service_account", ...}',
            allowed_domain="yourcompany.com"
        )
        
        # Should pass
        auth._validate_email("alice@yourcompany.com")
        
        # Should fail
        with pytest.raises(ServiceAccountAuthError):
            auth._validate_email("hacker@evil.com")
    
    def test_rejects_empty_email(self):
        auth = ServiceAccountAuth(key_json='{"type": "service_account", ...}')
        
        with pytest.raises(ServiceAccountAuthError):
            auth._validate_email("")
    
    def test_caches_credentials(self):
        auth = ServiceAccountAuth(key_json='...')
        
        creds1 = auth.get_credentials("alice@yourcompany.com")
        creds2 = auth.get_credentials("alice@yourcompany.com")
        
        assert creds1 is creds2  # Same cached object
```

### 5.2 Integration Tests

```python
# tests/test_service_account_integration.py

import pytest
from googleapiclient.discovery import build
from auth.service_account_auth import get_impersonated_credentials


@pytest.mark.integration
def test_can_access_drive_as_user():
    """Verify impersonation works for Drive API."""
    creds = get_impersonated_credentials("test.user@yourcompany.com")
    
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(pageSize=1).execute()
    
    assert "files" in results


@pytest.mark.integration  
def test_cannot_access_other_users_files():
    """Verify user isolation - Alice can't see Bob's private files."""
    alice_creds = get_impersonated_credentials("alice@yourcompany.com")
    
    service = build("drive", "v3", credentials=alice_creds)
    
    # This should NOT return Bob's private files
    results = service.files().list(
        q="'bob@yourcompany.com' in owners",
        pageSize=10
    ).execute()
    
    # Alice should only see files Bob has shared with her
    for file in results.get("files", []):
        assert file.get("shared") == True or "alice" in str(file.get("permissions", []))
```

### 5.3 Manual Validation Checklist

- [ ] Service account key loads correctly
- [ ] Domain validation rejects external emails
- [ ] User can access their own Drive files
- [ ] User can read their own Gmail
- [ ] User can see their own Calendar
- [ ] User CANNOT see other users' private files
- [ ] Audit logs show correct user identity
- [ ] Token refresh works for long sessions

---

## Phase 6: Documentation & Rollout

**Owner**: Developer + Platform Team  
**Duration**: 1 day

### 6.1 Internal Documentation

Create `docs/INTERNAL_SETUP.md`:

```markdown
# Workspace MCP - Internal Setup Guide

## Quick Start

1. Get the service account key from [internal location]
2. Save to `~/.config/workspace-mcp/service-account.json`
3. Configure your MCP client (see examples below)
4. Start using!

## Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

\`\`\`json
{
  "mcpServers": {
    "workspace": {
      "command": "uvx",
      "args": ["workspace-mcp"],
      "env": {
        "USE_SERVICE_ACCOUNT": "true",
        "ALLOWED_DOMAIN": "yourcompany.com",
        "USER_GOOGLE_EMAIL": "YOUR_EMAIL@yourcompany.com"
      }
    }
  }
}
\`\`\`

## Troubleshooting

### "Email not from allowed domain"
Make sure you're using your @yourcompany.com email.

### "Service account key not found"
Ensure the key is at `~/.config/workspace-mcp/service-account.json`
```

### 6.2 Rollout Plan

| Week | Action |
|------|--------|
| Week 1 | Beta with engineering team (5-10 users) |
| Week 2 | Expand to willing early adopters |
| Week 3 | Company-wide announcement + documentation |
| Week 4 | Support period, gather feedback |

---

## Security Considerations

### What the Service Account CAN Do

- Access any user's data when impersonating them
- Only within the scopes granted in Admin Console
- Only for users in the delegated domain

### What the Service Account CANNOT Do

- Access data without specifying a user to impersonate
- Access users outside the domain
- Exceed the impersonated user's permissions
- Access scopes not granted in Admin Console

### Mitigations

| Risk | Mitigation |
|------|------------|
| Key exposure | Store in Secret Manager, rotate regularly |
| Unauthorized impersonation | Domain validation, audit logs |
| Scope creep | Minimal scopes in Admin Console |
| Key in git | `.gitignore`, pre-commit hooks |

### Audit & Monitoring

- Enable Cloud Audit Logs for the service account
- Monitor for unusual access patterns
- Set up alerts for access from unexpected IPs
- Regular review of who has key access

---

## Timeline Summary

| Phase | Duration | Owner |
|-------|----------|-------|
| Phase 1: GCP Setup | 1-2 hours | Admin |
| Phase 2: Auth Implementation | 2-3 days | Developer |
| Phase 3: Configuration | 0.5 days | Developer |
| Phase 4: Key Distribution | 1 day | Platform |
| Phase 5: Testing | 1 day | Developer |
| Phase 6: Documentation & Rollout | 1 day | Team |

**Total: ~1 week**

---

## Success Criteria

- [ ] Employees can install and use MCP server without OAuth flow
- [ ] Each user only sees their own data
- [ ] Service account key is securely distributed
- [ ] Audit logs correctly attribute actions to users
- [ ] Documentation enables self-service setup
- [ ] Engineering team can contribute to internal repo
