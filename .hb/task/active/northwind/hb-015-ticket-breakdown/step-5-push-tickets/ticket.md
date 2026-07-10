# Background

The current single-shot `hb-ticket-discuss` (Steps 3–6 of its skill file, before this task's loop restructuring) already implements pushing one ticket to Jira via MCP — including NL-driven field resolution, create-vs-update detection, and offering an Epic→Idea link — falling back to stdout copy-paste when no Jira MCP is connected or the user declines. The task ticket (AC 8) requires this same procedure to become a **Push ticket(s)** loop action operating on one or more tickets held in context, looping through each target and stopping early if the user asks to.

---

# Acceptance Criteria

1. **Push ticket(s)** action is added to the loop's menu, selectable via natural language, targeting:
    1. A single named ticket, or "the active ticket" (default when the user says just "push" with one ticket in context or an unambiguous active ticket).
    2. Several named tickets in one request.
    3. All tickets currently in context.
2. For each targeted ticket, the existing push procedure runs unchanged in substance:
    1. Detect a Jira-capable MCP by capability; if none, fall back to emitting the ticket for copy-paste (unchanged graceful-degradation contract).
    2. NL description → resolution → confirmation loop for create vs. update fields, exactly as today.
    3. Push (create or update), reporting the resulting issue key and browse URL on success; on failure, surface the error verbatim and fall through to copy-paste emission for that ticket — no dead-end.
    4. When the pushed/updated issue's type is exactly `Epic`, offer the Idea-link step exactly as today (ask, resolve `$IDEA_REF`, `createIssueLink`, report or degrade gracefully on failure).
3. When multiple tickets are targeted, the action loops through them one at a time (not concurrently), stopping before processing the next if the user requests it (e.g. "stop", "that's enough") — tickets not yet processed remain in context, unpushed.
4. Each ticket's outcome (pushed with key/URL, emitted for copy-paste, or skipped by user request) is tracked per-ticket and summarized to the user once the batch finishes (or is stopped early).
5. A ticket remains in context after being pushed — Push does not implicitly clear it; clearing is a separate, explicit action.
6. This action's logic (the per-ticket push procedure plus the multi-target looping/early-stop wrapper) lives in its own reference subflow file(s), following the established pattern; `references/references-toc.md` is updated accordingly.
7. The `allowed-tools` frontmatter in `hb-ticket-discuss.md` still lists exactly the Jira MCP tools this procedure calls (unchanged from today, since no new integrations are introduced).

---

# Out of scope

- New MCP/source integrations beyond the Jira push flow that already exists today.
- Any change to the Idea-linking direction or semantics (`createIssueLink` with `inwardIssue` = Epic, `outwardIssue` = Idea) — carried over verbatim.
- Concurrent/parallel pushing of multiple tickets — sequential only, per AC 3 above.
