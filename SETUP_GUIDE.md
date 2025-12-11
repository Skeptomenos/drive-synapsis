# Google Drive MCP Server Setup Guide

This guide explains how to install the Google Drive MCP Server and connect it with the Gemini CLI.

## 1. Installation

### Prerequisites
- Python 3.10+
- Google Cloud Project with Drive, Docs, and Sheets APIs enabled
- `uv` (recommended) or `pip`

### Steps

1.  **Clone the repository:**
    ```bash
    git clone <repo_url>
    cd gdrive-mcp
    ```

2.  **Install dependencies:**
    Using `uv`:
    ```bash
    uv pip install -e .
    ```
    
    Using `pip`:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

3.  **Setup Google Cloud Credentials:**
    - Create a project in Google Cloud Console.
    - Enable **Drive API**, **Docs API**, and **Sheets API**.
    - Configure OAuth Consent Screen (User Type: External/Test, add your email as tester).
    - Create OAuth 2.0 Client ID (Application type: Desktop app).
    - Download JSON as `client_secret.json`.

4.  **Run Setup Wizard:**
    The wizard will handle moving credentials, authentication, and client configuration.
    ```bash
    uv run drive-synapsis-config
    ```

## 2. Connect with Gemini CLI

The wizard (Step 4 above) can automatically configure Gemini CLI for you.

### Manual Configuration
If you skipped the wizard, add the following to `~/.gemini/settings.json`:

```json
{
  "mcpServers": [
    {
      "name": "drive-synapsis",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/gdrive-mcp",
        "drive-synapsis"
      ]
    }
  ]
}
```
*Replace `/ABSOLUTE/PATH/TO/gdrive-mcp` with your actual project path.*

## 3. Verification

Restart Gemini CLI and run:
```
List available MCP tools
```
You should see tools like `search_google_drive`, `read_google_doc`, etc.

## 4. Usage Example

To search for files:
```
Search my Drive for "Quarterly Report"
```
