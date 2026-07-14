---
name: hb-task-step-execute
argument-hint: "[--help] <author/task-id/step-n>"
arguments: step_ref
description: >
  /hb-task-step-execute [--help] <author/task-id/step-n>

  Read plan.md in a step folder and execute the plan, then record an execution summary.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write Edit Bash(*)
---

# hb-task-step-execute

Execute the plan described in `plan.md` for one task step, then write an execution summary file into the step folder.

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

### 3. Read plan

- read `$STEP_PATH/plan.md`
- if the file does not exist:
  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill hb-task-step-execute --outcome failure --task "$TASK_REF" --step "$N"
  ```
  then abort with: `error: plan.md not found in $STEP_PATH — run /hb-task-step-plan first`

### 4. Read facts store

Follow [${CLAUDE_SKILL_DIR}/references/facts-write-subflow.md](references/facts-write-subflow.md) § Part A.

### 5. Execute the plan

- carry out every task described in `plan.md` exactly as specified
- follow all constraints, boundaries, and verification steps stated in the plan
- take `$FACTS` into account when executing the plan — if a fact is relevant to this step's implementation, apply it without requiring it be restated in `plan.md`

### 6. Write execution summary

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step execution-slug
```

- captures the output as `$SLUG`
- read [${CLAUDE_SKILL_DIR}/references/execution-template.md](references/execution-template.md) for the required structure
- write `$STEP_PATH/$SLUG` populated from that template with the factual record of this execution

### 7. Update facts store

Set the caller contract:

- `$CONTEXT_LABEL` = `"this execution"`
- `$SELF_COMMIT` = `false`

Follow [${CLAUDE_SKILL_DIR}/references/facts-write-subflow.md](references/facts-write-subflow.md) § Part B.

### 8. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including all files changed during execution, `$STEP_PATH/$SLUG`, and `.hb/facts.md` if it was changed in the previous step; pass `--tag step-execute`

### 9. Prompt user

Tell the user:

> Step executed. `/clear` this conversation, then run `/hb-flow` to see what to do next.

### 10. Record execution state

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill hb-task-step-execute --outcome success --task "$TASK_REF" --step "$N"
```

## Output

Report the step path, the execution summary path, and the list of changed files. If any command fails, surface the error verbatim to the caller.
