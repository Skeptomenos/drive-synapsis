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

Since your app is in testing mode, you need to whitelist users:

1. Click **"Add Users"**
2. Enter your Google email address
3. Click **"Add"** → **"Save and Continue"**

> [!IMPORTANT]
> Only users added as test users can authenticate with your app while it's in testing mode.

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

## Step 2: Install Dependencies

### Option A: Using uv (Recommended)

**uv** is a fast, modern Python package manager that provides better performance and dependency resolution.

#### Install uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Homebrew (macOS):**
```bash
brew install uv
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Sync Project Dependencies

Navigate to the project directory and run:

```bash
cd /path/to/drive-synapsis
uv sync
```

This will:
- Create a virtual environment in `.venv/`
- Install all required dependencies
- Lock dependency versions

### Option B: Using pip

If you prefer using standard Python tooling:

#### Create Virtual Environment

```bash
cd /path/to/drive-synapsis
python3 -m venv .venv
```

#### Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install fastmcp google-api-python-client google-auth-oauthlib python-dotenv
```

## Step 3: Initial Authentication

Before you can use the MCP server with Gemini CLI, you must authenticate manually to generate a token.

### Run Authentication Flow

**Using uv:**
```bash
uv run src/drive_synapsis/main_server.py
```

**Using pip (with activated venv):**
```bash
python src/drive_synapsis/main_server.py
```

### Complete Authorization

1. A browser window will automatically open
2. Sign in with your Google account (must be a test user)
3. You may see a warning: **"App isn't verified"**
   - Click **"Advanced"**
   - Click **"Go to [App Name] (unsafe)"**
4. Review and accept the requested permissions
5. You should see a success message in your browser
6. A `token.json` file will be created in your project directory

### Stop the Server

Press `Ctrl+C` in your terminal to stop the server.

> [!NOTE]
> The `token.json` file contains your authentication credentials. Keep it secure and do not commit it to version control.

## Step 4: Configure Gemini CLI

To use this MCP server with Gemini CLI, you need to add it to your MCP configuration.

### Locate MCP Configuration File

The configuration file is typically located at:
- **macOS/Linux**: `~/.gemini/settings.json`
- **Windows**: `%USERPROFILE%\.gemini\settings.json`

### Add Server Configuration

Edit your configuration file and add the `gdrive` server:

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "/path/to/uv",
      "args": [
        "run",
        "--quiet",
        "/absolute/path/to/drive-synapsis/src/drive_synapsis/main_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Find Correct Paths

**Find uv path:**
```bash
which uv
```

**Find project path:**
```bash
cd /path/to/drive-synapsis
pwd
```

### Example Configuration

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--quiet",
        "/Users/davidhelmus/Repos/drive-synapsis/src/drive_synapsis/main_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

> [!IMPORTANT]
> Always use **absolute paths** in the configuration. Relative paths will not work.

### Configuration for pip Users

If you're using pip instead of uv:

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "/path/to/.venv/bin/python",
      "args": [
        "/absolute/path/to/drive-synapsis/src/drive_synapsis/main_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
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
