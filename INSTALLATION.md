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
8. **Create** the directory `~/.config/drive-synapsis/` and **move** `client_secret.json` there.
   ```bash
   mkdir -p ~/.config/drive-synapsis
   mv ~/Downloads/client_secret.json ~/.config/drive-synapsis/
   ```

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

## Step 3: Run Setup Wizard

We provide an interactive wizard to automate the rest of the setup (credentials, authentication, and client configuration).

Run:
```bash
uv run drive-synapsis-config
```

The wizard will:
1.  Ask for the path to your downloaded `client_secret.json`.
2.  Move it to the secure directory `~/.config/drive-synapsis/`.
3.  Launch the browser to authenticate you with Google.
4.  Automatically update the configuration file for your chosen AI client (Gemini CLI, Claude Code, or OpenCode).

## Step 4: Verify Installation

### Restart Client

After the wizard completes, restart your AI client (Gemini CLI, Claude Code, etc.) for changes to take effect.

### Test Connection

In your AI assistant, try a simple command:

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
1. Delete the existing `token.json` file (in `~/.config/drive-synapsis/`)
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
- Check that `client_secret.json` and `token.json` exist in `~/.config/drive-synapsis/`
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
- Ensure it's in `~/.config/drive-synapsis/`
- Check file permissions (must be readable)

## Enterprise Deployment (Google Workspace)

If you are deploying this within a company using Google Workspace, you can avoid the "Testing" mode limitations (7-day token expiry, user limits) by configuring the app as **Internal**.

### 1. Configure "Internal" User Type

1.  In Google Cloud Console, go to **OAuth consent screen**.
2.  Click **Edit App**.
3.  Change User Type from **External** to **Internal**.
    *   *Note: This option is only available if you are part of a Google Workspace organization.*
4.  Save changes.

**Benefits:**
*   **No User Cap**: Any user in your organization (`@yourcompany.com`) can sign in.
*   **No Whitelist**: You don't need to add individual email addresses.
*   **No 7-Day Expiry**: Refresh tokens last indefinitely (or until revoked).

### 2. Credential Distribution Strategy

To share the tool with your team, follow this security best practice:

*   **Share `client_secret.json` (The App Identity)**:
    *   It is generally acceptable to distribute this file internally (e.g., in a private Git repo or internal shared drive).
    *   This file identifies the *application*, not a user.
    *   **Do NOT** commit this to a public repository.

*   **Do NOT Share `token.json` (The User Identity)**:
    *   This file contains the *access tokens* for a specific user.
    *   **Each user must generate their own `token.json`**.

### 3. User Onboarding Workflow

1.  **Distribute**: Provide the code/container and the `client_secret.json` to users.
2.  **Authenticate**: Instruct each user to run the one-time setup command:
    ```bash
    uv run drive-synapsis
    ```
3.  **Sign In**: They will sign in with their corporate Google account.
4.  **Ready**: A unique `token.json` is created on their machine.

## Next Steps

Now that you've successfully installed the server, check out the [Usage Guide](USAGE.md) to learn how to use all the available features!

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [Usage Guide](USAGE.md) for feature-specific help
2. Review the [README](README.md) for architecture and design information
3. Verify your Google Cloud Console configuration
4. Ensure all prerequisites are met
