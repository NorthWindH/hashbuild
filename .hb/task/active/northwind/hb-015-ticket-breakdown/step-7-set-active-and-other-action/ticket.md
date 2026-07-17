# Background

- In `hb-ticket-discuss`'s loop, users have asked to set a specific ticket active without loading/describing/breaking it down again — currently unsupported (falls through to "ask a clarifying question").
- Users have also made requests that don't map to any registered action (e.g. reformatting an existing ticket's content) — currently handled ad hoc rather than through a defined escape hatch.
- This step adds two actions to the registry: an explicit "set active ticket" action, and an "other" action for natural-language requests outside the fixed action set.

---

# Acceptance Criteria

1. A "Set active ticket" action is added to `ticket-loop-subflow.md`'s Action Registry (§B), dispatching to a new `set-active-ticket-subflow.md`.
    1. Selectable via phrasings like "set ticket 2 as active", "make CSS-2664 active".
    2. Resolves the named entry by semantic match against `id_or_summary` (ambiguous/zero matches → ask, never auto-select), unsets `active` on every other entry, sets it on the resolved one.
    3. Mutates only the `active` flags — never ticket `content`.
2. An "Other" action is added to the Action Registry, dispatching to a new `other-action-subflow.md`, for replies that don't semantically match any other registered action.
    1. Prompts the user in natural language for what they'd like to do.
    2. Handles the request directly when it's a lightweight, well-scoped operation on data already in `$TICKET_CONTEXT` (e.g. reformatting an existing entry's content) — otherwise reports back that it isn't supported yet.
3. Both new subflows follow the existing row shape from §B's extensibility note (one new row + one sibling subflow file each) — no changes to `describe-ticket-subflow.md`, `load-ticket-subflow.md`, `breakdown-ticket-subflow.md`, `clear-ticket-subflow.md`, `push-ticket-subflow.md`, or `exit-ticket-loop-subflow.md`.
4. `ticket-loop-subflow.md` §C (present) lists both new actions alongside the existing five when presenting the menu.
