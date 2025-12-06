# Drive Synapsis: Intelligent Google Drive MCP Server

> **Drive Synapsis** is a production-grade Model Context Protocol server that transforms AI assistants into powerful Google Drive collaborators with **bidirectional synchronization**, **intelligent search**, and **comprehensive file management**.

Transform your AI assistant (Gemini CLI, Claude Desktop, or any MCP-compatible client) into a Google Drive power user with natural language commands.

---

## 🚀 Unique Selling Proposition

### Why This MCP Server?

Unlike basic Drive integrations, this server provides:

1. **🔄 Bidirectional Sync**: Full two-way synchronization between local Markdown files and Google Docs with conflict detection and diff previews
2. **🧠 Intelligent Search**: Context-aware search with confidence scoring, content snippets, and smart ranking
3. **🎯 Production-Ready**: Modular architecture, comprehensive error handling, and robust state management
4. **📝 Rich Format Conversion**: Seamless Markdown ↔ Google Docs conversion preserving formatting, links, tables, and comments
5. **🔐 Safe by Default**: Dry-run mode for all destructive operations, conflict detection, and rollback support
6. **🏗️ Enterprise Features**: Bulk operations, folder mirroring, template management, and advanced permissions

### What Sets It Apart

| Feature | This Server | Typical Drive APIs |
|---------|-------------|-------------------|
| Natural Language Interface | ✅ Via MCP | ❌ Programmatic only |
| Bidirectional Sync | ✅ With conflict detection | ❌ One-way at best |
| Local File Integration | ✅ Seamless linking | ❌ Manual tracking |
| Format Intelligence | ✅ Markdown ↔ Docs | ⚠️ Basic export |
| Search Ranking | ✅ AI-optimized scoring | ⚠️ Simple matching |
| Safety Features | ✅ Dry-run, diffs, conflicts | ❌ Direct operations |
| Alias System | ✅ User-friendly references | ❌ Long IDs only |

---

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)**: Complete setup walkthrough from Google Cloud to Gemini CLI
- **[Usage Guide](USAGE.md)**: Comprehensive feature documentation with examples and workflows
- **Architecture**: See [below](#-architecture)

---

## ✨ Comprehensive Features

### 🔍 Search & Discovery

<table>
<tr><td width="50%">

**Basic Search**
- Natural language queries
- Confidence-based ranking (0-100%)
- Content snippet previews
- Smart file type boosting

</td><td width="50%">

**Advanced Search**
- Filter by type, date, owner
- Folder-scoped search
- Multiple criteria combining
- Cached results with aliases

</td></tr>
</table>

**Example:**
```
Search for spreadsheets modified after 2024-01-01 containing "budget"
```

### 📄 Google Docs Operations

<table>
<tr><td width="50%">

**Read & Convert**
- Docs → Markdown conversion
- Preserve rich formatting
- Extract comments
- Multi-tab document support
- Table of contents extraction

</td><td width="50%">

**Create & Edit**
- Create from Markdown
- Template-based creation
- Append, insert, replace content
- Apply formatting styles
- Batch operations

</td></tr>
</table>

**Example:**
```
Create doc "Meeting Notes" from template A and share with team@company.com
```

### 📊 Google Sheets Operations

<table>
<tr><td width="50%">

**Read & Export**
- Sheets → CSV conversion
- Range-specific reads
- Multi-sheet handling
- Preserves formulas option

</td><td width="50%">

**Create & Update**
- Create from CSV/data
- Update cell ranges
- Append rows
- Format cells (colors, fonts)
- Add/remove sheets

</td></tr>
</table>

**Example:**
```
Create spreadsheet "Sales Report" with headers: Date, Product, Revenue
Append row: 2024-12-06, Widget, $1250
```

### 🔄 Local Synchronization (The Killer Feature)

<table>
<tr><td width="50%">

**File Linking**
- Link local ↔ Drive files
- Track sync state
- Persistent mappings
- Automatic conflict detection

</td><td width="50%">

**Bidirectional Sync**
- Upload: local → Drive
- Download: Drive → local
- Diff previews (dry-run)
- Force override option

</td></tr>
</table>

**Advanced Sync Features:**
- **Comment extraction**: Inline and suggestion comments as Markdown footnotes
- **Smart link rewriting**: Automatic Drive URL ↔ local path conversion
- **Folder mirroring**: Recursive download/upload with structure preservation
- **Conflict resolution**: Three-way merge awareness

**Example:**
```
Link ./docs/api.md to Doc A
Update Doc A from local (shows diff)
Update Doc A from local with dry_run=False (applies changes)
```

### 📁 File Management

<table>
<tr><td width="50%">

**Organization**
- Move, copy, rename files
- Create folder hierarchies
- Upload local files
- List folder contents

</td><td width="50%">

**Operations**
- Delete files (to trash)
- Get file metadata
- Batch file operations
- Folder recursion

</td></tr>
</table>

**Example:**
```
Upload ./reports/ to Drive folder "2024 Reports"
Copy all PDFs in folder A to folder B
```

### 🔐 Sharing & Permissions

<table>
<tr><td width="50%">

**Access Control**
- Share with users/groups
- Set permission levels (reader/writer)
- Domain-wide sharing
- Public link generation

</td><td width="50%">

**Management**
- List current permissions
- Update permission levels
- Remove access
- Transfer ownership

</td></tr>
</table>

**Example:**
```
Share Doc A with user@example.com as editor
Make spreadsheet B public with read-only access
```

---

## 🏗️ Architecture

### Design Philosophy

**Modular, scalable, and maintainable** architecture using industry best practices:

- **Separation of Concerns**: Client, server, and utilities clearly separated
- **Mixin Pattern**: Composable functionality without deep inheritance
- **State Management**: Dedicated managers for search results and sync state
- **Error Handling**: Comprehensive error recovery with user-friendly messages

### Client Layer (`src/client/`)

Google Drive client split into **focused mixins**:

| Module | Responsibility | Methods |
|--------|---------------|---------|
| `base.py` | Core API initialization | Service factory |
| `search.py` | Search & folder ops | 7 methods |
| `documents.py` | Doc read/write/templates | 15 methods |
| `sheets.py` | Spreadsheet CRUD | 8 methods |
| `files.py` | File management | 9 methods |
| `sharing.py` | Permissions & access | 4 methods |
| `comments.py` | Comment operations | 3 methods |

**Mixin composition** in `client/__init__.py` creates the complete `GDriveClient`.

### Server Layer (`src/server/`)

MCP tools organized by domain:

| Module | MCP Tools | Purpose |
|--------|-----------|---------|
| `main.py` | - | Server initialization |
| `managers.py` | - | State management |
| `search_tools.py` | 3 tools | Search operations |
| `doc_tools.py` | 9 tools | Document operations |
| `sheet_tools.py` | 7 tools | Spreadsheet operations |
| `file_tools.py` | 10 tools | File management |
| `sync_tools.py` | 5 tools | Local sync |
| `sharing_tools.py` | 5 tools | Sharing & permissions |

**Total: 39 MCP tools** across 6 functional domains.

### State Management

**SearchManager**: 
- Caches search results
- Assigns short aliases (A, B, C...)
- Resolves aliases to file IDs
- Manages session state

**SyncManager**:
- Tracks local ↔ Drive mappings
- Stores last known states
- Detects sync conflicts
- Persists to `.sync_map.json`

### Utilities (`src/utils/`)

- **`conversion.py`**: Markdown ↔ Google Docs rich text conversion
- **`errors.py`**: Centralized error handling and user-friendly messages
- **`constants.py`**: Configuration and scoring constants

---

## 🎯 Quick Start

### 1. Install

See [INSTALLATION.md](INSTALLATION.md) for complete setup guide.

**TL;DR:**
```bash
# Install dependencies
uv sync  # or: pip install -r requirements.txt

# Authenticate (opens browser)
uv run src/drive_synapsis/main_server.py
```

### 2. Configure Gemini CLI

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "/path/to/uv",
      "args": ["run", "--quiet", "/path/to/drive-synapsis/src/drive_synapsis/main_server.py"],
      "env": {"PYTHONUNBUFFERED": "1"}
    }
  }
}
```

### 3. Use!

```
Search my Drive for "Project Plan"
Read document A and summarize it
Create a new doc called "Ideas" with bullet points
Link ./notes.md to Doc B and sync changes
```

---

## 💡 Example Workflows

### Collaborative Document Editing

```
1. Search for "Team Meeting Agenda"
2. Download Doc A to ./meetings/agenda.md with dry_run=False
3. (Edit locally in your favorite editor)
4. Update Doc A from ./meetings/agenda.md (preview diff)
5. Update Doc A from ./meetings/agenda.md with dry_run=False
6. Share updated doc with team@company.com
```

### Data Analysis Pipeline

```
1. Search for "Sales Data 2024"
2. Read spreadsheet A as CSV
3. (AI analyzes the CSV data)
4. Create doc "Sales Analysis - Dec 2024" with findings
5. Create chart in new spreadsheet from analysis
```

### Backup & Archive

```
1. Search for files modified this week
2. Mirror Drive folder "Important Docs" to ./backups/
3. (Backups now tracked and syncable)
```

---

## 🔧 Advanced Features

### Comment Extraction

Download documents with inline comments as Markdown footnotes:

```markdown
This section needs review.[^1]

[^1]: **Jane Doe** (2024-12-01): Please add citations.
```

### Smart Link Rewriting

Links automatically adapt to context:

**In Google Docs:**
```
See [API Docs](https://docs.google.com/document/d/abc123/edit)
```

**Downloaded locally (if linked):**
```
See [API Docs](./docs/api.md)
```

**Uploaded back:**
```
See [API Docs](https://docs.google.com/document/d/abc123/edit)
```

### Multi-Tab Document Support

Handle Google Docs with multiple tabs:

```
Read all tabs from document A
```

Returns organized content from each tab with proper separation.

---

## 🛡️ Safety & Best Practices

### Built-in Safety

1. **Dry-run by default**: All destructive operations preview changes first
2. **Conflict detection**: Warns when remote files changed since last sync
3. **Diff previews**: See exactly what will change before applying
4. **Alias validation**: Prevents accidental operations on wrong files

### Recommended Practices

- ✅ Always preview diffs before syncing
- ✅ Use version control (Git) for local files
- ✅ Link important files for tracked sync
- ✅ Review permissions when sharing
- ✅ Use specific search queries for better results
- ⚠️ Handle sync conflicts carefully
- ⚠️ Use `force=True` only when certain

---

## 🤝 Contributing

Contributions welcome! The modular architecture makes it easy to add features:

- **New client methods**: Add to appropriate mixin in `src/client/`
- **New MCP tools**: Add to relevant `*_tools.py` in `src/server/`
- **New utilities**: Add to `src/utils/`

---

## 📜 License

MIT License - see LICENSE file for details

---

## 🆘 Support

- **Installation help**: See [INSTALLATION.md](INSTALLATION.md)
- **Usage examples**: See [USAGE.md](USAGE.md)
- **Architecture questions**: Check this README's architecture section
- **Issues**: File an issue with detailed reproduction steps

---

## 🎉 What's Next?

This server is **production-ready** with 39 MCP tools. Future enhancements could include:

- Real-time collaboration awareness
- More advanced comment threading
- Google Slides support
- Automated conflict resolution strategies
- Performance analytics

**But it's already comprehensive!** Start using it now to supercharge your AI assistant's Google Drive capabilities.

---

**Built with ❤️ for the MCP community**
