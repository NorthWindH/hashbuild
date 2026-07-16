# Step 4 Plan — Clear ticket(s) action

`hb-ticket-discuss`'s loop (shipped in steps 1-3) offers Load, Describe, and
Breakdown — all three only ever *add* to `$TICKET_CONTEXT`. The **motivating
case**: a user accumulates several tickets across a session, decides one is a
dead end, and says "clear PROJ-123" or "clear the active ticket" — today no
Action Registry row recognizes that, so the only way to remove a ticket is to
`/clear` the whole conversation and lose every other ticket in context too.
This step adds a fourth action, **Clear ticket(s)**, covering the **general
class** of removing any subset of tickets currently held in context — one, a
named several, or all — including the active one, with an explicit
confirmation gate whenever more than one ticket would be removed at once.
Scope boundary: **additive only, in-memory context mutation only** — no file
I/O, no new tool grant, and no persistence implication, since nothing was ever
written to `.hb/` by these tickets. Externally observable effect once this
lands: saying "clear the active ticket", "remove PROJ-123 and PROJ-124", or
"clear all tickets" at any loop iteration removes exactly the named
ticket(s) from context (asking for confirmation first when more than one
would go), and the very next iteration's summary reflects the updated count,
id list, and active-ticket state immediately.

Source ticket: `./ticket.md`. Builds on the **shipped** Load/Describe/
Breakdown/Exit actions and loop skeleton (`skills/hb-ticket-discuss.md`,
`skills/references/ticket-loop-subflow.md`,
`skills/references/load-ticket-subflow.md`,
`skills/references/describe-ticket-subflow.md`,
`skills/references/breakdown-ticket-subflow.md`,
`skills/references/exit-ticket-loop-subflow.md`) — all read in full during
planning, current as of commit `3b14702` (the last commit to touch any of
these files; repo HEAD is `40a198c`, an unrelated task-archive commit). This
plan targets that code as it exists **now**.

> **Design decision — resolve "clear all" through the same count-based
> confirmation rule as everything else, not a special-cased always-confirm
> path.** The ticket's AC5 reads "Clearing is confirmed... when it would
> remove more than one ticket at once (e.g. "clear all")" — a naive reading
> might hard-code "any 'all' request always confirms." But the rule as
> stated is about *how many tickets would be removed*, not the phrasing used
> to select them: a context holding exactly one ticket and a "clear all"
> request removes exactly one ticket, identical in effect to naming that one
> ticket directly. Hard-coding "all" as always-confirm would make the
> confirmation gate depend on phrasing instead of blast radius, which is the
> wrong axis and harder to reason about. This plan's §A/§B therefore resolve
> `$TARGETS` first (regardless of how it was selected — named, active, or
> all) and gate confirmation purely on `|$TARGETS| > 1`, exactly mirroring
> how `breakdown-ticket-subflow.md` §A resolves a target before any
> downstream branching. See §1 and the AC-traceability table (§7, AC5).

---

## 0. Current-state facts (verified during planning)

- **`skills/references/ticket-loop-subflow.md`** (73 lines, read in full): §A
  (lines 12-26) defines the ticket entry as `{ id_or_summary, content, active
  }` with an explicit extensibility note that later steps may attach
  *additional* optional fields without revisiting this file. §B (Action
  Registry, lines 28-39) has exactly 4 rows today: Load, Describe, Breakdown,
  Exit — in that order, matching the task ticket's AC numbering (Load=AC4,
  Describe=AC5, Breakdown=AC6, Clear=AC7, Push=AC8, Exit=AC9 — Clear belongs
  between Breakdown and Exit). §D (Dispatch, lines 53-60): "invoke the
  matched action's dispatch subflow, passing `$TICKET_CONTEXT` by reference
  (the callee mutates it in place)" — no other formal parameter; the
  triggering utterance is already visible in conversation, mirroring
  Load/Breakdown's own precedent for actions that need to parse it.
- **`skills/references/breakdown-ticket-subflow.md`** (74 lines, read in
  full): established the precedent this step reuses directly — §A's
  target-resolution algorithm (semantic-match a named reference against every
  entry's `id_or_summary`; zero matches → ask and re-match; multiple matches
  → numbered list, user picks, never auto-select; no name → default to the
  `active: true` entry). This step's own §A follows the identical posture,
  extended to resolve a *set* of targets instead of exactly one.
- **`skills/references/load-ticket-subflow.md`** (100 lines) and
  **`skills/references/describe-ticket-subflow.md`** (21 lines): both confirm
  the "unset `active` on every existing entry, then set the new one" mechanic
  for *adding* an active entry — this step is the mirror-image "remove
  entries, set no new active entry" case; neither file needs to change,
  since neither reads or writes any field this step doesn't already use
  (`id_or_summary`, `active`).
- **`skills/references/exit-ticket-loop-subflow.md`** (16 lines): confirms
  `$TICKET_CONTEXT` is read-only there and unaffected by this step.
- **`skills/hb-ticket-discuss.md`** (56 lines, read in full): frontmatter
  `allowed-tools` (lines 12-24) — 6 `/tmp`-scoped Read/Write/Edit grants + 5
  Atlassian Rovo Jira tools; **no** unrestricted `Read`, **no** `WebFetch`,
  **no** `Bash`. `description:` (frontmatter, lines 4-11) and the body prose
  at line 28 both read "...a menu of next actions (e.g. describe, load,
  breakdown, exit) selectable via natural language" — the same two-location
  pattern updated each time a prior action shipped (steps 2-3); this step
  adds "clear" to both, following that exact precedent.
- **`skills/references/references-toc.md`** (22 rows, read in full): rows for
  `ticket-loop-subflow.md`, `load-ticket-subflow.md`,
  `describe-ticket-subflow.md`, `breakdown-ticket-subflow.md`,
  `exit-ticket-loop-subflow.md` appear consecutively in that order —
  mirroring the Action Registry's own row order.
- **This step's own `ticket.md`** (AC7, read in full): confirms out-of-scope
  bullets — Push is the next step (not this one), and "no persistence
  implications... nothing was ever written to `.hb/` by these tickets," i.e.
  this step touches only `$TICKET_CONTEXT`, never any file under `.hb/`.
- **No automated test harness** — markdown-procedure repo (confirmed by every
  prior step-0 through step-3 execution summary in this task). Verification
  is structural grep + dry-run trace, matching established convention.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "clear the active ticket" (1 other ticket also in context) | Not recognized — no Clear action exists | Active entry removed (single, unambiguous target — no confirm needed); no new entry promoted to active; other ticket remains |
| "remove PROJ-123 and PROJ-124" (both present, unambiguous) | Not recognized | Both resolved via §A, confirmation asked (2 targets), on yes both removed |
| "clear all tickets" (3 in context) | Not recognized | All 3 resolved as `$TARGETS`, confirmation asked (3 > 1), on yes context emptied |
| "clear all tickets" (exactly 1 in context) | Not recognized | 1 resolved as `$TARGETS`, no confirm needed (count == 1), removed directly |
| Named reference matches two entries | Not recognized | Numbered list scoped to that reference, user picks — never auto-cleared |
| Named reference matches zero entries | Not recognized | User asked to clarify; reply re-matched |
| No name, no "all", not "active ticket" | Not recognized | User asked "Which ticket(s) would you like to clear?" |
| Confirmation declined | N/A | No mutation; outcome logged as declined |
| Load, Describe, Breakdown, Exit | Unchanged | Unchanged — Sections A/C/D/E and all three existing action subflows untouched |
| `hb-ticket-discuss.md` `allowed-tools` | 6 `/tmp` grants + 5 Jira tools | Unchanged — Clear needs no file/MCP access, only context-list mutation |

Kind of change: **additive only**. New Action Registry row + new subflow file
+ new TOC row + a one-word text tweak in two existing prose locations. No
existing row, section, or tool grant changes behavior.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Load / Describe / Breakdown dispatch | §B rows 1-3 → their own subflow files | Files untouched; §B gains one row, existing rows keep their text |
| Exit dispatch | §B row 4 → `exit-ticket-loop-subflow.md` | File untouched |
| §A ticket-entry model `{id_or_summary, content, active}` | 3 required fields, plus optional `source`/`parent` | Clear only *removes* entries and unsets `active`; it introduces no new field, so it cannot violate the extensibility note |
| §C present-state / §D dispatch / §E log+continue | Unchanged control flow | Clear is invoked exactly like the other three: matched via NL, mutates `$TICKET_CONTEXT` by reference, returns an outcome string for §E to log |
| Auto-promotion of a new active ticket after removal | N/A (no such action exists yet) | AC4 explicitly forbids auto-promotion — §C step 2 below asserts this as a rule, not an oversight |
| `hb-ticket-discuss.md` `allowed-tools` | No unrestricted `Read`, no `WebFetch`, no `Bash` | Unchanged — Clear needs zero capability beyond what's already granted (pure list mutation over data already in conversation context) |

Purely additive and, unlike Load/Describe/Breakdown, this action never writes
any file — the only new risk is the new subflow's own correctness (target-set
resolution, confirmation gating, no-auto-promotion), covered in §5/§6 below.

---

## 1. Design overview

One new action, dispatched like Load/Describe/Breakdown, that resolves a
*set* of targets (rather than exactly one), gates on a count-based
confirmation rule, then removes them:

```
Action Registry (ticket-loop-subflow.md §B) — new row:
  Clear ticket(s) → clear-ticket-subflow.md

clear-ticket-subflow.md:
  §A Resolve target set (empty context → tell user, no-op; "all" → every
     entry; "the active ticket" only → active entry; named reference(s) →
     NL match per reference, numbered-list on ambiguity, ask on zero-match;
     nothing recognized → ask "which ticket(s)?" and re-run §A)
       │
       ▼
  §B Confirm (|$TARGETS| > 1 → present list, ask; decline → stop, no
     mutation. |$TARGETS| == 1 → skip straight to §C)
       │
       ▼
  §C Apply (remove every resolved entry; never auto-promote a new active
     entry; compose outcome string)
```

**Target-set resolution, not single-target resolution:** `breakdown-ticket-
subflow.md` §A resolves exactly one target because breakdown only ever
targets one parent. Clear must resolve *zero-or-more* named references into
a set, so §A below generalizes that same match/ambiguity/zero-match posture
per named reference, then unions the results:

```
precedence:  "all" request  >  named reference(s) (one or more)  >
             "the active ticket" alone  >  ask-user
(tie-break inside "named references": each reference is matched
 independently — zero matches on any one reference asks the user to
 clarify that reference; multiple matches on any one reference presents a
 numbered list scoped to it; never guess on either)
```

**Confirmation gate is count-based, not phrasing-based** (see the Design
decision above): `|$TARGETS| > 1` triggers a single confirm-list prompt
covering the whole set; `|$TARGETS| == 1` clears directly, whether that one
target came from a name, from "the active ticket," or from an "all" request
against a single-ticket context.

**No auto-promotion:** §C never sets `active: true` on a surviving entry,
even when the removed set included the previously-active one. This is a
explicit rule, not a gap — `ticket-loop-subflow.md` §C's existing "No active
ticket" presentation already covers the resulting state with zero changes to
that file.

**Failure/degradation** mirrors the sibling actions' own posture: every
early-return path (empty context, no active ticket, unresolved reference,
declined confirmation) returns without mutating `$TICKET_CONTEXT` and without
raising an error.

**Alternatives considered and rejected:**
- *Always confirm on any "clear all" phrasing, regardless of resulting
  count* — rejected: see the Design decision above; ties the gate to
  phrasing instead of blast radius, and produces an inconsistent user
  experience (a context with exactly one ticket, cleared via "all," would
  demand a confirmation that clearing it by name would not).
- *Auto-promote the most-recently-added surviving entry to active after a
  clear* — rejected: AC4 explicitly says no new entry is auto-promoted;
  inventing an implicit promotion rule would silently contradict the
  ticket and surprise the user mid-session.
- *Resolve the whole target set with one NL match against the full
  utterance instead of splitting named references first* — rejected: a
  single combined match can't distinguish "PROJ-123 and PROJ-124" (two
  targets) from a single ticket whose summary happens to contain "and";
  splitting first, matching each reference independently, mirrors how a
  human would parse the same sentence and reuses `breakdown-ticket-
  subflow.md`'s own per-reference matching exactly, just applied N times
  instead of once.

---

## 2. `clear-ticket-subflow.md` — specification

**New file.** One subflow, three lettered sections (A resolve target set, B
confirm, C apply), matching the opening-blockquote + "Caller contract." +
lettered-sections shape already used by `breakdown-ticket-subflow.md`,
`load-ticket-subflow.md`, and `ticket-loop-subflow.md`.

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- (implicit) the user's triggering utterance — already in conversation
  context, not a formal parameter (mirrors Load/Breakdown's own precedent)

**§A Resolve target set** — algorithm:
1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to clear."
   → return outcome `"Clear: no tickets in context."` (no mutation).
2. Utterance requests the whole context ("clear all," "clear everything," or
   an equivalent) → `$TARGETS` = every entry in `$TICKET_CONTEXT`. Continue
   to §B.
3. Utterance refers only to "the active ticket" (no other ticket named) →
   the entry with `active: true`. None active → tell the user "No active
   ticket to clear." → return outcome `"Clear: no active ticket."` (no
   mutation). Otherwise `$TARGETS` = `[that entry]`. Continue to §B.
4. Utterance names one or more tickets (by id/summary):
   1. Split the utterance into its distinct named references (one or
      several — e.g. "PROJ-123 and PROJ-124" is two).
   2. For each named reference, semantic-match against every entry's
      `id_or_summary` — same posture as `breakdown-ticket-subflow.md` §A /
      `load-ticket-subflow.md` §A ("never guess"):
      - Zero matches → ask the user to clarify that one reference; treat
        the clarifying reply as the name and re-match it.
      - Multiple matches → present a numbered list of the matching
        entries' `id_or_summary`s, scoped to that one reference; the user
        picks one — never auto-select.
      - One match → include it in the resolving set.
   3. `$TARGETS` = the deduplicated union of every entry resolved across
      all named references. Continue to §B.
5. Utterance requests none of the above (no "all," no named reference, no
   "active ticket" phrasing) → ask the user "Which ticket(s) would you like
   to clear?" and re-run this §A against the reply.

**§B Confirm** — algorithm:
1. `|$TARGETS|` > 1 (true for any multi-entry "all" or multi-name request) →
   present the list of `$TARGETS`' `id_or_summary`s and ask the user to
   confirm removal. Decline → return outcome `"Clear: declined, nothing
   removed."` (no mutation).
2. `|$TARGETS|` == 1 → skip confirmation; proceed directly to §C.

**§C Apply** — algorithm:
1. Remove every entry in `$TARGETS` from `$TICKET_CONTEXT`, matched by
   entry identity (the exact entries resolved in §A, not a fresh
   `id_or_summary` re-match).
2. Do not set `active: true` on any remaining entry, even if the removed
   set included the previously-active one — no auto-promotion (AC4). If
   entries remain and none is active, `ticket-loop-subflow.md` §C's
   existing presentation already shows "No active ticket" — no change
   needed there.
3. Return outcome:
   - Whole-context ("all") request → `"Cleared all N ticket(s) from
     context."`
   - Otherwise → `"Cleared N ticket(s): <label1>, <label2>, ...."`
   (N = `|$TARGETS|`; labels = each target's `id_or_summary`, in the order
   resolved.)

**Failure/degradation contract**: §A's empty-context, no-active-ticket, and
unresolved-reference cases, and §B's decline, all return without mutating
`$TICKET_CONTEXT`. No partial removal ever occurs — §C only runs once
`$TARGETS` is fully resolved and (when required) confirmed.

---

## 3. Integration / wiring

- **`ticket-loop-subflow.md` §B (Action Registry)** — one new row added:

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Clear ticket(s) | "clear the active ticket", "remove PROJ-123 and PROJ-124", "clear all tickets" | `clear-ticket-subflow.md` |

  Inserted after the existing "Breakdown ticket" row and before "Exit"
  (matching the task ticket's own AC ordering: Breakdown=AC6, Clear=AC7,
  Push=AC8, Exit=AC9). **Sections A, C, D, E of `ticket-loop-subflow.md` are
  not touched** — per that file's own contract ("Later steps extend this
  skill's action set only via §B").
- **`skills/hb-ticket-discuss.md`** — `description:` (frontmatter) and the
  body prose both change "(e.g. describe, load, breakdown, exit)" →
  "(e.g. describe, load, breakdown, clear, exit)" — a wording-only tweak,
  matching how steps 2-3 updated the same two locations when Load/Breakdown
  shipped. **No `allowed-tools` change** — Clear needs no file or MCP
  access. No `Steps` section change — Clear is reachable purely through the
  Action Registry, exactly like the other three actions.
- **`skills/references/references-toc.md`** — one new row for
  `clear-ticket-subflow.md`, placed directly after the
  `breakdown-ticket-subflow.md` row and before `exit-ticket-loop-subflow.md`
  (mirroring the Action Registry's new ordering).
- No configuration, build wiring, or dependency-manifest changes — this
  repo's skill layer has none.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/clear-ticket-subflow.md` | **new** — full Clear action subflow (§A-C as specified in §2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — one new Action Registry row (§B); Sections A, C, D, E untouched |
| `skills/hb-ticket-discuss.md` | **edit** — `description:` and body-prose example-actions list gain "clear"; `allowed-tools` and `Steps` section untouched |
| `skills/references/references-toc.md` | **edit** — one new row for `clear-ticket-subflow.md` |
| `.hb/facts.md` | **edit (conditional)** — only if this step's own process (§6) finds a candidate fact that passes the gate; not pre-asserted here |

No dependency manifest or lockfile in this repo's skill layer.

---

## 5. Tests

No automated harness (markdown-procedure repo, confirmed by every prior
execution summary in this task). Coverage is static/structural + dry-run
trace, matching the established convention from steps 0-3.

**Structural (grep/read-checkable):**
- `grep -n "Clear ticket(s)" skills/references/ticket-loop-subflow.md` →
  exactly one Action Registry row, positioned between Breakdown and Exit;
  the other three rows' text unchanged.
- `grep -c "^####" skills/references/clear-ticket-subflow.md` → 3 (§A-C).
- `git diff --stat -- skills/references/load-ticket-subflow.md
  skills/references/describe-ticket-subflow.md
  skills/references/breakdown-ticket-subflow.md
  skills/references/exit-ticket-loop-subflow.md
  skills/references/breakdown-subflow.md` → no output (all five untouched).
- `grep -n "allowed-tools" -A 15 skills/hb-ticket-discuss.md` → identical to
  the pre-step-4 frontmatter (no new grants); `git diff --
  skills/hb-ticket-discuss.md` shows only the two wording hunks.
- `grep -n "clear-ticket-subflow" skills/references/references-toc.md` →
  exactly one row, positioned between the `breakdown-ticket-subflow.md` and
  `exit-ticket-loop-subflow.md` rows.
- **Reuse guard**: `grep -n "^Bash\|hb-sdk" skills/references/clear-ticket-subflow.md`
  → no matches (pure conversational state mutation, no SDK/shell side
  effects inlined, matching sibling subflows' convention).
- **No-file-write guard**: `grep -n "Write\|mkdir\|TARGET_PATH"
  skills/references/clear-ticket-subflow.md` → no matches (unlike Load/
  Describe/Breakdown, Clear never resolves or writes a scratch path).

**Dry-run traces (exercised when `/hb-ticket-discuss` is run):**
- **Single named target, unambiguous**: one entry's `id_or_summary`
  matches "PROJ-123" uniquely → §A resolves `$TARGETS` = `[that entry]` →
  §B skips confirm (count == 1) → §C removes it, returns "Cleared 1
  ticket(s): ...".
- **Active-ticket target**: utterance says "clear the active ticket," one
  entry has `active: true` → §A §3 resolves it → §B skips confirm → §C
  removes it and does not promote any remaining entry to active; next
  iteration's summary shows "No active ticket" if entries remain.
- **Multiple named targets**: "remove PROJ-123 and PROJ-124," both present
  and unambiguous → §A resolves both via two independent matches →
  `$TARGETS`, size 2 → §B asks for confirmation listing both → on yes, §C
  removes both.
- **"Clear all," multiple tickets**: 3 entries in context → §A §2 resolves
  all 3 → §B confirms (3 > 1) → on yes, §C empties `$TICKET_CONTEXT`,
  returns "Cleared all 3 ticket(s) from context."
- **"Clear all," single ticket**: exactly 1 entry in context → §A §2
  resolves `$TARGETS` = that one entry → §B skips confirm (count == 1,
  even though the request was "all") → §C removes it directly.
- **Named reference, ambiguous**: two entries share a substring the named
  reference could match either of → §A presents a numbered list scoped to
  that reference; user picks one; continues with the resolved single
  entry for that reference.
- **Named reference, zero match**: reference names a ticket not present →
  §A asks the user to clarify that reference rather than guessing or
  erroring.
- **No target recognized**: utterance names nothing, no "all," no "active
  ticket" phrasing → §A §5 asks "Which ticket(s) would you like to
  clear?"; reply re-parsed through §A.
- **Decline at confirmation**: multi-target case, user declines → §B
  returns "Clear: declined, nothing removed."; `$TICKET_CONTEXT` unchanged.
- **Empty context**: `/hb-ticket-discuss` freshly started, Clear invoked
  before anything is loaded/described → §A §1 tells the user, no mutation.
- **No active ticket, "clear the active ticket" requested**: context
  non-empty but no entry marked active (contrived state) → §A §3 tells the
  user, no mutation.
- **Load/Describe/Breakdown/Exit non-regression**: dry-run traces from
  steps 1-3's execution summaries re-verified unaffected — Clear reads and
  removes existing entries but adds no new field and touches no other
  subflow's logic.

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A (markdown repo); structural
   checks below are authoritative.
2. **Scope check** — `git status --short` shows exactly the 4 files in §4
   (plus `.hb/facts.md` only if this step's own process changed it, and
   this step's own `.hb/task/...` artifacts).
3. **Action Registry row** — `ticket-loop-subflow.md` §B has exactly 5 rows
   (Load, Describe, Breakdown, Clear, Exit) in that order; Sections A/C/D/E
   byte-unchanged (`git diff` shows only the §B table hunk).
4. **New subflow shape** — `clear-ticket-subflow.md` opens with a `>`
   blockquote + "Caller contract." line, has exactly 3 `####` sections
   (A-C), and ends with a "Failure/degradation contract" line — matching
   sibling subflow shape.
5. **`allowed-tools` unchanged** — `git diff -- skills/hb-ticket-discuss.md`
   shows no hunk touching the `allowed-tools:` block; only the two wording
   hunks appear.
6. **Per-AC checks** — read `clear-ticket-subflow.md` end-to-end and
   confirm each of the ticket's ACs is textually satisfied (full mapping in
   §7 below); specifically confirm: §A never auto-selects on an ambiguous
   or zero-match reference; §B's confirm gate is stated as count-based
   (`|$TARGETS| > 1`), not phrasing-based; §C explicitly states no
   auto-promotion of a new active entry.
7. **Non-regression** — `git diff --stat` for `load-ticket-subflow.md`,
   `describe-ticket-subflow.md`, `breakdown-ticket-subflow.md`,
   `exit-ticket-loop-subflow.md`, `breakdown-subflow.md` shows no changes.
8. **TOC row** — `references-toc.md` has exactly one new row for
   `clear-ticket-subflow.md`, correctly pointing at the new file's path,
   positioned between the Breakdown and Exit rows.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Clear ticket(s) action added to menu, NL-selectable | §3 (Action Registry row) | |
| 2.1 — targets a single ticket, by id/summary or "the active ticket" | §2 §A steps 3-4 | |
| 2.2 — targets several named tickets in one request | §2 §A step 4 (split references, match each) | |
| 2.3 — targets all tickets currently in context | §2 §A step 2 | |
| 3 — ambiguous NL references present a numbered list; never auto-cleared | §2 §A step 4.2 ("never auto-select") | Mirrors `breakdown-ticket-subflow.md` §A's own posture |
| 4 — clearing active ticket unsets active state; no auto-promotion | §2 §C step 2 | Explicit rule, not an omission — see Design decision |
| 5 — confirm before clearing >1 at once; single unambiguous target clears without extra confirm | §2 §B | Count-based gate (`|$TARGETS| > 1`), not phrasing-based — see Design decision |
| 6 — next-iteration summary reflects updated context immediately | §1 (no new presentation logic needed) | `ticket-loop-subflow.md` §C already reads live `$TICKET_CONTEXT` each iteration; Clear's in-place mutation is picked up with zero changes to §C |
| 7 — logic lives in its own subflow file; TOC updated | §2 (new file `clear-ticket-subflow.md`); §3 (TOC row) | |

---

## 8. Out of scope (per ticket)

- Push action — that is step 5 of this task.
- Any persistence implications — Clear only mutates the in-conversation
  `$TICKET_CONTEXT` model; nothing was ever written to `.hb/` by these
  tickets, and this step writes nothing there either (beyond the
  conditional facts-store edit already covered by every step in this task).
- Auto-promoting a new active ticket after a clear — explicitly excluded by
  AC4; not a follow-up left for a later step, just a rule this step
  enforces by not implementing promotion at all.
