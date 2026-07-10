# Step 6 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-6-REVIEW-1 | ✅ Addressed — write-after judgement clause now explicitly counts user session corrections/interruptions as a fact source, not just written-artifact content |
| STEP-6-REVIEW-2 | ✅ Addressed — confirmed STEP-6-REVIEW-1's judgement-clause fix would have caught this session's interruption, and backfilled the missed fact (`skills/hb-*.md` is canonical source, `~/.claude/skills/hb-*/` is the installed copy) into `.hb/facts.md` |
| STEP-6-REVIEW-3 | ✅ Addressed — reassessed all 5 facts against the comment's 3 criteria; dropped 2 status-snapshot facts, kept 3 planning-relevant ones compressed to <=120 chars each |

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

**Resolution:** Read the referenced session transcript
(`~/.claude/projects/-Users-hasan-kamal-al-deen-repos-hashbuild/ad4cd403-cfa7-40ae-b075-0c8e9d6fbeb4.jsonl`).
The interruption was: after the assistant began `/hb-task-step-plan northwind/hb-015/1`,
the user cut in with "skills and references are in project in ./skills/hb-\*.md" —
correcting an assumption about where skill source files live. Checked
`skills/hb-task-step-plan.md:79` (the file this session was itself running) and confirmed
the write-after judgement clause already carries the STEP-6-REVIEW-1 fix — it now
explicitly names "corrections or clarifications the user gave by interrupting this
session" as a fact source. That wording, had it been in place during the ad4cd403
session, would have caught this exact interruption, so the procedural gap this item
points at is already closed by REVIEW-1.
What was still missing: the fact itself — that `skills/hb-*.md` in the project repo is
the canonical source for skill definitions, and `~/.claude/skills/hb-*/` is a separate
installed/deployed copy — was never backfilled into `.hb/facts.md`, even though this
same distinction had already tripped up sessions before (see resolutions in
`.hb/task/archive/northwind/hb-008-.../step-1-.../plan.md:190` and
`.hb/task/archive/northwind/hb-005-.../step-1-.../review.md:30`), meaning this is a
recurring point of confusion, not a one-off. Added that fact to `.hb/facts.md` now so
future sessions don't need a fourth correction.

**Disposition:** ✅ Addressed

### STEP-6-REVIEW-3: Facts store content is too long and duplicates info derivable from disk

- **file(s):** `.hb/facts.md`
- Current facts look bad:
  - all are too long; ideally a fact (the full fact) is less than 120 characters
  - the only one that is actually relevant between plannings is the one relating to `skills/hb-*.md`
  - all others can be inferred from the current state of files on disk as they are updated;
    meaning, they should not be facts (duplicating knowledge that can be found elsewhere)
- This signals that the fact collection approach is flawed; a task will be filed to
  improve it. For now:
  - reassess all facts for the following:
    - if the knowledge can be found elsewhere, it does not need to be here so drop it from here
    - all facts should be short (less than 120 characters IN TOTAL per fact)
    - focus ONLY on information that corrects a planning error, as that information will help future planning
- **source:** `TODO REVIEW` in commit `55a0bf4f2b93eeaf8d7d27d3d0aefd1773cc651f` — delete comment from source file after addressing

**Resolution:** Reassessed all five facts that were in `.hb/facts.md` against the three
criteria the comment specified: (1) drop what's inferable elsewhere, (2) keep each fact
under 120 characters total, (3) keep only what corrects a planning error and helps
future planning.
- Dropped the read-before/write-after-pattern-adoption fact and the write-after-clause-
  update-status fact: both were snapshots of which skill files currently contain which
  wording — fully recoverable by reading those skill files directly, and neither
  corrects a planning error (they're implementation status, not gotchas).
- Kept, compressed to one line each (<=120 chars):
  - the `skills/hb-*.md` vs `~/.claude/skills/hb-*/` canonical-source fact (the one the
    comment itself called out as relevant) — not fully inferable from disk alone and
    has caused repeated real confusion (hb-005/step-1, hb-008/step-1, this step's
    STEP-6-REVIEW-2).
  - the hb-015/step-1 deviation fact (Jira push logic deleted, needs re-authoring in
    hb-015/step-5, recoverable via a specific git commit) — this is exactly a
    "corrects a planning error, helps future planning" fact: hb-015/step-5 planning
    would otherwise miss that this logic needs to be re-authored from git history.
  - the hb-015/step-2 allowed-tools decision fact (Read/WebFetch omission is deliberate,
    already litigated) — prevents a future session from "fixing" something that was
    already explicitly rejected.
  The mechanism-level concern ("fact collection approach is flawed") is explicitly
  out of scope for this cleanup per the comment's own wording ("will file a task to
  improve this") — not addressed here.

**Disposition:** ✅ Addressed

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
