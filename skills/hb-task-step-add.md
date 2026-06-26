---
name: hb-task-step-add
description: >
  /hb-task-step-add [--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>

  Idempotent. Add the next step folder to an existing task. Accepts an optional ticket file to seed the step.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---

# hb-task-step-add

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to add the next step folder to an existing task.

## Inputs

| Parameter              | Required | Description                                                                                                                                       |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Task name in `author/abc-123` or `author/abc-123-optional-flavor` format. The flavor is optional — the SDK matches on author and task ID alone. See [${CLAUDE_SKILL_DIR}/references/structure.md](references/structure.md). |
| `--flavor <slug>`      | no       | Optional step flavor suffix appended to the step folder name (e.g. `scaffold-routes` → `step-0-scaffold-routes`). Slug chars: `[a-z-]`.           |
| `--ticket <path>`      | no       | Path to a `.md` ticket file. When provided, copied to `ticket.md` inside the new step folder instead of generating the default template.          |
| `--ticket-overwrite`   | no       | Whether to overwrite an existing `ticket.md` if its content differs. Default: false                                                               |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Add step

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step add [--flavor <slug>] [--ticket <ticket_path>] [--ticket-overwrite] <name>
```

- include `--flavor <slug>` only when a flavor was provided
- include `--ticket <ticket_path>` only when a ticket file was provided
- include `--ticket-overwrite` only when `--ticket-overwrite` was provided
- `<name>` is the task name exactly as received; flavor is optional (e.g. `author/abc-123` or `author/abc-123-some-stuff`)
- the SDK reads `next_step` from `.hb-task.json`, creates the folder, then increments `next_step`
- capture the paths reported through stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 3. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this step

### 4. Prompt user

Tell the user:

> Step added. `/clear` this conversation, then: if the step ticket is ready, run `/hb-task-step-plan <step_ref>` to create the implementation plan. If the ticket still needs its acceptance criteria filled in, edit `ticket.md` in the step folder first.

## Output

Report the step path and changed/created files. If any command fails, surface the error verbatim to the caller.
