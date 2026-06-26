---
name: hb-task-create
argument-hint: "[--help] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>"
arguments: task_id
description: >
  /hb-task-create [--help] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>

  Idempotent. Ensure a task skeleton exists for a given fully-qualified task name. Accepts an optional ticket file to seed the task.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)
---

# hb-task-create

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to create or verify the task skeleton for one task.

## Inputs

| Parameter              | Required | Description                                                                                                                                       |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Fully-qualified task name in `author/abc-123-optional-flavor` format. See [${CLAUDE_SKILL_DIR}/references/structure.md](references/structure.md). |
| `--ticket <path>`      | no       | Path to a ticket file (must be `.md`). When provided, `hb-sdk` seeds the task from its content.                                                   |
| `--ticket-overwrite`   | no       | Whether to overwrite ticket file if it already exists. Default: false                                                                             |
| `--no-interactive`     | no       | Skip interactive ticket creation. Creates a skeleton only, with no ticket.                                                                        |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Flag precedence / interactive ticket

Set:

- `$TICKET_SUPPLIED` = `true` if `--ticket <path>` was provided; otherwise `false`
- `$NO_INTERACTIVE` = `true` if `--no-interactive` was provided; otherwise `false`

Evaluate in order (first match wins):

1. **`$TICKET_SUPPLIED` is `true`** — proceed to Step 3; pass `--ticket <ticket_path>` to the SDK as today.
2. **`$NO_INTERACTIVE` is `true`** — skeleton-only mode; proceed to Step 3 without a ticket.
3. **Neither flag** — interactive mode:
   a. Set `$TARGET_PATH` = `/tmp`.
   b. Follow [${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](references/interactive-ticket-subflow.md) with:
   - `$TARGET_PATH` = `/tmp`
   - `$TICKET_SUPPLIED` = `false`
   - `$NO_INTERACTIVE` = `false`

   The subflow writes `ticket.md` to `/tmp/ticket.md`.
   c. Set `$WRITTEN_TICKET` = `/tmp/ticket.md`.
   d. Proceed to Step 3 with `--ticket $WRITTEN_TICKET`.

### 3. Create task skeleton

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task create [--ticket <ticket_path>] <name>
```

- include `--ticket <ticket_path>` when `$TICKET_SUPPLIED` is `true` (use user-supplied path) or when interactive mode ran (use `$WRITTEN_TICKET`); omit in skeleton-only mode
- include `--ticket-overwrite` only when `--ticket-overwrite` was provided
- `<name>` is the fully-qualified name exactly as received (e.g. `author/abc-123-some-stuff`)
- the SDK is idempotent — safe to call if the skeleton already exists
- capture the paths reported through stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 4. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task; pass `--tag task-create`
- when interactive mode ran (Step 2, case 3): also stage the permanent `ticket.md` path reported by the SDK in Step 3 (not the temporary `$WRITTEN_TICKET`)

### 5. Prompt user

**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Task and ticket created. `/clear` this conversation, then run `/hb-task-plan <name>` to analyze acceptance criteria and create step tickets. When steps are ready, run `/hb-task-step-plan <name/step-n>` for each step.

**All other modes (skeleton-only or `--ticket` supplied):**

> Task created. `/clear` this conversation, then: if you have a task `ticket.md`, run `/hb-task-plan <name>` to analyze acceptance criteria and create steps to cover them. If not, write a `ticket.md` first (Background, Acceptance Criteria, Out of scope), then run `/hb-task-plan`. To add the first step manually instead, run `/hb-task-step-add <name>`.

## Output

Report the task path and changed/created files. If any command fails, surface the error verbatim to the caller.
