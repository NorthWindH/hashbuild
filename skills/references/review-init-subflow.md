> **Subflow — review.md file creation.** Shared by `hb-task-step-review-init` and
> `hb-task-step-review-address`. Contains no side effects (no user notification, no commit).

#### A. Resolve step folder

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step path <step_ref>
```

- captures the absolute path as `$STEP_PATH`
- if an error occurs, surface it verbatim and stop

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step number <step_ref>
```

- captures the numeric step number as `$N`
- if an error occurs, surface it verbatim and stop

#### B. Check for existing review.md

If `$STEP_PATH/review.md` already exists:

- read it and verify the required structure is present:
  - a `## Status` section containing a table with at least one row
  - a `## Notes` section containing at least one `### STEP-N-REVIEW-` heading
  - IDs in the status table match IDs in the notes section
- if structure is intact: report "review.md already exists — nothing to do" and stop
- if structure has drifted in a meaningful way (missing sections, empty table, mismatched IDs): notify the user of what is missing or inconsistent, then stop without modifying the file

#### C. Create review.md

Write `$STEP_PATH/review.md` with the following content (substituting `N` with the actual step number):

```markdown
# Step N Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-N-REVIEW-1 |            |

---

## Notes

###

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
```
