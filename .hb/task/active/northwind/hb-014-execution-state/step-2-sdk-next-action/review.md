# Step 2 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-2-REVIEW-1 |            |
| STEP-2-REVIEW-2 |            |

---

## Notes

### STEP-2-REVIEW-1: Clarify when `/clear` should be run after a skill

- **file(s):** `skills/scripts/hb_sdk/next_action.py` (module-level comment above `_resolve`)
- `/clear` should be executed before any next step when presented at the end of most skills. Exceptions are when presented at the end of `hb-status`, `hb-task-step-review-*` skills, and `hb-flow` (not yet written) prior to taking an action.
- **source:** `TODO REVIEW` in commit `5d942071e385059cf23e515195fa3f829f1fa23e` — delete comment from source file after addressing

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
