---
name: hb-task-step-execute
description: >
  Read plan.md in a step folder and execute the plan, then record an execution summary.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write Edit Bash(*) 
---

# hb-task-step-execute

Execute the plan described in `plan.md` for one task step, then write an execution summary file into the step folder.

## Inputs

| Parameter              | Required | Description                                                                                                                                                         |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `step_ref`             | yes\*    | Step reference in `author/task_id/step_n` format. `task_id` flavor is optional. `step_n` accepts: bare integer (`0`), `step-<n>`, or full step name (`step-<n>-<flavor>`). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                                         |

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Resolve step folder

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step path <step_ref>
```

- prints the absolute path of the step folder to stdout; capture it as `$STEP_PATH`
- if an error occurs, surface it verbatim and stop

### 3. Read plan

- read `$STEP_PATH/plan.md`
- if the file does not exist, abort with: `error: plan.md not found in $STEP_PATH — run /hb-task-step-plan first`

### 4. Execute the plan

- carry out every task described in `plan.md` exactly as specified
- follow all constraints, boundaries, and verification steps stated in the plan

### 5. Write execution summary

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step execution-slug
```

- captures the output as `$SLUG`
- write `$STEP_PATH/$SLUG` with a structured summary of this execution:
  - what was done (tasks completed)
  - outcome per acceptance criterion from `plan.md`
  - any deviations from the plan and their justification
  - commands run and their results where relevant

### 6. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including all files changed during execution and `$STEP_PATH/$SLUG`

## Output

Report the step path, the execution summary path, and the list of changed files. If any command fails, surface the error verbatim to the caller.
