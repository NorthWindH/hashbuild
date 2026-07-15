# Background

The interactive ticket subflow (used by `hb-task-create` and `hb-task-step-add`) writes the drafted ticket to a fixed path, `$TARGET_PATH/ticket.md`, where `$TARGET_PATH` is hardcoded to `/tmp` by both callers. When multiple sessions run this flow concurrently, they collide on the same `/tmp/ticket.md` file — one session's draft can be overwritten by another's before it's consumed.

---

# Acceptance Criteria

1. Concurrent interactive-ticket-creation sessions (via `hb-task-create` and `hb-task-step-add`) no longer collide on a shared temp file path.
2. The temp file path used for writing an in-progress ticket is randomized/unique per invocation, rather than the fixed `/tmp/ticket.md`.
3. Explore whether the harness/agent can supply its own session-specific temporary path (e.g. a scratchpad directory) for this purpose, and prefer that mechanism over hand-rolled randomization if it's available and suitable.
4. The resulting path remains a valid `.md` file usable as-is for `hb-sdk`'s `--ticket <path>` argument.
5. Skeleton-only mode and the `--ticket <path>`-supplied mode are unaffected — only the interactive-mode temp path changes.
