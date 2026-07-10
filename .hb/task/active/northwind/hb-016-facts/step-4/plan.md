# Step 4 Plan — Wire Facts Store Into Review Addressing

This step wires the facts store (`hb-sdk facts read`/`write`, shipped in step-0;
already consumed by planning in step-1 and execution in step-2) into
`hb-task-step-review-address.md`'s per-item addressing loop (§9) — the one
long-running, code-changing loop in this repo's skill set that the parent
ticket named (`hb-task-step-review-address`) but step-1/step-2 explicitly did
not touch, since it wasn't among the skills their own tickets scoped. Today
`hb-task-step-review-address.md` has zero references to `facts`
(`grep -c facts skills/hb-task-step-review-address.md` → `0`): an item can be
addressed — arbitrary investigation and code changes — without ever seeing,
or updating, the project's recorded facts, and any fact that addressing an
item renders stale silently rots exactly like the gap step-2 closed for plain
execution. This is a documentation-only change to one skill `.md` file: one
new sub-step before the existing "Read the item"/"Address the concern"
sub-steps (9a/9b), one new sub-step after "Address the concern" and before
"Commit," and one edited sentence in the existing per-item Commit sub-step so
facts-store changes ride in the same commit as the review item they
describe. No `hb_sdk` Python changes — `facts read`/`facts write` already
have the exact contract this step depends on (step-0, re-confirmed live by
step-1 and step-2). The externally observable effect: running
`/hb-task-step-review-address` now surfaces the current facts store to the
model before it addresses each review item, and after addressing that item
reconciles the store (pruning stale facts, adding durable new ones) before
that item's own commit lands.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-sdk facts
read`/`write` CLI from step-0 (`skills/scripts/hb_sdk/facts.py`,
`skills/references/facts-template.md`) and mirrors the wiring pattern step-1
established for planning (`skills/hb-task-step-plan.md`) and step-2
established for execution (`skills/hb-task-step-execute.md`:
`step-2-facts-in-execution/plan.md`). This step is purely a consumer of that
CLI surface, not a change to it. This plan targets
`skills/hb-task-step-review-address.md` as it exists now
(`skills/hb-task-step-review-address.md:174-233`, section "9. Address each
unresolved item").

> **Design decision — facts are read and reconciled per-item, inside the
> 9a–9g loop, not once per skill invocation.** The parent step-4 ticket's
> Background is explicit that this extends "the same read-before/write-after
> pattern" to review addressing "so facts discovered stale or newly learned
> while resolving a review item are captured just as they would be during
> execution" — and AC1/AC2 both anchor the new sub-steps to the existing
> per-item sub-steps 9a/9b and 9e (old numbering), not to the skill's
> top-level Steps 1–11. A single invocation of
> `/hb-task-step-review-address` addresses N unresolved items in one pass
> (§9's "Repeat 9a–9e for the next unresolved item"); reading/reconciling
> facts once for the whole invocation would mean item 2's addressing can't
> see a fact item 1 just corrected, and item 1's own commit (9e/AC3) would
> never carry the facts-store change it caused (a per-invocation read/write
> straddles multiple item commits, breaking AC3 outright). Per-item
> read/reconcile is therefore the only placement that satisfies AC1–AC3
> simultaneously. See §1 for the full sub-step reordering and the
> AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `grep -c facts skills/hb-task-step-review-address.md` → `0` — the skill
  currently has no facts-store references at all, confirming this step is
  purely additive.
- `skills/hb-task-step-review-address.md`'s current section 9 sub-steps
  (`skills/hb-task-step-review-address.md:174-217`), inside "For each
  unresolved item, in ID order":
  - 9a. Read the item (`:180-184`) — reads the `### STEP-N-REVIEW-M:` body;
    prompts user if empty
  - 9b. Address the concern (`:186-193`) — investigates and addresses;
    prompts if unclear; writes per `review-template.md`'s note structure
  - 9c. Update review.md (`:195-201`) — updates the `## Notes` body and the
    `## Status` table's `Resolution` cell
  - 9d. Delete TODO REVIEW comment(s) (`:203-211`) — removes sourced `TODO
    REVIEW` marker + continuation lines
  - 9e. Commit (`:213-215`) — follows `committing.md`, "including any files
    changed while addressing this item"; tag `step-review`
  - followed by "Repeat 9a–9e for the next unresolved item." (`:217`)
- `hb-task-step-plan.md`'s step-1 wiring and `hb-task-step-execute.md`'s
  step-2 wiring (both already shipped) are the direct structural precedent
  this step mirrors: a bare bash fence calling
  `${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read`, two bullets ("captures
  stdout as `$FACTS`"/`$FACTS_AFTER`, "never errors ... proceeds
  unaffected"), inserted as its own step immediately before the step that
  consumes it (pre-read) or immediately before the commit step (post-read +
  reconcile), per `step-2-facts-in-execution/plan.md:192-247`.
- `hb-sdk facts read`/`facts write` contracts (step-0, re-verified live by
  step-1 and step-2): `read` never errors and returns `""` when
  `.hb/facts.md` or `.hb/` itself is missing; `write` dies only if `.hb/`
  itself is missing — and by the time any step of this repo's own workflow
  reaches `hb-task-step-review-address` (a `review.md` already exists under
  a step folder), `.hb/` already exists, so `write` will not die in normal
  operation.
- `.hb/facts.md` is **not** git-ignored (re-confirmed at step-2:
  `git check-ignore -v .hb/facts.md` → exit 1, no match). It lives outside
  `$STEP_PATH`, so — exactly as step-2 found for `hb-task-step-execute.md`'s
  Commit step — the existing 9e Commit wording ("any files changed while
  addressing this item") does not unambiguously cover it; it must be named
  explicitly.
- `skills/references/facts-template.md` (shipped in step-0) is already
  registered in `skills/references/references-toc.md:15`, which
  `hb-task-step-review-address.md`'s own "## Reference Files" section
  already injects verbatim via
  `!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`` (`:29`) — no new
  reference-file registration needed for this step.
- No `allowed-tools` change needed:
  `skills/hb-task-step-review-address.md:11` already includes
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` (and, redundantly, a bare
  `Bash(*)`), so both the new `facts read` and `facts write` invocations are
  already permitted.
- `committing.md`'s staging rule (added in this same parent task's step-3:
  "if this skill's execution updated `.hb/facts.md`, include it among the
  relevant files staged," `skills/references/committing.md:65-66`) already
  makes the 9e/9g Commit sub-step's `committing.md` follow-through
  facts-aware generically — this step's edit to 9e/9g's own prose (§2.4)
  makes that explicit at the point of use, matching step-2's precedent of
  naming the file directly rather than relying solely on the generic rule.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `.hb/facts.md` has content, address an item via `/hb-task-step-review-address` | content never read; the item is investigated and addressed from ticket/code context alone; facts store untouched regardless of what addressing reveals | `$FACTS` captured before addressing (9a) and taken into account (9c); after addressing, `$FACTS_AFTER` is re-read and reconciled (9f) before that item's own commit (9g) |
| `.hb/facts.md` missing or `.hb/` missing, address an item | n/a | both reads return `""`; addressing proceeds identically to before this change; the reconciliation sub-step only calls `facts write` if new/changed content is warranted |
| A fact becomes stale while addressing one item, and a later unresolved item is addressed in the same invocation | stays in `.hb/facts.md`, silently misleading the next item's addressing within the same run | corrected or removed by 9f before item 1's own commit; item 2's 9a re-read (next loop iteration) sees the corrected store |

Purely additive to section 9: the existing 9a–9e sub-steps are unchanged in
content (only relettered where they shift, plus one added bullet in
addressing and one extended sentence in Commit); no other section of the
skill file changes, and the top-level Steps 1–8, 10, 11 keep their exact
current numbering and wording.

### 0.2 Non-regression proof

Additive-only at the document level: this step inserts two new sub-steps
(9a, 9f in the new lettering) and edits two sentences (the addressing
sub-step gains one bullet; the Commit sub-step's file list gains one clause)
within section 9; it does not remove, reorder the *content* of, or alter the
pass/fail contract of 9b ("Read the item"), 9d ("Update review.md"), or 9e
("Delete TODO REVIEW comment(s)") relative to their old-lettered selves.
`hb-sdk facts read` is read-only with no side effects and never errors, so
inserting it cannot cause a previously-succeeding invocation to fail.
`hb-sdk facts write` is only invoked when 9f's judgement determines a change
is warranted; when it is not, nothing is written and behavior is identical
to before this change. Sections 1–8 and 10–11 (help check, folder
resolution, `review.md` creation, TODO-scan-and-append, ID normalisation,
status-table sync, prompt, state-record) are untouched in substance — this
step edits only inside section 9's per-item loop.

---

## 1. Design overview

Two linear insertions plus two edits, entirely inside section 9 of one file:

```
skills/hb-task-step-review-address.md, section "9. Address each unresolved item":
  9a Read facts store                 (NEW)
  9b Read the item                    (was 9a; unchanged)
  9c Address the concern              (was 9b; +1 instruction bullet)
  9d Update review.md                 (was 9c; unchanged)
  9e Delete TODO REVIEW comment(s)    (was 9d; unchanged)
  9f Update facts store               (NEW)
  9g Commit                           (was 9e; wording extended to name facts-store changes)
  "Repeat 9a–9g for the next unresolved item."   (was "Repeat 9a–9e"; updated)
```

9a mirrors `hb-task-step-plan.md`'s / `hb-task-step-execute.md`'s pre-read
step exactly — a bare bash fence plus the two standard bullets, scoped here
to run once per item rather than once per invocation (per the Design
decision above). 9f mirrors `hb-task-step-execute.md`'s step-2 "Update facts
store" step exactly in internal logic (read → judgement-gated
prune/correct/add, weighed against the 100/1000/120 size guidance from
`facts-template.md` → write only if content changed), placed after the item's
substantive work (9b–9e: read, address, record, delete markers) and before
its commit (9g), matching step-2's placement of its analogous step
immediately before Commit.

**Alternatives considered and rejected:**

- *Read/reconcile facts once per skill invocation (before/after the whole
  section-9 loop) instead of once per item* — rejected per the Design
  decision above: breaks AC3 (a per-invocation write straddles multiple
  items' commits) and can't reflect item-to-item corrections within one run.
- *Reuse `$FACTS` (from 9a) instead of a fresh `$FACTS_AFTER` read in 9f* —
  rejected, same reasoning as step-2: 9b–9e may take arbitrary,
  possibly long-running investigative/code-changing actions, and nothing
  prevents a concurrent or item-driven change to `.hb/facts.md` between 9a
  and 9f; a fresh read is cheap and matches the ticket's own "re-reads" (AC2.1)
  wording exactly.
- *Fold the "take `$FACTS` into account" instruction into 9a itself rather
  than as a bullet on 9c ("Address the concern")* — rejected: 9a is a pure
  mechanical read (mirrors the `$FACTS`-read shape used everywhere else in
  this repo); the instruction to *apply* the facts belongs on the sub-step
  that does the applying, per AC1's own phrasing ("the item-addressing step
  is instructed to take the returned facts into account").
- *Place 9f ("Update facts store") before 9d/9e (immediately after "Address
  the concern") instead of after them* — rejected: AC2 only requires
  "before its commit (9e [old numbering])"; placing it after `review.md` is
  updated and TODO markers are deleted lets 9f's judgement draw on the
  now-finalized note/resolution text and the fully-cleaned-up source files
  as additional signal for what's worth recording, at no extra cost — the
  same ordering rationale step-2 used for placing its analogous step after
  "Write execution summary."
- *Have 9f always call `facts write`, even with unchanged content* —
  rejected: `facts write` is a full overwrite, so an unconditional call is
  harmless but pointless busywork and would make every addressed item touch
  `.hb/facts.md` in git status even when nothing changed. 9f only writes
  when judgement finds a real change.

---

## 2. Skill-file changes — specification

One prose/structure change to
`skills/hb-task-step-review-address.md`'s section 9; no code module.
Specified as two insertions plus two edits, all within section 9.

### 2.1 New sub-step 9a — "Read facts store"

Inserted as the first sub-step of "For each unresolved item, in ID order,"
before the sub-step currently lettered 9a ("Read the item"), reslottering
9a→9b, 9b→9c, 9c→9d, 9d→9e, 9e→9g (with new 9f inserted per §2.3):

```markdown
#### 9a. Read facts store

\`\`\`bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
\`\`\`

- captures stdout as `$FACTS` (may be empty)
- never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds
  unaffected — no error, no blocking prompt
```

### 2.2 Edited sub-step 9c — "Address the concern" (was 9b)

One bullet added after the existing three, content otherwise unchanged:

> - take `$FACTS` into account when addressing this concern — if a fact is
>   relevant to this item, apply it without requiring it be restated in the
>   review item

### 2.3 New sub-step 9f — "Update facts store"

Inserted between the sub-step now lettered 9e ("Delete TODO REVIEW
comment(s)," was 9d) and the sub-step now lettered 9g ("Commit," was 9e):

```markdown
#### 9f. Update facts store

\`\`\`bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
\`\`\`

- captures stdout as `$FACTS_AFTER` (may be empty)
- read [${CLAUDE_SKILL_DIR}/references/facts-template.md](references/facts-template.md)
  for size guidance (target <= 100 lines, hard max 1000 lines, <= 120
  chars/line) before composing any changes
- using judgement, based on what addressing this item revealed:
  - remove or correct any fact in `$FACTS_AFTER` found to be stale or
    incorrect
  - add new facts discovered while addressing this item only when they are
    likely to matter for future planning/execution/review, weighed against
    the size guidance
  - if pruning is needed to stay within guidance, prune stale/superseded
    facts before adding new ones
- if the composed content differs from `$FACTS_AFTER`:
  \`\`\`bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts write "<composed content>"
  \`\`\`
- if the composed content is unchanged from `$FACTS_AFTER`, skip the write —
  no-op
```

### 2.4 Edited sub-step 9g — "Commit" (was 9e)

Wording extended to name the facts-store file explicitly, since it lives
outside `$STEP_PATH` and would otherwise be ambiguous under "any files
changed while addressing this item":

> Commit `review.md` as a step commit together with any files changed while
> addressing this item (including source files where `TODO REVIEW` comments
> were deleted, and `.hb/facts.md` if it was changed in the previous
> sub-step), by following
> [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md);
> pass `--tag step-review`.

### 2.5 Edited loop-repeat line

The line following the sub-steps, "Repeat 9a–9e for the next unresolved
item," is updated to "Repeat 9a–9g for the next unresolved item."

- All other sub-steps (relettered 9b, 9d, 9e) keep their exact current
  wording; all other top-level Steps (1–8, 10, 11) are untouched.
- **Failure / degradation contract:** identical to `facts read`/`facts
  write` themselves. `read` never errors — an empty `$FACTS`/`$FACTS_AFTER`
  means "take into account" / "reconcile" are trivially satisfied by doing
  nothing. `write` dies only if `.hb/` itself is missing, which cannot occur
  mid-way through `hb-task-step-review-address` (a `review.md` already
  exists under the step folder being addressed, which itself lives under
  `.hb/`).
- **Conflict resolution:** N/A — `facts write` is a last-writer-wins full
  overwrite; 9f composes the complete replacement content itself, so there
  is no merge logic to specify. Concurrent edits across items in the same
  invocation are naturally serialized since section 9's items are addressed
  one at a time, in ID order.

---

## 3. Integration / wiring

- No frontmatter changes — `skills/hb-task-step-review-address.md:11`
  already includes `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` (and a bare
  `Bash(*)`), covering both new `facts` invocations.
- No `references-toc.md` change — `facts-template.md` is already registered
  there (step-0) and already surfaces in this skill's injected Reference
  Files section.
- No change to `skills/scripts/hb_sdk/facts.py`, `common.py`, or
  `__main__.py` — this step is a pure consumer of the step-0 CLI surface,
  identical in spirit to step-1's and step-2's wiring.
- No change to `skills/references/committing.md` — its existing
  facts-staging rule (from this task's step-3) already covers the 9g Commit
  sub-step generically; §2.4's edit only makes that explicit at the point of
  use.
- No build config, dependency manifest, or entry-point script changes.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-step-review-address.md` | **edit** — insert new sub-step 9a ("Read facts store"); add one bullet to sub-step 9c ("Address the concern," was 9b); insert new sub-step 9f ("Update facts store") between "Delete TODO REVIEW comment(s)" (9e, was 9d) and "Commit" (9g, was 9e); extend 9g's wording to name `.hb/facts.md`; update the "Repeat 9a–9e" line to "Repeat 9a–9g"; reletter unchanged sub-steps 9b/9d/9e accordingly |

No other files change — no Python, no tests, no other skill `.md` file, no
dependency manifest. (`.hb/facts.md` itself may change at *run time* when
this plan is executed against a real review item, per §2.3, but that is a
data file this step's own future execution may write, not a source file this
plan edits.)

---

## 5. Tests

Same precedent as step-1 and step-2
(`step-2-facts-in-execution/plan.md:303-308`): this repo's automated suite
(`tests/skills/scripts/hb_sdk/`) covers the `hb_sdk` Python package, not
skill-markdown prose, and this step introduces no Python. Verification is
manual/behavioral (§6).

- **Happy path (AC1):** manually drive `/hb-task-step-review-address` on a
  step with an unresolved review item, having first recorded a relevant fact
  via `hb-sdk facts write` — confirm the model applies that fact while
  addressing the item (9c) without it being restated in the review item's
  body.
- **Reconciliation path (AC2):** manually drive `/hb-task-step-review-address`
  on an item whose addressing reveals a fact in `.hb/facts.md` to be stale —
  confirm 9f corrects or removes it, and that a genuinely new, durable fact
  discovered while addressing the item gets added (weighed against the
  100/1000/120 guidance).
- **Commit inclusion (AC3):** after the reconciliation-path run above,
  confirm `.hb/facts.md`'s change is present in that item's own commit
  (`git show --stat <sha>` includes `.hb/facts.md`), not folded into a later
  item's commit.
- **Multi-item ordering (AC1/AC2 combined):** address two unresolved items
  in the same invocation where item 1's addressing corrects a fact; confirm
  item 2's 9a re-read (next loop iteration) reflects item 1's correction,
  and item 1's commit (not item 2's) carries the facts-store change.
- **Missing-facts case (AC4):** manually drive
  `/hb-task-step-review-address` in a state where `.hb/facts.md` does not
  exist — confirm addressing proceeds to completion with no error and no
  blocking prompt, and 9f either skips the write (no new facts warranted) or
  creates the file for the first time (a genuinely new, durable fact was
  discovered).
- **Non-regression:** re-run `/hb-task-step-review-address` on an existing
  reviewed step from this repo's own `.hb/` state and confirm item reading,
  concern addressing, `review.md`/status-table updates, TODO-comment
  deletion, the prompt step, and the state-record step are unchanged from
  before this edit.

---

## 6. Verification (after implementation)

1. **Static check:** `grep -c "facts read" skills/hb-task-step-review-address.md`
   → `2` (9a and 9f); `grep -c "facts write" skills/hb-task-step-review-address.md`
   → `1` (9f); `grep -n "^#### " skills/hb-task-step-review-address.md` shows
   the expected relettered sequence 9a–9g with no gaps or duplicate letters;
   `grep -n "Repeat 9a" skills/hb-task-step-review-address.md` shows
   `Repeat 9a–9g`.
2. **Baseline:** capture the current rendered section 9
   (`git show HEAD:skills/hb-task-step-review-address.md`) before editing,
   to diff against after.
3. **Exercise the real change, empty-facts case:** in a scratch project with
   `.hb/` initialized but no `.hb/facts.md`, run
   `${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read` directly and confirm empty
   stdout + exit 0 — the condition 9a and 9f both rely on to never block.
4. **Exercise the real change, populated + reconciliation case:** `hb-sdk
   facts write "- <a fact relevant to a real review item>"`, then drive
   `/hb-task-step-review-address` on a step with an unresolved item touching
   that fact; confirm addressing reflects the fact, and — in a separate run
   where the fact is deliberately made stale first — confirm 9f corrects or
   removes it and the change lands in that item's own commit.
5. **Per-AC checks:**
   - AC1: new sub-step 9a present, calls `hb-sdk facts read`, and sub-step
     9c ("Address the concern") contains the "take `$FACTS` into account"
     bullet.
   - AC2.1–AC2.3: new sub-step 9f present, re-reads via `hb-sdk facts read`
     into `$FACTS_AFTER`, and its bullets cover stale-fact removal/correction,
     judgement-gated new-fact addition, and the size guidance from
     `facts-template.md`.
   - AC3: sub-step 9g ("Commit")'s wording names `.hb/facts.md`; manual run
     in step 4 above shows it staged and committed alongside that item's
     `review.md` change.
   - AC4: manual run in step 3 above (empty-facts case) demonstrates
     no-error, no-block behavior.
6. **Scope check:** `git diff --stat` shows only
   `skills/hb-task-step-review-address.md` changed (plus, at execution time
   against a real item, whatever `.hb/facts.md` change 9f itself makes — not
   a plan-time edit); no `.py` file, test file, or other skill `.md` file
   touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 (new sub-step 9a), §2.2 (sub-step 9c bullet) | |
| 2.1 | §2.3 (new sub-step 9f — `$FACTS_AFTER` re-read) | |
| 2.2 | §2.3 (stale-fact removal/correction bullet) | |
| 2.3 | §2.3 (judgement-gated new-fact bullet, weighed against `facts-template.md` guidance) | |
| 3 | §2.4 (Commit sub-step wording names `.hb/facts.md`), §0 (`.hb/facts.md` not git-ignored; `committing.md`'s generic staging rule already in place) | |
| 4 | §6 step 3 and step 5's AC4 row (manual empty-facts verification) | |

---

## 8. Out of scope (per ticket)

- Reads/updates during `review.md` creation, normalisation, or status-table
  sync (top-level Steps 3, 5–8) — this step scopes facts handling to the
  per-item addressing loop (section 9) only.
- Planning-time or execution-time reads/updates — already covered by step-1
  (`hb-task-step-plan.md`, `hb-task-plan.md`) and step-2
  (`hb-task-step-execute.md`).
- Automatic/programmatic detection of which facts are stale — 9f relies
  entirely on the executing agent's judgement, per the parent ticket's Out
  of scope; no code enforces or scores staleness.
- Hard enforcement of the 100/1000/120 size limits — `facts-template.md`
  states them as guidance only; this step's 9f does not add validation logic
  to `hb_sdk`.
