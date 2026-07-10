# Step 6 Plan — Write-after facts in the planning skills

This step closes the last gap in the read-before/write-after facts pattern:
`hb-task-step-execute.md` (step 7) and `hb-task-step-review-address.md`
(step 9f) already re-read `.hb/facts.md` after doing their work and correct or
extend it before committing, but the two planning skills —
`hb-task-step-plan.md` and `hb-task-plan.md` — only read facts before
planning (step-1 of this task) and never write back. A fact discovered while
drafting a `plan.md` (e.g. "the auth module always validates tokens
server-side, contrary to what the ticket assumed") or while doing gap
analysis in `hb-task-plan` is silently dropped instead of being captured for
future steps. This is a **documentation-only change**: both files are
Markdown skill definitions, no application code changes, no new public API.
The externally observable effect: after this step, running either planning
skill can leave `.hb/facts.md` corrected or extended, committed alongside the
skill's other output.

Source ticket: `./ticket.md`. Builds on the **shipped** work from
step-1 (`hb-sdk facts read` wired into both planning skills as an
already-existing "Read facts store" step) and step-2/step-4 (the
write-after pattern already proven in `hb-task-step-execute.md` and
`hb-task-step-review-address.md`). This plan targets `skills/hb-task-step-plan.md`
and `skills/hb-task-plan.md` as they exist now (92 and 92 lines respectively,
see §0).

> **Design decision — where does the write-after step's own commit come from
> in `hb-task-plan.md`?** `hb-task-step-plan.md` already ends its flow with a
> single "Commit" step (current step 6) that commits `plan.md`; AC1 slots the
> facts write immediately before that existing commit, so facts.md rides
> along for free (§2.1). `hb-task-plan.md` has **no equivalent top-level
> commit step** — its only commits happen per confirmed child, inside the
> shared `breakdown-subflow.md`, executed by the *separate* `hb-task-step-add`
> skill (confirmed at `skills/hb-task-plan.md:79` and
> `skills/references/breakdown-subflow.md:46`). Editing the shared subflow is
> out of scope (the ticket scopes AC2 to `hb-task-plan.md`'s own Steps, and
> the subflow is shared with the not-yet-built `hb-ticket-discuss`). So the
> new step in `hb-task-plan.md` must be self-contained: it reads, composes,
> writes, **and commits** `.hb/facts.md` itself (task-level commit, tag
> `task-plan`) if and only if the composed content differs from what it
> read. See §2.2 and the AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `skills/hb-task-step-plan.md` (92 lines) has, in order: 1 Help check, 2
  Resolve step folder, 3 Read facts store, 4 Read inputs, 5 Generate
  plan.md, 6 Commit, 7 Prompt user, 8 Record execution state. Step 6 commits
  only `$STEP_PATH/plan.md` (`skills/hb-task-step-plan.md:73`).
- `skills/hb-task-plan.md` (92 lines) has, in order: 1 Help check, 2 Resolve
  task path, 3 Read facts store, 4 Load task-level ticket, 5 Discover
  existing steps, 6 Report missing step tickets, 7 Breakdown via shared
  subflow, 8 Report, 9 Prompt user. There is **no** step that records
  execution state and **no** step that performs a top-level commit — the
  only commit-producing action is `$MATERIALIZE_CHILD` inside
  `breakdown-subflow.md` §D.4, invoked once per confirmed child
  (`skills/hb-task-plan.md:79`).
- The write-after pattern already exists twice and is the template to
  mirror:
  - `skills/hb-task-step-execute.md:85-101` (step 7 "Update facts store"):
    re-reads facts as `$FACTS_AFTER`, reads
    `references/facts-template.md` for size guidance, composes
    corrections/additions by judgement, writes only if the composed content
    differs, otherwise no-ops. The following step (8, Commit) includes
    `.hb/facts.md` in the same commit "if it was changed in the previous
    step" (`skills/hb-task-step-execute.md:105`).
  - `skills/hb-task-step-review-address.md:223-239` (step 9f, identical
    shape, run once per resolved review item) followed by 9g's commit
    (`skills/hb-task-step-review-address.md:243`).
- `skills/references/facts-template.md` states the size guidance to cite
  verbatim in both new steps: target <= 100 lines, hard max 1000 lines, <=
  120 chars/line; prune stale/superseded facts before adding new ones if
  pruning is needed.
- `skills/references/committing.md`: `hb-task-plan` operates on a task, not
  a step, so any commit it makes directly must use `commit write-message-file
  task` (no `--step`), matching the existing task-level commits in
  `hb-task-create.md:73` (`--tag task-create`) and `hb-task-archive.md:48`
  (`--tag task-archive`). By the same convention this step uses `--tag
  task-plan`.
- `.hb/facts.md` does not currently exist in this repo (`hb-sdk facts read`
  returned empty, confirmed live during step 3 of this planning run) — both
  skills' existing "never errors on missing store" contract is unaffected by
  this change.

### 0.1 Impact (before → after)

| Skill | Before | After |
|---|---|---|
| `hb-task-step-plan` | Reads facts before drafting `plan.md`; never writes back. Facts discovered while planning are lost. | Reads facts before drafting; after drafting, re-reads, corrects/extends by judgement, writes if changed — included in the existing plan.md commit. |
| `hb-task-plan` | Reads facts before gap analysis; never writes back. Facts discovered during breakdown are lost. | Reads facts before gap analysis; after breakdown completes, re-reads, corrects/extends by judgement, writes if changed, and commits `.hb/facts.md` alone (task-level, tag `task-plan`) since no other commit step exists to piggyback on. |

Additive-only change: no existing step is removed or given different
semantics; new steps are inserted and later steps renumbered.

### 0.2 Non-regression proof / risk

Purely additive — no existing behavior changes:

| Case | Current behavior | Why it can't change |
|---|---|---|
| Facts store missing/empty | Both skills proceed unaffected (established step-1 contract) | New steps reuse the identical `hb-sdk facts read` call and the same "may be empty, never errors" wording; an empty read composes to empty/no-op write |
| `plan.md` generation (hb-task-step-plan) | Drafted from ticket + template + facts | Unchanged — new step runs strictly after plan.md is written, never before |
| Gap analysis / breakdown (hb-task-plan) | Unchanged subflow, per-child materialize commits | Unchanged — new step runs strictly after the breakdown subflow returns, does not touch `breakdown-subflow.md` or `$MATERIALIZE_CHILD` |
| Existing commit of `plan.md` | Commits only `plan.md` | Still commits `plan.md`; now conditionally also stages `.hb/facts.md` if changed, exactly like `hb-task-step-execute.md`'s step 8 |

Risk deferred to verification (§6): confirming the renumbered step
references (`step N`, cross-references to "the previous step") are internally
consistent after insertion.

---

## 1. Design overview

Single linear change in two files, no new components: insert one
"Update facts store" step into each skill's `## Steps` section, mirroring the
already-proven shape from `hb-task-step-execute.md` step 7 /
`hb-task-step-review-address.md` step 9f — re-read, compose by judgement
against the size guidance, write only if changed.

Placement differs per file because the surrounding commit structure differs:

| Skill | New step placement | Commit handling |
|---|---|---|
| `hb-task-step-plan.md` | Between step 5 (Generate plan.md) and step 6 (Commit) — new step 6, existing Commit renumbered to 7 | Facts write folded into the existing renumbered Commit step (7), same as `hb-task-step-execute.md` |
| `hb-task-plan.md` | Between step 7 (Breakdown via shared subflow) and step 8 (Report) — new step 8, existing Report renumbered to 9, Prompt user to 10 | New step performs its own commit (no existing commit step to fold into) |

**Alternatives considered and rejected:**
- Inserting the `hb-task-plan.md` facts write *inside* `breakdown-subflow.md`
  (e.g. before each `$MATERIALIZE_CHILD` call): rejected — the ticket scopes
  AC2 to `hb-task-plan.md`'s own Steps, and the subflow is shared with the
  not-yet-built `hb-ticket-discuss`, which has no facts-store concept yet;
  changing shared, multi-consumer subflow behavior for one consumer is the
  wrong layer.
- Making `hb-task-plan.md`'s new step fold its facts commit into one of the
  per-child `hb-task-step-add` commits: rejected — those commits belong to
  individual steps, not the task as a whole, and `hb-task-plan` does not
  control `hb-task-step-add`'s commit contents.
- Skipping the commit and leaving `.hb/facts.md` as an uncommitted change:
  rejected — violates AC3 ("facts-store changes... included in the relevant
  commit") and leaves dangling working-tree state after the skill exits.

---

## 2. Step specification

### 2.1 `hb-task-step-plan.md` — new step 6 "Update facts store"

- **Trigger**: runs after step 5 (Generate plan.md), before the renumbered
  Commit (step 7).
- **Behavior** (mirrors `hb-task-step-execute.md:85-101` verbatim in shape):
  1. run `hb-sdk facts read`, capture as `$FACTS_AFTER`
  2. read `references/facts-template.md` for size guidance before composing
  3. using judgement, based on what drafting this `plan.md` revealed:
     remove/correct stale or incorrect facts in `$FACTS_AFTER`; add new facts
     discovered while planning only when likely to matter for future
     planning/execution/review, weighed against the size guidance; prune
     before adding if needed to stay within guidance
  4. if composed content differs from `$FACTS_AFTER`: `hb-sdk facts write
     "<composed content>"`
  5. if unchanged: skip the write — no-op
- **Failure/degradation contract**: identical to the existing "Read facts
  store" step — never errors; missing/empty store composes to an empty or
  no-op write.
- Renumbered step 7 (Commit, was step 6) gains one clause: include
  `.hb/facts.md` in the commit "if it was changed in the previous step"
  (verbatim pattern from `skills/hb-task-step-execute.md:105`).

### 2.2 `hb-task-plan.md` — new step 8 "Update facts store"

- **Trigger**: runs after step 7 (Breakdown via shared subflow) completes —
  i.e. after the propose-confirm loop and all per-child materialize calls
  have returned — before the renumbered Report (step 9).
- **Behavior**: same 5-part read/compose/write shape as §2.1, phrased around
  what gap analysis and breakdown revealed instead of what drafting a plan
  revealed.
- **New here (no analog in AC1)**: since `hb-task-plan.md` has no existing
  top-level commit step, this step performs its own commit when the
  composed content differs:
  1. if composed content differs from `$FACTS_AFTER`: `hb-sdk facts write
     "<composed content>"`, then create a task-level commit by following
     `committing.md` including only `.hb/facts.md`, mode `task`, `--tag
     task-plan`
  2. if unchanged: skip both the write and the commit — no-op
- **Failure/degradation contract**: identical to §2.1 — never errors on a
  missing/empty store.
- Existing step 8 (Report) renumbers to 9; step 9 (Prompt user) renumbers to
  10. No content change to either beyond the number.

Conflict resolution: N/A — single deterministic path per skill, no
alternative sources to arbitrate.

---

## 3. Integration / wiring

- No call sites outside these two files change. No script, config, or
  dependency-manifest changes — `hb-sdk facts read`/`facts write` are already
  wired and used by three other skills.
- Both files' YAML frontmatter (`allowed-tools`, etc.) already permits
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)`, so no frontmatter edit is
  needed.
- Step renumbering is confined to each file's own `## Steps` list; no other
  skill references `hb-task-step-plan.md` or `hb-task-plan.md` by step
  number.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-step-plan.md` | **edit** — insert new step 6 "Update facts store" after step 5; renumber old 6→7 (Commit, gains one clause about `.hb/facts.md`), old 7→8 (Prompt user, untouched text), old 8→9 (Record execution state, untouched text) |
| `skills/hb-task-plan.md` | **edit** — insert new step 8 "Update facts store" (read/compose/write + its own commit) after step 7; renumber old 8→9 (Report, untouched text), old 9→10 (Prompt user, untouched text) |

No other files change. `.hb/facts.md` itself is not created or modified by
this step — it is only ever written at *runtime* by the two skills once
this plan is executed and later invoked.

---

## 5. Tests

These are Markdown skill-definition files with no application test suite;
"tests" here means dry-run trace verification against the edited step text,
matching how step-2 and step-4 of this task were verified.

- **Happy path A (`hb-task-step-plan`)**: trace a run where drafting
  `plan.md` reveals a stale fact — confirm the new step 6 composes a
  corrected `$FACTS_AFTER`, step 7 writes it and stages `.hb/facts.md`
  alongside `plan.md` in one commit.
- **Happy path B (`hb-task-plan`)**: trace a run where gap analysis reveals a
  new durable fact — confirm new step 8 writes it and produces a **separate**
  task-level commit (tag `task-plan`) containing only `.hb/facts.md`,
  distinct from any per-child `hb-task-step-add` commits made during step 7.
- **No-op case**: trace a run where nothing changed — confirm both new steps
  skip the write (and, for `hb-task-plan`, skip the commit) with no error.
- **Missing/empty store**: trace a run with no `.hb/facts.md` — confirm both
  new steps proceed with an empty `$FACTS_AFTER` and either no-op or produce
  a fresh, small facts file, per the established "never errors" contract.
- **Non-regression**: `hb-task-step-execute.md` and
  `hb-task-step-review-address.md` are unread and unmodified by this step;
  their existing write-after steps remain the reference implementation, not
  a dependency that could regress.

---

## 6. Verification (after implementation)

1. `git diff` shows only the two files listed in §4 changed.
2. Read `skills/hb-task-step-plan.md` end to end: confirm step numbers are
   sequential 1–9 with no gaps or duplicates, and step 7 (Commit) explicitly
   mentions `.hb/facts.md`.
3. Read `skills/hb-task-plan.md` end to end: confirm step numbers are
   sequential 1–10 with no gaps or duplicates, and the new step 8 states its
   own commit (mode `task`, `--tag task-plan`).
4. Confirm both new steps cite `references/facts-template.md` and the same
   size guidance figures (<=100 target, 1000 hard max, <=120 chars/line) used
   in the existing write-after steps.
5. Per-AC check: for each of AC1–AC4 (§7), point to the exact line range in
   the edited files that satisfies it.
6. Scope check: no changes to `skills/hb-task-step-execute.md`,
   `skills/hb-task-step-review-address.md`, `skills/references/*.md`, or any
   file under `.hb/`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 (new step 6 in `hb-task-step-plan.md`) | Read-then-write placed after plan.md generation, before its commit |
| 2 | §2.2 (new step 8 in `hb-task-plan.md`) | Analogous read-then-write placed after breakdown, before its own (new) commit |
| 3 | §2.1's renumbered Commit clause; §2.2's self-contained commit | Both paths stage `.hb/facts.md` into a real commit per `committing.md` |
| 4 | §0 current-state facts; §0.2 non-regression table | Missing/empty store already proven never to error; new steps reuse the identical read call |

---

## 8. Out of scope (per ticket)

- Planning-time reads before generating output — already covered by step-1
  of this task.
- Execution-time (`hb-task-step-execute.md`) or review-addressing
  (`hb-task-step-review-address.md`) writes — already covered by step-2 and
  step-4; neither file is touched here.
- Any change to `breakdown-subflow.md` or `$MATERIALIZE_CHILD` /
  `hb-task-step-add.md` commit behavior.
