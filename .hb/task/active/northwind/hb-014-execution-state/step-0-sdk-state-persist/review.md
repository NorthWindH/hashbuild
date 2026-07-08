# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 |            |

---

## Notes

### STEP-0-REVIEW-1: ensure_gitignore_entry should not take an argument and should anchor its entry to the repo root

- **file(s):** `skills/scripts/hb_sdk/common.py` (`ensure_gitignore_entry`), `skills/scripts/hb_sdk/init_cmd.py` (`cmd_init` call site)
- `ensure_gitignore_entry` should not receive an argument — it should already know the exact correct entry to ignore. The entry should also match only at repo root.
- **source:** `TODO REVIEW` in commit `f958f2f9bb381c57534b8e84097f1f5ce9d1a6a2` — delete comment from source file after addressing

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
