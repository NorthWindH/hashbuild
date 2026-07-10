# Step 6 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-6-REVIEW-1 | ✅ Addressed — write-after judgement clause now explicitly counts user session corrections/interruptions as a fact source, not just written-artifact content |
| STEP-6-REVIEW-2 |            |

---

## Notes

### STEP-6-REVIEW-1: Give attention to user input or interruptions

- **file(s):** `skills/hb-task-step-plan.md` (step 6, "Update facts store"), `skills/hb-task-plan.md` (step 8, "Update facts store")
- Not seeing input provided by interrupting step planning be picked up for fact writing
- Need to fix this

**Resolution:** The "Update facts store" judgement clause in both files scoped its
fact-gathering to "what drafting this `plan.md` revealed" / "what gap analysis and
breakdown revealed" — wording that reads as *what ended up in the written artifact*,
missing the common case where the user interrupts the session mid-flow to correct a
wrong assumption or add context that never gets written into `plan.md`/a step ticket.
Updated both judgement clauses (`skills/hb-task-step-plan.md:79`,
`skills/hb-task-plan.md:91`) to explicitly state that user corrections/clarifications
given by interrupting the session count as a fact source, not only what lands in the
drafted artifact. Also recorded a fact noting the same latent gap exists in
`hb-task-step-execute.md` step 7 and `hb-task-step-review-address.md` step 9f
(their wording says "based on what this execution revealed" without the same
explicit callout) — left as-is since fixing those is out of scope for this step.

**Disposition:** ✅ Addressed

### STEP-6-REVIEW-2: Still seeing user input not get written to facts

- For example, load this claude session: ad4cd403-cfa7-40ae-b075-0c8e9d6fbeb4
- after initial plan prompt (`/hb-task-step-plan northwind/hb-015/1`), user interrupted and added a correction, but that correction was never added to facts
- use this as a motivating example
- update procedure to ensure that user inputs and interruptions are recorded in facts if they apply to future planning and execution (like in this case)

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
