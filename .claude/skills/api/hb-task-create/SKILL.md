---
name: hb-task-create
description: "[API] Atomic operation: create a new hashbuild task directory with proper structure under tasks/active/. Not user-facing — invoked by user-tier skills like hb-new-task and hb-import-ticket. Requires a task_id and task.md content."
---

# hb-task-create

Atomic: create the directory structure for one task and write its `task.md`.

## Shared scripts
- `python .claude/skills/shared/scripts/ensure_dirs.py <task_id>` — creates `tasks/active/<task_id>/` and `tasks/active/<task_id>/steps/`
- `python .claude/skills/shared/scripts/query_tasks.py next-task-id` — get next available TASK-NNN id

## Steps

1. Determine the `task_id`. If not provided by the caller, run `query_tasks.py next-task-id`.
2. Run `ensure_dirs.py <task_id>` to create the directory structure.
3. Write `tasks/active/<task_id>/task.md` using the template below.
4. Output the task path.

## task.md template

```markdown
# <title>

**ID:** <task_id>
**Created:** <ISO date>
**Status:** active

## Description

<description>

## Acceptance Criteria

<criteria — bullet list>

## Source Ticket

<source reference or "none">
```
