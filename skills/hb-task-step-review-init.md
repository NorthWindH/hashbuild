---
name: hb-task-step-review-init
argument-hint: "[--help] <author/task-id/step-n>"
arguments: step_ref
description: >
  /hb-task-step-review-init [--help] <author/task-id/step-n>

  Idempotent. Create review.md in a step folder seeded with one placeholder review item. Does nothing if review.md already exists with required structure.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write
---

# hb-task-step-review-init

Create `review.md` in a step folder, seeded from [${CLAUDE_SKILL_DIR}/references/review-template.md](references/review-template.md) with one placeholder review item. Idempotent — skips creation if `review.md` already exists with the required structure.

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

### 2–4. Resolve step folder, check for existing review.md, and create review.md

!`cat ${CLAUDE_SKILL_DIR}/references/review-init-subflow.md`

### 5. Notify user

Tell the user:

> `review.md` created at `$STEP_PATH/review.md`. Fill in the review items under `## Notes` — one `### STEP-N-REVIEW-M:` heading per concern, with body per the commented example at the bottom of the file. **Do not edit the `## Status` table** — it is maintained by the hashbuild skills.
>
> You can also leave `TODO REVIEW` comments anywhere in the codebase (e.g. `// TODO REVIEW: this function duplicates logic in X`). When you run `/hb-task-step-review-address`, those comments are automatically picked up — from the HEAD commit and from any uncommitted changed files — and added as review items, then deleted from the source after they are addressed. Pass `--no-todo-scan` to skip this behavior, or `--commits N` to scan more than one commit.
>
> When done, `/clear` this conversation, then run `/hb-task-step-review-address <step_ref>` to work through the review items.

Also show the user:

- README-1 defined in subflow step C above
- README-2 defined in subflow step C above

### 6. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including `$STEP_PATH/review.md`; pass `--tag step-review`

### 7. Record execution state

- set `$TASK_REF` = `step_ref` with the trailing `/<step_n>` segment removed

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill hb-task-step-review-init --outcome success --task "$TASK_REF" --step "$N"
```

## Output

Report the path to the created `review.md`. If any command fails, surface the error verbatim to the caller.
