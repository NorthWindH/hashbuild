# Background

The shared breakdown subflow (extracted in an earlier step from `hb-task-plan`) implements gap analysis, propose-confirm, and per-child create-confirm generically over a parent ticket and its existing children. The task ticket (AC 6) requires `hb-ticket-discuss` to add a **Breakdown ticket** action that wires the loop up to that same subflow, so a ticket held in context can be decomposed into child tickets without duplicating any of that logic (AC 11).

---

# Acceptance Criteria

1. **Breakdown ticket** action is added to the loop's menu, selectable via natural language, targeting a ticket in context (defaults to the active ticket if the user doesn't name one; if ambiguous, asks which).
2. The action supplies the shared breakdown subflow (from `references/breakdown-subflow.md`) with:
    1. **Parent** = the targeted ticket's acceptance criteria.
    2. **Children** = any tickets already in context that were previously created as children of this parent (tracked via the loop's ticket model — e.g. a parent reference stored on each child entry).
3. The subflow's gap report, "no gaps" exit, propose-confirm loop, and per-child create-confirm loop behave exactly as specified in the shared subflow ticket — this step does not re-implement or diverge from that behavior.
4. On confirmation of each child ticket, the child is added to context (following the loop's ticket model) with a record that it is a child of the targeted parent, and becomes the active ticket; the previously active ticket (if different) is not removed from context.
5. When the subflow reports no gaps, the action returns to the top-level menu without creating anything, per the subflow's "no gaps" contract.
6. This action's logic (the loop-specific wiring: resolving the target ticket, supplying parent/children, materializing confirmed children into the loop's context model) lives in its own reference subflow file, separate from the shared breakdown subflow itself; `references/references-toc.md` is updated accordingly.

---

# Out of scope

- Any change to the shared breakdown subflow's internal logic (gap analysis, propose-confirm, create-confirm) — this step only supplies the caller-side wiring it already expects.
- Load, Clear, and Push actions — other steps.
- Persisting the parent/child relationship to `.hb/` — it lives only in the loop's in-conversation context model.
