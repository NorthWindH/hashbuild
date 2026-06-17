---
name: hb-address-review
description: "Address review comments or feedback on a task step's execution. Use when the user provides review notes, says 'fix these comments', 'address review for STEP-X', or pastes PR/code review feedback. Reads execution notes for context, applies fixes, updates step status."
---

# hb-address-review

Apply review feedback to a step's execution.

## Steps

1. **Identify step**: resolve task ID and step ID from context. Confirm if ambiguous.

2. **Load context**:
   - Read `tasks/active/<task_id>/steps/<step_id>/plan.md`
   - Read `tasks/active/<task_id>/steps/<step_id>/execution/notes.md` (what was done)
   - Read the review feedback (from user message, pasted PR comments, etc.)

3. **Parse review items**: list each distinct piece of feedback. Group related items.

4. **Confirm scope**: show the list — "I see N review items. Addressing all of them — any to skip or clarify?"

5. **Address each item**:
   - Make the required change
   - For substantive disagreements, surface the tradeoff to the user rather than silently deferring

6. **Update execution notes**: append a `## Review Round N` section to `execution/notes.md`:
   - Date
   - Items addressed (brief, one line each)
   - Items deferred/discussed (if any)

7. **Update step status**: if all items resolved, change `**Status:** needs-review` → `**Status:** complete`. If further review needed, keep as `needs-review`.

8. **Report**: what was changed, what (if anything) was deferred.

## Handling ambiguous feedback

"This is wrong" or "clean this up" — ask the reviewer what specifically they want instead of guessing. It's better to ask once than to re-address repeatedly.
