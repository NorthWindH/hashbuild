# Background

The interactive ticket subflow (used by `hb-task-create` and `hb-task-step-add`) writes the drafted ticket to a fixed path, `$TARGET_PATH/ticket.md`, where `$TARGET_PATH` is hardcoded to `/tmp` by both callers. When multiple sessions run this flow concurrently, they collide on the same `/tmp/ticket.md` file — one session's draft can be overwritten by another's before it's consumed.

Some harnesses/agents expose a per-session scratch or temp directory (e.g. Claude Code surfaces one as "Scratchpad Directory" guidance in-session) that is isolated from other sessions and intended for exactly this kind of temporary file need. `interactive-ticket-subflow.md` is invoked across different harnesses/agents, not just one, so the detection of such a directory must stay harness-agnostic (e.g. read from an environment variable or convention that isn't tied to one specific product's naming) rather than hardcoding a single harness's mechanism. Where no such directory is detected, the subflow must fall back to hand-rolled randomization (e.g. `mktemp`, uuid-suffixed filenames under the OS temp dir) so the fix still works standalone.

---

# Goal

Replace the hardcoded `/tmp` target path in `interactive-ticket-subflow.md` (and its two callers, `hb-task-create` and `hb-task-step-add`) with a session-scoped, collision-free temp path, without changing behavior for skeleton-only or `--ticket <path>`-supplied modes.

---

# Acceptance Criteria

1. Concurrent interactive-ticket-creation sessions (via `hb-task-create` and `hb-task-step-add`) no longer collide on a shared temp file path.
    1. Two sessions running the interactive flow at the same time each get their own writable target path.
2. The temp file path used for writing an in-progress ticket is randomized/unique per invocation, rather than the fixed `/tmp/ticket.md`.
3. The mechanism for detecting a harness/agent-supplied session-specific temporary path is harness-agnostic — it does not hardcode logic specific to one particular harness/agent product.
    1. When such a path is detected, it is preferred over hand-rolled randomization.
    2. When no such path is detected (e.g. running standalone, or under a harness that exposes none), the subflow falls back to hand-rolled randomization (e.g. `mktemp`, uuid-suffixed filenames) so the fix still works without any harness support.
    3. The detection mechanism and fallback are documented inline (comment or facts-store entry) where non-obvious.
4. The resulting path is a valid `.md` file (e.g. ends in `ticket.md` or `<slug>.md`) usable as-is for `hb-sdk`'s `--ticket <path>` argument.
5. Skeleton-only mode and the `--ticket <path>`-supplied mode in `hb-task-create` and `hb-task-step-add` are unaffected — only the interactive-mode temp path changes.
    1. Existing skeleton-only and `--ticket`-supplied invocations behave identically before and after this change.
6. `hb-ticket-discuss`'s ticket-creation actions (`describe-ticket-subflow.md`, `load-ticket-subflow.md`) share the same underlying collision class through their own `$TICKET_SEQ`-based `/tmp/hb-ticket-discuss/ticket-N` path — unique only within one conversation, not across concurrent sessions, which each start `$TICKET_SEQ` at the same value. They move onto the same session-scoped/collision-free resolution as the other callers rather than being left on a parallel, still-collision-prone scheme.
    1. `$TICKET_SEQ`'s sole purpose today is constructing that per-call subfolder; once no longer needed for that, it is removed as dead state from the loop's threaded parameters (`ticket-loop-subflow.md`, `describe-ticket-subflow.md`, `load-ticket-subflow.md`, and `hb-ticket-discuss.md`'s own initialization) rather than left unused.

---

# Out of scope

- Changing the ticket content/structure produced by the interactive flow — only the target path changes.
- Cleanup/lifecycle management of old temp files beyond what the chosen mechanism already provides.
