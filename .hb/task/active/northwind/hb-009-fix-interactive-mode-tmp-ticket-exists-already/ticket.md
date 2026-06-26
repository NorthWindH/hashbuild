# Background

The `hb-task-create` and `hb-task-step-add` interactive ticket subflow always writes its temporary ticket file to the hardcoded path `/tmp/ticket.md`. If a previous run left that file behind, the next invocation silently overwrites stale content without any guard. The fix should either delete `/tmp/ticket.md` before proceeding if it already exists, or let the AI agent choose a unique temp path each run so stale files can never interfere.

---

# Acceptance Criteria

1. The interactive-ticket-subflow no longer risks colliding with a stale `/tmp/ticket.md` from a prior run — one of the following two approaches is implemented:
    1. Option A: the subflow (or its caller) explicitly deletes `/tmp/ticket.md` if it exists before writing the new ticket.
    2. Option B: the subflow uses a unique temp path chosen by the AI agent at runtime (not hardcoded to `/tmp/ticket.md`) so each invocation writes a distinct file.
2. The fix is reflected in the shared subflow reference (`interactive-ticket-subflow.md`) and applies to both callers: `hb-task-create` and `hb-task-step-add`.
3. All other interactive subflow behavior is unchanged: the ticket is written, passed to the SDK via `--ticket`, and the task or step skeleton is created normally.
