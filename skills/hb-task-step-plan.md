---
name: hb-task-step-plan
description: >
  Idempotent. Create or update plan.md in a step folder based on the step's ticket.md and the plan template.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write
---

# hb-task-step-plan

Generate or update the `plan.md` for one task step. Reads `ticket.md` from the step folder and the template from `${CLAUDE_SKILL_DIR}/references/plan-template.md`, then writes `plan.md` into the same step folder.

## Inputs

| Parameter              | Required | Description                                                                                                                                          |
| ---------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `step_ref`             | yes\*    | Step reference in `author/task_id/step_n` format. `task_id` flavor is optional. `step_n` accepts: bare integer (`0`), `step-<n>`, or full step name (`step-<n>-<flavor>`). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                          |

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Resolve step folder

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step path <step_ref>
```

- prints the absolute path of the step folder to stdout; capture it as `$STEP_PATH`
- if an error occurs, surface it verbatim and stop

### 3. Read inputs

- read `$STEP_PATH/ticket.md` — the acceptance criteria driving this plan
- read `${CLAUDE_SKILL_DIR}/references/plan-template.md` — the structural template to follow

### 4. Generate plan.md

- write `$STEP_PATH/plan.md` using the template structure, filled with content derived from `ticket.md`
- if `plan.md` already exists, update it to reflect the current ticket; preserve any sections that remain accurate

### 5. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including `$STEP_PATH/plan.md`

### 6. Prompt user

Tell the user:

> Plan ready. `/clear` this conversation, then run `/hb-task-step-execute <step_ref>` to carry out the plan.

## Output

Report the path to the written `plan.md`. If any command fails, surface the error verbatim to the caller.
