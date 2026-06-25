---
name: hb-init
description: >
  Idempotent. Ensure that hashbuild directory structure exists (.hb directory).
  Should be called before any other /hb-* skills are invoked for the first time.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---

# hb-init

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to create hashbuild directory structure (.hb directory).

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Initialize hashbuild structure

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk init
```

### 3. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task

### 4. Prompt user to create their first task

Tell the user:

> Hashbuild is ready. To start your first task, `/clear` this conversation to free context, then run `/hb-task-create` with the task name and an optional ticket file.
>
> At any point, run `/hb-status` to see the current state of all active tasks and get a recommended next action.
>
> A ticket file is a Markdown file that defines what the task must achieve. It has three sections:
>
> - **Background** — one sentence (or more, if needed) on what you need and why
> - **Acceptance Criteria** — numbered, concrete, checkable conditions; every criterion must be falsifiable ("input X produces output Y", not "handles X correctly")
> - **Out of scope** — what this task deliberately does not do
>
> Example invocation:
>
> ```
> /hb-task-create author/abc-123-my-task --ticket path/to/ticket.md
> ```
>
> The ticket file is optional — you can add it later — but starting with one keeps planning grounded.

## Output

Report the task path and changed/created files. If any command fails, surface the error verbatim to the caller.
