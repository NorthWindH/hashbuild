# Background

`interactive-ticket-subflow.md` hardcodes `/tmp/ticket.md` as its temp file path. If a prior run left that file behind, the next invocation overwrites it silently, risking stale content sneaking in. The fix updates the shared subflow so the temp path is either deleted before use or chosen uniquely at runtime — eliminating the collision risk for both callers (`hb-task-create` and `hb-task-step-add`).

---

# Acceptance Criteria

1. `interactive-ticket-subflow.md` no longer uses a hardcoded `/tmp/ticket.md` path — one of the following approaches is implemented:
    1. Option A: the subflow instructs the AI agent to delete `/tmp/ticket.md` if it exists before writing the new ticket there.
    2. Option B: the subflow instructs the AI agent to choose a unique temp path at runtime (e.g. `/tmp/ticket-<timestamp>.md` or similar) so each invocation writes a distinct file.
2. The fix applies automatically to both callers: `hb-task-create` and `hb-task-step-add` use the same shared subflow and require no separate changes beyond any cosmetic reference updates in their own files.
3. All other interactive subflow behavior is unchanged: the ticket content is still written to the temp file, passed to the SDK via `--ticket <path>`, and the task or step skeleton is created normally.

---

# Out of scope

- Changes to any other behavior of `hb-task-create`, `hb-task-step-add`, or the SDK itself.
- Choosing between Option A and Option B is left to the planner — either satisfies the contract.
