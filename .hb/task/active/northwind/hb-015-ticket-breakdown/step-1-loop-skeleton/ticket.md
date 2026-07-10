# Background

`hb-ticket-discuss` is currently single-shot: it generates one standalone ticket, offers to push it, then exits. The task ticket (AC 1, 2, 3) requires it to become a persistent loop that holds any number of tickets in context across iterations, with at most one marked active, presenting a menu of next actions each time through. AC 10 requires this restructuring to keep the skill file readable by splitting the loop and each action into separate reference subflow files rather than inlining everything.

This step builds that skeleton and wires the two simplest actions end-to-end — **Describe ticket** (AC 5, mostly a re-wire of the existing `interactive-ticket-subflow.md` call, redirected to add its result into context instead of writing once to `/tmp` and pushing) and **Exit** (AC 9) — to prove the loop shape before later steps add the remaining actions (Load, Breakdown, Clear, Push) as additional subflow files following the same pattern.

---

# Acceptance Criteria

## A. Loop structure

1. `hb-ticket-discuss` no longer exits after producing one ticket; it returns to a menu of next actions after each completed action, until the user explicitly exits.
2. At the start of each iteration, the skill presents:
    1. The currently active ticket, if any (its identifying summary).
    2. The number of tickets currently held in context.
    3. The ids/identifying summaries of all tickets in context.
    4. The list of available next actions (for this step: Describe ticket, Exit — later steps add more to this menu without needing to revisit this structure).
3. The loop's in-conversation model supports holding any number of tickets, with at most one marked active at a time; the model (what a "ticket" entry looks like: its content, id/summary, active flag) is defined once here and reused unmodified by every later action step.
4. Actions are selectable via natural language, not just an exact menu keyword match.

## B. Actions

5. **Describe ticket**: creates a new ticket via `references/interactive-ticket-subflow.md` (same transform/write logic as today), adds it to context, and makes it the active ticket. The user-facing review loop (confirm/revise before it's considered final) is preserved from the current single-shot flow.
6. **Exit**: leaves the loop; summarizes the number and ids of tickets left in context and the actions taken during the session; prompts the user to `/clear` the conversation. No ticket is discarded on exit — this action only ends the loop.

## C. Structure and reuse

7. The loop's iteration logic (presenting state, dispatching to an action, returning to the top) lives in its own reference subflow file, separate from the main `hb-ticket-discuss.md` skill file.
8. The Describe and Exit actions each live in their own reference subflow file (or a shared small file if genuinely trivial enough that splitting further would be noise — judgment call, but default to separate files per action to match the pattern later steps must follow).
9. `hb-ticket-discuss.md` itself is reduced to: help check, initializing the loop, and injecting the loop subflow — no action logic inlined.
10. `references/references-toc.md` is updated to list the new subflow file(s).

---

# Out of scope

- Load, Breakdown, Clear, and Push actions (later steps in this task) — the menu in this step only needs to offer Describe and Exit; later steps append to it.
- Persisting context to `.hb/` — the skill continues to make no `.hb/` writes; tickets live only in the loop's in-conversation model (and scratch files under `/tmp` as needed for the underlying ticket-creation subflow).
- Any change to the existing NL-driven Jira push flow — untouched until the Push step.
