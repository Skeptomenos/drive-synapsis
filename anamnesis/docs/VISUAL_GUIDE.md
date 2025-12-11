# Visual Guide to Anamnesis Framework

> **Purpose:** Visual reference for humans to understand framework flows and relationships.
> **Note:** This file is NOT loaded by AI. It contains diagrams for human understanding only.

---

## Framework Overview

```mermaid
graph TB
    subgraph "Anamnesis Framework"
        A[AGENTS.md<br/>Entry Point] --> B[.context/<br/>State Management]
        A --> C[directives/<br/>AI Behavior]
        A --> D[standards/<br/>Code Quality]
        A --> E[specs/<br/>Specifications]
        A --> F[templates/<br/>File Templates]
    end
    
    subgraph "State Files"
        B --> B1[mission.md<br/>Living Objective]
        B --> B2[active_state.md<br/>Current Session]
        B --> B3[handover.md<br/>Session Handover]
        B --> B4[board.md<br/>Kanban Board]
        B --> B5[workstreams/<br/>Parallel Contexts]
    end
    
    subgraph "Directives"
        C --> C1[THINKING.md<br/>First Principles]
        C --> C2[EXECUTION.md<br/>Build & Deliver]
    end
    
    subgraph "Specifications"
        E --> E1[problem.md<br/>Problem Definition]
        E --> E2[options.md<br/>Solution Options]
        E --> E3[requirements.md<br/>EARS Syntax]
        E --> E4[design.md<br/>Architecture]
        E --> E5[tasks.md<br/>Implementation Plan]
        E --> E6[tech.md<br/>Technical Stack]
        E --> E7[product.md<br/>Product Definition]
    end
```

---

## Thinking Phase Flow

```mermaid
graph LR
    subgraph "Phase T1: Problem Decomposition"
        T1[Strip to<br/>Fundamentals] --> T1_2[Challenge<br/>Assumptions] --> T1_3[Identify<br/>Physics]
    end
    
    subgraph "Phase T1-RCA: Root Cause Analysis"
        RCA1[Expected vs<br/>Actual] --> RCA2[Trace<br/>Data Path] --> RCA3[Challenge<br/>Obvious] --> RCA4[Formulate<br/>Hypothesis]
    end
    
    subgraph "Phase T2: User Understanding"
        T2_1[Empathize] --> T2_2[Define<br/>Problem]
    end
    
    subgraph "Phase T3: Solution Exploration"
        T3_1[Generate<br/>Options] --> T3_2[Evaluate<br/>Constraints] --> T3_3[Consensus<br/>Gate]
    end
    
    subgraph "Phase T4: Transition"
        T4_1[Required<br/>Artifacts] --> T4_2[Task<br/>Generation] --> T4_3[Transition<br/>Checklist] --> T4_4[The<br/>Handshake]
    end
    
    T1 --> T2_1
    T1_3 --> RCA1
    T2_2 --> T3_1
    T3_3 --> T4_1
    
    T4_4 --> EXEC[EXECUTION<br/>Phase]
    
    T1_3 -.-> T1
    RCA4 -.-> T1
```

---

## Execution Phase Flow

```mermaid
graph TB
    subgraph "Phase 0: Context & State"
        E0[Environment<br/>Check] --> E0_2[Check<br/>State] --> E0_3[Generate<br/>Board]
    end
    
    subgraph "Phase 1: Specification & Planning"
        E1[Spec<br/>Loop] --> E1_2[Recursive<br/>Decomposition] --> E1_3[Modularity<br/>Design] --> E1_4[Radical<br/>Simplicity] --> E1_5[Consensus<br/>Gate]
    end
    
    subgraph "Phase 2: Build & Implement"
        E2[Read<br/>Tasks] --> E2_2[Implement<br/>Task] --> E2_3[Verify<br/>Result] --> E2_4[Mark<br/>Done] --> E2_5[Unblock<br/>Check] --> E2_6[Update<br/>Board]
    end
    
    subgraph "Phase 3: Verify & Secure"
        E3[Unit<br/>Tests] --> E3_2[Contract<br/>Tests] --> E3_3[Drift<br/>Detection]
    end
    
    subgraph "Phase 4: Delivery & Epilogue"
        E4[Documentation<br/>Sync] --> E4_2[Reflective<br/>Learning] --> E4_3[Archival<br/>Rotation]
    end
    
    subgraph "Escape & Return Paths"
        OODA[OODA<br/>Loop] -.-> E2_2
        RETURN[Return to<br/>THINKING] -.-> E1
    end
    
    E0 --> E1
    E1_5 --> E2
    E2_6 --> E3
    E3_3 --> E4
```

---

## Task State Machine

```mermaid
stateDiagram-v2
    [*] --> Backlog: New idea
    Backlog --> Open: Dependencies met
    Open --> InProgress: Work started
    InProgress --> Blocked: Dependency fails
    InProgress --> Done: Task complete
    Blocked --> Open: Dependencies resolved
    Done --> Archive: Periodic cleanup
    Archive --> [*]
```

---

## Session Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant AI as AI Agent
    participant Context as .context/
    participant Specs as anamnesis/specs/
    participant Directives as directives/

    User->>AI: Request

    rect rgb(40, 40, 40)
    Note right of AI: CONTEXT (Phase 0)
    AI->>Context: Load mission & handover
    AI->>Directives: Read THINKING.md
    end

    alt Complex Task
        rect rgb(60, 30, 70)
        Note right of AI: THINKING (Phases T1-T4)
        AI->>AI: First Principles decomposition
        AI->>Specs: Draft problem.md, options.md
        AI->>User: 🛑 Consensus Gate - WAIT
        end
        
        User->>AI: Approved

        rect rgb(30, 50, 80)
        Note right of AI: EXECUTION (Phases 0-4)
        AI->>Directives: Read EXECUTION.md
        loop Task by Task
            AI->>Specs: Read → Build → Test → Mark Done
            opt 3+ Failures
                AI-->>AI: OODA Loop
            end
        end
        end

        rect rgb(30, 70, 40)
        Note right of AI: EPILOGUE (Phase 4)
        AI->>AI: T-RFL: Synthesize learnings
        AI->>Context: Archive state, update handover
        AI->>User: Session complete
        end
    else Simple Task
        AI->>User: Answer (Escape Hatch)
    end
```

---

## File Relationships

```mermaid
graph LR
    subgraph "Entry Points"
        AGENTS[AGENTS.md<br/>AI Entry Point]
        CLAUDE[CLAUDE.md<br/>Claude Code Wrapper]
        GEMINI[GEMINI.md<br/>Gemini CLI Wrapper]
    end
    
    subgraph "Living State"
        MISSION[.context/mission.md<br/>Project Objective]
        ACTIVE[.context/active_state.md<br/>Current Session]
        HANDOVER[.context/handover.md<br/>Previous Session]
        BOARD[.context/board.md<br/>Task Progress]
    end
    
    subgraph "Specifications"
        PROBLEM[specs/problem.md<br/>Problem Definition]
        OPTIONS[specs/options.md<br/>Solution Options]
        REQUIRE[specs/requirements.md<br/>EARS Rules]
        DESIGN[specs/design.md<br/>Architecture]
        TASKS[specs/tasks.md<br/>Implementation Plan]
        TECH[specs/tech.md<br/>Technical Stack]
        PRODUCT[specs/product.md<br/>Product Definition]
    end
    
    subgraph "Wisdom"
        LEARNINGS[PROJECT_LEARNINGS.md<br/>Accumulated Wisdom]
        DECISIONS[DECISION_LOG.md<br/>Architectural Decisions]
    end
    
    AGENTS --> MISSION
    AGENTS --> ACTIVE
    ACTIVE --> HANDOVER
    ACTIVE --> BOARD
    
    AGENTS --> PROBLEM
    PROBLEM --> OPTIONS
    OPTIONS --> REQUIRE
    REQUIRE --> DESIGN
    DESIGN --> TASKS
    TECH --> TASKS
    PRODUCT --> TASKS
    
    ACTIVE --> LEARNINGS
    ACTIVE --> DECISIONS
```

---

## Consensus Gate Handshake

```mermaid
sequenceDiagram
    participant AI as AI Agent
    participant User
    
    rect rgb(60, 30, 70)
    Note right of AI: PLANNING COMPLETE
    AI->>AI: Generated plan and specs
    AI->>User: Present summary with:
        - Problem definition
        - Options considered
        - Recommended approach
        - Trade-offs accepted
    AI->>User: "Does this framing match your understanding?"
    AI->>User: "Should we proceed with this approach?"
    Note right of AI: 🛑 MANDATORY STOP
    end
    
    User->>AI: "Approved" / "Proceed" / "Go"
    
    rect rgb(30, 50, 80)
    Note right of AI: EXECUTION PHASE
    AI->>AI: Begin implementation
    end
```

---

## OODA Debugging Loop

```mermaid
graph TB
    subgraph "OODA Loop"
        O[Observe<br/>Gather Evidence] --> O2[Orient<br/>Update Mental Model] --> O3[Decide<br/>Form Hypothesis] --> O4[Act<br/>Test Change]
    end
    
    subgraph "After 3 Failures: Stop-Gap"
        O4 --> SG[Assess<br/>Confidence]
        SG --> SG1[< 50%<br/>Return to Thinking]
        SG --> SG2[50-80%<br/>Consult User]
        SG --> SG3[> 80%<br/>Continue with Justification]
    end
    
    SG1 --> O
    SG2 --> O
    SG3 --> O4
```

---

## Workstream & Dependency Management

```mermaid
graph TB
    subgraph "Task Dependencies"
        T1[TASK-001<br/>Foundation] --> T2[TASK-002<br/>Build on T1]
        T1 --> T3[TASK-003<br/>Uses T1]
        T2 --> T4[TASK-004<br/>Needs T2]
        T3 --> T5[TASK-005<br/>Depends on T3]
    end
    
    subgraph "Workstreams"
        WS1[main<br/>Primary Objective]
        WS2[docs<br/>Documentation]
        WS3[feature-x<br/>Specific Feature]
        WS4[bug-fix<br/>Issue Resolution]
    end
    
    subgraph "Task Status Flow"
        BACKLOG[Backlog] --> OPEN[Open<br/>Dependencies Met]
        OPEN --> INPROGRESS[In Progress<br/>Working]
        INPROGRESS --> BLOCKED[Blocked<br/>Waiting]
        BLOCKED --> OPEN
        INPROGRESS --> DONE[Done<br/>Complete]
        DONE --> ARCHIVE[Archive<br/>Historical]
    end
```

---

## How to Use This Guide

1. **Framework Overview** - Understand all components and their relationships
2. **Phase Flows** - See detailed flow of THINKING and EXECUTION phases
3. **Task State Machine** - Understand task lifecycle and valid transitions
4. **Session Lifecycle** - See complete interaction from request to completion
5. **File Relationships** - Understand how different files connect and influence each other
6. **Specific Patterns** - Deep dive into Consensus Gate, OODA Loop, and Workstream management

For detailed instructions, see the directive files:
- `directives/THINKING.md` - First principles and design thinking
- `directives/EXECUTION.md` - Build, test, and delivery protocols