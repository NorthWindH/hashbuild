---
name: hb-status
argument-hint: "[--help]"
description: >
  /hb-status [--help]

  Report the current state of .hb: initialization, active tasks with step progress,
  archive summary, and recommended next action.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Read
---

# hb-status

Run `hb-sdk summarize` to gather workspace state, then render a status report using
the structure defined in `${CLAUDE_SKILL_DIR}/references/status-template.md`.

## Inputs

| Parameter              | Required | Description          |
| ---------------------- | -------- | -------------------- |
| `help`, `--help`, `-h` | no       | Print help and exit. |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Gather workspace summary

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize
```

- prints a JSON object to stdout; capture and parse it
- the JSON structure is:
  ```
  {
    "initialized": bool,
    "active_tasks": [
      {
        "author": str,
        "task_id": str,
        "task_folder": str,
        "task_path": str,
        "has_ticket": bool,
        "total_steps": int,
        "steps": [
          { "name": str, "has_ticket": bool, "has_plan": bool, "has_execution": bool }
        ],
        "steps_pending_execution": int,
        "next_pending_step": str | null
      }
    ],
    "archive": {
      "count": int,
      "last_archived": str | null   // "author/task_id" (no flavor), or null if empty
    }
  }
  ```
- never exits non-zero; reports `initialized: false` when `.hb/` is absent
- if the command fails, surface the error verbatim and stop

### 3. Read status template

- read `${CLAUDE_SKILL_DIR}/references/status-template.md` for the report structure and Next Action decision tree

### 4. Render and output status report

Produce the report by filling the template with data from the summary JSON:

- **Initialization**: "`.hb/` initialized" if `initialized` is true; otherwise "`.hb/` not found — run `/hb-init`"
- **Active Tasks**: one table with columns Task, Steps pending execution, Total steps — one row per entry in `active_tasks` using `author/task_folder`; omit the section entirely when `active_tasks` is empty
- **Archive**: fill `count` and `last_archived`; omit the "Last archived" row when `last_archived` is null; omit the section entirely when `count` is 0
- **Next Action**: apply the decision tree from the template's `## Next Action` comment — evaluate conditions in order and output the first that applies

Output the rendered report as markdown.

## Output

The filled status report as markdown. No commits or file writes.
