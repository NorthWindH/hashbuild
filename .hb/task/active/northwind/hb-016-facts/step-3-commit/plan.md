# Step 3 Plan — Note Facts-Store Staging Rule in `committing.md`

One-paragraph framing: today, if a skill's execution updates `.hb/facts.md`
(via `hb-sdk facts write`, added in step-0 and wired into planning/execution
in step-1/step-2), nothing in the shared committing reference tells a skill
to stage that updated file — the only place this was made explicit was a
one-off, skill-specific sentence added directly to
`skills/hb-task-step-execute.md`'s own Commit step in step-2. Any other
`hb-*` skill whose execution touches `facts.md` (or any future skill) has no
such reminder and could silently leave `.hb/facts.md` uncommitted. This step
adds one general bullet to `committing.md`'s staging step so the rule applies
uniformly to all 11 `hb-*` skills that reference `committing.md` for their
commit step, without editing each skill individually. Doc-only change, no
code, no behavior change to any script. Once this lands, every `hb-*` skill
that follows `committing.md`'s staging step will be instructed to stage
`.hb/facts.md` if that skill's execution updated it.

Source ticket: `./ticket.md`. Builds on the **shipped** work of step-0 (facts
store CLI: `hb-sdk facts read`/`facts write`, confirmed live in
`skills/scripts/hb_sdk/facts.py`), step-1 (facts read wired into planning
skills), and step-2 (facts read/write wired into `hb-task-step-execute.md`,
which already independently names `.hb/facts.md` in its own step 8). This
plan targets `skills/references/committing.md` as it exists now.

> **Design decision — leave `hb-task-step-execute.md`'s existing
> `.hb/facts.md` mention alone.** Step-2 already added an explicit
> `.hb/facts.md` callout to `hb-task-step-execute.md`'s own step 8 (see §0.2).
> Once this step's general note lands in `committing.md`, that callout
> becomes redundant with (but not contradictory to) the shared rule. The
> ticket's two ACs only require the `committing.md` edit; neither asks for
> cleanup elsewhere, and removing it would touch a file outside this step's
> ticket. Resolution: leave it as harmless duplication — a reader hits the
> same instruction twice, never a conflicting one. See §8 (Out of scope).

---

## 0. Current-state facts (verified during planning)

- `skills/references/committing.md` §"Process" → "### 1. Stage relevant
  files ONLY" (lines 25–64) has four numbered items: `1. [IDENTIFY]`,
  `2. [CHECK]`, `3. [COMMITREQUIRED]`, `4. [ADD]`. Item 4 `[ADD]`
  (lines 62–64) is the exact point where "relevant files" are staged:
  ```
  4. [ADD] add modifications to relevant files to stage:
     - for each relevant file:
       `git add <file_or_directory>`
  ```
  This is the chokepoint for this step's change — the note belongs here,
  inside the enumerated staging step the AC names, not as prose bolted onto
  the section header.
- `.hb/facts.md` is **not** git-ignored: `git check-ignore -v .hb/facts.md`
  returns nothing (only `.hb/.state.ignore.json` is ignored, per
  `.gitignore` line 6), and step-2's execution summary independently
  confirmed `.hb/facts.md` surfaces as a normal `??`/modified path in
  `git status --short`. So the existing `[IDENTIFY]`/`[CHECK]` machinery in
  `committing.md` already sees it like any other file — the only gap is that
  nothing tells the skill to *choose* to add it.
- Blast radius: `grep -rln "committing.md" skills/*.md` → 11 skill files
  reference `committing.md` for their commit step (confirmed count). All 11
  inherit this note the moment `committing.md` changes — no per-skill edits
  needed, matching ticket AC2's framing.
- `skills/hb-task-step-execute.md:105` already reads: `"...including all
  files changed during execution, $STEP_PATH/$SLUG, and .hb/facts.md if it
  was changed in the previous step..."` — this is the one skill-specific
  precedent the ticket's background paragraph refers to when it says
  documenting the rule in `committing.md` "propagates it to all of them
  without touching each skill individually." This step generalizes that
  precedent; it does not remove it (§ design decision above).

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| `committing.md` step 4 `[ADD]` | 2-line instruction: add modifications to relevant files, `git add` per file | Same 2-line instruction + 1 new bullet: if this skill's execution updated `.hb/facts.md`, include it among the staged files |
| Skills other than `hb-task-step-execute` that update facts in future | No written reminder to stage `.hb/facts.md` | Reminded via the shared reference they already follow |
| `hb-task-step-execute.md` | Explicitly names `.hb/facts.md` in its own step 8 | Unchanged (redundant-but-consistent with the new general note) |

Purely additive: one new bullet in one existing numbered item of one
reference doc. No existing bullet's wording changes.

### 0.2 Non-regression proof

| Case | Current behavior | Why it can't change |
|---|---|---|
| `[IDENTIFY]`/`[CHECK]`/`[COMMITREQUIRED]` steps (items 1–3) | Untouched — only item 4 gets a new bullet appended | Change is an addition to item 4 only; items 1–3 are not edited |
| Skills that never touch `facts.md` (most skills, most runs) | Stage only the files they actually changed | New bullet is conditional ("if this skill's execution updated `.hb/facts.md`") — a no-op when the condition is false, so unrelated commits are unaffected |
| `hb-task-step-execute.md`'s existing step 8 wording | Explicitly names `.hb/facts.md` | Not edited by this step (see design decision) — stays exactly as step-2 left it |

Change is purely additive to prose in one reference file; no script,
test, or CLI behavior is touched.

---

## 1. Design overview

Single linear change: insert one conditional bullet into
`committing.md`'s existing item `4. [ADD]`, immediately after the existing
`git add <file_or_directory>` line. No ordered alternatives, no
precedence table — there is exactly one integration point (the staging
step the AC names) and exactly one new bullet.

**Alternatives considered and rejected:**
- *Add a new numbered item (`5.`) to the staging step, separate from
  `[ADD]`* — rejected: the note is specifically about what counts as a
  "relevant file" to stage, which is `[ADD]`'s existing job; a new sibling
  item would duplicate/compete with it rather than extend it.
- *Add the note to the section header prose (before item 1) instead of
  inside item 4* — rejected: AC1 says the staging step should "note" the
  rule, but the most literal, unambiguous placement is at the exact
  sub-step that performs staging (`[ADD]`), so a future reader can't miss
  it while skimming the numbered list.
- *Edit each of the 11 referencing skills individually* — rejected: this is
  precisely what AC2 and the ticket's background paragraph rule out; it
  would multiply the edit 11x and drift out of sync over time.

---

## 2. `committing.md` — specification

- **Content change** — one new bullet under item `4. [ADD]`:
  > if this skill's execution updated `.hb/facts.md`, include it among the
  > relevant files staged
- **Contract** — generic across all `hb-*` skills: does not name
  `hb-task-step-execute` or any other specific skill (AC2). Conditional: a
  no-op for any commit where `facts.md` wasn't touched (§0.2).
- **Failure/degradation contract** — N/A, this is static prose, not
  executable logic; there is no failure mode to define.
- **Conflict resolution** — N/A, no competing sources/candidates involved.

---

## 3. Integration / wiring

- No call sites, no code, no scripts changed. `committing.md` is a
  markdown reference injected by skills via the pattern
  `[${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md)`
  — those 11 injection points are untouched; they'll simply see the updated
  reference content the next time an agent reads the file.
- No config, build wiring, entry points, or dependency manifests change.
  Self-contained: editing prose in one already-existing reference file
  requires no other wiring because every consuming skill already points at
  this same file by reference rather than by copy.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/committing.md` | **edit** — add one bullet to item `4. [ADD]` (lines 62–64) per §2; all other lines (rules, other process items, commit-message modes/examples, commit step) untouched |

No dependency-manifest or lockfile effects — no `pyproject.toml` or lockfile
touched.

---

## 5. Tests

N/A — this repo's automated suite (`tests/skills/scripts/hb_sdk/`) covers
`hb_sdk` Python behavior, not skill/reference markdown prose (same
precedent noted in step-1's and step-2's execution summaries: no test file
exercises `committing.md`'s wording). Verification is manual/textual, per
§6 below.

---

## 6. Verification (after implementation)

1. **Diff check**: `git diff skills/references/committing.md` shows exactly
   one new bullet added under item `4. [ADD]`; no other line changed.
2. **AC1 check**: `grep -A3 "4\. \[ADD\]" skills/references/committing.md`
   shows the new bullet mentioning `facts.md` immediately following the
   existing `git add` line, inside the staging step's numbered process.
3. **AC2 check**: `grep -n "facts.md" skills/references/committing.md`
   returns a line whose text contains no skill name (`hb-task-step-execute`,
   etc.) — confirms the note is generic.
4. **Propagation check**: `grep -rln "committing.md" skills/*.md | wc -l`
   still returns `11` (unchanged) — confirms no skill file needed editing
   for the rule to apply to all of them.
5. **Scope check**: `git status --short` shows only
   `skills/references/committing.md` modified; no `.py`, test, or other
   `.md` file touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2, §4 — new bullet under `committing.md` item `4. [ADD]` | Verified by §6 step 2 |
| 2 | §2 — bullet wording names no specific skill | Verified by §6 step 3; propagation confirmed by §6 step 4 |

---

## 8. Out of scope (per ticket)

- Removing or rewording `hb-task-step-execute.md`'s existing, now-redundant
  `.hb/facts.md` mention in its own step 8 — the ticket's ACs only cover
  `committing.md`; see the design-decision note above.
- Any enforcement/automation of the staging rule (e.g. a git hook or CI
  check that fails a commit if `facts.md` changed but wasn't staged) — the
  ticket asks for a documented note, not tooling.
- Any change to `hb-sdk facts read`/`facts write` themselves, or to the
  100/1000/120 size-guidance in `facts-template.md` — both are out of scope
  per prior steps and untouched here.
