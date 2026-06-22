---
name: hb-task-create
description: >
  Idempotent. Ensure a task skeleton exists for a given fully-qualified task name. Accepts an optional ticket file to seed the task.
---

# hb-task-create

Atomic: call `scripts/hb-sdk` to create or verify the task skeleton for one task.

## Inputs

| Parameter              | Required | Description                                                                                          |
| ---------------------- | -------- | ---------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Fully-qualified task name in `author/abc-123-optional-flavor` format. See `references/structure.md`. |
| `--ticket <path>`      | no       | Path to a ticket file (any format). When provided, `hb-sdk` seeds the task from its content.         |
| `--ticket-overwrite`   | no       | Whether to overwrite ticket file if it already exists. Default: false                                |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                          |

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow `references/skill-help.md`. Stop.

### 2. Create task skeleton

```bash
scripts/hb-sdk task create [--ticket <ticket_path>] <name>
```

- include `--ticket <ticket_path>` only when a ticket file was provided
- include `--ticket-overwrite` only when `--ticket-overwrite` was provided
- `<name>` is the fully-qualified name exactly as received (e.g. `author/abc-123-some-stuff`)
- the SDK is idempotent — safe to call if the skeleton already exists
- capture the paths reported through stdout for use in the next step
- if an error occurs, present error message on stderr verbatim

### 3. Commit

- create a non-step commit by following `references/committing.md` and including any new or changed files related to this task

## Output

Report the task path and changed/created files. If any command fails, surface the error verbatim to the caller.
