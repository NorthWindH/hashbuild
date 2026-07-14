# Step 3 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-3-REVIEW-1 | ✅ Addressed — added "Create a new task" → `hb-task-create` row to Action Registry |
| STEP-3-REVIEW-2 |            |
| STEP-3-REVIEW-3 |            |

---

## Notes

### STEP-3-REVIEW-1: Register hb-task-create in the Action Registry

- **file(s):** `skills/hb-flow.md` (Step 5, Action Registry)
- The Action Registry table in Step 5 lists actions like "Plan task into steps", "Add a step", etc. but does not include an entry routing to `hb-task-create` (creating a brand-new task). Add a row for it so `/hb-flow` can route "create a task" style requests.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing
- **Resolution:** Added a "Create a new task" row to the Action Registry table, routing to `hb-task-create` with args shape `<author/task-id> [--flavor <slug>]` and example phrasings "create a new task", "start a task for X". Disposition: **Addressed**.

---

### STEP-3-REVIEW-2: Derive flavor from user's natural language in step-add/task-create

- **file(s):** `skills/hb-flow.md` (Step 5, near Action Registry)
- When `/hb-flow` routes to `hb-task-step-add` or `hb-task-create`, those skills should always derive their `--flavor` from the user's provided natural-language request rather than leaving it unset/interactive. The user can still drop or update the derived flavor during that skill's own confirmation step.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing

---

### STEP-3-REVIEW-3: Read facts store before invoking target skill

- **file(s):** `skills/hb-flow.md` (Step 8, Invoke)
- Step 8 (Invoke) currently calls the `Skill` tool directly without first reading `.hb/facts.md`. Add a step to read the facts store so relevant facts are available/passed along to the invoked skill.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing

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
