# Tech Stack

## Core Technologies
- **Language:** Python 3.10+
- **MCP Framework:** `fastmcp` (for rapid tool definition and server lifecycle)
- **Package Manager:** `uv` (for fast dependency resolution and virtual environments)

## Google Integration
- **Auth:** `google-auth-oauthlib` (OAuth 2.0 flow)
- **API Client:** `google-api-python-client` (Drive v3, Docs v1, Sheets v4)
- **Credential Storage:** Local filesystem at `~/.config/drive-synapsis/` (JSON)

## Architecture
- **Server (`src/drive_synapsis/server`):**
    - Defines MCP tools (e.g., `search_files`, `read_doc`).
    - Handles request routing via `fastmcp`.
- **Client (`src/drive_synapsis/client`):**
    - **Mixin Pattern:** `GDriveClient` composes functionality from `SearchMixin`, `FilesMixin`, etc.
    - **Service Layer:** Wrpas raw Google API calls with error handling and typing.
- **State Management:**
    - `SyncManager`: Tracks local <-> remote file mappings in `.sync_map.json`.
    - `SearchManager`: Caches search results and handles pagination.

## Configuration
- **Wizard:** `src/drive_synapsis/config_gen.py` (Interactive CLI)
- **Env Vars:** `.env` (supported but config wizard preferred)

## Standards
- **Typing:** Full `mypy` compliance (aiming for strict).
- **Style:** Google Python Style Guide (via `ruff` or `flake8` if configured).