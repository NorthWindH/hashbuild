# Background

Step-0 added the positional `MODE` argument to `hb-sdk commit write-message-file` (`plain`, `task`, `task-step`). `hb-init` still contains a manually hard-coded commit message string instead of calling the SDK. This step wires `hb-init` to the new `plain` mode and updates `committing.md` to document all three modes.

# Acceptance Criteria

1. `hb-init` generates its commit message by calling `hb-sdk commit write-message-file plain --short "initialize hashbuild"`
    1. The skill no longer contains any manually written commit message strings for the init commit
    2. The generated subject line is `hb: initialize hashbuild`
2. `committing.md` documents all three modes of `hb-sdk commit write-message-file`:
    1. `plain` — for framework bootstrap commits (e.g. `hb-init`) where no task exists; `--task` and `--step` must not be passed; subject is `hb: <short>`
    2. `task` — for task-level commits; `--task` required, `--step` forbidden; subject is `<task_id>: <short>`
    3. `task-step` — for step-level commits; `--task` and `--step` both required; subject is `<task_id>/step-<n>: <short>`
    4. Each mode entry states: when to use it, which flags are required, which are forbidden, and the resulting subject line format
    5. A usage example is shown for each mode

# Out of scope

- Changes to `hb-sdk` itself (completed in step-0)
- Changes to any hb-* skill other than `hb-init`
- Changes to the task or step name format
