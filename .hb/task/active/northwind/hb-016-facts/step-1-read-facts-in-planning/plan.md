# Step 1 Plan — Read Facts Store During Planning

This step wires `hb-sdk facts read` (shipped in step-0) into the two planning
skills the parent ticket names: `hb-task-step-plan` and `hb-task-plan`. Today
neither skill's `.md` Steps sections mention `facts` at all — grep confirms
zero hits for `facts` in either file — so a recorded fact like "skills live in
the project under `./skills`" is silently unavailable to plan generation and
gap analysis, forcing the same context to be re-typed into every ticket. This
is a documentation-only change to two skill `.md` files: one new "read facts"
step is inserted into each skill's Steps section, plus one instruction each
telling the downstream generation/analysis step to take the returned facts
into account. No `hb_sdk` Python code changes — `facts read` already has the
exact contract this step depends on (prints `""` with exit 0 whether
`.hb/facts.md` or even `.hb/` itself is missing; confirmed live via
`hb-sdk facts read` in a bare scratch dir). The externally observable effect:
running `/hb-task-step-plan` or `/hb-task-plan` now surfaces the current facts
store content to the model before it drafts `plan.md` or step tickets, with
zero behavior change when the store is empty.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-sdk facts read`/
`write` CLI from step-0 (`skills/scripts/hb_sdk/facts.py`,
`skills/references/facts-template.md`) — this step is purely a consumer of
that surface, not a change to it. This plan targets
`skills/hb-task-step-plan.md` and `skills/hb-task-plan.md` as they exist now.

> **Design decision — insert the facts-read step immediately before the
> ticket-read step in each skill, not merged into an existing step.** Both
> skills already have a numbered "read the ticket" step
> (`hb-task-step-plan.md` step 3 "Read inputs"; `hb-task-plan.md` step 3 "Load
> task-level ticket"). Rather than editing those steps' bodies to smuggle in a
> `facts read` call, this plan adds a **new** step immediately before each, so
> renumbering only shifts steps downward by one and the diff stays additive
> and easy to review. The generation/analysis step immediately after (step 4
> in both files, post-renumber) gets one added instruction sentence pointing
> back at the captured variable — see §2 and the AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `grep -c facts skills/hb-task-step-plan.md skills/hb-task-plan.md` → both
  `0` — neither skill currently references `facts` in any form.
- `hb-sdk facts read` is live and behaves exactly as step-0 specified: printed
  `""` with exit 0 on a bare directory with no `.hb/` at all, and again after
  `hb-sdk init` with no `.hb/facts.md` yet written (verified by direct
  execution in a scratch dir, this session). This is the contract AC3 of this
  step's ticket depends on: "when the facts store is empty or missing ... the
  skill proceeds unaffected — no error, no blocking prompt." Nothing in either
  skill's new step needs a conditional branch for "missing" — the command
  itself never errors or blocks.
- `hb-task-step-plan.md`'s current Steps (`skills/hb-task-step-plan.md:29-75`):
  1. Help check
  2. Resolve step folder (`$STEP_PATH`, `$N`, `$TASK_REF`)
  3. Read inputs (`ticket.md`, `plan-template.md`)
  4. Generate `plan.md`
  5. Commit
  6. Prompt user
  7. Record execution state
- `hb-task-plan.md`'s current Steps (`skills/hb-task-plan.md:29-82`):
  1. Help check
  2. Resolve task path (`$TASK_PATH`)
  3. Load task-level ticket
  4. Discover existing steps
  5. Report missing step tickets
  6. Breakdown via shared subflow (gap analysis + step creation)
  7. Report
  8. Prompt user
- The established convention in this repo for capturing a CLI command's stdout
  into a named variable inside a skill's Steps section is a bare bash fence
  followed by a bullet "captures stdout as `$VAR`" — used verbatim in
  `skills/hb-status.md` step 2 for `$SUMMARY_MD`. This plan's new steps mirror
  that exact phrasing for `$FACTS`.
- Neither skill currently declares any `Bash(...)` scope beyond
  `${CLAUDE_SKILL_DIR}/scripts/hb-sdk *`, `Bash(git *)` (and, for
  `hb-task-plan`, `Bash(find *)`) in frontmatter — both already allow
  `hb-sdk facts read` since it's covered by the existing
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` wildcard. No frontmatter change
  needed.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `.hb/facts.md` has content, run `/hb-task-step-plan <step_ref>` | content never read; plan drafted from ticket only | `hb-sdk facts read` output captured as `$FACTS`; plan-generation step instructed to take it into account |
| `.hb/facts.md` missing or `.hb/` missing, run `/hb-task-step-plan <step_ref>` | n/a (facts didn't exist as a concept) | `$FACTS` is `""`; step proceeds identically to before this change — no error, no prompt |
| `.hb/facts.md` has content, run `/hb-task-plan <name>` | content never read; gap analysis drafted from ticket only | `$FACTS` captured before step 6 (breakdown); breakdown step instructed to reflect it in drafted step tickets |
| `.hb/facts.md` missing or `.hb/` missing, run `/hb-task-plan <name>` | n/a | `$FACTS` is `""`; step proceeds identically to before this change |

Purely additive to both skills' Steps sections: existing step numbers 1–2 are
unchanged in content (only renumbered where they shift), and no existing
step's *behavior* changes — only new instructions are appended to the
generation/analysis step referencing the new variable.

### 0.2 Non-regression proof

Additive-only at the document level: this step inserts one new step and one
new sentence per skill file; it does not remove, reorder the *content* of, or
alter the pass/fail contract of any existing step. `hb-sdk facts read` is a
read-only CLI call with no side effects (confirmed in §2 of step-0's plan —
`read_facts()` never writes) and never errors, so inserting it cannot cause a
previously-succeeding invocation of either skill to fail. The `$STEP_PATH`/
`$N`/`$TASK_REF`/`$TASK_PATH` resolution steps, the ticket-read steps, the
commit step, and the state-record step are all untouched in substance.

---

## 1. Design overview

Single linear addition, identical shape in both files: one new numbered step
that shells out to `hb-sdk facts read` and captures its stdout, placed
directly before the step that reads `ticket.md`, followed by one added
instruction sentence on the step that consumes the ticket to also consider the
captured facts.

```
hb-task-step-plan.md:
  1 Help check                (unchanged)
  2 Resolve step folder       (unchanged)
  3 Read facts store          (NEW)
  4 Read inputs               (was 3; unchanged content)
  5 Generate plan.md          (was 4; +1 instruction sentence)
  6 Commit                    (was 5; unchanged)
  7 Prompt user                (was 6; unchanged)
  8 Record execution state    (was 7; unchanged)

hb-task-plan.md:
  1 Help check                (unchanged)
  2 Resolve task path         (unchanged)
  3 Read facts store          (NEW)
  4 Load task-level ticket    (was 3; unchanged content)
  5 Discover existing steps   (was 4; unchanged content)
  6 Report missing step tickets (was 5; unchanged content)
  7 Breakdown via shared subflow (was 6; +1 instruction sentence)
  8 Report                    (was 7; unchanged)
  9 Prompt user                (was 8; unchanged)
```

Each new "Read facts store" step is a single bash fence:

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- captures stdout as `$FACTS` (may be empty)
- never errors; if empty, proceed unaffected — no error, no blocking prompt

**Alternatives considered and rejected:**

- *Merge the `facts read` call into the existing ticket-read step* — rejected
  per the design decision above: keeps each step's diff isolated and avoids
  editing the wording of an already-correct existing step.
- *Add a conditional ("if `$FACTS` is non-empty, do X") to the new step* —
  rejected: `read_facts()` already returns `""` uniformly for both "no
  `.hb/facts.md`" and "no `.hb/` at all" (step-0 §2), so there is no
  distinct-missing-vs-empty case to branch on; the consuming step's
  instruction to "take `$FACTS` into account" degrades naturally to a no-op
  when `$FACTS` is empty.
- *Wire facts into `hb-task-step-execute` in this same step* — rejected per
  this ticket's own Out-of-scope section (that's step-2's job).
- *Add a new frontmatter `allowed-tools` entry for `facts read`* — rejected:
  already covered by the existing `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)`
  wildcard in both files' frontmatter (`hb-task-step-plan.md:9`,
  `hb-task-plan.md:9`).

---

## 2. Skill-file changes — specification

Both edits are prose/structure changes to `.md` Steps sections; there is no
code module. Each is specified as an exact insertion + one-sentence edit.

### 2.1 `skills/hb-task-step-plan.md`

- **New step**, inserted between current step 2 ("Resolve step folder") and
  current step 3 ("Read inputs"), renumbering step 3 onward by +1:

  ```markdown
  ### 3. Read facts store

  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
  ```

  - captures stdout as `$FACTS` (may be empty)
  - never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds
    unaffected — no error, no blocking prompt
  ```

- **Edit** to what is now step 5, "Generate plan.md" (was step 4), adding one
  bullet:

  > - take `$FACTS` into account when drafting `plan.md` — if a fact is
  >   relevant to this step's ticket, reflect it in the plan without
  >   requiring it be restated in `ticket.md`

- All other steps (renumbered 4, 6, 7, 8) keep their exact current wording.

### 2.2 `skills/hb-task-plan.md`

- **New step**, inserted between current step 2 ("Resolve task path") and
  current step 3 ("Load task-level ticket"), renumbering step 3 onward by +1:

  ```markdown
  ### 3. Read facts store

  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
  ```

  - captures stdout as `$FACTS` (may be empty)
  - never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds
    unaffected — no error, no blocking prompt
  ```

- **Edit** to what is now step 7, "Breakdown via shared subflow" (was step 6),
  adding one bullet to the caller-contract list already set there:

  > - `$FACTS` = the facts captured in Step 3 — drafted step tickets should
  >   reflect known facts without requiring them restated in
  >   `$PARENT_CRITERIA`

- All other steps (renumbered 4, 5, 6, 8, 9) keep their exact current wording.

- **Failure / degradation contract** (both files): identical to `facts read`
  itself — never errors, never blocks; an empty `$FACTS` means the
  "take into account" instruction is trivially satisfied by doing nothing.
- **Conflict resolution:** N/A — read-only, no merge/write logic involved.

---

## 3. Integration / wiring

- No frontmatter changes to either skill file — `allowed-tools` in both
  already includes `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)`
  (`hb-task-step-plan.md:9`, `hb-task-plan.md:9`), which covers the new
  `facts read` invocation.
- No `references-toc.md` change — this step doesn't add a new reference file,
  only new steps referencing the already-registered `hb-sdk` script.
- No change to `skills/scripts/hb_sdk/facts.py`, `common.py`, or
  `__main__.py` — this step is a pure consumer of the step-0 CLI surface.
- No build config, dependency manifest, or entry-point script changes.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-step-plan.md` | **edit** — insert new step 3 ("Read facts store"); renumber steps 3–7 to 4–8; add one bullet to the generation step (now step 5) |
| `skills/hb-task-plan.md` | **edit** — insert new step 3 ("Read facts store"); renumber steps 3–8 to 4–9; add one bullet to the breakdown step's caller contract (now step 7) |

No other files change — no Python, no tests, no reference docs, no
dependency manifest.

---

## 5. Tests

This repo's automated test suite (`tests/skills/scripts/hb_sdk/`) covers the
`hb_sdk` Python package, not the prose content of skill `.md` files — there is
no existing precedent for testing skill-markdown Steps sections
programmatically, and this step introduces no Python. Verification is
therefore manual/behavioral (§6), matching how skill-file-only changes have
been verified in prior steps of this repo (e.g. no test file was added for the
`breakdown-subflow.md` skill-wiring commit `6912b92`).

- **Happy path:** manually drive `/hb-task-step-plan` against a step whose
  ticket concerns skill files, with a fact recorded via `hb-sdk facts write`
  stating "skills live in the project under `./skills`" — confirm the
  resulting `plan.md` reflects that path without it being restated in the
  step's `ticket.md` (this is AC4 of this step's ticket, the manual
  verification criterion).
- **Missing-facts case:** manually drive `/hb-task-step-plan` and
  `/hb-task-plan` in a state where `.hb/facts.md` does not exist — confirm
  both proceed to completion with no error and no blocking prompt (AC3).
- **Non-regression:** re-run `/hb-task-step-plan` and `/hb-task-plan` on an
  existing ticketed step/task from this repo's own `.hb/` state and confirm
  the rest of each skill's behavior (step resolution, commit, state record /
  breakdown subflow) is unchanged from before this edit.

---

## 6. Verification (after implementation)

1. **Static check:** `grep -c "facts read" skills/hb-task-step-plan.md
   skills/hb-task-plan.md` → `1` in each file; `grep -n "^### " skills/hb-task-step-plan.md`
   and `skills/hb-task-plan.md` show the expected renumbered sequence with no
   gaps or duplicate numbers.
2. **Baseline:** capture the current rendered Steps section of both files
   (`git show HEAD:skills/hb-task-step-plan.md`,
   `git show HEAD:skills/hb-task-plan.md`) before editing, to diff against
   after.
3. **Exercise the real change, empty-facts case:** in a scratch project with
   `.hb/` initialized but no `.hb/facts.md`, run
   `${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read` directly and confirm empty
   stdout + exit 0 (already reverified live this session) — this is the
   condition the new step 3 in each skill relies on to never block.
4. **Exercise the real change, populated-facts case:** `hb-sdk facts write
   "- skills live in the project under \`./skills\`"`, then drive
   `/hb-task-step-plan` on a step whose ticket concerns skill files; confirm
   the emitted `plan.md` correctly references `./skills` without that path
   being stated in the step's own `ticket.md`.
5. **Per-AC checks:**
   - AC1: `hb-task-step-plan.md`'s new step 3 present, calls
     `hb-sdk facts read`, and step 5 ("Generate plan.md") contains the
     "take `$FACTS` into account" bullet.
   - AC2: `hb-task-plan.md`'s new step 3 present, calls `hb-sdk facts read`,
     and step 7 ("Breakdown via shared subflow") contains the `$FACTS`
     caller-contract bullet.
   - AC3: manual runs in step 3 above show no error/prompt when
     `.hb/facts.md` or `.hb/` is missing.
   - AC4: manual run in step 4 above shows the fact reflected in the
     generated plan.
6. **Scope check:** `git diff --stat` shows only
   `skills/hb-task-step-plan.md` and `skills/hb-task-plan.md` changed; no
   `.py` file, test file, or other skill `.md` file touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 (new step 3 + step 5 bullet in `hb-task-step-plan.md`) | |
| 2 | §2.2 (new step 3 + step 7 bullet in `hb-task-plan.md`) | |
| 3 | §1 alternatives-rejected, §2 failure/degradation contract, §6 step 3 | relies on `facts read`'s existing never-errors contract from step-0 |
| 4 | §6 step 4 (manual verification) | end-to-end manual check per this step's own AC4 |

---

## 8. Out of scope (per ticket)

- Execution-time reads or post-execution updates to the facts store —
  deferred to step-2 (`step-2-facts-in-execution`).
- Any planning-adjacent skill not named in the parent ticket, e.g.
  `hb-task-step-add`, `hb-ticket-discuss` — not touched by this step.
