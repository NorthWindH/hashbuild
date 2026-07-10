# Step 7 Plan — Extract shared `facts-write-subflow.md`

This step de-duplicates the facts-store read/compose/gate/write logic that is
currently copy-pasted, with slightly drifting wording, into four skills:
`hb-task-step-plan.md`, `hb-task-plan.md`, `hb-task-step-execute.md`, and
`hb-task-step-review-address.md`. Today, fixing the composition criteria (e.g. the
STEP-6-REVIEW-3 trim rules applied by hand in hb-016/step-6) means editing four
near-identical blocks and hoping the wording stays in sync; the general class is
"a shared behavior duplicated across N skill files with no single source of truth."
Scope boundary: **pure refactor** — no change to `hb-sdk facts read`/`facts write`
CLI behavior, no change to any skill's externally observable output or commit
structure. The single externally observable effect once this lands: editing the
facts composition criteria in one place (`facts-write-subflow.md`) is sufficient to
change behavior everywhere it's used, and the STEP-6-REVIEW-3 discipline is applied
automatically on every write instead of only during periodic review.

Source ticket: `./ticket.md`. Builds on the **shipped** work from hb-016/steps 0–6
(the facts store's existence, its use in planning/execution, its `.hb/` structure,
and the STEP-6-REVIEW-3 trim of `.hb/facts.md` itself). This plan targets the four
skill files and `.hb/facts.md` as they exist **now** (verified below).

> **Design decision — one file, two independently-invoked parts, not one wholesale
> `!cat` injection.** The ticket's AC1 names a single new file
> (`references/facts-write-subflow.md`), but the duplicated logic in each of the
> four skills actually has two distinct moments: an early plain "read for
> consumption during the step's own work" (`$FACTS`) and a late "re-read → compose
> → gate → write" (`$FACTS_AFTER` onward). Between those two moments each skill
> does real work (drafting a plan, executing, breakdown, addressing a review item)
> that the late part's composition judgement depends on — so the two moments can't
> collapse into one call site. `review-init-subflow.md`'s `!cat`-at-one-point
> convention doesn't fit here since `!cat` inlines the whole file verbatim and
> would dump the early-read text into the late call site (and vice versa).
> Instead this plan follows `breakdown-subflow.md`'s convention: a **caller
> contract** of variables the calling skill sets, then a prose "follow
> `references/facts-write-subflow.md` § Part A/B" reference at each of the two call
> sites — this is also "an injection convention already used for other shared
> subflows" in this codebase, just a different existing example than the one the
> ticket cited. See §1 for the full design and §7 for the AC-to-section mapping.

---

## 0. Current-state facts (verified during planning)

- The exact duplicated "late" sequence (read → guidance → compose → gate → write)
  appears, near-verbatim, at these four locations:
  - `skills/hb-task-step-plan.md:71-87` (Step 6 "Update facts store")
  - `skills/hb-task-plan.md:83-100` (Step 8 "Update facts store")
  - `skills/hb-task-step-execute.md:85-101` (Step 7 "Update facts store")
  - `skills/hb-task-step-review-address.md:223-239` (sub-step 9f, invoked once per
    unresolved review item in the loop starting at Step 9)
- The exact duplicated "early" sequence (plain read, capture `$FACTS`, "never
  errors ... proceeds unaffected") appears at:
  - `skills/hb-task-step-plan.md:51-58` (Step 3)
  - `skills/hb-task-plan.md:42-49` (Step 3)
  - `skills/hb-task-step-execute.md:60-67` (Step 4)
  - `skills/hb-task-step-review-address.md:180-187` (sub-step 9a, per loop
    iteration)
- One of the four — `hb-task-plan.md` — differs from the other three in one
  material way: its "late" step performs its **own commit** immediately after a
  successful write (mode `task`, only `.hb/facts.md`, `--tag task-plan`), because
  no later step in that skill already bundles `.hb/facts.md` into a broader commit.
  The other three defer the commit to a later step in their own sequence that
  already includes `.hb/facts.md` alongside other changed files
  (`hb-task-step-plan.md` Step 7, `hb-task-step-execute.md` Step 8,
  `hb-task-step-review-address.md` sub-step 9g). The subflow must preserve this
  difference, not flatten it (ticket AC4: no behavior regression).
- Existing shared-subflow conventions in this repo (confirmed by reading both):
  - `references/review-init-subflow.md` — single wholesale block, injected via
    `` !`cat ...` `` at exactly one call site in each of its two callers.
  - `references/breakdown-subflow.md` — a `> **Subflow — ...**` intro, a
    `**Caller contract.**` section of `$VAR` bullets the caller must set first,
    lettered sections (`#### A.`, `#### B.`, ...), and a closing
    `**Failure/degradation contract:**` / `**Return value:**` pair. Invoked by
    prose ("Follow `.../breakdown-subflow.md` with the above") from
    `hb-task-plan.md` Step 7, not by `!cat`.
- `references/facts-template.md` is the existing, unchanged sizing-guidance doc
  (target <= 100 lines, hard max 1000, <= 120 chars/line) already read by all four
  "late" blocks; the new subflow re-reads it rather than duplicating its content.
- `references/references-toc.md` is the table of reference files, itself `!cat`-ed
  into every skill's "## Reference Files" section; it currently lists
  `review-init-subflow.md`, `breakdown-subflow.md`, etc. but has no row for a
  facts-write subflow.
- `.hb/facts.md` current content (3 facts, confirmed via `hb-sdk facts read`):
  1. `` `skills/hb-*.md` is the canonical skill source; `~/.claude/skills/hb-*/` is
     just the installed copy. `` — 103 chars.
  2. `hb-015/step-5: re-author Jira push logic deleted in step-1 from
     hb-ticket-discuss.md (recover via git show 7bd2c42).` — 116 chars.
  3. `hb-ticket-discuss.md allowed-tools omits Read/WebFetch on purpose; don't
     re-add (rejected in hb-015/step-2).` — 108 chars.
  None of these three facts is a value the STEP-6-REVIEW-3 criteria (as
  generalized into the new subflow, §2) would flag: none is trivially re-derivable
  from current on-disk state alone (each encodes a past decision/commit reference
  that isn't visible just by looking at the file itself), and all three are at or
  under the ~120-char target. This directly satisfies ticket AC5 — no changes to
  `.hb/facts.md` content are required by this step.
- No test suite covers these markdown skill files (`tests/` only covers
  `hb_sdk` Python CLI modules, e.g. `tests/skills/scripts/hb_sdk/test_hb_sdk_facts.py`
  for `facts.py`'s `read`/`write` commands, which this step does not touch).
  Verification here is necessarily structural (grep/diff over the markdown), not
  an automated test run.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| Duplicated "late" sequence | 4 near-identical copies, ~17 lines each, wording already drifted once (STEP-6-REVIEW-3 fix applied only to the concept, not propagated to the other 3 call sites) | 1 canonical copy in `facts-write-subflow.md` § Part B; each of the 4 skills has a ~4-6 line caller-contract + prose-follow block |
| Duplicated "early" sequence | 4 identical copies, ~4 lines each | 1 canonical copy in `facts-write-subflow.md` § Part A; each of the 4 skills has a 1-2 line prose-follow reference |
| STEP-6-REVIEW-3 discipline | Applied once, by hand, during a review pass | Baked into § Part B, applied on every write by construction |
| `.hb/facts.md` content | 3 facts | unchanged — 3 facts (this is a doc-refactor step, not a facts-content edit) |
| `hb-sdk facts read`/`facts write` CLI | unchanged | unchanged (not touched) |

This is a **behavior-preserving refactor**: every externally observable
decision point (when to read, what judgement criteria to apply, when to gate on
diff, when to write, when to self-commit vs. defer) is preserved exactly — only
where the prose lives changes.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| `hb-task-step-plan` / `-execute` / `-review-address`: facts write deferred to a later bundled commit | `.hb/facts.md` left uncommitted after the "late" step; picked up by the skill's own next commit step | Subflow's caller contract sets `$SELF_COMMIT=false` for these three; § Part B's write branch performs no commit when `$SELF_COMMIT` is false — identical to today's silence on committing |
| `hb-task-plan`: facts write self-commits | Immediate standalone commit, mode `task`, `--tag task-plan`, only `.hb/facts.md` | Subflow's caller contract sets `$SELF_COMMIT=true` + `$COMMIT_ARGS` for this one caller only; § Part B's write branch commits via `$COMMIT_ARGS` exactly when `$SELF_COMMIT` is true |
| No-op path (composed content == current content) | Skip write entirely (and, for `hb-task-plan`, skip the commit too) | § Part B states the no-op explicitly for both write and (when applicable) commit |
| Missing `.hb/facts.md` / `.hb/` | Read step never errors, proceeds with empty `$FACTS` | § Part A states this explicitly, unchanged from today's wording |
| Review-address per-item loop | Facts read/write happens **once per unresolved item**, not once per skill invocation | Both parts remain invoked from inside the existing 9a/9f per-item loop positions — the subflow itself doesn't know or care how many times it's invoked; the loop structure stays in the calling skill |

Purely additive at the file level (`facts-write-subflow.md` is new) plus
mechanical substitution at the four call sites (replacing inline prose with a
caller-contract + follow-reference that resolves to the same instructions) — no
new decision points, no removed decision points.

---

## 1. Design overview

Single new reference file, two lettered parts, invoked from two different points
in each of the four calling skills:

| Part | When invoked | What it does | Replaces |
|---|---|---|---|
| Part A — Read | Once, early, before the step's own work that may consult facts | Read `.hb/facts.md` via `hb-sdk facts read`, capture `$FACTS`, no-op on missing file | The 4 "early" blocks (§0 bullet 2) |
| Part B — Compose, gate, write | Once, late, after the work that may have revealed new facts (or once per loop iteration for `hb-task-step-review-address`) | Re-read (`$FACTS_AFTER`), read `facts-template.md` for sizing, compose per judgement criteria, gate on diff, write if changed, self-commit only if the caller contract says so | The 4 "late" blocks (§0 bullet 1) |

```
caller sequence:  ... → Part A (read $FACTS) → [step's own work, may use $FACTS] → Part B (compose/gate/write, may self-commit) → ...
```

**Caller contract** (set before invoking Part B; mirrors `breakdown-subflow.md`'s
convention):

- `$CONTEXT_LABEL` — short phrase for what just happened, used only to judge which
  facts are worth recording (e.g. `"drafting this plan.md"`, `"this execution"`).
- `$SELF_COMMIT` — `true` if Part B must create its own commit for
  `.hb/facts.md` right after a successful write; `false` if a later step in the
  caller's own sequence already bundles `.hb/facts.md` into a broader commit.
- `$COMMIT_ARGS` — required only when `$SELF_COMMIT` is `true`: the exact
  `committing.md` invocation (mode, files, `--tag`) to use.

**Alternatives considered and rejected:**

- *Wholesale `!cat` injection of the whole file at each of the two call sites* —
  rejected: `!cat` has no notion of "just this part," so it would inline both
  parts' text at both call sites, which is misleading (e.g. the early call site
  would show write/commit instructions for logic that hasn't happened yet).
- *Two separate files (`facts-read-subflow.md` + `facts-write-subflow.md`)* —
  rejected: contradicts ticket AC1, which names one new file.
  Also splits the two moments' shared context (sizing guidance, judgement
  criteria) across files for no benefit — they're one concern (facts-store
  hygiene) with two invocation points, not two concerns.
- *Fold `$SELF_COMMIT`/self-commit handling out of the subflow entirely (subflow
  never commits; callers always commit separately)* — rejected: would force
  `hb-task-plan.md` to duplicate its own commit-after-write logic outside the
  subflow anyway, defeating the point of consolidating the write path, and risks
  the exact "committed only if content changed" gate drifting out of sync with the
  no-op check that lives in the subflow.

---

## 2. `facts-write-subflow.md` — specification

- **File**: `skills/references/facts-write-subflow.md` (new).
- **Structure** (mirrors `breakdown-subflow.md`): opening `> **Subflow — ...**`
  blockquote naming its four callers and both parts' one-line purpose; a
  `**Caller contract.**` section (the three `$VAR`s from §1); `#### Part A —
  Read (early)`; `#### Part B — Compose, gate, write (late)`; closing
  `**Failure/degradation contract:**` and `**Return value:**` lines.
- **Part A — Read (early)** (new; generalized from the 4 "early" blocks, wording
  otherwise unchanged):
  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
  ```
  - captures stdout as `$FACTS` (may be empty)
  - never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds
    unaffected — no error, no blocking prompt
  - the caller takes `$FACTS` into account during its own work: if a fact is
    relevant, it applies without requiring the fact be restated in the caller's
    own inputs (ticket, plan, execution, review item, etc.)
- **Part B — Compose, gate, write (late)** (new; generalized from the 4 "late"
  blocks — this is where the STEP-6-REVIEW-3 discipline is baked in per ticket
  AC2):
  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
  ```
  - captures stdout as `$FACTS_AFTER` (may be empty)
  - read [facts-template.md](facts-template.md) for size guidance (target <= 100
    lines, hard max 1000 lines, <= 120 chars/line) before composing any changes
  - using judgement, based on what `$CONTEXT_LABEL` revealed — including any
    corrections or clarifications the user gave by interrupting the session
    (e.g. redirecting a wrong assumption), not only what ended up written into the
    caller's own output artifact:
    - **prefer dropping** any fact that is trivially re-derivable from current
      on-disk state rather than keeping it "just in case" (STEP-6-REVIEW-3
      criterion 1)
    - remove or correct any fact in `$FACTS_AFTER` found to be stale or incorrect
    - keep each fact short — target <= 120 characters total (STEP-6-REVIEW-3
      criterion 2)
    - add new facts only when they correct a planning error or otherwise inform
      future planning/execution/review (STEP-6-REVIEW-3 criterion 3), weighed
      against the size guidance
    - if pruning is needed to stay within guidance, prune stale/superseded facts
      before adding new ones
  - if the composed content differs from `$FACTS_AFTER`:
    ```bash
    ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts write "<composed content>"
    ```
    - if `$SELF_COMMIT` is `true`: commit now via `$COMMIT_ARGS`, following
      [committing.md](committing.md)
    - if `$SELF_COMMIT` is `false`: leave `.hb/facts.md` uncommitted for the
      caller's own later commit step to pick up
  - if the composed content is unchanged from `$FACTS_AFTER`: skip the write
    entirely (and, when `$SELF_COMMIT` is `true`, skip the commit too) — no-op
- **Failure/degradation contract**: identical to today, restated explicitly —
  missing facts store never blocks either part; an unchanged compose result is a
  clean no-op, not an error.
- **Return value**: none (side-effecting only) — matches all 4 current call
  sites, none of which consume a return value from the facts logic beyond
  `$FACTS`/`$FACTS_AFTER` themselves.

---

## 3. Integration / wiring

Four call sites edited, each losing its inline prose and gaining a caller-contract
+ follow-reference. Step/sub-step **numbering and headings in all four skills stay
exactly as they are today** — only the body content under each heading changes.
No skill's `allowed-tools`, `argument-hint`, or other frontmatter changes (facts
subflow uses only `hb-sdk` and, conditionally, `git`/committing.md, already covered
by each skill's existing `allowed-tools`). `references-toc.md` gains one new row
(consumed via the existing `!cat references-toc.md` already present in every
skill's "## Reference Files" section — no per-skill edit needed beyond the table
itself).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/facts-write-subflow.md` | **new** — full content per §2 |
| `skills/references/references-toc.md` | **edit** — add one row: `facts-write-subflow.md` — "Shared subflow for facts-store read/compose/gate/write (Part A read, Part B compose+write); injected via caller contract by `hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address`." Existing rows untouched. |
| `skills/hb-task-step-plan.md` | **edit** — Step 3 body → follow Part A; Step 6 body → set `$CONTEXT_LABEL="drafting this plan.md"`, `$SELF_COMMIT=false`, follow Part B. Step 7 ("Commit ... including `.hb/facts.md` if it was changed") stays untouched — it's already the deferred-commit consumer. |
| `skills/hb-task-plan.md` | **edit** — Step 3 body → follow Part A; Step 8 body → set `$CONTEXT_LABEL="gap analysis and breakdown"`, `$SELF_COMMIT=true`, `$COMMIT_ARGS="mode task, only .hb/facts.md, --tag task-plan"`, follow Part B (Part B's own commit branch replaces today's inline steps 8.1–8.2). |
| `skills/hb-task-step-execute.md` | **edit** — Step 4 body → follow Part A; Step 7 body → set `$CONTEXT_LABEL="this execution"`, `$SELF_COMMIT=false`, follow Part B. Step 8 (bundled commit) untouched. |
| `skills/hb-task-step-review-address.md` | **edit** — sub-step 9a body → follow Part A; sub-step 9f body → set `$CONTEXT_LABEL="addressing this item"`, `$SELF_COMMIT=false`, follow Part B. Sub-step 9g (bundled per-item commit) untouched; loop structure (9a–9g repeated per unresolved item) untouched. |

No dependency-manifest or lockfile effects — all changes are within
`skills/**/*.md`.

---

## 5. Tests

N/A — no automated test suite covers skill markdown content (`tests/` only
exercises `hb_sdk` Python modules; `facts.py`'s `read`/`facts write` CLI commands
are unchanged by this step, so `tests/skills/scripts/hb_sdk/test_hb_sdk_facts.py`
needs no new cases and must still pass as a non-regression check on the untouched
CLI). Verification is structural (§6).

---

## 6. Verification (after implementation)

1. **Existing Python tests still pass** (non-regression on the untouched
   `hb_sdk` facts CLI):
   ```bash
   cd /Users/hasan.kamal-al-deen/repos/hashbuild && python -m pytest tests/skills/scripts/hb_sdk/test_hb_sdk_facts.py -q
   ```
2. **No leftover duplicated inline sequence.** Confirm the literal duplicated
   phrase is gone from all four callers, and present exactly once in the new
   subflow:
   ```bash
   grep -rn "using judgement, based on what" skills/*.md skills/references/*.md
   ```
   Expect all matches inside `skills/references/facts-write-subflow.md` only.
3. **Every caller references the new subflow.** Confirm each of the 4 skills now
   points at `facts-write-subflow.md`:
   ```bash
   grep -l "facts-write-subflow.md" skills/hb-task-step-plan.md skills/hb-task-plan.md skills/hb-task-step-execute.md skills/hb-task-step-review-address.md
   ```
   Expect all 4 files listed.
4. **`references-toc.md` lists the new file** and every skill still `!cat`s it
   (no per-skill Reference Files edit needed):
   ```bash
   grep -n "facts-write-subflow.md" skills/references/references-toc.md
   grep -rln '!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`' skills/*.md
   ```
5. **Per-AC checks** (§7 maps each; concretely):
   - AC1/AC2: read `facts-write-subflow.md` in full — confirm both parts present,
     confirm the three STEP-6-REVIEW-3 criteria appear explicitly in Part B.
   - AC3: read each of the 4 edited skills' changed sections — confirm no inline
     "read/compose/gate/write" prose remains; only caller-contract + follow
     references remain.
   - AC4: re-derive, from the edited skill text alone, the exact commit behavior
     of each of the 4 callers (self-commit vs. deferred) and confirm it matches
     §0.2's table.
   - AC5: `hb-sdk facts read` — confirm output is byte-identical to the "before"
     capture in §0 (this step makes no `.hb/facts.md` content change).
6. **Scope check**: `git status --short` shows only the 6 files in §4 changed;
   no `.py` files, no other skill files, no `.hb/facts.md` content diff.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2, §4 (`facts-write-subflow.md` row) | New file, generalized from all 8 duplicated blocks (4 early + 4 late) across the 4 named skills |
| 2 | §2 Part B bullet list | STEP-6-REVIEW-3's three criteria stated explicitly and applied "using judgement" on every write, not just during review |
| 3 | §3, §4 (four skill rows) | Each of the 4 skills replaces inline prose with caller-contract + follow-reference, per the breakdown-subflow-style convention (§1 design decision) |
| 4 | §0.2, §6 step 5 (AC4 check) | Read/write/gate/self-commit-vs-defer behavior preserved exactly per caller, verified by re-reading the edited text |
| 5 | §0 (facts.md bullet), §6 step 5 (AC5 check) | Current 3 facts already satisfy the generalized criteria; no `.hb/facts.md` edit needed or made |

---

## 8. Out of scope (per ticket)

- No change to `.hb/facts.md`'s current content (confirmed already valid, §0).
- No change to `hb-sdk facts read`/`facts write` CLI behavior or `facts.py`.
- No change to `facts-template.md`'s sizing guidance content — only re-read by
  the new subflow, same as today.
- No change to any skill's step **numbering**, `allowed-tools`, or other
  frontmatter.
- No new automated test coverage for skill markdown structure — out of scope for
  this refactor (no such test convention exists in this repo today).
