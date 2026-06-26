---
applies_to: "hb-* skills"
enforcement: "MUST follow these rules exactly when executing any skill that starts with hb-"
---

# Committing

To generate a commit message, use `${CLAUDE_SKILL_DIR}/scripts/hb-sdk`.

## Rules

- a single commit should be done at the end of the execution of any skill that starts with `hb-` if any relevant files have changed
- skills that operate on a single task step (any that start with `hb-step`) should include step number
  - examples:
    - hb-step-create
    - hb-step-remove
    - hb-step-plan
    - hb-step-execute
    - hb-step-address-review
  - all other skills should NOT include step number
- some skills may require intemediate commits; defer to instructions in those skills

## Process

### 1. Stage relevant files ONLY

1. [IDENTIFY] identify currently staged and changed files:
   `git status --short -b`
   - first line reports branch; if default branch (typically `master` or `main`), notify user
   - following lines show file statuses; first 2 characters indicate file status:
     - left character is staged status
     - right character is unstaged status
     - common statuses:
       - `??`: untracked file
       - `A `: staged new file
       - `M `: staged file modification to committed file
       - `D `: staged file deletion of committed file
       - ` M`: unstaged modifications to committed file
       - ` D`: unstaged deletion of committed file
     - less common status combinations:
       - one of `A`, `M`, `D` as first character, `M` as second character:
         staged new file or modifications to committed file then unstaged modifications added
       - one of `A`, `M`, `D` as first character, `D` as second character:
         staged new file or modifications to committed file then unstaged file deletion
     - for any other status, see: `${CLAUDE_SKILL_DIR}/references/git-status-short-format.adoc`

2. [CHECK] if any unrelated file is already staged:
   - if not: proceed
   - otherwise:
     - if user has allowed "staged but unrelated" files to be committed: proceed
     - otherwise:
       - STOP TO PROMPT USER to unstage, commit, or allow "staged but unrelated" files to be committed
       - await user prompt
       - try again starting at `2. [CHECK]`

3. [COMMITREQUIRED]
   - if no relevant files have changed:
     - NOTIFY USER THEN END THIS SUBFLOW WITHOUT COMMITTING
     - RETURN TO CALLING FLOW
   - otherwise, proceed

4. [ADD] add modifications to relevant files to stage:
   - for each relevant file:
     `git add <file_or_directory>`

### 2. Generate commit message

Invoke `${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file <MODE>` to generate a commit message.
Choose the mode that matches the current context:

| Mode        | When to use                                               | Required flags                | Optional flags        | Forbidden flags    | Subject format                          |
| ----------- | --------------------------------------------------------- | ----------------------------- | --------------------- | ------------------ | --------------------------------------- |
| `plain`     | Framework bootstrap commits with no task (e.g. `hb-init`) | `--short`                    | `--long`              | `--task`, `--step` | `hb: <short>`                           |
| `task`      | Task-level commits (skill operates on a task, not a step) | `--task`, `--short`          | `--long`, `--tag`     | `--step`           | `<task_id>: <short>` or `<task_id>: (<tag>) <short>` |
| `task-step` | Step-level commits (skill operates on a specific step)    | `--task`, `--step`, `--short` | `--long`, `--tag`    | —                  | `<task_id>/step-<n>: <short>` or `<task_id>/step-<n>: (<tag>) <short>` |

All modes accept an optional `--long <desc>` for a longer explanation of why the change was made (only include when the why is non-obvious). `task` and `task-step` accept an optional `--tag <slug>` to identify the lifecycle skill that produced the commit; the slug is injected as `(<tag>)` immediately after the colon-space separator. Tag must match `[a-z][a-z0-9]*(-[a-z0-9]+)*` (lowercase slug). Wrap `--short`, `--long`, and `--tag` values in `""` to avoid shell issues.

Returns the path to the commit message file on stdout. Returns error messages on stderr. If any error occurs, surface verbatim to the user or fix automatically if possible.

**Examples:**

```bash
# plain — hb-init bootstrap commit
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file plain \
  --short "initialize hashbuild"
# → subject: hb: initialize hashbuild

# task — operating on a task (no step)
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task \
  --task northwind/hb-001-init-commit-support \
  --short "add step-1 ticket"
# → subject: hb-001: add step-1 ticket

# task — with lifecycle tag
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task \
  --task northwind/hb-001-init-commit-support \
  --tag "task-create" \
  --short "create task skeleton"
# → subject: hb-001: (task-create) create task skeleton

# task-step — operating on a specific step
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task-step \
  --task northwind/hb-001-init-commit-support \
  --step 1 \
  --short "wire hb-init to plain mode"
# → subject: hb-001/step-1: wire hb-init to plain mode

# task-step — with lifecycle tag
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task-step \
  --task northwind/hb-001-init-commit-support \
  --step 2 \
  --tag "step-execute" \
  --short "implement tag flag"
# → subject: hb-001/step-2: (step-execute) implement tag flag
```

### 3. Commit

Commit staged changes: `git commit -F <commit_message_file>`

- `<commit_message_file>` should be path generated by `${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file`
