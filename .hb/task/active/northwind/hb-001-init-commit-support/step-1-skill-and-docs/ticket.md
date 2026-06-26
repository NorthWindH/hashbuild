# Background

Once `hb-sdk commit write-message-file --init` is available (step 1), `hb-init` must be updated to use it instead of its current hard-coded commit message. Additionally, `committing.md` must document the new `--init` flag so skill authors know when and how to use it.

# Acceptance Criteria

1. `hb-init` generates its commit message by calling `hb-sdk commit write-message-file --init` (short form for the subject, long form for the full message, consistent with how other skills use the SDK)
    1. The skill no longer contains any manually written commit message strings for the init commit
2. `committing.md` documents the `--init` flag:
    1. States that `--init` is for framework bootstrap commits only — before any task exists
    2. States that `--init` is mutually exclusive with `--task` and `--step`
    3. Gives a usage example showing `hb-sdk commit write-message-file --init --short` and `--long`

# Out of scope

- Changes to any hb-* skill other than `hb-init`
- Changes to `hb-sdk` itself (completed in step 1)
