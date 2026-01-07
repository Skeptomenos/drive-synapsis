# Active State

> **Update:** At end of session.
> **Read:** At start of session.

## Current Context
We have just completed a major refactor of the installation process. The "Interactive Configuration Wizard" (`drive-synapsis-config`) is now the primary way for users to set up credentials and configure their AI clients. We are currently enriching the "Anamnesis" operational framework to ensure future development is grounded in this project's specific context.

## Current Focus
- [x] Implement interactive `config_gen.py`.
- [x] Update documentation (`README`, `INSTALLATION`, `SETUP_GUIDE`) to reflect new setup flow.
- [x] Enrich `AGENTS.md` and `mission.md` with project context.
- [ ] Continue enriching `anamnesis/specs/` (Product, Tech Stack) if needed.

## Recent Accomplishments
- **Interactive Wizard:** Replaced manual JSON copying with a CLI wizard that moves secrets to `~/.config/drive-synapsis` and auto-configures Claude/Gemini/OpenCode.
- **Safety Upgrade:** Moved credentials out of the project root to `~/.config/drive-synapsis` for better security.
- **Framework Initialization:** Populated `AGENTS.md` and `mission.md` with real project data.

## Open Questions / Blockers
- None at this time.

## Next Session Goal
- Review `anamnesis/specs/` to ensure technical specs match the actual codebase (e.g., verifying `fastmcp` usage in tech specs).
