# Hashbuild

Hashbuild is a structured workflow framework for AI-assisted software development. It adds a set of slash commands (skills) to your AI coding agent that guide you and the agent through a disciplined task lifecycle: create a task, break it into steps, plan and execute each step, optionally review the result, then archive when done.

Each skill is a focused, atomic operation. Each step in the lifecycle produces a durable artifact — a ticket, a plan, an execution summary, a review — that keeps work grounded and auditable across conversations.

**Supported harnesses:** Claude Code · OpenCode

---

## Skills

| Skill                          | What it does                                                         |
| ------------------------------ | -------------------------------------------------------------------- |
| `/hb-init`                     | Initialize `.hb/` in your project (idempotent, run once per project) |
| `/hb-status`                   | Show workspace state and recommended next action                     |
| `/hb-task-create`              | Create a task skeleton                                               |
| `/hb-task-plan`                | Analyze task ticket vs. step tickets; create steps for any gaps      |
| `/hb-task-step-add`            | Add the next step folder to a task                                   |
| `/hb-task-step-plan`           | Write `plan.md` for a step from its `ticket.md`                      |
| `/hb-task-step-execute`        | Execute a step's `plan.md` and record an execution summary           |
| `/hb-task-step-review-init`    | Create `review.md` in a step folder                                  |
| `/hb-task-step-review-address` | Normalize and address all open review items                          |
| `/hb-task-archive`             | Move a completed task from active to the archive                     |

---

## Installation

**Prerequisites:** Python 3.10+ and Claude Code or OpenCode.

Clone this repository and run the installer from its root:

```bash
python install
```

The installer auto-detects your installed harnesses (`~/.claude` for Claude Code, `~/.config/opencode` for OpenCode), symlinks the skills into your harness's skills directory, and patches its `settings.json` with the read permissions the skills require.

To target a specific harness explicitly:

```bash
python install --harness claude
python install --harness opencode
```

To uninstall:

```bash
python install --uninstall
```

---

## Getting started

### 1. Initialize your project

In your project directory:

```
/hb-init
```

Creates `.hb/` at the project root and commits it. Run once per project.

### 2. Write a ticket (optional but recommended)

A ticket is a Markdown file that defines what a task must achieve. Three sections:

```markdown
# Background

One sentence (or more) on what you need and why.

# Acceptance Criteria

1. Concrete, checkable condition — "input X produces output Y"
2. Another criterion

# Out of scope

- What this task deliberately does not do
```

### 3. Create a task

Task names follow the format `author/prefix-123[-optional-flavor]`:

```
/hb-task-create author/abc-123-my-feature --ticket ticket.md
```

Creates `.hb/task/active/author/abc-123-my-feature/` with your ticket seeded in, and commits the skeleton.

### 4. Plan the task

```
/hb-task-plan author/abc-123
```

Reads your task ticket's acceptance criteria, compares them against any existing step tickets, and interactively creates steps to cover the gaps. Each step gets a scoped `ticket.md`.

### 5. Plan and execute each step

For each step in order, `/clear` between each skill invocation to keep context fresh:

```
/hb-task-step-plan author/abc-123/0
```

Reads the step's `ticket.md` and writes `plan.md` — a detailed, mechanical implementation plan.

```
/hb-task-step-execute author/abc-123/0
```

Carries out `plan.md` and writes an `execution-*.md` summary recording what was built, any deviations from the plan, and verification evidence.

Optionally, start a code review after execution:

```
/hb-task-step-review-init author/abc-123/0
```

Fill in your review concerns in `review.md`. You can also leave `TODO REVIEW` comments anywhere in the codebase (e.g. `// TODO REVIEW: this duplicates logic in X`) and commit them — they are automatically picked up from the HEAD commit and added as review items when you run the next command. Then:

```
/hb-task-step-review-address author/abc-123/0
```

`TODO REVIEW` comments are deleted from the source files once their review item is addressed. Pass `--no-todo-scan` to skip comment scanning, or `--commits N` to scan more than one commit.

Review is iterative — add more concerns and re-run `/hb-task-step-review-address` as needed.

Repeat for each step. Add more steps at any time with `/hb-task-step-add` or update a task's ticket.md then `/hb-task-plan` again to cover any new gaps.

### 6. Archive the task

When all steps are done:

```
/hb-task-archive author/abc-123
```

Moves the task from `.hb/task/active/` to `.hb/task/archive/`.

### Check status at any time

```
/hb-status
```

Shows active tasks with step progress, archive summary, and a recommended next action.

---

## Lifecycle

```
/hb-init
    │
    ▼
[.hb/ initialized]
    │
    │  /hb-task-create [--ticket ticket.md]
    ▼
[task created — no steps]
    │
    │  /hb-task-plan                   ◀──── /hb-task-step-add
    ▼                                         (add steps manually
[steps created]                                or fill gaps later)
    │
    │  for each step:
    │  ┌─────────────────────────────────────────────────────────┐
    │  │                                                         │
    │  │  [step-N created — ticket.md seeded]                    │
    │  │       │                                                 │
    │  │       │  (edit ticket.md if needed)                     │
    │  │       │                                                 │
    │  │       │  /hb-task-step-plan                             │
    │  │       ▼                                                 │
    │  │  [plan.md written]                                      │
    │  │       │                                                 │
    │  │       │  /hb-task-step-execute                          │
    │  │       ▼                                                 │
    │  │  [execution-*.md written]                               │
    │  │       │                                                 │
    │  │       │         ╔══ optional review ══╗                 │
    │  │       │         ║                     ║                 │
    │  │       ├────────▶║ /hb-task-step-      ║                 │
    │  │       │         ║   review-init       ║                 │
    │  │       │         ║   (fill review.md)  ║                 │
    │  │       │         ║ /hb-task-step-      ║                 │
    │  │       │         ║   review-address    ║                 │
    │  │       │         ║  (repeat as needed) ║                 │
    │  │       │         ╚═════════════════════╝                 │
    │  │       │                                                 │
    │  │       ▼                                                 │
    │  │  [step done] ──────────────── next step ───────────────▶│
    │  │                                                         │
    │  └─────────────────────────────────────────────────────────┘
    │
    │  /hb-task-archive
    ▼
[archived]
```

---

## File structure

```
.hb/
└── task/
    ├── active/
    │   └── <author>/
    │       └── <task_id>[-flavor]/
    │           ├── .hb-task.json      task metadata
    │           ├── ticket.md          task-level acceptance criteria
    │           └── step-N[-flavor]/
    │               ├── ticket.md      step acceptance criteria
    │               ├── plan.md        implementation plan
    │               ├── execution-<timestamp>.md   what was built + verification
    │               └── review.md      review items and dispositions
    └── archive/
        └── <author>/
            └── <task_id>[-flavor]/
                └── ...
```
