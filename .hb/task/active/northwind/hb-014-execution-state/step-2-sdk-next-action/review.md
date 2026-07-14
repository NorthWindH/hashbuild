# Step 2 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-2-REVIEW-1 | ✅ Addressed — `next_action.py`'s "Move to the next step" choice now carries the `/clear` reminder when the target stage's own message includes one |
| STEP-2-REVIEW-2 |            |

---

## Notes

### STEP-2-REVIEW-1: Clarify when `/clear` should be run after a skill — ADDRESSED

- **file(s):** `skills/scripts/hb_sdk/next_action.py` (module-level comment above `_resolve`)
- `/clear` should be executed before any next step when presented at the end of most skills. Exceptions are when presented at the end of `hb-status`, `hb-task-step-review-*` skills, and `hb-flow` (not yet written) prior to taking an action.
- **source:** `TODO REVIEW` in commit `5d942071e385059cf23e515195fa3f829f1fa23e` — delete comment from source file after addressing

**Resolution:** This surfaced a real gap, not just a docs question. Every skill's own final prompt already follows this rule correctly (e.g. `hb-task-step-execute.md:97`, `hb-task-step-add.md:82`, `hb-task-plan.md:97` all say "Run `/clear`, then run `<next skill>`"; `hb-task-step-review-address.md:237` and `hb-task-step-review-init.md:45` correctly omit it before re-entering a review-\* skill). But `next_action.py`'s `_resolve` had a bug: in the `review_or_next` stage, the "Move to the next step" `Choice` was built from `move_on.invocation` alone, dropping `move_on.message` — which is exactly where the `/clear` instruction lives for `plan_step`/`execute_step` stages. So a user driven by `/hb-status` (an explicitly `/clear`-exempt skill per this same comment) never saw the reminder that a user hitting the same transition via a skill's own final prompt would see.

Fixed in `next_action.py` (`_resolve`): the "Move to the next step" choice label now appends `" (run `/clear` first)"` when `"/clear" in move_on.message`, i.e. whenever the downstream stage's own message would have included the reminder:

```python
if move_on.invocation is not None:
    label = "Move to the next step"
    if "/clear" in move_on.message:
        label += " (run `/clear` first)"
    rest = [Choice(label, move_on.invocation)]
```

Updated the existing test asserting the old exact label (`test_next_action_stage_review_or_next_has_next_step`) to expect `"Move to the next step (run `/clear` first)"`. `hb-status`'s own message/choices for `review_or_next` and `steps_complete` were left unchanged — those stages never included a `/clear` reminder even at top level, consistent with the exception this comment describes.

Verified: `uv run pytest tests/skills/scripts/hb_sdk/test_hb_sdk_next_action.py -q` → 18 passed. `uv run ruff check` / `uv run ruff format --check` on both changed files → clean.

---

### STEP-2-REVIEW-2: Prefer `review-address` over `review-init` in docs/guidance

- **file(s):** `skills/scripts/hb_sdk/next_action.py` (module-level comment above `_resolve`)
- Prefer `/hb-task-step-review-address` to `/hb-task-step-review-init`; `init` is only used in specialty scenarios when the user needs a plain skeleton-only `review.md` file.
- **source:** `TODO REVIEW` in commit `5d942071e385059cf23e515195fa3f829f1fa23e` — delete comment from source file after addressing

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
