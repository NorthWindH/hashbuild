---
name: hb-task-create
description: "Ensure a task skeleton exists for a given fully-qualified task name. Idempotent. Accepts an optional ticket file to seed the task."
---

# hb-task-create

Atomic: call `scripts/hb-sdk` to create or verify the task skeleton for one task.

## Inputs

| Parameter | Required | Description                                                                                          |
| --------- | -------- | ---------------------------------------------------------------------------------------------------- |
| `name`    | yes      | Fully-qualified task name in `author/abc-123-optional-flavor` format. See `references/structure.md`. |
| `ticket`  | no       | Path to a ticket file (any format). When provided, `hb-sdk` seeds the task from its content.         |

## Steps

### 1. Create task skeleton

```bash
scripts/hb-sdk task create [--ticket <ticket_path>] <name>
```

- include `--ticket <ticket_path>` only when a ticket file was provided
- `<name>` is the fully-qualified name exactly as received (e.g. `author/abc-123-some-stuff`)
- the SDK is idempotent — safe to call if the skeleton already exists
- capture the task path returned from stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 2. Commit skeleton

-

Stage and commit the new task files:

```bash
git add <task_path>
git commit -m "<task_id>: create task skeleton."
```

- `<task_path>` is the path printed by `hb-sdk` in step 1.
- `<task_id>` is the ticket ID extracted from `name` (e.g. `abc-123`).
- Follow commit message format in `references/commit-message-format.md`.
- Skip commit if `hb-sdk` indicated the skeleton already existed (idempotent no-op).

## Output

Report the task path. If any command fails, surface the error verbatim to the caller.
