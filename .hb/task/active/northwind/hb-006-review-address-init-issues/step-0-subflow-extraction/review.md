# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 |            |
| STEP-0-REVIEW-2 |            |

---

## Notes

### STEP-0-REVIEW-1: Add uncommitted file scanning to hb-task-step-review-address

- **file(s):** `skills/hb-task-step-review-address.md` (step 4 — scan commits for TODO REVIEW comments)
- In addition to scanning commits, when `--no-todo-scan` is not provided, the skill should also scan files that have been changed but not committed for `TODO REVIEW` comments. If found, the user should be asked whether to commit those files before continuing the flow. If accepted, commit the changed files containing `TODO REVIEW` comments, then continue; if declined, just continue.
- **source:** `TODO REVIEW` in commit `4895b102d24203269a5fcfdf64a57842aebbdcfe` — delete comment from source file after addressing

---

### STEP-0-REVIEW-2: Test review message — delete comment from references-toc.md

- **file(s):** `skills/references/references-toc.md` (bottom of file)
- This is a test review message left as a `TODO REVIEW` comment. It should be addressed by going through the normal review address flow, then deleted.
- **source:** `TODO REVIEW` in commit `4895b102d24203269a5fcfdf64a57842aebbdcfe` — delete comment from source file after addressing

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
