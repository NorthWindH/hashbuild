---
name: hb-task-step-plan
argument-hint: "[--help] <author/task-id/step-n>"
arguments: step_ref
description: >
  /hb-task-step-plan [--help] <author/task-id/step-n>

  Idempotent. Create or update plan.md in a step folder based on the step's ticket.md and the plan template.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write
---

# hb-task-step-plan

Generate or update the `plan.md` for one task step. Reads `ticket.md` from the step folder and the template from `${CLAUDE_SKILL_DIR}/references/plan-template.md`, then writes `plan.md` into the same step folder.

## Inputs

| Parameter              | Required | Description                                                                                                                                                                |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `step_ref`             | yes\*    | Step reference in `author/task_id/step_n` format. `task_id` flavor is optional. `step_n` accepts: bare integer (`0`), `step-<n>`, or full step name (`step-<n>-<flavor>`). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                                                |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Resolve step folder

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step path <step_ref>
```

- prints the absolute path of the step folder to stdout; capture it as `$STEP_PATH`
- if an error occurs, surface it verbatim and stop

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step number <step_ref>
```

- captures the numeric step number as `$N`
- if an error occurs, surface it verbatim and stop

- set `$TASK_REF` = `step_ref` with the trailing `/<step_n>` segment removed

### 3. Read facts store

Follow [${CLAUDE_SKILL_DIR}/references/facts-write-subflow.md](references/facts-write-subflow.md) § Part A.

### 4. Read inputs

- read `$STEP_PATH/ticket.md` — the acceptance criteria driving this plan
- read `${CLAUDE_SKILL_DIR}/references/plan-template.md` — the structural template to follow

### 5. Generate plan.md

- write `$STEP_PATH/plan.md` using the template structure, filled with content derived from `ticket.md`
- if `plan.md` already exists, update it to reflect the current ticket; preserve any sections that remain accurate
- take `$FACTS` into account when drafting `plan.md` — if a fact is relevant to this step's ticket, reflect it in the plan without requiring it be restated in `ticket.md`

### 6. Update facts store

Set the caller contract:

- `$CONTEXT_LABEL` = `"drafting this plan.md"`
- `$SELF_COMMIT` = `false`

Follow [${CLAUDE_SKILL_DIR}/references/facts-write-subflow.md](references/facts-write-subflow.md) § Part B.

### 7. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including `$STEP_PATH/plan.md` and `.hb/facts.md` if it was changed in the previous step; pass `--tag step-plan`

### 8. Prompt user

Tell the user:

> Plan ready, `present plan` to present the created plan and discuss/update it, or `/clear` this conversation, then run `/hb-flow` to see what to do next.

### 9. Record execution state

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill hb-task-step-plan --outcome success --task "$TASK_REF" --step "$N"
```

## Output

Report the path to the written `plan.md`. If any command fails, surface the error verbatim to the caller.
