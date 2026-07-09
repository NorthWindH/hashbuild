# Step 1 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-1-REVIEW-1 |            |
| STEP-1-REVIEW-2 |            |

---

## Notes

### STEP-1-REVIEW-1: Ensure all skills pass full `author/task_id` when passing `--task` to `hb-sdk state record`

Looking at updated skills, unclear if agent will pass just task name or the required `author/task_id` to hb-sdk.

Ensure all skills are passing the required `author/task_id` when passing `--task` to `hb-sdk state record`

---

### STEP-1-REVIEW-2: Report the gitignore path when it gets updated by `ensure_gitignore_entry()`

- **file(s):** `skills/scripts/hb_sdk/init_cmd.py` (`cmd_init`, `ensure_gitignore_entry`)
- `ensure_gitignore_entry()` may add an entry to `.gitignore` but its result is not appended to the `paths` list, so `cmd_init` never reports that the gitignore file was updated.
- **source:** `TODO REVIEW` in commit `2343e6729e4166328e21b5dc68b44f8b47a06b8d` — delete comment from source file after addressing

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
