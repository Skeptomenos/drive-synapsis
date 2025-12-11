# Migration Guide

## Upgrading to Anamnesis 4.3+ (Task Awareness)

### What's New in 4.3

- **Enhanced Tasks:** Dependencies, Status, and Workstream fields
- **Status Workflow:** 6-status system (Backlog, Open, In Progress, Blocked, Done, Archive)
- **Kanban Board:** Auto-generated `board.md` for visual progress tracking
- **Workstreams:** Parallel work context management for features and investigations
- **User Commands:** Explicit commands for board and task operations
- **AI-Assisted Task Generation:** Automatic task creation from requirements

### Migration Steps

#### Step 1: Update tasks.md Format

Add Dependencies, Status, and Workstream fields to existing tasks:

**Before (v4.2):**
```markdown
- [ ] **TASK-001:** Implement login
    - **Context/Constraints:** Use Zod for validation
    - **Status:** Pending
```

**After (v4.3+):**
```markdown
- [ ] **TASK-001:** Implement login
    - **Dependencies:** None
    - **Status:** Open
    - **Workstream:** main
    - **Context/Constraints:** Use Zod for validation
```

#### Step 2: Add Status Legend

Add the Status Legend section to the top of your `tasks.md`:

```markdown
## Status Legend

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `Backlog` | Idea captured, not prioritized | Prioritize or park |
| `Open` | Ready to work, dependencies met | Start work |
| `In Progress` | Currently being worked on | Complete or block |
| `Blocked` | Cannot proceed, waiting for dependency | Resolve blocker |
| `Done` | Verified and complete | Archive when ready |
| `Archive` | Historical reference | None |
```

#### Step 3: Add Workstreams Section

Add the Workstreams section to organize your tasks:

```markdown
## Workstreams

| Workstream | Description | Status |
|------------|-------------|--------|
| `main` | Primary project objective | Active |
```

#### Step 4: Generate Initial Board

Ask AI to generate `anamnesis/.context/board.md`:

> "Generate board from my current tasks"

The AI will parse your tasks.md and create a visual kanban board.

#### Step 5: Create Workstreams Directory

Create `anamnesis/.context/workstreams/` directory for parallel work contexts:

```bash
mkdir -p anamnesis/.context/workstreams
```

#### Step 6: Update Active State (Optional)

If you have an existing `active_state.md`, add the workstream reference:

```markdown
### Active Workstream

**Current:** main
**Available:** main

> To switch workstreams, use command: "Switch to [workstream-name]"
> Workstream files: `anamnesis/.context/workstreams/[name].md`
```

### Backward Compatibility

The framework maintains backward compatibility:

- **Missing Dependencies:** Treated as "None"
- **Missing Status:** Treated as "Backlog"
- **Missing Workstream:** Treated as "main"
- **Old Status Values:** See mapping below

### Status Mapping

| Old Status (v4.2) | New Status (v4.3+) |
|-------------------|-------------------|
| Pending | Backlog or Open (depending on dependencies) |
| In Progress | In Progress |
| Blocked | Blocked |
| Done | Done |
| (completed tasks) | Archive |

### New User Commands

After upgrading, you can use these commands:

| Command | Action |
|---------|--------|
| "Generate board" | Regenerate board from tasks |
| "Next task" | Find and start next Open task |
| "Switch to [workstream]" | Change active workstream |
| "Archive done tasks" | Move Done tasks to Archive |
| "Block task [ID]" | Mark task as Blocked |
| "List workstreams" | Show available workstreams |

### New Files and Directories

After migration, your project should include:

```
anamnesis/
├── .context/
│   ├── board.md              # NEW: Kanban board (auto-generated)
│   └── workstreams/          # NEW: Parallel work contexts
│       └── .gitkeep
├── templates/
│   ├── board.md              # NEW: Board template
│   └── workstream.md         # NEW: Workstream template
├── docs/
│   └── MIGRATION.md          # NEW: This file
└── specs/
    └── tasks.md              # UPDATED: New task format
```

### Troubleshooting

**Q: AI doesn't recognize new task fields?**
A: Ensure AGENTS.md and EXECUTION.md are updated to v4.3+. The AI reads these files for task management rules.

**Q: Board.md not generating?**
A: Use explicit command "Generate board" or check that Phase 0.1 in EXECUTION.md includes board generation step.

**Q: Workstreams not working?**
A: Create `anamnesis/.context/workstreams/` directory and add workstream files using the template from `anamnesis/templates/workstream.md`.

**Q: Dependencies not being checked?**
A: Verify EXECUTION.md Phase 2.1 includes the dependency check step. The AI should check `Dependencies` field before selecting a task.

**Q: Tasks showing wrong status?**
A: Ensure you're using the new 6-status vocabulary: Backlog, Open, In Progress, Blocked, Done, Archive.

### Quick Migration Script

For projects with many tasks, you can use this pattern to bulk update:

1. Open `anamnesis/specs/tasks.md`
2. For each task, add:
   - `- **Dependencies:** None` (or identify actual dependencies)
   - Change `- **Status:** Pending` to `- **Status:** Backlog` or `- **Status:** Open`
   - Add `- **Workstream:** main`

3. Ask AI: "Generate board from my current tasks"

### Version History

- **v4.2:** Basic task management with checkboxes
- **v4.3:** Enhanced task awareness with dependencies, status workflow, workstreams, and kanban board
