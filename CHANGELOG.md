# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.3.0] - 2025-12-09

### Added
- **Enhanced Task Management:** Tasks now include Dependencies, Status, and Workstream fields
- **Status Workflow:** 6-status system (Backlog, Open, In Progress, Blocked, Done, Archive)
- **Kanban Board:** Auto-generated `board.md` for visual progress tracking
- **Workstreams:** Parallel work context management via `.context/workstreams/`
- **User Commands:** Explicit commands for board generation, task management, and workstream switching
- **AI-Assisted Task Generation:** Automatic task creation from requirements in THINKING.md Phase T4.2
- **Migration Guide:** `anamnesis/docs/MIGRATION.md` for upgrading from v4.2

### Changed
- **EXECUTION.md:** Enhanced Phase 0.1 with board generation, Phase 2.1 with dependency checks
- **THINKING.md:** Added Phase T4.2 for AI-assisted task generation
- **AGENTS.md:** Added Task Management section with selection rules and user commands
- **active_state.md template:** Added Active Workstream section
- **tasks.md template:** Complete restructure with Status Legend, Workstreams, and Archive sections

### Templates Added
- `anamnesis/templates/board.md` - Kanban board template
- `anamnesis/templates/workstream.md` - Workstream context template

### Directories Added
- `anamnesis/.context/workstreams/` - Directory for parallel work contexts
- `anamnesis/docs/` - Documentation directory

## [4.2.0] - 2025-11-27

### Added
- Initial release with Spec-Driven Development framework
- THINKING.md and EXECUTION.md directives
- Template system for active_state, handover
- Standards framework (global, python, typescript, rust)
- Spec files (problem, options, requirements, design, tasks, tech, product)
