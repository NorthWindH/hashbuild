---
name: hb-task-step-review-address
description: >
  Read review.md in a step folder, normalise review item IDs, sync the status table, then address each unresolved item one by one with a commit per item.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Read Write Edit Bash(*)
---

# hb-task-step-review-address

Work through every unresolved review item in `review.md` for a task step. Normalises IDs and the status table first, then addresses each open item in order, committing after each one.

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

### 3. Read review.md

- read `$STEP_PATH/review.md`
- if the file does not exist, abort with: `error: review.md not found in $STEP_PATH — run /hb-task-step-review-init first`

### 4. Normalise review item IDs

Scan `## Notes` for all `### ` headings that are review items.

A heading is a review item if it either:

- already has the prefix `STEP-N-REVIEW-M:` (well-formed), or
- is a bare or partially-formed heading that should be a review item based on context

**For each item without a well-formed `STEP-N-REVIEW-M:` prefix:**

- assign the next available `M` value (monotonically increasing from 1, no duplicates across all items)
- if the title text already starts with a partial ID or a number, use best judgement to infer the intended `M`; fall back to next-available when ambiguous
- if an item is so ambiguous that no safe `M` can be assigned (e.g. two items with the same explicit number, or an ID that conflicts with a well-formed item), **STOP**: notify the user of the specific conflict and do not modify `review.md`; await user correction

Rewrite any headings that needed normalisation in `review.md`.

### 5. Sync status table

Rebuild the `## Status` table so it has exactly one row per review item (in ID order):

- items already in the table: preserve their existing `Resolution` cell as-is
- items missing from the table: add a new row with an empty `Resolution` cell
- rows in the table with no matching `## Notes` item: remove them

### 6. Commit normalisation (if review.md changed)

If `review.md` was modified in steps 4–5, commit it now by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) to do a step commit before proceeding.

### 7. Address each unresolved item

An item is **unresolved** when its `Resolution` cell in the status table is empty.

For each unresolved item, in ID order:

#### 7a. Read the item

Read the `### STEP-N-REVIEW-M:` section body from `## Notes`.

- if the body is empty or only a bare heading with no concern stated, **prompt the user** to fill in the concern before continuing with this item; await their response

#### 7b. Address the concern

- investigate and address the concern described in the item
- if the concern is unclear even after reading context, prompt the user for clarification before acting
- follow the note structure from [${CLAUDE_SKILL_DIR}/references/review-template.md](references/review-template.md):
  - state the original feedback
  - write a `**Resolution:**` section describing what was done (or why nothing was done, with evidence)
  - disposition: **Addressed**, **Assessed**, or **Deferred**

#### 7c. Update review.md

- update the `### STEP-N-REVIEW-M:` body in `## Notes` with the full note (concern + resolution)
- update the item's `Resolution` cell in the `## Status` table with the disposition and one-line summary:
  - `✅ Addressed — <one-line what changed>`
  - `✅ Assessed — <one-line kept-as-is + why>`
  - `⏭️ Deferred — <one-line + pointer to where>`

#### 7d. Commit

Commit `review.md` together with any files changed while addressing this item, by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md).

Repeat 7a–7d for the next unresolved item.

## Output

Report the step path, the final state of the status table, and the list of commits made. If any command fails, surface the error verbatim to the caller.
