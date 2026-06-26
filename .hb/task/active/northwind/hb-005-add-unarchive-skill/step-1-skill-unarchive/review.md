# Step 1 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-1-REVIEW-1 | ✅ Addressed — added skill row to table + "Unarchive a task" section in Getting Started |
| STEP-1-REVIEW-2 |            |

---

## Notes

### STEP-1-REVIEW-1: README.md Skills table missing unarchive skill

- **file(s):** `skills/references/README.md` (around `TODO REVIEW` marker)
- The Skills table and the sections below it do not yet document the `/hb-task-unarchive` skill; they need to be updated to include it alongside the archive skill.
- **source:** `TODO REVIEW` in commit `29fa290` — delete comment from source file after addressing

**Resolution:** Added `/hb-task-unarchive` row to the Skills table after `/hb-task-archive`, and added an "Unarchive a task" section in Getting Started (§6 follow-on) showing the command and what it does. The `TODO REVIEW` comment was deleted from the source file.

---

### STEP-1-REVIEW-2: references-toc.md missing unarchive skill row

- **file(s):** `skills/references/references-toc.md` (around `TODO REVIEW` marker)
- The references TOC table does not include a row for the unarchive skill file; it needs an entry pointing to `hb-task-unarchive.md`.
- **source:** `TODO REVIEW` in commit `29fa290` — delete comment from source file after addressing

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
