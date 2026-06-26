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
  ```json
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
          {
            "name": str,
            "has_ticket": bool,
            "has_plan": bool,
            "has_execution": bool,
            "has_review": bool,
            "status": str
          }
        ],
        "steps_skeleton": int,
        "steps_ticketed": int,
        "steps_planned": int,
        "steps_executed": int,
        "steps_review_open": int,
        "steps_reviewed": int,
        "steps_needs_review": [str],
        "steps_needs_work": [str],
        "next_pending_step": str | null
      }
    ],
    "archive": {
      "count": int,
      "recent": [
        { "author": str, "task_id": str, "task_folder": str }
      ]
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
- **Active Tasks**: one table with columns Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total — one row per entry in `active_tasks` using `author/task_folder`; show `—` for any count column that is zero (Total column always shows the raw integer); below each row render two indented lists (each omitted when the corresponding array is empty): **Needs review** (names from `steps_needs_review`) and **Needs work** (names from `steps_needs_work`); omit the section entirely when `active_tasks` is empty
- **Archive**: render a count-only row (`Archived tasks | <count>`) then a bulleted list of `author/task_folder` from `archive.recent` (up to 5 entries); omit the section entirely when `archive.recent` is empty
- **Next Action**: apply the decision tree from the template's `## Next Action` comment — evaluate conditions in order and output the first that applies

Output the rendered report as markdown.

## Output

The filled status report as markdown. No commits or file writes.
