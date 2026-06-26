# Background

`hb-sdk commit write-message-file` currently requires `--task`, making it impossible to generate an SDK-authored commit message during `hb-init` (which runs before any task exists). The workaround is a manually hard-coded message in the skill, which breaks the invariant that all hb-* commit messages are SDK-generated.

**The problem:** Running the SDK at init time fails:

```
hb-sdk commit write-message-file: error: the following arguments are required: --task
```

**The motivating case:** `hb-init` needs to call `hb-sdk commit write-message-file plain --short "initialize hashbuild"` and receive a valid commit message without supplying `--task`.

# Acceptance Criteria

1. `hb-sdk commit write-message-file` accepts a required positional `MODE` argument; valid values are `plain`, `task`, and `task-step`
2. In `plain` mode:
    1. `--task` and `--step` are not accepted; passing either is a hard error (non-zero exit, descriptive message)
    2. `--short` is required; `--long` is optional
    3. Subject line is `hb: <short>`
3. In `task` mode:
    1. `--task` is required; `--step` is not accepted (hard error if passed)
    2. `--short` is required; `--long` is optional
    3. Subject line is `<task_id>: <short>`
4. In `task-step` mode:
    1. `--task` and `--step` are both required
    2. `--short` is required; `--long` is optional
    3. Subject line is `<task_id>/step-<n>: <short>`
5. All existing skill call sites updated to use the explicit mode argument

# Out of scope

- Changes to `hb-init` skill or `committing.md` (deferred to next step)
- Changes to any other `hb-sdk` subcommand
