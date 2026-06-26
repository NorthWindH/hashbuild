# Step 2 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-2-REVIEW-1 |            |

---

## Notes

### STEP-2-REVIEW-1: Stage permanent ticket.md path, not temporary ticket file

- **file(s):** `skills/hb-task-create.md` (Step 4 — Commit), `skills/hb-task-step-add.md` (Step 4 — Commit)
- Both skill files instruct Claude to stage `$WRITTEN_TICKET` (the temporary ticket path), but `hb-sdk` reports the permanent `ticket.md` destination path — that permanent path is what should be staged instead.
- **source:** `TODO REVIEW` in commit `18383c6` — delete comment from source file after addressing

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
