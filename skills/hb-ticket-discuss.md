---
name: hb-ticket-discuss
argument-hint: "[--help]"
description: >
  /hb-ticket-discuss [--help]

  Run hashbuild's interactive ticket-creation flow to produce a standalone ticket
  (not attached to any task or step) and print it for copy-paste. Makes no .hb/ writes.
allowed-tools: Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)
---

# hb-ticket-discuss

Run the interactive ticket-creation flow to produce a standalone `ticket.md` at a scratch path and print it for copy-paste — no task or step folder is created.

## Inputs

| Parameter              | Required | Description                |
| ---------------------- | -------- | -------------------------- |
| `help`, `--help`, `-h` | no       | Print help and exit.       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Generate standalone ticket

- Set `$TARGET_PATH` = `/tmp` (scratch; the generated ticket is standalone — it lives only here and is never moved into `.hb/`).
- Follow [${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](references/interactive-ticket-subflow.md) with:
  - `$TARGET_PATH` = `/tmp`
  - `$TICKET_SUPPLIED` = `false`
  - `$NO_INTERACTIVE` = `false`

  The subflow writes `ticket.md` to `/tmp/ticket.md`.
- Set `$WRITTEN_TICKET` = `/tmp/ticket.md`.

### 3. Emit ticket

- Read `$WRITTEN_TICKET` and print its full content to stdout inside a fenced block so the user can copy-paste it.
- State that this is the standalone ticket — no `.hb/` task or step folder was created — and that this stdout emission is the fallback output path step 1 will keep when no Jira MCP is available.

### 4. Prompt user

Tell the user:

> Standalone ticket is ready above — copy-paste it wherever you need it. Nothing was written to `.hb/`. Pushing this ticket to Jira will be added by step 1 of this task.

## Output

Print the generated ticket content and the scratch path. If any step fails, surface the error verbatim to the caller.
