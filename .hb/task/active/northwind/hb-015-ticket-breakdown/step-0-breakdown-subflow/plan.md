# Step 0 Plan — Extract shared breakdown subflow

This step extracts `hb-task-plan`'s inline gap-analysis / propose-confirm /
per-step-creation logic (currently `skills/hb-task-plan.md:64-96`, Steps 6-8)
into a new, generalized reference subflow, `skills/references/breakdown-subflow.md`,
parameterized over a **parent** (with acceptance criteria) and a set of
**existing children** (each with acceptance criteria, possibly none) — so a
later step can make `hb-ticket-discuss`'s Breakdown action the subflow's second
consumer without duplicating this logic. Scope: pure extraction — no new
breakdown capability, no change to `hb-task-plan`'s task→step mechanics beyond
routing through the shared file. The observable effect once this lands:
`hb-task-plan` produces byte-for-byte-equivalent gap reports, confirmation
prompts, and created steps as before, but its Steps 6-8 are now three lines
that inject a shared file instead of thirty-three lines of inline logic.

Source ticket: `./ticket.md`. This is the first step of the task — there is no
prior-step work to build on; this plan targets `hb-task-plan.md` and the
`references/` folder as they exist in the repo today.

> **Design decision — where does the "would you like to add steps?" decline
> gate live?** `hb-task-plan.md:76-77` (today's Step 7) asks the user to
> confirm *before* proposing a breakdown, and lets them decline outright. The
> ticket's AC 1.3 describes the subflow's propose-confirm loop as starting
> from "given the gaps, propose ... present it, and loop ... until confirmed"
> — it doesn't call out a separate pre-proposal yes/no gate. Rather than add a
> second gate (which `hb-ticket-discuss`'s AC 6.5 never asked for, and which
> would make the subflow's control flow diverge from AC 1.3's stated shape),
> this plan folds the decline option into the propose-confirm loop itself:
> Section C presents the gap report *and* the proposed breakdown together and
> offers confirm / revise / decline as the three outcomes of one loop. This
> keeps one confirmation surface (matching AC 1.3) while preserving
> `hb-task-plan`'s AC-5 requirement that a user who declines still gets an
> equivalent "how would you like to proceed" outcome — see §2 Section C and
> the AC-traceability table (§7, AC 1.3 / AC 5).

---

## 0. Current-state facts (verified during planning)

- `skills/hb-task-plan.md:64-96` (Steps 6-8) contains the current inline logic:
  - Step 6 (gap analysis, lines 64-71): extract parent AC, extract each step's
    AC, list uncovered task-level criteria with notes on partial coverage by
    existing steps.
  - Step 7 (prompt, lines 73-77): if no gaps → notify "All task acceptance
    criteria appear covered by existing steps." and stop. Otherwise present
    the gap list and ask "Would you like to add steps to cover these gaps?" —
    if declined, ask "How would you like to proceed?" and stop the flow.
  - Step 8 (create, lines 79-96): for each gap/group, draft a ticket via
    `references/ticket-template.md` to a temp path, clarify with the user if
    ambiguous, then invoke `hb-task-step-add --ticket <path> [--flavor <slug>]`.
- Two existing subflow files establish the pattern to follow:
  - `skills/references/interactive-ticket-subflow.md:1-9` opens with a
    `> **Subflow — ...**` blockquote stating what it's shared by and its
    side-effect scope, followed by a `**Caller contract.**` paragraph naming
    the exact `$VAR`s the caller must resolve before injection.
  - `skills/references/review-init-subflow.md` uses lettered sections
    (`#### A.`, `#### B.`, `#### C.`) for resolve / check / create.
- `skills/references/references-toc.md:1-15` is the single table of reference
  files, `cat`-interpolated into every skill's "## Reference Files" section
  (e.g. `hb-task-plan.md:25`); every reference file the task references is
  listed there.
- `skills/references/ticket-template.md` defines the three-section
  (`# Background` / `# Acceptance Criteria` / `# Out of scope`) ticket
  structure already used by today's Step 8.1 — the subflow's per-child draft
  step reuses this unchanged.
- `skills/hb-task-step-add.md:22,70` confirms the materialization contract
  `hb-task-plan` must supply: `--ticket <path>` copies the drafted file into
  the new step's `ticket.md`, `--flavor <slug>` names the step folder, and the
  skill prints the created step's absolute path to stdout (captured as
  `$STEP_PATH`).
- No Python code in `skills/scripts/hb_sdk/*.py` implements gap analysis or
  breakdown logic (confirmed: `grep -rn "gap\|breakdown" skills/scripts/hb_sdk/*.py`
  returns no matches) — this logic is, and remains, conversational/prose
  instructions interpreted by the calling skill, not a code path.
- `tests/skills/scripts/hb_sdk/` only covers the Python `hb_sdk` package; no
  test infrastructure exists for `.md` skill/subflow content.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| Logic location | Inline in `hb-task-plan.md` Steps 6-8 (33 lines) | `skills/references/breakdown-subflow.md` (new, generalized over parent/children) |
| `hb-task-plan.md` Steps 6-8 | Gap analysis, propose/confirm, per-gap create (inline) | One step: resolve caller-contract vars, inject subflow |
| Consumers of the logic | `hb-task-plan` only | `hb-task-plan` now; `hb-ticket-discuss` in a later step (not yet wired) |
| `hb-task-plan` observable behavior | Baseline (gap report wording, confirm/decline prompts, created steps) | Unchanged — same wording, same prompts, same steps created via same `hb-task-step-add` call |

This is a **behavior-preserving refactor** for `hb-task-plan` (AC 5) plus one
**additive** new file and one additive table row (AC 1, AC 6). No existing
callers of `hb-task-plan` change their invocation; its argument surface
(`skills/hb-task-plan.md:3-8`) is untouched.

### 0.2 Non-regression proof

Purely additive/extractive change with one at-risk surface: `hb-task-plan`'s
user-facing wording and control flow must survive the extraction unchanged
(AC 5).

| Behavior | Current source | Why it can't change | Guard |
|---|---|---|---|
| Gap report format (uncovered criteria + partial-coverage notes) | `hb-task-plan.md:69-71` | Subflow Section A (§2) copies this wording verbatim into the generalized version | Verification #4 |
| "All task acceptance criteria appear covered..." + stop | `hb-task-plan.md:75` | Subflow Section B (§2) is this exact message, parameterized only by "parent"/"children" nouns → `hb-task-plan` still says "task"/"steps" via its contract labels | Verification #4 |
| "Would you like to add steps..." confirm/decline gate | `hb-task-plan.md:76-77` | Folded into Subflow Section C's confirm/revise/decline outcomes (see Design decision above); `hb-task-plan`'s injection step states the caller-specific wording | Verification #4 |
| Draft-via-`ticket-template.md`, clarify-if-ambiguous, size guidance (<300 lines) | `hb-task-plan.md:81-89` | Subflow Section D (§2) reuses `ticket-template.md` unchanged and keeps the size guidance | Verification #4 |
| `hb-task-step-add --ticket <path> [--flavor <slug>]` materialization | `hb-task-plan.md:91-94` | Not moved into the subflow (AC 3) — stays as `hb-task-plan`'s own `$MATERIALIZE_CHILD` contract value | Verification #4, #5 |
| Final report + "Steps ready..." prompt | `hb-task-plan.md:98-107` | Untouched — renumbered but not reworded (§3) | Verification #1 |

---

## 1. Design overview

Single generalization, not an ordered-alternatives change. The subflow has
four lettered sections, each mapping to one AC 1 sub-bullet:

| Section | Responsibility | AC |
|---|---|---|
| A. Gap analysis | Diff parent AC against every child's AC; produce the gap report | AC 1.1 |
| B. No-gaps exit | If Section A's report is empty, notify and stop | AC 1.2 |
| C. Propose-confirm loop | Present gaps + proposed breakdown; loop confirm / revise / decline | AC 1.3 |
| D. Per-child create-confirm loop | Draft each confirmed child via `ticket-template.md`; loop confirm / revise / skip; call back into the caller's materialization step | AC 1.4 |

Parameterization is via a caller contract (four `$VAR`s: `$PARENT_LABEL`,
`$PARENT_CRITERIA`, `$CHILDREN`, `$MATERIALIZE_CHILD` — full spec in §2),
following the same "state the vars the caller must resolve first" pattern as
`interactive-ticket-subflow.md:5-9`. `hb-task-plan` supplies: task ticket as
parent, discovered step tickets as children (§0's Step 4 discovery, already
present), and `$MATERIALIZE_CHILD` = "invoke `hb-task-step-add --ticket <path>
[--flavor <slug>]`, capture `$STEP_PATH`".

**Alternatives considered and rejected:**

- **Leave the logic duplicated inline in both skills** — rejected: AC 11 (of
  the task ticket) explicitly requires one shared subflow so neither skill
  maintains a second copy.
- **Implement gap analysis as a `hb_sdk` Python function** — rejected: no
  precedent exists (confirmed by the `grep` in §0), the task's Out-of-scope
  bars new tooling/integrations, and the logic is inherently
  judgment-based (assessing whether an existing child "addresses" a
  criterion) rather than a deterministic diff a script could perform.
- **One combined "no gaps or declined" exit section instead of two (B and
  C's decline branch)** — rejected: they have different trigger conditions
  (nothing to propose at all, vs. a valid proposal the user rejects) and AC
  1.2 calls for "no gaps" as its own named exit path, distinct from the
  propose-confirm loop.

---

## 2. `breakdown-subflow.md` — specification

**File:** `skills/references/breakdown-subflow.md` (new).

**Opening block** (mirrors `interactive-ticket-subflow.md:1-9`):

```
> **Subflow — breakdown.** Shared by `hb-task-plan` and (in a later step)
> `hb-ticket-discuss`'s Breakdown ticket action. Drafts child ticket files at
> temp paths for review; it does not decide where or how a confirmed child
> becomes durable — that is the calling skill's responsibility (AC 3).

**Caller contract.** Before injecting this subflow, the calling skill must
have resolved:

- `$PARENT_LABEL` — a short identifying label for the parent, used only in
  user-facing messages (e.g. the task name, or a ticket id/summary)
- `$PARENT_CRITERIA` — the parent's Acceptance Criteria section (numbered
  list), already extracted from its `ticket.md`
- `$CHILDREN` — a list of existing children, each with a label and its
  Acceptance Criteria section (or "no ticket" if it has none); may be empty
- `$MATERIALIZE_CHILD` — how the calling skill turns one confirmed child
  ticket (a drafted file at a temp path) into something durable (e.g.
  "invoke `hb-task-step-add --ticket <path> [--flavor <slug>]`" or "add it to
  the in-conversation ticket list as the active ticket"); the subflow calls
  back into this once per confirmed child and performs no persistence itself
```

**Data model:** no new persisted types — `$CHILDREN` entries are
transient `{label, criteria|none}` pairs the caller already holds (from its
own discovery step); the subflow does not define a storage format.

**Sections (interfaces/algorithm), each new:**

| Section | Contract |
|---|---|
| A. Gap analysis | For each top-level condition in `$PARENT_CRITERIA`: check whether any `$CHILDREN` entry addresses it (fully/partially) via its Acceptance Criteria text. If `$CHILDREN` is empty, every condition is a gap. Output: gap report — uncovered conditions, each annotated with any partially-addressing children. |
| B. No-gaps exit | If Section A's report has zero entries: notify the user all of `$PARENT_LABEL`'s acceptance criteria appear covered by existing children, and **stop** — return control to the caller; propose nothing. |
| C. Propose-confirm loop | Present the Section A gap report together with a proposed high-level breakdown of the gaps into candidate children (grouped small-to-medium, sized against sibling children when available). Ask the user to **confirm**, **request changes**, or **decline**. Revise-and-re-present on changes; on decline, **stop** — return control to the caller noting the decline (the caller decides the follow-up, e.g. `hb-task-plan`'s "how would you like to proceed?"); on confirm, proceed to Section D with the confirmed candidate list. |
| D. Per-child create-confirm loop | For each confirmed candidate, in order: (1) **draft** a temp ticket file using `references/ticket-template.md` (Background states which parent criteria it closes; Acceptance Criteria are concrete/checkable; Out of scope defers anything left to siblings); (2) **present** the draft; (3) loop **confirm / request changes / skip** until resolved; (4) on confirm, invoke `$MATERIALIZE_CHILD` with the temp path and collect the result (created path or error); on skip, record it as skipped and continue. Repeat until no candidates remain. |

**Failure/degradation contract:** empty `$CHILDREN` → Section A treats every
parent condition as a gap (no error). User declines in Section C → clean
stop, no drafts written, no materialization calls made. User skips a child in
Section D → that child is neither drafted-and-abandoned in a durable location
nor materialized; move on. Endless revision requests in either loop are
supported (no iteration cap) since both existing single-consumer flows
(`hb-task-plan.md:76-77` and step-1's Describe action) already loop without a
cap.

**Conflict resolution:** N/A — children are materialized strictly one at a
time in Section D; there is no concurrent-candidate collision to resolve.

**Return value:** the list of materialized children (temp-draft path × which
gap(s) it closes × the `$MATERIALIZE_CHILD` result), plus any skipped
entries — for the caller's own reporting step.

---

## 3. Integration / wiring

Only `hb-task-plan.md` is rewired; its argument surface
(`skills/hb-task-plan.md:1-9`) and Steps 1-5 are untouched.

- **Replace** `hb-task-plan.md`'s Steps 6-8 (`hb-task-plan.md:64-96`) with a
  single new Step 6, "Breakdown via shared subflow":
  1. Set the caller contract: `$PARENT_LABEL` = the task name; `$PARENT_CRITERIA`
     = the task ticket's Acceptance Criteria section (from Step 3); `$CHILDREN`
     = each Step-4-discovered step that has a `ticket.md`, labeled by its step
     path, with its Acceptance Criteria section; `$MATERIALIZE_CHILD` = "invoke
     `hb-task-step-add --ticket <path> [--flavor <slug>]`, capturing the printed
     step path".
  2. `Follow [${CLAUDE_SKILL_DIR}/references/breakdown-subflow.md](references/breakdown-subflow.md)`
     with the above.
- **Renumber** (wording unchanged, per §0.2): old Step 9 "Report"
  (`hb-task-plan.md:98-101`) → new Step 7, now reporting from the subflow's
  returned materialized/skipped list instead of a locally-tracked list. Old
  Step 10 "Prompt user" (`hb-task-plan.md:103-107`) → new Step 8, verbatim.
- Public signature: `hb-task-plan`'s command arguments and outputs are
  preserved — this is why callers/tests of the skill (there are none
  automated; see §5) stay unaffected.
- No config, build, entry-point, or dependency-manifest changes — this is a
  `.md`-only, self-contained edit; `hb-task-plan.md`'s `allowed-tools`
  (`hb-task-plan.md:9`) already covers everything the new Step 6 needs (it
  invokes no new tool).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/breakdown-subflow.md` | **new** — the shared subflow (§2) |
| `skills/hb-task-plan.md` | **edit** — replace Steps 6-8 with contract-setup + injection (new Step 6); renumber old Steps 9→7, 10→8, no wording change |
| `skills/references/references-toc.md` | **edit** — add one row for `breakdown-subflow.md`, placed alongside the other subflow rows |

No dependency manifest or lockfile exists for this repo's skill layer — none affected.

---

## 5. Tests

N/A — this step touches only `.md` prompt content; no `hb_sdk` Python code
path is added or changed (confirmed in §0: no existing gap/breakdown code to
extend). The repo's only automated test suite,
`tests/skills/scripts/hb_sdk/`, covers the Python `hb_sdk` package and has no
analog for skill/subflow markdown — it is unaffected and requires no new
cases. Verification is manual: a structural read-through (§6 #1-#3) plus a
side-by-side wording/behavior trace of `hb-task-plan`'s new Step 6 against
its old Steps 6-8 (§6 #4), which is the applicable non-regression check for
this kind of change.

---

## 6. Verification (after implementation)

1. **Structural check** — `grep -n "^###" skills/hb-task-plan.md` shows 8
   numbered steps (was 10 before the edit; two collapsed into one).
2. **New file shape** — `head -20 skills/references/breakdown-subflow.md`
   shows a `> **Subflow — ...**` opening line and a `**Caller contract.**`
   paragraph naming `$PARENT_LABEL`, `$PARENT_CRITERIA`, `$CHILDREN`,
   `$MATERIALIZE_CHILD` — matching the shape of
   `interactive-ticket-subflow.md:1-9`.
3. **TOC updated** — `grep -n "breakdown-subflow" skills/references/references-toc.md`
   returns exactly one row.
4. **Per-AC wording/behavior trace (non-regression, AC 5)** — read
   `hb-task-plan.md`'s new Step 6 + injected subflow Sections A-D side by
   side against the old Steps 6-8 text captured in §0; confirm: the gap
   report still lists uncovered task-level criteria with partial-coverage
   notes; the no-gaps message and the confirm/decline gate still produce
   equivalent user-facing prompts; drafts still use `ticket-template.md` with
   the same three sections and the <300-line sizing guidance; materialization
   still calls `hb-task-step-add --ticket <path> [--flavor <slug>]`.
5. **Side-effect-free subflow (AC 3)** — `grep -n "hb-sdk\|git " skills/references/breakdown-subflow.md`
   returns no matches — the subflow itself issues no SDK/git calls; only
   `$MATERIALIZE_CHILD` (defined by the caller) does.
6. **Scope check** — `git status --short` shows exactly the three files from
   §4 changed; nothing under `skills/hb-ticket-discuss.md`,
   `skills/hb-task-step-add.md`, or `skills/scripts/` touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1.1 | §2 Section A | Gap report generalized over `$PARENT_CRITERIA`/`$CHILDREN` |
| 1.2 | §2 Section B | Distinct no-gaps exit, separate from Section C's decline |
| 1.3 | §2 Section C | Propose-confirm loop; decline folded in per the Design decision above |
| 1.4 | §2 Section D | Per-child draft/present/confirm loop, calling back to `$MATERIALIZE_CHILD` |
| 2 | §2 "Caller contract" block | States the four `$VAR`s explicitly, matching `interactive-ticket-subflow.md`'s style |
| 3 | §2 Section D contract + Verification #5 | Subflow drafts to temp paths only; persistence is always via caller-supplied `$MATERIALIZE_CHILD` |
| 4 | §3 "Replace" bullet | Steps 6-8 → contract setup + injection; `hb-task-plan` supplies task ticket / step tickets / `hb-task-step-add` call |
| 5 | §0.2 non-regression table + Verification #4 | Wording and prompts traced 1:1 against the pre-edit text |
| 6 | §4 references-toc.md row + Verification #3 | New row added for `breakdown-subflow.md` |

---

## 8. Out of scope (per ticket)

- `hb-ticket-discuss` is not touched — it does not yet consume this subflow
  (a later step in this task wires it as the second consumer).
- No change to `hb-task-plan`'s task→step scoping, step-numbering, or
  step-creation mechanics beyond routing Steps 6-8 through the shared
  subflow.
- No new MCP/source integrations.
