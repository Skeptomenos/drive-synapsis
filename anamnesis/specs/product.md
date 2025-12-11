# Product Spec (The "Why")

## 1. Core Philosophy
*   **User Persona:** AI Power Users & Developers who want to give their AI assistants (Claude, Gemini) "eyes and hands" in their Google Drive.
*   **Key Value:** **"Your AI, connected to your Drive."** Seamlessly search, read, and edit Drive files using natural language, with a focus on bidirectional syncing for local-first workflows.
*   **Tone/Vibe:** Professional, Safe, Transparent. The tool is a "trustworthy extension" of the user.

## 2. Business Goals
*   [x] **Reduce Friction:** Eliminate the complexity of setting up Google Cloud credentials manually.
*   [ ] **Increase Adoption:** Become the standard "Drive" MCP server for the community.
*   [ ] **Reliability:** Ensure sync operations are idempotent and conflict-aware.

## 3. Anti-Goals (Critical: What we are NOT building)
*   [ ] **We are NOT building a Google Drive UI replacement.** This is a headless server for agents.
*   [ ] **We are NOT a real-time collaborative editor.** We do not support Operational Transformation (OT) or live cursors. Sync is snapshot-based.
*   [ ] **We are NOT a SaaS.** We do not host user data or keys. Everything runs locally.
