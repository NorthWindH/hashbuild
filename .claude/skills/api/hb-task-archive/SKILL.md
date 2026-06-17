---
name: hb-task-archive
description: "[API] Atomic operation: move a task from tasks/active/ to tasks/archive/ and update its status field in task.md. Not user-facing — invoked by hb-complete-task."
---

# hb-task-archive

Atomic: move completed task from active to archive.

## Shared scripts
- `python .claude/skills/shared/scripts/ensure_dirs.py <task_id> --archive` — creates `tasks/archive/<task_id>/`
- `python .claude/skills/shared/scripts/query_tasks.py status <task_id>` — verify task exists and is active

## Steps

1. Verify task exists: `query_tasks.py status <task_id>`. Abort if not active.
2. Create archive destination: `ensure_dirs.py <task_id> --archive`.
3. Move: `mv tasks/active/<task_id>/* tasks/archive/<task_id>/` (preserving all contents including steps).
4. Remove now-empty active dir: `rmdir tasks/active/<task_id>/steps tasks/active/<task_id>` (only if empty).
5. Update `tasks/archive/<task_id>/task.md`: change `**Status:** active` → `**Status:** archived` and append `**Archived:** <ISO date>`.
6. Confirm move succeeded and output archive path.
