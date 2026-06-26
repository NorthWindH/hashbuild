---
name: hb-task-unarchive
argument-hint: "[--help] <author/task-id>"
arguments: task_id
description: >
  /hb-task-unarchive [--help] <author/task-id>

  Unarchive a task by moving its folder from `task/archive` to `task/active`.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---

# hb-task-unarchive

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to move a task from `archive` to `active`.

## Inputs

| Parameter              | Required | Description                                                                                                                                                                                                                 |
| ---------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Task name in `author/abc-123` or `author/abc-123-optional-flavor` format. The flavor is optional — the SDK matches on author and task ID alone. See [${CLAUDE_SKILL_DIR}/references/structure.md](references/structure.md). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                                                                                                 |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Unarchive task

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task unarchive <name>
```

- `<name>` is the task name exactly as received; flavor is optional (e.g. `author/abc-123` or `author/abc-123-some-stuff`)
- the SDK locates the task folder under `task/archive/` and moves it to `task/active/`
- errors if the task is not found, already active, or destination already exists
- capture the paths reported through stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 3. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task; pass `--tag task-unarchive`

### 4. Prompt user

Tell the user:

> Task restored. `/clear` this conversation, then run `/hb-status` to see active tasks or `/hb-task-step-add` to continue working on it.

## Output

Report the restored task path. If any command fails, surface the error verbatim to the caller.
