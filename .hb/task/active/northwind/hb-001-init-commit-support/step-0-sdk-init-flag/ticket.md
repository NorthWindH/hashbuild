# Background

`hb-sdk commit write-message-file` currently requires `--task`, making it impossible to generate an SDK-authored commit message during `hb-init` (which runs before any task exists). The workaround is a manually hard-coded message in the skill, which breaks the invariant that all hb-* commit messages are SDK-generated.

**The problem:** Running the SDK at init time fails:

```
hb-sdk commit write-message-file: error: the following arguments are required: --task
```

**The motivating case:** `hb-init` needs to call `hb-sdk commit write-message-file --init` and receive a valid short/long commit message without supplying `--task`.

# Acceptance Criteria

1. `hb-sdk commit write-message-file` accepts `--init` as an alternative to `--task`
    1. When `--init` is passed, `--task` and `--step` must be omitted; passing `--init` together with `--task` or `--step` is a hard error (non-zero exit, descriptive message)
    2. The generated message identifies the commit as an `hb-init` commit — subject line is `hb: initialize hashbuild`
    3. `--short` and `--long` remain valid and optional alongside `--init` and continue to work as documented
2. All existing invocations of `hb-sdk commit write-message-file --task <name>` (with or without `--step`) continue to produce the same output as before this change

# Out of scope

- Changes to `hb-init` skill or `committing.md` (deferred to next step)
- Changes to any other `hb-sdk` subcommand
