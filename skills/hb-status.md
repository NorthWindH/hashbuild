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

- if the command fails, surface the error verbatim and stop
- captures stdout as $SUMMARY_MD
- read $SUMMARY_MD and use judgement to add any natural language take aways or summary then store those as $ADDITIONS

### 3. Print
- print out the following:
  ```
  <output_format>
  $SUMMARY_MD

  ---

  $ADDITIONS
  </output_format>
  ```
