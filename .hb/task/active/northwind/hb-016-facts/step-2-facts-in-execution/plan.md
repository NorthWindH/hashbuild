# Step 2 Plan — Wire Facts Store Into Step Execution

This step wires the facts store (`hb-sdk facts read`/`write`, shipped in step-0;
already consumed by planning in step-1) into `hb-task-step-execute.md`, the one
skill the parent ticket names that step-1 explicitly deferred
(`step-1-read-facts-in-planning/plan.md:158-159`, "Wire facts into
`hb-task-step-execute` in this same step — rejected per this ticket's own
Out-of-scope section (that's step-2's job)"). Today `hb-task-step-execute.md`
has zero references to `facts` (`grep -c facts skills/hb-task-step-execute.md`
→ `0`) — a step can execute without ever seeing, or updating, the project's
recorded facts, and any fact a step's execution renders stale (e.g. "skills
live in the project under `./skills`" if that ever changed) silently rots.
This is a documentation-only change to one skill `.md` file: one new step
before "Execute the plan" (read), one new step after it and before "Commit"
(re-read + reconcile + write), and one edited sentence in the existing Commit
step so facts-store changes ride in the same commit as the code they
describe. No `hb_sdk` Python changes — `facts read`/`facts write` already
have the exact contract this step depends on (step-0, re-confirmed live in
step-1). The externally observable effect: running `/hb-task-step-execute`
now surfaces the current facts store to the model before it executes
`plan.md`, and after execution reconciles that store (pruning stale facts,
adding durable new ones) before the step's commit lands.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-sdk facts
read`/`write` CLI from step-0 (`skills/scripts/hb_sdk/facts.py`,
`skills/references/facts-template.md`) and mirrors the planning-side wiring
pattern step-1 already established in `skills/hb-task-step-plan.md` and
`skills/hb-task-plan.md`. This step is purely a consumer of that CLI surface,
not a change to it. This plan targets `skills/hb-task-step-execute.md` as it
exists now (`skills/hb-task-step-execute.md:1-94`).

> **Design decision — the post-execution read is a fresh `hb-sdk facts read`
> call, not a reuse of the pre-execution `$FACTS` variable.** AC2.1 says the
> step must "re-read the current facts store," and "Execute the plan" (§2,
> step 5) is exactly the step that may take arbitrary, possibly long-running
> actions per `plan.md` — nothing prevents a concurrent or plan-driven change
> to `.hb/facts.md` between the pre- and post-execution reads (and even
> without one, re-reading is the literal, cheap, and unambiguous reading of
> the ticket's own wording over relying on step 4's now-possibly-stale
> variable). The new post-execution step therefore issues its own `facts
> read` into a distinct variable, `$FACTS_AFTER` — see §2.2 and the
> AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `grep -c facts skills/hb-task-step-execute.md` → `0` — the skill currently
  has no facts-store references at all, confirming this step is purely
  additive.
- `skills/hb-task-step-execute.md`'s current Steps
  (`skills/hb-task-step-execute.md:27-93`):
  1. Help check (`:29-31`)
  2. Resolve step folder (`:33-49`) — resolves `$STEP_PATH`, `$N`,
     `$TASK_REF`
  3. Read plan (`:51-58`) — reads `$STEP_PATH/plan.md`; aborts + records
     failure state if missing
  4. Execute the plan (`:60-63`) — two bullets: carry out every task in
     `plan.md`; follow constraints/verification stated in the plan
  5. Write execution summary (`:65-73`) — captures `$SLUG` from `hb-sdk task
     step execution-slug`, writes `$STEP_PATH/$SLUG`
  6. Commit (`:75-77`) — follows `committing.md`, "including all files
     changed during execution and `$STEP_PATH/$SLUG`"; tag `step-execute`
  7. Prompt user (`:79-83`)
  8. Record execution state (`:85-89`)
- `hb-task-step-plan.md`'s step-1 wiring (already shipped, at
  `skills/hb-task-step-plan.md`) is the direct structural precedent this step
  mirrors for the *read* half: a bare bash fence calling
  `${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read`, two bullets ("captures
  stdout as `$FACTS`", "never errors ... proceeds unaffected"), inserted as
  its own numbered step immediately before the step that consumes it.
- `hb-sdk facts read`/`facts write` contracts (step-0, re-verified live by
  step-1): `read` never errors and returns `""` when `.hb/facts.md` or `.hb/`
  itself is missing; `write` dies via `path_hb_asserted()` only if `.hb/`
  itself is missing — and by the time any step of this repo's own workflow
  runs `hb-task-step-execute`, `.hb/` already exists (task/step folders
  already live under it), so `write` will not die in normal operation.
- `.hb/facts.md` is **not** git-ignored — confirmed via `git check-ignore -v
  .hb/facts.md` (exit 1, no match) against `.gitignore`, whose only `.hb`-scoped
  entry is `/.hb/.state.ignore.json` (the JSON state file, deliberately
  ignored per its own `.ignore` naming convention). This is the load-bearing
  fact behind AC3: unlike `.hb/.state.ignore.json`, a changed `.hb/facts.md`
  shows up as a normal modified/untracked path in `git status --short -b`
  and must be named explicitly for the Commit step to stage it, since it
  lives outside `$STEP_PATH` and the existing Commit step's wording ("all
  files changed during execution and `$STEP_PATH/$SLUG`") does not
  unambiguously cover a file changed by a *new* step that isn't "Execute the
  plan" itself.
- `skills/references/facts-template.md` (shipped in step-0) is already
  registered in `skills/references/references-toc.md`, which every skill
  file (including `hb-task-step-execute.md`) injects verbatim via `! cat
  ${CLAUDE_SKILL_DIR}/references/references-toc.md` in its own "Reference
  Files" section — no new reference-file registration needed for this step.
- Neither `allowed-tools` change is needed:
  `skills/hb-task-step-execute.md:9` already includes
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` (and, redundantly, a bare
  `Bash(*)`), so both the new `facts read` and `facts write` invocations are
  already permitted.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `.hb/facts.md` has content, run `/hb-task-step-execute <step_ref>` | content never read; step executes from `plan.md` alone; facts store untouched regardless of what execution reveals | `$FACTS` captured before execution and taken into account; after execution, `$FACTS_AFTER` is re-read and reconciled (stale facts pruned/corrected, durable new facts added) before commit |
| `.hb/facts.md` missing or `.hb/` missing, run `/hb-task-step-execute <step_ref>` | n/a | both reads return `""`; execution proceeds identically to before this change; the post-execution step only calls `facts write` if new/changed content is warranted (and `.hb/` already exists by construction whenever a step folder exists, so `write` will not die in practice) |
| A fact becomes stale during execution (e.g. a path or convention changes) | stays in `.hb/facts.md` indefinitely, silently misleading future planning/execution | corrected or removed by the new post-execution step, in the same commit as the code change that made it stale |

Purely additive to the skill's Steps section: existing steps 1–3 are
unchanged in content (only renumbered where they shift), and no existing
step's *behavior* changes except the Commit step's wording, which is
extended (not altered) to name an additional file class it stages.

### 0.2 Non-regression proof

Additive-only at the document level: this step inserts two new steps and
edits one sentence in the existing Commit step; it does not remove, reorder
the *content* of, or alter the pass/fail contract of any existing step.
`hb-sdk facts read` is read-only with no side effects (step-0 `read_facts()`
never writes) and never errors, so inserting it cannot cause a
previously-succeeding invocation to fail. `hb-sdk facts write` is only
invoked when the new step's judgement determines a change is warranted; when
it is not, nothing is written and behavior is identical to before this
change. `$STEP_PATH`/`$N`/`$TASK_REF` resolution, plan-reading, plan
execution itself, execution-summary writing, the prompt step, and the
state-record step are all untouched in substance.

---

## 1. Design overview

Two linear insertions plus one edit, in one file:

```
skills/hb-task-step-execute.md:
  1 Help check                (unchanged)
  2 Resolve step folder       (unchanged)
  3 Read plan                 (unchanged)
  4 Read facts store          (NEW)
  5 Execute the plan          (was 4; +1 instruction bullet)
  6 Write execution summary   (was 5; unchanged)
  7 Update facts store        (NEW)
  8 Commit                    (was 6; wording extended to name facts-store changes)
  9 Prompt user               (was 7; unchanged)
  10 Record execution state   (was 8; unchanged)
```

Step 4 ("Read facts store") mirrors `hb-task-step-plan.md`'s equivalent step
exactly — a bare bash fence plus the two standard bullets. Step 7 ("Update
facts store") is new in shape (no prior step in this repo re-reads and
conditionally re-writes the store), but its internal logic is fully
specified by the ticket and `facts-template.md`'s existing guidance: read →
apply judgement (prune/correct/add, weighed against the 100/1000/120 size
guidance) → write only if content changed.

**Alternatives considered and rejected:**

- *Reuse `$FACTS` (from step 4) instead of a fresh `$FACTS_AFTER` read in
  step 7* — rejected per the design decision above: AC2.1 says "re-read,"
  and execution may take arbitrary, possibly long-running actions that could
  change `.hb/facts.md` out from under a stale variable.
- *Merge "Update facts store" into "Write execution summary"* — rejected:
  the execution summary is a factual record of what happened (per
  `execution-template.md`), not a place to compose facts-store edits;
  keeping them separate keeps each step's diff and purpose isolated, mirrors
  step-1's own precedent of adding new steps rather than editing existing
  ones' content, and lets the Commit step's file list (§2.3) point at a
  single, clearly-named prior step.
- *Place "Update facts store" before "Write execution summary" instead of
  after* — rejected: no AC requires a specific ordering relative to the
  summary (only "after execution and before the commit step"), and ordering
  it after the summary lets the reconciliation step's judgement draw on the
  now-written summary text as one more source of "what happened this
  execution" alongside direct observation, at no extra cost.
- *Add a conditional branch in step 4 for "if `$FACTS` is empty"* —
  rejected, same reasoning as step-1: `read_facts()` already returns `""`
  uniformly for "no file" and "no `.hb/` at all," so there's no
  distinct-missing-vs-empty case to branch on.
- *Have step 7 always call `facts write`, even with unchanged content* —
  rejected: `facts write` is a full overwrite (step-0 §2), so an
  unconditional call is harmless but pointless busywork and would make every
  execution touch `.hb/facts.md` in git status even when nothing changed,
  needlessly widening the Commit step's file list on every single step of
  every task. Step 7 only writes when judgement finds a real change.

---

## 2. Skill-file changes — specification

One prose/structure change to `skills/hb-task-step-execute.md`'s Steps
section; no code module. Specified as two insertions plus one edit.

### 2.1 New step 4 — "Read facts store"

Inserted between current step 3 ("Read plan") and current step 4 ("Execute
the plan"), renumbering step 4 onward by +1:

```markdown
### 4. Read facts store

\`\`\`bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
\`\`\`

- captures stdout as `$FACTS` (may be empty)
- never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds
  unaffected — no error, no blocking prompt
```

### 2.2 Edited step 5 — "Execute the plan" (was step 4)

One bullet added to the existing two, content otherwise unchanged:

> - take `$FACTS` into account when executing the plan — if a fact is
>   relevant to this step's implementation, apply it without requiring it be
>   restated in `plan.md`

### 2.3 New step 7 — "Update facts store"

Inserted between current step 5 ("Write execution summary", renumbered from
step 5 to 6) and current step 6 ("Commit", renumbered to 8):

```markdown
### 7. Update facts store

\`\`\`bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
\`\`\`

- captures stdout as `$FACTS_AFTER` (may be empty)
- read [${CLAUDE_SKILL_DIR}/references/facts-template.md](references/facts-template.md)
  for size guidance (target <= 100 lines, hard max 1000 lines, <= 120
  chars/line) before composing any changes
- using judgement, based on what this execution revealed:
  - remove or correct any fact in `$FACTS_AFTER` found to be stale or
    incorrect
  - add new facts discovered during this execution only when they are
    likely to matter for future planning or execution, weighed against the
    size guidance
  - if pruning is needed to stay within guidance, prune stale/superseded
    facts before adding new ones
- if the composed content differs from `$FACTS_AFTER`:
  \`\`\`bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts write "<composed content>"
  \`\`\`
- if the composed content is unchanged from `$FACTS_AFTER`, skip the write —
  no-op
```

### 2.4 Edited step 8 — "Commit" (was step 6)

Wording extended to name the facts-store file explicitly, since it lives
outside `$STEP_PATH` and would otherwise be ambiguous under "all files
changed during execution":

> create a step commit by following
> [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md)
> including all files changed during execution, `$STEP_PATH/$SLUG`, and
> `.hb/facts.md` if it was changed in the previous step; pass `--tag
> step-execute`

- All other steps (renumbered 1, 2, 3, 6, 9, 10) keep their exact current
  wording.
- **Failure / degradation contract:** identical to `facts read`/`facts
  write` themselves. `read` never errors — an empty `$FACTS`/`$FACTS_AFTER`
  means "take into account" / "reconcile" are trivially satisfied by doing
  nothing. `write` dies only if `.hb/` itself is missing, which cannot occur
  mid-way through `hb-task-step-execute` (the step folder being executed
  already lives under `.hb/`).
- **Conflict resolution:** N/A — `facts write` is a last-writer-wins full
  overwrite; step 7 composes the complete replacement content itself, so
  there is no merge logic to specify.

---

## 3. Integration / wiring

- No frontmatter changes — `skills/hb-task-step-execute.md:9` already
  includes `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` (and a bare
  `Bash(*)`), covering both new `facts` invocations.
- No `references-toc.md` change — `facts-template.md` is already registered
  there (step-0) and already surfaces in every skill's injected Reference
  Files table, including this one.
- No change to `skills/scripts/hb_sdk/facts.py`, `common.py`, or
  `__main__.py` — this step is a pure consumer of the step-0 CLI surface,
  identical in spirit to step-1's wiring.
- No build config, dependency manifest, or entry-point script changes.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-step-execute.md` | **edit** — insert new step 4 ("Read facts store"); add one bullet to step 5 ("Execute the plan"); insert new step 7 ("Update facts store"); extend step 8's ("Commit") wording to name `.hb/facts.md`; renumber steps 6, 9, 10 accordingly |

No other files change — no Python, no tests, no other skill `.md` file, no
dependency manifest. (`.hb/facts.md` itself may change at *run time* when
this plan is executed, per §2.3, but that is a data file this step's own
future execution may write, not a source file this plan edits.)

---

## 5. Tests

Same precedent as step-1 (`step-1-read-facts-in-planning/plan.md:257-265`):
this repo's automated suite (`tests/skills/scripts/hb_sdk/`) covers the
`hb_sdk` Python package, not skill-markdown prose, and this step introduces
no Python. Verification is manual/behavioral (§6).

- **Happy path (AC1):** manually drive `/hb-task-step-execute` on a step
  whose `plan.md` concerns skill files, with a fact recorded via `hb-sdk
  facts write` stating "skills live in the project under `./skills`" —
  confirm the model applies that fact during execution without it being
  restated in `plan.md`.
- **Reconciliation path (AC2):** manually drive `/hb-task-step-execute` on a
  step whose execution reveals a fact in `.hb/facts.md` to be stale (e.g.
  edit the fact to reference a wrong path, then execute a step that touches
  that path) — confirm the post-execution step corrects or removes it, and
  that a genuinely new, durable fact discovered during execution gets added
  (weighed against the 100/1000/120 guidance).
- **Commit inclusion (AC3):** after the reconciliation-path run above,
  confirm `.hb/facts.md`'s change is present in the resulting commit (`git
  show --stat <sha>` includes `.hb/facts.md`).
- **End-to-end (AC4, parent ticket AC5):** record "skills live in the
  project under `./skills`" via `hb-sdk facts write`; run
  `/hb-task-step-plan` or `/hb-task-step-execute` and confirm it's read back
  (step-1/this step); then run an execution that finds it stale and confirm
  it's removed or updated by this step's new step 7 — this is the exact
  chain the parent ticket's AC5 and this step's own AC4 describe.
- **Missing-facts case:** manually drive `/hb-task-step-execute` in a state
  where `.hb/facts.md` does not exist — confirm the step proceeds to
  completion with no error and no blocking prompt, and step 7 either skips
  the write (no new facts warranted) or creates the file for the first time
  (a genuinely new, durable fact was discovered).
- **Non-regression:** re-run `/hb-task-step-execute` on an existing planned
  step from this repo's own `.hb/` state and confirm plan-reading, plan
  execution itself, execution-summary writing, the prompt step, and the
  state-record step are unchanged from before this edit.

---

## 6. Verification (after implementation)

1. **Static check:** `grep -c "facts read" skills/hb-task-step-execute.md` →
   `2` (steps 4 and 7); `grep -c "facts write" skills/hb-task-step-execute.md`
   → `1` (step 7); `grep -n "^### " skills/hb-task-step-execute.md` shows the
   expected renumbered sequence 1–10 with no gaps or duplicate numbers.
2. **Baseline:** capture the current rendered Steps section
   (`git show HEAD:skills/hb-task-step-execute.md`) before editing, to diff
   against after.
3. **Exercise the real change, empty-facts case:** in a scratch project with
   `.hb/` initialized but no `.hb/facts.md`, run
   `${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read` directly and confirm empty
   stdout + exit 0 — the condition steps 4 and 7 both rely on to never
   block.
4. **Exercise the real change, populated + reconciliation case:** `hb-sdk
   facts write "- skills live in the project under \`./skills\`"`, then
   drive `/hb-task-step-execute` on a step whose plan touches skill files;
   confirm the execution reflects the fact, and — in a separate run where
   the fact is deliberately made stale first — confirm step 7 corrects or
   removes it and the change lands in the step's commit.
5. **Per-AC checks:**
   - AC1: new step 4 present, calls `hb-sdk facts read`, and step 5
     ("Execute the plan") contains the "take `$FACTS` into account" bullet.
   - AC2.1–AC2.3: new step 7 present, re-reads via `hb-sdk facts read` into
     `$FACTS_AFTER`, and its bullets cover stale-fact removal/correction,
     judgement-gated new-fact addition, and the size guidance from step-0.
   - AC3: step 8 ("Commit")'s wording names `.hb/facts.md`; manual run in
     step 4 above shows it staged and committed alongside the code change.
   - AC4: manual run in step 4 above demonstrates the full write → read-back
     → stale → corrected chain.
6. **Scope check:** `git diff --stat` shows only
   `skills/hb-task-step-execute.md` changed (plus, at execution time,
   whatever `.hb/facts.md` change step 7 itself makes — not a plan-time
   edit); no `.py` file, test file, or other skill `.md` file touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 (new step 4), §2.2 (step 5 bullet) | |
| 2.1 | §2.3 (new step 7 — `$FACTS_AFTER` re-read) | |
| 2.2 | §2.3 (stale-fact removal/correction bullet) | |
| 2.3 | §2.3 (judgement-gated new-fact bullet, weighed against `facts-template.md` guidance) | |
| 3 | §2.4 (Commit step wording names `.hb/facts.md`), §0 (`.hb/facts.md` not git-ignored) | |
| 4 | §6 step 4 (manual verification) | end-to-end manual check per this step's own AC4 and the parent ticket's AC5 |

---

## 8. Out of scope (per ticket)

- Planning-time reads — already covered by step-1
  (`skills/hb-task-step-plan.md`, `skills/hb-task-plan.md`).
- Automatic/programmatic detection of which facts are stale — step 7 relies
  entirely on the executing agent's judgement, per the parent ticket's Out
  of scope; no code enforces or scores staleness.
- Hard enforcement of the 100/1000/120 size limits — `facts-template.md`
  states them as guidance only; this step's step 7 does not add validation
  logic to `hb_sdk`.
