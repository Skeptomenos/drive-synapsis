# Installation Guide

This guide walks you through setting up the Google Drive MCP Server from scratch.

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: macOS, Linux, or Windows
- **Google Account**: A Google account with access to Google Drive

### Required Tools

Choose one of the following package managers:

- **uv** (Recommended): Fast Python package manager
- **pip**: Standard Python package manager

## Step 1: Google Cloud Setup

Before installing the server, you need to configure Google Cloud credentials to enable API access.

### 1.1 Create a Google Cloud Project

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter a project name (e.g., "Google Drive MCP Server")
4. Click **"Create"**

### 1.2 Enable Required APIs

Enable the following APIs for your project:

1. Go to **"APIs & Services"** → **"Library"**
2. Search for and enable each of these APIs:
   - **Google Drive API**
   - **Google Docs API**
   - **Google Sheets API**

> [!TIP]
> You can enable all APIs from a single page by searching for "Drive" in the API Library.

### 1.3 Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** user type (or "Internal" if you're a Google Workspace user)
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: Choose a descriptive name (e.g., "My Drive MCP")
   - **User support email**: Your email address
   - **Developer contact email**: Your email address
5. Click **"Save and Continue"**

### 1.4 Add Scopes

1. Click **"Add or Remove Scopes"**
2. Filter and select the following scopes:
   - `https://www.googleapis.com/auth/drive` (Full Drive access)
   - `https://www.googleapis.com/auth/documents` (Google Docs access)
   - `https://www.googleapis.com/auth/spreadsheets` (Google Sheets access)
3. Click **"Update"** → **"Save and Continue"**

### 1.5 Add Test Users

Since your app is likely just for you or your team, you will keep it in **"Testing"** mode. This avoids Google's strict verification process but requires you to explicitly list who can use the app.

1. Click **"Add Users"**
2. Enter your Google email address (and any others who will use this server)
3. Click **"Add"** → **"Save and Continue"**

> [!NOTE]
> **What implies "Testing Mode"?**
> Google Cloud apps start in "Testing" mode. This means the app is not verified by Google for public use.
> *   **Pros**: Free, instant setup, no verification review.
> *   **Cons**: Only users you explicitly "whitelist" (add to the list above) can sign in. The token expires every 7 days (requiring re-login).
> *   **Why we use it**: For a personal or internal tool like this, "Testing" mode is the standard approach. "Production" mode requires a weeks-long security review process.

> [!IMPORTANT]
> If you see "Access Blocked: App has not completed the Google verification process", it usually means the user trying to sign in was NOT added to this list.

### 1.6 Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Select **"Desktop app"** as the application type
4. Enter a name (e.g., "MCP Desktop Client")
5. Click **"Create"**
6. Click **"Download JSON"** to download the credentials file
7. **Rename** the downloaded file to `client_secret.json`
8. **Move** `client_secret.json` to the root directory of this project

Your Google Cloud setup is now complete! ✅

## Step 2: Install Package

### Using uv (Recommended)

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/drive-synapsis.git
    cd drive-synapsis
    ```

2.  Install in editable mode:
    ```bash
    uv pip install -e .
    ```

### Using pip

1.  Clone and navigate:
    ```bash
    git clone https://github.com/your-repo/drive-synapsis.git
    cd drive-synapsis
    ```

2.  Create virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

3.  Install:
    ```bash
    pip install -e .
    ```

## Step 3: Authenticate

Run the server once to trigger the OAuth flow:

```bash
uv run drive-synapsis
# or if using pip/venv:
drive-synapsis
```

A browser window will open. detailed steps:
1.  Sign in with your Google account.
2.  If you see "App isn't verified", click **Advanced** -> **Go to [App Name] (unsafe)**.
3.  Grant the requested permissions.
4.  A `token.json` file will be created in your project root.

## Step 4: Configure Your Client

We provide a helper tool to generate the configuration for you.

Run:
```bash
uv run drive-synapsis-config
```

This will print the exact JSON configuration you need for:
-   **Claude Desktop / Claude Code**
-   **VS Code (Copilot, Continue, etc.)**
-   **Gemini CLI / OpenCode**

### Manual Configuration (Gemini CLI)

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": [
    {
      "name": "drive-synapsis",
      "command": "/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/drive-synapsis",
        "drive-synapsis"
      ]
    }
  ]
}
```

## Step 5: Verify Installation

### Restart Gemini CLI

After updating the configuration, restart your Gemini CLI for changes to take effect.

### Test Connection

In the Gemini CLI, try a simple command:

```
List the available MCP tools
```

You should see Google Drive tools listed among the available tools.

### Test Functionality

Try searching your Drive:

```
Search my Google Drive for files modified today
```

If this works, your installation is complete! 🎉

## Troubleshooting

### Authentication Issues

**Problem**: `token.json` not found or invalid

**Solution**:
1. Delete the existing `token.json` file (if it exists)
2. Run the authentication flow again: `uv run src/drive_synapsis/main_server.py`
3. Complete the browser authorization

### "App is not verified" Warning

**Problem**: Google shows a security warning during OAuth

**Solution**: This is expected for testing apps. Click **"Advanced"** → **"Go to [App Name] (unsafe)"** to proceed.

### Server Connection Errors

**Problem**: Gemini CLI can't connect to the MCP server

**Solutions**:
- Verify `uv` or `python` is in your system PATH
- Use absolute paths in configuration
- Check that `client_secret.json` and `token.json` exist in the project directory
- Ensure the virtual environment has all dependencies installed

### Permission Errors

**Problem**: "Insufficient permissions" errors when accessing files

**Solution**:
1. Check that you added all required scopes in the OAuth consent screen
2. Delete `token.json` and re-authenticate to grant new permissions
3. Verify your test user is properly configured in Google Cloud Console

### Import Errors

**Problem**: `ModuleNotFoundError` when running the server

**Solution**:
- Ensure you've run `uv sync` or `pip install` with all dependencies
- Verify your virtual environment is activated (for pip users)
- Check Python version: `python --version` (must be 3.10+)

### File Not Found Errors

**Problem**: Can't find `client_secret.json`

**Solution**:
- Verify the file is named exactly `client_secret.json`
- Ensure it's in the root project directory (same level as `pyproject.toml`)
- Check file permissions (must be readable)

## Next Steps

Now that you've successfully installed the server, check out the [Usage Guide](USAGE.md) to learn how to use all the available features!

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [Usage Guide](USAGE.md) for feature-specific help
2. Review the [README](README.md) for architecture and design information
3. Verify your Google Cloud Console configuration
4. Ensure all prerequisites are met
