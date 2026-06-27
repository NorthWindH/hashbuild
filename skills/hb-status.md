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

Run `hb-sdk summarize --format md` to render and output the status report.

## Inputs

| Parameter              | Required | Description          |
| ---------------------- | -------- | -------------------- |
| `help`, `--help`, `-h` | no       | Print help and exit. |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Render and output status report

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize --format md
```

- captures stdout and writes it directly to the user
- if the command fails, surface the error verbatim and stop

## Output

The filled status report as markdown. No commits or file writes.
