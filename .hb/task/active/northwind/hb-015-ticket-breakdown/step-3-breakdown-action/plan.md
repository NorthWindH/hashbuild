# Step 3 Plan — Breakdown ticket action

`hb-ticket-discuss`'s loop (shipped in steps 1-2) currently offers Load and
Describe, both of which only ever *add* a single ticket to context. The
**motivating case**: a user has an Epic-shaped ticket active in context and says
"break this down" — today that phrase matches no Action Registry row; the user
has to manually Describe each child and has no gap-coverage check against the
parent's own acceptance criteria. This step adds a third action, **Breakdown
ticket**, covering the **general class** of decomposing any ticket already held
in the loop's context into child tickets, reusing the gap-analysis/propose-confirm/
per-child create-confirm logic `breakdown-subflow.md` already implements for
`hb-task-plan`'s task→step case (task ticket AC 11: one shared subflow, no
duplicated logic). Scope boundary: **additive only, and it does not touch
`breakdown-subflow.md` itself** — one new subflow file that supplies that shared
subflow's caller contract from the loop's ticket-entry model, one new Action
Registry row, one new TOC row, and a `description:`/prose wording tweak;
`breakdown-subflow.md`, `ticket-loop-subflow.md` §A/C/D/E, `load-ticket-subflow.md`,
`describe-ticket-subflow.md`, `exit-ticket-loop-subflow.md`, and
`hb-ticket-discuss.md`'s `allowed-tools` are all unchanged. Externally observable
effect once this lands: saying "break this down" (or naming a specific ticket in
context) at any loop iteration either reports "no gaps" or walks the user through
confirming child tickets, each of which is added to context as the active ticket
and tagged as a child of the ticket that was broken down.

Source ticket: `./ticket.md`. Builds on the **shipped** Load/Describe/Exit
actions and loop skeleton (`skills/hb-ticket-discuss.md`,
`skills/references/ticket-loop-subflow.md`,
`skills/references/load-ticket-subflow.md`,
`skills/references/describe-ticket-subflow.md`,
`skills/references/exit-ticket-loop-subflow.md`) and the pre-existing
`skills/references/breakdown-subflow.md` (already shared-shaped, written for
`hb-task-plan` but explicitly designed for a second caller) — all read in full
during planning, current as of commit `2373a5f` (the last commit to touch any of
these files; repo HEAD is `6e37394`, an unrelated facts-gate commit). This plan
targets that code as it exists **now**, not as any prior step's `plan.md`
described it — notably, step-2's `plan.md` referenced a `$TICKET_SEQ` counter and
a `Read`/`WebFetch`/`Bash(find *)` tool-grant widening that were **not** what
shipped: the live `ticket-loop-subflow.md` §D passes only `$TICKET_CONTEXT` by
reference (no `$TICKET_SEQ`), and the live `hb-ticket-discuss.md` frontmatter
still has no unrestricted `Read`, no `WebFetch`, no `Bash(find *)` — confirmed by
this task's own fact "`hb-ticket-discuss.md` allowed-tools omits Read/WebFetch on
purpose; don't re-add (rejected in hb-015/step-2)".

> **Design decision — do not widen `hb-ticket-discuss.md`'s `allowed-tools` to
> read `ticket-template.md`.** `breakdown-subflow.md` §D step 1 says to draft
> each child using `ticket-template.md` "as the structural template" — a naive
> reading would add an unrestricted `Read` grant so the running skill can open
> that file, exactly the widening step-2 proposed and review rejected (see the
> fact above). But every reference file a skill "Follow"s (`ticket-loop-subflow.md`,
> `load-ticket-subflow.md`, `breakdown-subflow.md` itself, and now
> `ticket-template.md` transitively through it) is already resolved by the
> skill-loading mechanism the same way `hb-ticket-discuss.md` resolves its own
> `Steps` section's `[...](references/...)` links — none of steps 1-2's own
> reference reads required a `Read` grant, and `breakdown-subflow.md` has been
> loadable by `hb-task-plan` (which *does* have unrestricted `Read`, but only for
> *ticket* file I/O, not for loading its own reference docs) on the same
> mechanism. The child-draft write itself lands under `/tmp` by the same
> convention `interactive-ticket-subflow.md` §A.1 already establishes, which
> `hb-ticket-discuss.md`'s existing `Write(//tmp/*)`/`Edit(//tmp/*)` grants
> already cover. So this step adds **zero** new `allowed-tools` entries. See §1
> and §3.

---

## 0. Current-state facts (verified during planning)

- **`skills/hb-ticket-discuss.md`** (56 lines, read in full): frontmatter
  `allowed-tools` (lines 12-24) — 6 `/tmp`-scoped Read/Write/Edit grants + 5
  Atlassian Rovo Jira tools; **no** unrestricted `Read`, **no** `WebFetch`, **no**
  `Bash`. `description:` (lines 4-11) and the body prose at line 28 both read
  "...a menu of next actions (e.g. describe, load, exit) selectable via natural
  language" — two occurrences of the same parenthetical example list, both
  already updated to mention `load` when that action shipped (step-2), confirming
  both occurrences move together.
- **`skills/references/ticket-loop-subflow.md`** (72 lines, read in full): §A
  (lines 12-26) defines the ticket entry as `{ id_or_summary, content, active }`
  plus an explicit **extensibility note** (lines 23-26): "Later steps may attach
  *additional* optional fields to an entry for their own bookkeeping — that is
  additive, not a redefinition, and doesn't require revisiting this subflow."
  §B (Action Registry, lines 28-38) has exactly 3 rows today: Load, Describe,
  Exit — in that order, matching the task ticket's own AC numbering (Load=AC4,
  Describe=AC5, Exit=AC9; Breakdown=AC6 belongs between Describe and Exit). §D
  (Dispatch, lines 52-59): "invoke the matched action's dispatch subflow, passing
  `$TICKET_CONTEXT` by reference (the callee mutates it in place)" — no other
  formal parameter; the user's triggering utterance is already visible in
  conversation, so an action needing to parse it (Breakdown does, to resolve its
  target) does not need a new formal parameter, mirroring Load's own precedent.
- **`skills/references/breakdown-subflow.md`** (52 lines, read in full): caller
  contract (lines 6-11) is exactly `$PARENT_LABEL`, `$PARENT_CRITERIA`,
  `$CHILDREN` (list of `{label, criteria}`, may be empty), `$MATERIALIZE_CHILD`
  (prose description of how the caller turns one confirmed child draft into
  something durable — "the subflow calls back into this once per confirmed
  child and performs no persistence itself"). §A treats an empty `$CHILDREN` as
  "every condition is a gap" (line 17) — no special-case needed for a
  freshly-targeted parent with no children yet. §B's no-gaps exit and §C's
  decline path both `**stop**` and return control to the caller with no
  materialization calls (lines 22, 29) — this step's subflow must pass that
  return straight through to the loop, per AC5. §D step 4 "Materialize" invokes
  `$MATERIALIZE_CHILD` "with the temp path" and collects "its result (created
  path or error)" (line 46) — for this caller, the "result" is the new context
  entry's `id_or_summary`, since there is no durable path to report (§1, §2 §C
  below). Return value (line 52): "the list of materialized children ... plus
  any skipped entries."
- **`skills/references/load-ticket-subflow.md`** (100 lines, read in full):
  established precedent for an additive, optional field on a ticket-context
  entry — `source: {type, ref}` (§E step 6, lines 88-92) — added without
  touching §A's required-field trio, exactly the extensibility note's intended
  use. Also confirms `$TARGET_PATH` for a fresh draft is resolved via
  `interactive-ticket-subflow.md` §A.1 (harness scratch dir, else
  `mktemp -d /tmp/hb-ticket.XXXXXXXX`) — **not** a `$TICKET_SEQ`-keyed path;
  that scheme was replaced by hb-013's randomized-temp-path fix (git log:
  `2373a5f`, `95934cf`), confirming step-2's `plan.md` (which still describes
  `$TICKET_SEQ`) is stale relative to the live file and must not be mirrored.
- **`skills/references/describe-ticket-subflow.md`** (21 lines): confirms the
  `id_or_summary`-derivation convention this step reuses unchanged — "the
  ticket's Background section, its first clause or sentence, truncated to
  roughly 8 words" (line 17) — and the active-flag mechanic: "Unset `active` on
  every existing entry ..., then append ... `active: true`" (line 18), which is
  exactly what AC4's "previously active ticket ... is not removed from context"
  requires (unsetting a flag is not removal).
- **`skills/references/references-toc.md`** (21 rows, read in full): rows for
  `ticket-loop-subflow.md`, `load-ticket-subflow.md`, `describe-ticket-subflow.md`,
  `exit-ticket-loop-subflow.md` appear consecutively in that order — mirroring
  the Action Registry's own row order (Load, Describe, Exit).
- **hb-013 landed after step-2** and only changed
  `interactive-ticket-subflow.md` §A.1 and its callers' path-resolution wording
  — confirmed no `$TICKET_SEQ`, no per-source scratch-dir naming scheme survives
  in any file this step touches or reads.
- **No automated test harness** — markdown-procedure repo (confirmed by every
  prior step-0/1/2 execution summary in this task). Verification is structural
  grep + dry-run trace.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "break this down" (active ticket has no children yet) | Not recognized — no Breakdown action exists | `$CHILDREN` = `[]` → every AC is a gap → propose-confirm → per-child confirm → each confirmed child added to context, active, tagged `parent: <active's id_or_summary>` |
| "break down the login epic" (ticket named, not active) | Not recognized | Same flow, targeting the named entry after NL match (never auto-selected if ambiguous) |
| Re-running Breakdown on the same parent after some children exist | N/A | `$CHILDREN` now includes the previously-created children (filtered by `parent` field) — gap report reflects their coverage |
| Subflow reports no gaps | N/A | User told "no gaps"; returns to top-level menu; `$TICKET_CONTEXT` unchanged (AC5) |
| User declines the propose-confirm step | N/A | Clean stop, nothing created, returns to menu |
| Load, Describe, Exit | Unchanged | Unchanged — Sections A/C/D/E and both existing action subflows untouched |
| `hb-ticket-discuss.md` `allowed-tools` | 6 `/tmp` grants + 5 Jira tools | Unchanged — zero new grants (see Design decision) |

Kind of change: **additive only**. New Action Registry row + new subflow file +
new TOC row + a two-word text tweak in two existing prose locations. No existing
row, section, or tool grant is edited in a way that changes its behavior.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Load / Describe dispatch | §B rows 1-2 → their own subflow files | Files untouched; §B gains a row, existing rows keep their text |
| Exit dispatch | §B row 3 → `exit-ticket-loop-subflow.md` | File untouched |
| §A ticket-entry model `{id_or_summary, content, active}` | 3 required fields | Breakdown only *appends* an optional `parent` field, per §A's own extensibility note — Load/Describe/Exit never read `parent`, so they're unaffected (mirrors `source`'s precedent exactly) |
| §C present-state / §D dispatch / §E log+continue | Unchanged control flow | Breakdown is invoked exactly like Load/Describe (matched via NL, mutates `$TICKET_CONTEXT` by reference, returns an outcome string for §E to log) |
| `breakdown-subflow.md` internal logic (gap analysis, propose-confirm, create-confirm) | Used as-is by `hb-task-plan` | Explicitly out of scope per this step's ticket; this step only supplies its caller contract, never edits the file |
| `hb-ticket-discuss.md` `allowed-tools` | No unrestricted `Read`, no `WebFetch`, no `Bash` | Unchanged by design (see Design decision) — nothing in this step's new logic needs a capability not already granted |

Purely additive — no table entry changes an existing behavior, so this is a
low-regression-risk step; the only new risk is the new subflow's own
correctness (target resolution, `parent`-field filtering, materialize callback),
covered in §5/§6 below.

---

## 1. Design overview

One new action, dispatched like Load/Describe, that resolves a target ticket
from context, supplies `breakdown-subflow.md`'s caller contract, and defines the
materialize callback the shared subflow calls back into per confirmed child:

```
Action Registry (ticket-loop-subflow.md §B) — new row:
  Breakdown ticket → breakdown-ticket-subflow.md

breakdown-ticket-subflow.md:
  §A Resolve target ticket (named → NL match/ambiguity-ask; unnamed → active
     entry; empty context → tell user, no-op)
       │
       ▼
  §B Supply + invoke breakdown-subflow.md
       ($PARENT_LABEL, $PARENT_CRITERIA from target's content;
        $CHILDREN = $TICKET_CONTEXT entries whose `parent` == target's
        id_or_summary; $MATERIALIZE_CHILD = "follow §C below")
       │
       ├──(breakdown-subflow.md §D, once per confirmed child)──► §C Materialize
       │                                                          callback
       ▼
  §D Compose return outcome (no-gaps / declined / created-N-skipped-M)
```

**Target resolution / ambiguity:** §A pattern-matches the user's triggering
utterance against every entry's `id_or_summary` (semantic match, same posture
as `load-ticket-subflow.md` §A/§B's "never guess"). Zero matches → ask which
ticket to target. Multiple matches → numbered list, user picks (never
auto-select) — identical convention to Load's multi-match handling. No name
given → default to the entry with `active: true`.

```
precedence: named-and-unambiguous match  >  default-to-active  >  ask-user
(tie-break: multiple name matches, or no name and no active entry → ask the
user to pick from a numbered list; never guess)
```

**`parent` field, not a new entry-identity scheme:** children are tracked by
setting an optional `parent: <parent's id_or_summary>` field on the child entry
at materialize time (§C) — the same additive-field mechanism `source` already
established for Load. `id_or_summary` is already the human-facing identifier
every other action treats as distinguishing; Breakdown does not add any new
uniqueness guarantee or dedup logic, matching the fact that no existing action
enforces `id_or_summary` uniqueness either.

**Failure/degradation** mirrors `breakdown-subflow.md`'s own contract exactly
(no-gaps → stop, decline → stop, skip → move on) — this subflow adds no new
failure branch beyond target-resolution's ambiguity/empty-context cases in §A.

**Alternatives considered and rejected:**
- *Widen `hb-ticket-discuss.md`'s `allowed-tools` to add unrestricted `Read` so
  the running skill can open `ticket-template.md` directly* — rejected: see the
  Design decision above; the reference-loading mechanism already covers this,
  and review already rejected this exact widening once in step-2.
- *Give child entries a numeric/UUID identity instead of reusing
  `id_or_summary` for the `parent` reference* — rejected: no existing entry
  field is a stable, hidden identity; introducing one would be a redefinition
  of §A's model (explicitly not this step's job), not an additive field. The
  known limitation (two entries sharing an `id_or_summary` makes `parent`
  ambiguous) is accepted as a pre-existing limitation of the model, not a new
  regression — nothing today disambiguates `id_or_summary` collisions elsewhere
  either.
- *Let `breakdown-subflow.md` resolve `$CHILDREN` itself by scanning
  `$TICKET_CONTEXT`* — rejected: the subflow's caller contract explicitly takes
  `$CHILDREN` as a pre-resolved list (line 8) precisely so it stays generic
  across callers with different storage models (loop context vs. step
  folders); resolving it is this subflow's job, not `breakdown-subflow.md`'s.

---

## 2. `breakdown-ticket-subflow.md` — specification

**New file.** One subflow, four lettered sections (A resolve, B supply+invoke, C
materialize callback, D compose return), matching the opening-blockquote +
"Caller contract." + lettered-sections shape already used by
`load-ticket-subflow.md` and `ticket-loop-subflow.md`.

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- (implicit) the user's triggering utterance — already in conversation context,
  not a formal parameter (see §1 alternatives-rejected, mirrors Load's own
  precedent)

**§A Resolve target ticket** — algorithm:
1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to break
   down." → return outcome `"Breakdown: no tickets in context."` (no subflow
   invocation, no mutation).
2. Utterance names a ticket → semantic-match against every entry's
   `id_or_summary`. Zero matches → ask which ticket to target; treat the
   clarifying reply as the name and re-match. Multiple matches → numbered list
   of `id_or_summary`s, user picks (never auto-select). One match → use it.
3. Utterance names no ticket → use the entry with `active: true`. If none is
   active (context non-empty but no active flag set — not reachable today
   since Load/Describe always leave exactly one entry active, but not
   structurally prevented) → ask the user which ticket to target.
4. Set `$PARENT_LABEL` = target's `id_or_summary`. Extract `$PARENT_CRITERIA` =
   target's `content`'s `# Acceptance Criteria` section (plain text
   extraction — the section already exists in every entry's `content` per the
   ticket-entry model; no new tool needed).

**§B Supply + invoke** — algorithm:
1. `$CHILDREN` = every `$TICKET_CONTEXT` entry (excluding the target itself)
   whose optional `parent` field equals `$PARENT_LABEL`, each mapped to
   `{label: entry.id_or_summary, criteria: entry.content's Acceptance Criteria
   section}`. May be empty (breakdown-subflow.md §A already handles this — every
   condition becomes a gap).
2. `$MATERIALIZE_CHILD` = "follow §C below, once per confirmed child."
3. Follow [${CLAUDE_SKILL_DIR}/references/breakdown-subflow.md](breakdown-subflow.md)
   with `$PARENT_LABEL`, `$PARENT_CRITERIA`, `$CHILDREN`, `$MATERIALIZE_CHILD` as
   resolved above. Capture its return value (materialized list + skipped list,
   or an early-stop signal from §B/§C of that subflow) for §D.

**§C Materialize callback** (invoked by `breakdown-subflow.md` §D step 4, once
per confirmed child, given the temp path of that child's drafted+confirmed
`ticket.md`) — algorithm:
1. Read `$TEMP_PATH/ticket.md`'s full text as `$content`.
2. Derive `$id_or_summary` from its Background section's first clause,
   truncated to ~8 words — same rule `describe-ticket-subflow.md` and
   `load-ticket-subflow.md` already use.
3. Unset `active` on every existing `$TICKET_CONTEXT` entry.
4. Append `{ id_or_summary: $id_or_summary, content: $content, active: true,
   parent: $PARENT_LABEL }`. `parent` is an additive, optional field per
   `ticket-loop-subflow.md` §A's extensibility note — Load/Describe/Exit ignore
   it safely, mirroring `source`'s precedent exactly.
5. Return `$id_or_summary` to `breakdown-subflow.md` §D step 4 as this
   materialize call's result (no durable path exists for the loop-context
   caller, so the entry's own label is the result it reports).

**§D Compose return outcome** — once `breakdown-subflow.md` itself returns
control (no-gaps exit, decline, or per-child loop exhausted):
- No-gaps exit → `"Breakdown '$PARENT_LABEL': no gaps found, nothing created."`
- Declined at propose-confirm → `"Breakdown '$PARENT_LABEL': declined, nothing
  created."`
- Otherwise → `"Breakdown '$PARENT_LABEL': created N child ticket(s):
  <label1>, <label2>, ...; M skipped."`, with N/labels/M read off
  `breakdown-subflow.md`'s own return value from §B step 3.

**Failure/degradation contract**: §A's empty-context and ambiguous-target cases
return without invoking `breakdown-subflow.md` at all (no mutation). Every other
failure/degradation mode is `breakdown-subflow.md`'s own (no-gaps, decline,
skip) — this subflow does not add a new one. No partial or malformed entry is
ever appended: §C only appends after a child is fully confirmed by
`breakdown-subflow.md` §D's own resolve loop (AC5 is satisfied by construction,
not by an extra check here).

---

## 3. Integration / wiring

- **`ticket-loop-subflow.md` §B (Action Registry)** — one new row added:

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Breakdown ticket | "break this down", "break down the login epic", "decompose this ticket into smaller ones" | `breakdown-ticket-subflow.md` |

  Inserted after the existing "Describe ticket" row and before "Exit" (matching
  the task ticket's own AC ordering: Load=AC4, Describe=AC5, Breakdown=AC6,
  Exit=AC9). **Sections A, C, D, E of `ticket-loop-subflow.md` are not touched**
  — per that file's own line 3-5 contract ("Later steps extend this skill's
  action set only via §B").
- **`skills/hb-ticket-discuss.md`** — `description:` (frontmatter) and the body
  prose at line 28 both change "(e.g. describe, load, exit)" →
  "(e.g. describe, load, breakdown, exit)" — a wording-only tweak, matching how
  step-2 updated the same two locations when Load shipped. **No `allowed-tools`
  change** (see Design decision). No `Steps` section change — Breakdown is
  reachable purely through the Action Registry, exactly like Load/Describe.
- **`skills/references/breakdown-subflow.md`** — **untouched.** This step only
  supplies its documented caller contract from a second caller; the file's own
  content is out of scope per the ticket.
- **`skills/references/references-toc.md`** — one new row for
  `breakdown-ticket-subflow.md`, placed directly after the
  `describe-ticket-subflow.md` row and before `exit-ticket-loop-subflow.md`
  (mirroring the Action Registry's new ordering).
- No configuration, build wiring, or dependency-manifest changes — this repo's
  skill layer has none.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/breakdown-ticket-subflow.md` | **new** — full Breakdown action subflow (§A-D as specified in §2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — one new Action Registry row (§B); Sections A, C, D, E untouched |
| `skills/hb-ticket-discuss.md` | **edit** — `description:` and body-prose example-actions list gain "breakdown"; `allowed-tools` and `Steps` section untouched |
| `skills/references/references-toc.md` | **edit** — one new row for `breakdown-ticket-subflow.md` |
| `.hb/facts.md` | **edit (conditional)** — only if this step's own process (§6) finds a candidate fact that passes the gate; not pre-asserted here |

No dependency manifest or lockfile in this repo's skill layer.

---

## 5. Tests

No automated harness (markdown-procedure repo, confirmed by every prior
execution summary in this task). Coverage is static/structural + dry-run trace,
matching the established convention from steps 0-2.

**Structural (grep/read-checkable):**
- `grep -n "Breakdown ticket" skills/references/ticket-loop-subflow.md` →
  exactly one Action Registry row, positioned between Describe and Exit; both
  existing rows' text unchanged.
- `grep -c "^####" skills/references/breakdown-ticket-subflow.md` → 4 (§A-D).
- `grep -n "breakdown-subflow" skills/references/breakdown-ticket-subflow.md` →
  references the shared subflow's caller contract, does not duplicate its
  gap-analysis/propose-confirm/create-confirm text inline.
- `git diff --stat -- skills/references/breakdown-subflow.md` → no output
  (untouched).
- `grep -n "allowed-tools" -A 15 skills/hb-ticket-discuss.md` → identical to
  the pre-step-3 frontmatter (no new grants); `git diff -- skills/hb-ticket-discuss.md`
  shows only the two-word wording hunks, not the `allowed-tools` block.
- `grep -n "breakdown-ticket-subflow" skills/references/references-toc.md` →
  exactly one row, positioned between the `describe-ticket-subflow.md` and
  `exit-ticket-loop-subflow.md` rows.
- **Reuse guard**: `grep -n "^Bash\|hb-sdk" skills/references/breakdown-ticket-subflow.md`
  → no matches (pure conversational state + `Follow`, no SDK/shell side effects
  inlined, matching sibling subflows' own convention).
- **Non-regression**: `git diff --stat -- skills/references/load-ticket-subflow.md
  skills/references/describe-ticket-subflow.md skills/references/exit-ticket-loop-subflow.md`
  → no output.

**Dry-run traces (exercised when `/hb-ticket-discuss` is run):**
- **No-gaps happy path**: active ticket has a matching child already in
  context (its `content` textually covers every parent AC) → §A resolves
  target = active entry → §B `$CHILDREN` = `[that child]` → `breakdown-subflow.md`
  §A/§B report no gaps → §D composes "no gaps found, nothing created" → context
  unchanged.
- **Gaps, full confirm**: active ticket has no children → §B `$CHILDREN` = `[]`
  → gap report = every AC → propose-confirm confirmed → per-child loop drafts 2
  candidates, both confirmed → §C called twice, each appends a new entry with
  `parent` = the active ticket's `id_or_summary`, each becomes active in turn
  (second unsets the first's `active`, doesn't remove it) → §D composes
  "created 2 child ticket(s): ...".
- **Named, ambiguous target**: two entries share a similar `id_or_summary`
  substring the user's utterance could match either of → §A presents a
  numbered list, user picks one → continues as single-target path.
- **Named, zero match**: utterance names a ticket not present → §A asks which
  ticket to target rather than guessing or erroring.
- **No name, no active entry** (contrived context state) → §A asks which
  ticket to target.
- **Decline at propose-confirm** → `breakdown-subflow.md` §C stop path → §D
  composes "declined, nothing created" → context unchanged.
- **Skip one of two candidates** → §C materialize called once (for the
  confirmed one only); §D's N/M counts reflect 1 created, 1 skipped.
- **Re-run Breakdown on the same parent after step above** → `$CHILDREN` now
  includes the previously-created child (filtered by `parent` == target's
  `id_or_summary`) → gap report reflects it.
- **Load/Describe/Exit non-regression**: dry-run traces from steps 1-2's
  execution summaries re-verified unaffected (no shared state touched by
  Breakdown's new `parent` field).

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A (markdown repo); structural checks
   below are authoritative.
2. **Scope check** — `git status --short` shows exactly the 4 files in §4
   (plus `.hb/facts.md` only if step 6's own process changed it, and this
   step's own `.hb/task/...` artifacts).
3. **Action Registry row** — `ticket-loop-subflow.md` §B has exactly 4 rows
   (Load, Describe, Breakdown, Exit) in that order; Sections A/C/D/E
   byte-unchanged (`git diff` shows only the §B table hunk).
4. **New subflow shape** — `breakdown-ticket-subflow.md` opens with a `>`
   blockquote + "Caller contract." line, has exactly 4 `####` sections (A-D),
   and ends with a "Failure/degradation contract" line — matching sibling
   subflow shape.
5. **`allowed-tools` unchanged** — `git diff -- skills/hb-ticket-discuss.md`
   shows no hunk touching the `allowed-tools:` block; only the two `description`/
   prose wording hunks appear.
6. **Per-AC checks** — read `breakdown-ticket-subflow.md` end-to-end and
   confirm each of the ticket's ACs is textually satisfied (full mapping in §7
   below); specifically confirm: §A's "ask which ticket" path appears for both
   the zero-match and no-name-no-active cases (never auto-select/guess), and §D
   never claims something was created on the no-gaps or decline paths.
7. **Non-regression** — `git diff --stat` for `load-ticket-subflow.md`,
   `describe-ticket-subflow.md`, `exit-ticket-loop-subflow.md`,
   `breakdown-subflow.md` shows no changes.
8. **TOC row** — `references-toc.md` has exactly one new row for
   `breakdown-ticket-subflow.md`, correctly pointing at the new file's path,
   positioned between the Describe and Exit rows.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Breakdown action added, NL-selectable, defaults to active ticket, asks if ambiguous | §3 (Action Registry row); §2 §A (default-to-active, ask-on-ambiguity/zero-match) | |
| 2 — supplies `breakdown-subflow.md` with parent criteria + tracked children | §2 §B | |
| 2.1 — Parent = targeted ticket's Acceptance Criteria | §2 §A step 4 | |
| 2.2 — Children = context entries previously created as children of this parent, via a parent reference on each child entry | §2 §B step 1 (filter by `parent` field); §2 §C step 4 (field set at materialize time) | `parent` is additive per `ticket-loop-subflow.md` §A's extensibility note — mirrors `source`'s precedent |
| 3 — subflow's own gap report / no-gaps / propose-confirm / per-child confirm behave exactly as specified there, not re-implemented | §2 §B step 3 (Follow, not re-derive); §1 (breakdown-subflow.md untouched) | |
| 4 — on child confirm, added to context with parent record, becomes active; previously active entry not removed | §2 §C steps 3-4 | Unset-then-append mechanic — same as Load/Describe, satisfies "not removed" |
| 5 — no-gaps → return to top-level menu, nothing created | §2 §D (no-gaps branch); §2 Failure/degradation contract | |
| 6 — this action's logic lives in its own subflow file, separate from the shared subflow; TOC updated | §2 (new file `breakdown-ticket-subflow.md`); §3 (TOC row) | |

---

## 8. Out of scope (per ticket)

- Any change to `breakdown-subflow.md`'s internal logic (gap analysis,
  propose-confirm, create-confirm) — this step only supplies the caller-side
  wiring it already expects.
- Load, Clear, and Push actions — other steps (Load already shipped in step-2;
  Clear/Push are steps 4/5 of this task).
- Persisting the parent/child relationship to `.hb/` — it lives only in the
  loop's in-conversation `$TICKET_CONTEXT` model, exactly like every other
  field on a ticket entry.
