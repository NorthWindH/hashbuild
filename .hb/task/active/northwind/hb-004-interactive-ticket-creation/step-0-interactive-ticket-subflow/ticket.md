# Background

Both `hb-task-create` and `hb-task-step-add` need identical logic for interactive ticket creation: prompt the user for content in any form, transform it into the standard three-section structure, and write `ticket.md` to a target folder. Extracting this into a shared reference file (following the pattern of `review-init-subflow.md`) avoids duplicating the prompt wording, transformation rules, and flag-precedence contract across two skill files.

---

# Acceptance Criteria

1. `skills/references/interactive-ticket-subflow.md` exists and contains:
    1. A header block identifying it as a shared subflow (no side effects — no commits, no SDK calls, no user notifications beyond the prompt itself).
    2. **Guard clause**: skip the entire subflow and do nothing if `--ticket <path>` was supplied (ticket file takes precedence) OR if `--no-interactive` was supplied (skeleton-only mode).
    3. **Prompt step**: instruct Claude to ask the user for ticket content in any form (freeform prose, bullet list, structured draft, or fully-formed Background/AC/Out of scope).
    4. **Transform step**: rules for converting received content to the standard `ticket.md` structure:
        - If the content already matches Background + Acceptance Criteria + optional Out of scope (perfect or near-perfect): transcribe verbatim or with minimal conforming adjustments.
        - Otherwise: derive the three sections from the freeform content; Background captures the "why", Acceptance Criteria captures checkable conditions, Out of scope captures explicit exclusions (omit section if none are present in the input).
    5. **Write step**: write the transformed content to `$TARGET_PATH/ticket.md`.
2. `skills/references/references-toc.md` gains a row for `interactive-ticket-subflow.md` with a description consistent with the `review-init-subflow.md` row style.

---

# Out of scope

- Updating `hb-task-create.md` or `hb-task-step-add.md` to invoke the subflow (steps 1 and 2).
- Any SDK changes.
- Validation of ticket quality or completeness.
