---
name: hb-task-step-review-init
description: >
  Idempotent. Create review.md in a step folder seeded with one placeholder review item. Does nothing if review.md already exists with required structure.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write
---

# hb-task-step-review-init

Create `review.md` in a step folder, seeded from [${CLAUDE_SKILL_DIR}/references/review-template.md](references/review-template.md) with one placeholder review item. Idempotent — skips creation if `review.md` already exists with the required structure.

## Inputs

| Parameter              | Required | Description                                                                                                                                                                |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `step_ref`             | yes\*    | Step reference in `author/task_id/step_n` format. `task_id` flavor is optional. `step_n` accepts: bare integer (`0`), `step-<n>`, or full step name (`step-<n>-<flavor>`). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                                                |

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Resolve step folder

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

### 3. Check for existing review.md

If `$STEP_PATH/review.md` already exists:

- read it and verify the required structure is present:
  - a `## Status` section containing a table with at least one row
  - a `## Notes` section containing at least one `### STEP-N-REVIEW-` heading
  - IDs in the status table match IDs in the notes section
- if structure is intact: report "review.md already exists — nothing to do" and stop
- if structure has drifted in a meaningful way (missing sections, empty table, mismatched IDs): notify the user of what is missing or inconsistent, then stop without modifying the file

### 4. Create review.md

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

### 5. Notify user

Tell the user:

> `review.md` created at `$STEP_PATH/review.md`. Fill in the review items under `## Notes` — one `### STEP-N-REVIEW-M:` heading per concern, with body per the commented example at the bottom of the file. **Do not edit the `## Status` table** — it is maintained by the hashbuild skills.
>
> When done, `/clear` this conversation, then run `/hb-task-step-review-address <step_ref>` to work through the review items.

Also show the user:

- README-1 defined in step 4
- README-2 defined in step 4

### 6. Commit

- create a step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including `$STEP_PATH/review.md`

## Output

Report the path to the created `review.md`. If any command fails, surface the error verbatim to the caller.
