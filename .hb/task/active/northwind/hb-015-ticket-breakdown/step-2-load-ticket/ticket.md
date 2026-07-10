# Background

The loop skeleton (prior step) offers Describe and Exit. The task ticket (AC 4) also requires a **Load ticket** action: pull an existing ticket into context from a source — a text file, an available MCP such as Jira, or web access — rather than authoring one from scratch.

---

# Acceptance Criteria

1. **Load ticket** action is added to the loop's menu of actions, selectable via natural language (e.g. "load the ticket from PROJ-123", "load this file as a ticket", "pull in the ticket at this URL").
2. Supports loading from:
    1. A text file: read it, and if it isn't already in the standard Background/Acceptance Criteria/Out-of-scope structure, transform it using the same rules as `references/interactive-ticket-subflow.md` Section C (transcribe near-perfect matches; derive from freeform otherwise).
    2. A connected MCP capable of reading an issue (e.g. Jira via Atlassian Rovo's `getJiraIssue` / JQL search, following the same discover-by-capability and resolution pattern already used for the push flow) — resolve ambiguous references (no exact key) by asking the user, never auto-selecting among multiple matches.
    3. Web access, when available to the agent harness (e.g. fetching and parsing a URL's content into the standard ticket structure).
3. On success, the loaded ticket is added to context (following the loop's ticket model from the prior step) and becomes the active ticket.
4. The loaded ticket becomes recallable in later loop iterations both by natural-language description of its summary/content and by any identifier present in its name/content (e.g. a Jira key).
5. Graceful degradation: if the requested source is unavailable (no matching MCP connected, file not found, fetch fails), surface the error/absence to the user and return to the loop menu without crashing or leaving a partial/malformed entry in context.
6. Ambiguous or multi-match load requests (e.g. a file glob matching several files, a JQL search returning multiple issues) present a numbered list for the user to pick from — never auto-selected.
7. This action's logic lives in its own reference subflow file, following the pattern established by the loop-skeleton step; `references/references-toc.md` is updated accordingly.

---

# Out of scope

- Breakdown, Clear, and Push actions — later steps.
- New MCP/source integrations beyond what's already available to the agent harness (Jira via the existing Atlassian Rovo MCP, local files, web fetch) — this step wires Load to existing means only.
- Any change to `hb-task-plan` or the shared breakdown subflow.
