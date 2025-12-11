# Project Objective

> **Purpose:** This is the living objective for this project. It evolves as understanding deepens through iteration.
> **Read this:** At session start to orient on the big picture.

---

## Current Idea

Build a robust, production-grade Model Context Protocol (MCP) server that empowers AI agents to interact with Google Drive. Key capabilities include bidirectional synchronization between local Markdown and Google Docs, intelligent context-aware search, and comprehensive file management. The system prioritizes safety ("dry-run" by default) and user experience (interactive setup wizards).

## Evolution

- 2024-12: Initial release with core MCP tools (Search, Read, Sync).
- 2025-01: Added interactive setup wizard and `~/.drive-synapsis` credential management.

## Success Looks Like

- [x] **Seamless Setup:** Users can install and configure in <2 minutes via CLI wizard.
- [ ] **Robust Sync:** Bidirectional sync handles conflicts and formatting fidelity (Markdown <-> Docs) with >95% accuracy.
- [ ] **Smart Search:** Users can find relevant documents using natural language queries.
- [ ] **Safe Operations:** No accidental data loss; all destructive actions have clear confirmations and rollbacks.

## Constraints

- **Credential Security:** Secrets MUST be stored in `~/.drive-synapsis`, not in the project root.
- **BYOK:** "Bring Your Own Keys" model; we do not host a central auth service.
- **Dependencies:** Minimize heavy dependencies; use `uv` for package management.

## Current Phase

**Phase 2: Polish & Documentation.**
We have a functional server and a new installation wizard. The focus is now on enriching the documentation, ensuring the "Anamnesis" framework is active, and refining the user journey.
