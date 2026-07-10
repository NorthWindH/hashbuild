# Background

With Load, Describe, and Breakdown all able to add tickets to context, the task ticket (AC 7) requires a way to remove them again: **Clear ticket(s)**, targeting one, several, or all tickets — including the active one.

---

# Acceptance Criteria

1. **Clear ticket(s)** action is added to the loop's menu, selectable via natural language (e.g. "clear the active ticket", "remove PROJ-123 and PROJ-124", "clear all tickets").
2. Supports targeting:
    1. A single ticket, referenced by id/summary or by "the active ticket".
    2. Several named tickets in one request.
    3. All tickets currently in context.
3. Ambiguous natural-language references (matches more than one ticket in context) present a numbered list for the user to pick from — never auto-cleared.
4. Clearing the active ticket unsets active-ticket state; if other tickets remain in context, no new ticket is auto-promoted to active — the next iteration's summary shows "no active ticket" until the user sets one (e.g. via Describe, Load, or an explicit "make X active" request handled by this action or an obvious extension of it).
5. Clearing is confirmed before it happens when it would remove more than one ticket at once (e.g. "clear all") — a single, unambiguous named target may be cleared without an extra confirmation prompt.
6. After clearing, the loop's next-iteration summary (count, ids, active ticket) reflects the updated context immediately.
7. This action's logic lives in its own reference subflow file, following the established pattern; `references/references-toc.md` is updated accordingly.

---

# Out of scope

- Push action — next step.
- Any persistence implications — clearing only affects the in-conversation context model; nothing was ever written to `.hb/` by these tickets.
