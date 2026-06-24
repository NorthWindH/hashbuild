---
name: hb-init
description: >
  Idempotent. Ensure that hashbuild directory structure exists (.hb directory).
  Should be called before any other /hb-* skills are invoked for the first time.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---

# hb-init

Atomic: call `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` to create hashbuild directory structure (.hb directory).

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Initialize hashbuild structure

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk init
```

### 3. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task

## Output

Report the task path and changed/created files. If any command fails, surface the error verbatim to the caller.
