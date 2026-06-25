---
name: hb-task-archive
description: >
  Archive a task by moving its folder from `task/active` to `task/archive`.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---

# hb-task-archive

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to move a task from `active` to `archive`.

## Inputs

| Parameter              | Required | Description                                                                                                                                       |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Task name in `author/abc-123` or `author/abc-123-optional-flavor` format. The flavor is optional — the SDK matches on author and task ID alone. See [${CLAUDE_SKILL_DIR}/references/structure.md](references/structure.md). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Archive task

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task archive <name>
```

- `<name>` is the task name exactly as received; flavor is optional (e.g. `author/abc-123` or `author/abc-123-some-stuff`)
- the SDK locates the task folder under `task/active/` and moves it to `task/archive/`
- errors if the task is not found, already archived, or destination already exists
- capture the paths reported through stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 3. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task

### 4. Prompt user

Tell the user:

> Task archived. `/clear` this conversation, then run `/hb-status` to see remaining active tasks and decide what to work on next, or `/hb-task-create` to start a new task.

## Output

Report the archived task path. If any command fails, surface the error verbatim to the caller.
