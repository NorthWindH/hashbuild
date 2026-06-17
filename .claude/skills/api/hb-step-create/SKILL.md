---
name: hb-step-create
description: "[API] Atomic operation: create a step directory under an existing task and write its step.md. Not user-facing — invoked by hb-import-steps and hb-import-ticket (when breaking a ticket into steps)."
---

# hb-step-create

Atomic: create one step under a task.

## Shared scripts
- `python .claude/skills/shared/scripts/ensure_dirs.py <task_id> --step <step_id>` — creates `tasks/active/<task_id>/steps/<step_id>/` and `execution/` subdirectory
- `python .claude/skills/shared/scripts/query_tasks.py next-step-id <task_id>` — get next available STEP-NNN id

## Steps

1. Determine `step_id`. If not provided, run `query_tasks.py next-step-id <task_id>`.
2. Run `ensure_dirs.py <task_id> --step <step_id>`.
3. Write `tasks/active/<task_id>/steps/<step_id>/step.md` using template below.
4. Output the step path.

## step.md template

```markdown
# <title>

**ID:** <step_id>
**Task:** <task_id>
**Order:** <n>
**Status:** pending

## Description

<description>

## Source Sub-ticket

<sub-ticket reference or "none">
```
