# Step 7 Plan — Set active ticket + Other action

`hb-ticket-discuss`'s loop (steps 1-5) ships Load, Describe, Breakdown,
Clear, Push, and Exit. None of them can make an already-loaded ticket active
without re-running Load, Describe, or Breakdown on it. The loop also has no
escape hatch for a request that matches no registered action.

**Motivating case A**: three tickets are loaded, and the user says "make
CSS-2664 active". No row matches this phrase today. Section D falls to a
generic re-prompt, even though the intent is unambiguous.

**Motivating case B**: the user says "reformat PROJ-123 to use bullet
points." This also matches no row today. It gets the same generic
re-prompt, with no attempt to help or explain why.

This step adds two actions. The first is explicit active-ticket selection
with no content mutation. The second is a bounded escape hatch for
unregistered requests.

Scope: additive, in-memory context mutation only. No file I/O and no new
tool grant — this mirrors Clear's own scope boundary exactly.

Externally observable effect: saying "set ticket 2 as active" flips one
entry's `active` flag, no content change. A reply matching none of the
first six actions now routes through `other-action-subflow.md` instead of a
bare re-prompt.

Source ticket: `./ticket.md`. This plan builds on the shipped loop skeleton
and five actions, read in full during planning:

- `skills/hb-ticket-discuss.md`
- `skills/references/ticket-loop-subflow.md`
- `skills/references/load-ticket-subflow.md`
- `skills/references/describe-ticket-subflow.md`
- `skills/references/breakdown-ticket-subflow.md`
- `skills/references/clear-ticket-subflow.md`
- `skills/references/push-ticket-subflow.md`
- `skills/references/exit-ticket-loop-subflow.md`

All eight are current as of commit `dcae201`, the repo HEAD at plan time.
This plan targets that code as it exists now.

Note: `skills/references/breakdown-subflow.md` carries an uncommitted TODO
comment. It belongs to a different task's in-flight review and is left
untouched here.

> **Design decision — split §D's single "ambiguous or unmatched" fallback
> into two outcomes.** `ticket-loop-subflow.md` §D (lines 57-62) today
> treats "ambiguous" and "unmatched" as one bucket: ask and re-prompt.
>
> Adding "Other" as AC2's catch-all for replies matching no registered
> action conflicts with that if left as one bucket. A confident zero-match
> reply must now route to `other-action-subflow.md`, which itself prompts
> and attempts the request, not a bare inline question.
>
> A reply that plausibly matches two or more known actions is a different
> failure mode. That is genuine ambiguity between defined options, not
> "nothing fits," and should still get a direct clarifying question, not
> the catch-all.
>
> §3 below rewrites §D to branch on this distinction. Ambiguous-among-known
> still asks directly and re-loops to §D. Confident zero-match, including
> against Other's own escape-hatch phrasing, dispatches
> `other-action-subflow.md`. See §1 and the AC-traceability table (§7,
> AC2).

---

## 0. Current-state facts (verified during planning)

- `ticket-loop-subflow.md` is 75 lines, read in full.
  - §B (Action Registry, lines 28-41) has 6 rows: Load, Describe,
    Breakdown, Clear, Push, Exit, in that order.
  - §C (Present, lines 43-53) step 4 says the menu lists whatever §B holds.
  - No edit is needed there for two new rows to show up (AC4 already holds).
  - §D (Dispatch, lines 55-62) is the section this step must edit.
  - §D's current single-bucket fallback is the tension described above.
  - §A and §E stay untouched by this step.
  - No field this step needs is missing from `{ id_or_summary, content,
    active }`.
- `clear-ticket-subflow.md` (68 lines, read in full) sets the match posture
  this step reuses.
  - Zero matches asks the user; multiple matches shows a numbered list;
    one match resolves — never a guess.
  - `set-active-ticket-subflow.md` §A reuses this directly for its by-name
    path.
- `push-ticket-subflow.md` (241 lines, read in full) confirms the shared
  subflow shape.
  - It opens with a blockquote, a "Caller contract." line, then lettered
    sections.
  - It also confirms a metadata-only action never writes `content` back —
    the same posture AC1.3 needs.
- Load and Describe already use an unset-then-set `active` mechanic when
  adding an entry.
  - `set-active-ticket-subflow.md` reuses that mechanic, without adding or
    removing any entry.
- `hb-ticket-discuss.md` is 56 lines, read in full.
  - `description:` (line 10) and body prose (line 28) both name five
    actions today: describe, load, breakdown, clear, push.
  - Steps 2-5 each appended their own action's name to that same wording.
  - This step's ticket names only `ticket-loop-subflow.md` and the two new
    subflow files (AC1-4).
  - See §3 for why this file stays untouched this time.
  - `allowed-tools` (lines 12-24) needs no change; neither new action calls
    any tool.
- `references-toc.md` (24 rows, read in full) lists every action subflow,
  mirroring §B's own row order.
  - This step adds two rows in the same relative position as the new §B
    rows.
- This step's own `ticket.md` has 4 ACs, read in full.
  - AC1.1 gives two example phrasings for Set active: a positional one
    ("ticket 2") and a by-name one ("CSS-2664").
  - Both must resolve via §A below.
  - AC2.2 scopes Other to data already in `$TICKET_CONTEXT`, with a
    not-supported report otherwise.
- No automated test harness exists; this is a markdown-procedure repo.
  - Every prior execution summary in this task (steps 0-5) confirms this.
  - Verification here is structural grep plus dry-run trace, matching that
    convention.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "set ticket 2 as active" (3 entries) | Not recognized, generic re-prompt | 2nd entry (§C order) becomes `active`; all others unset |
| "make CSS-2664 active" (unambiguous) | Not recognized | Entry resolved by `id_or_summary`, becomes `active` |
| Named/positional reference ambiguous or out of range | Not recognized | User asked to clarify — never auto-selected |
| No ticket named ("make it active") | Not recognized | User asked "Which ticket would you like to set active?" |
| "reformat PROJ-123 to use bullet points" (in-context) | Not recognized, generic re-prompt | Routed to `other-action-subflow.md`; content reformatted, reported |
| Request needing new data/external calls | Not recognized, generic re-prompt | Routed to `other-action-subflow.md`; works with the user toward an in-scope version, "not supported" only if nothing fits |
| Reply ambiguous between two known actions (e.g. Clear vs. Push) | Generic re-prompt | Still a direct clarifying question — not routed to Other |
| Load, Describe, Breakdown, Clear, Push, Exit | Unchanged | Unchanged — subflow files and §B rows untouched |
| `hb-ticket-discuss.md` wording/tools | 6 `/tmp` grants + 5 Jira tools; 5-action wording | Unchanged — no new grant needed; wording deliberately not extended |

Kind of change: additive, plus one behavior-altering edit scoped to §D's
zero-match fallback. Existing-action dispatch is unaffected by that edit.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Load/Describe/Breakdown/Clear/Push/Exit dispatch | §B rows 1-6 → own subflow files, matched first | Files and rows untouched; §D edit only changes the post-six-rows fallback |
| Reply ambiguous between 2+ known actions | Ask directly, re-loop to §D | §3 keeps this branch exactly; only the zero-match branch changes destination |
| §A entry model `{id_or_summary, content, active}` | 3 required fields, optional additive fields allowed | Neither new action adds a required field |
| §C present-state / §E log+continue | Unchanged control flow | Both new actions dispatch and log exactly like the existing six |
| `allowed-tools` | No unrestricted Read, no WebFetch, no Bash | Unchanged — both new actions are pure in-memory mutation |

The six shipped actions are unaffected. The one §D fallback change is the
ticket-mandated edit for AC2. It is safe because it only fires on a
zero-row match.

---

## 1. Design overview

Two new actions, dispatched like the existing six, plus one fallback-routing
change in §D:

```
Action Registry (ticket-loop-subflow.md §B) — two new rows:
  Set active ticket → set-active-ticket-subflow.md
  Other             → other-action-subflow.md

set-active-ticket-subflow.md:
  §A Resolve target (positional index into the last-presented numbered
     list, OR named id_or_summary match — never guess on ambiguous/zero/
     out-of-range; no reference at all → ask "which ticket?")
       │
       ▼
  §B Apply (set target.active = true; unset active on every other entry;
     content never touched; compose outcome string)

other-action-subflow.md:
  §A Establish request (triggering utterance is the candidate request; if
     too vague to act on, ask "what would you like to do?" and re-capture)
       │
       ▼
  §B Evaluate scope (lightweight, well-scoped op on data already in
     $TICKET_CONTEXT → perform it directly; else → negotiate toward an
     in-scope version with the user; still nothing fits → not supported)
       │
       ▼
  §C Compose outcome
```

**Other's out-of-scope handling.** A flat "not supported" reply leaves
the user no path forward on the first ask.

§B.2 now explains the specific constraint. It asks for a narrower,
in-scope version of the same request before falling back to "not
supported."

This never widens `allowed-tools` or fetches new data. It only checks
whether the user's need can be met with what's already in
`$TICKET_CONTEXT`.

**Positional vs. named resolution.** Clear and Push both resolve by name or
summary, or by an "active"/"all" keyword. Neither resolves by list
position, but AC1.1's own example ("ticket 2") needs exactly that.

`set-active-ticket-subflow.md` §A therefore adds a first-class positional
path. A bare integer or ordinal is matched against the most recent
`ticket-loop-subflow.md` §C list. This is checked ahead of the by-name
match:

```
precedence:  positional reference (in range)  >  named reference (id_or_
             summary match)  >  no reference at all → ask
(tie-break: an out-of-range positional reference is unresolved — tell the
 user, re-ask; never silently clamp)
```

**§D's fallback split** is the other structural change (see the Design
decision above):

```
precedence inside §D:  confident single-row match (existing)  >
  ambiguous among 2+ rows → ask directly, re-loop (existing, preserved)  >
  confident zero-row match → dispatch other-action-subflow.md (new)
```

**Alternatives considered and rejected:**
- Route every ambiguous-or-unmatched reply to Other — rejected: direct ask
  is cheaper than Other's generic prompt.
- Resolve "ticket N" against the raw array index — rejected: §C's numbered
  list already is that order.
- Let Other attempt anything, including new data or MCP calls — rejected:
  AC2.2 scopes it to data already in context.
- Decline out-of-scope requests immediately, no negotiation — rejected:
  an in-scope version is often nearby.
- Auto-select the last entry when Set-active gets no reference — rejected:
  AC1.2 allows no such carve-out.

---

## 2. New subflow specifications

### 2.1 `set-active-ticket-subflow.md`

New file. It opens with a blockquote and a "Caller contract." line, then two
lettered sections (A resolve, B apply). This matches
`clear-ticket-subflow.md`'s own shape.

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries, in and out.
- Mutated only via `active` flags, never `content` or `id_or_summary`.
- (implicit) the triggering utterance, already visible in conversation.
- (implicit) the order of the most-recently-presented §C numbered list.

**§A Resolve target:**
1. `$TICKET_CONTEXT` empty → tell the user there are no tickets to set
   active, return that outcome, no mutation.
2. Utterance holds a bare positional reference to the last-presented §C
   list, such as "ticket 2" or "the second one."
   - In range (`1..=|$TICKET_CONTEXT|`) → `$TARGET` = the entry at that
     position in §C's current order, continue to §B.
   - Out of range → tell the user, re-ask which ticket, re-run this §A.
3. Utterance names a ticket by `id_or_summary`, no positional reference:
   semantic-match, never guessing.
   - Zero matches → ask the user to clarify, then re-match the reply.
   - Multiple matches → numbered list of matches, user picks, never
     auto-selected.
   - One match → `$TARGET` = that entry, continue to §B.
4. Neither a positional nor a named reference → ask which ticket to set
   active, re-run this §A against the reply.

**§B Apply:**
1. Set `$TARGET.active = true`.
2. Unset `active` on every other entry, so at most one stays active.
3. Never modify `$TARGET.content` or any other field, per AC1.3.
4. Return the outcome string naming `$TARGET.id_or_summary` as now active.

**Failure/degradation contract:** every early-return path in §A leaves
`$TICKET_CONTEXT` unmutated. That covers empty context, out-of-range,
zero-match, and no-reference. A successful §B pass sets exactly one entry
active and unsets every other, with no partial state.

### 2.2 `other-action-subflow.md`

New file. Same opening shape: a blockquote, a "Caller contract." line, then
three lettered sections. Those are A establish request, B evaluate scope, C
compose outcome.

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries, in and out.
- Mutated only when §B edits an existing entry's `content` or
  `id_or_summary`, on explicit request.
- (implicit) the triggering utterance, matching none of the six other
  registered actions.

**§A Establish request:**
1. Treat the triggering utterance itself as the candidate request,
   `$OTHER_REQUEST`.
2. It already names a specific operation on `$TICKET_CONTEXT` data, such as
   reformatting content → skip to §B.
3. It's too vague, such as "something else" → ask what the user wants,
   capture as `$OTHER_REQUEST`.
4. Repeat step 3 until specific, or the user aborts → return "no action
   taken", no mutation.

**§B Evaluate scope:**
1. `$OTHER_REQUEST` is lightweight, well-scoped work on data already in
   `$TICKET_CONTEXT` (e.g. reformat content).
   - If it names a target entry, resolve it the same way as
     `set-active-ticket-subflow.md` §A step 3, never guessing.
   - Perform the requested edit directly, mutating only the named field on
     the resolved entry, then continue to §C.
2. Otherwise (`$OTHER_REQUEST` needs new data, an external call, or is
   out of scope for this subflow's tools):
   - Name the specific constraint: no new tool grant, no data beyond
     `$TICKET_CONTEXT`.
   - Ask for a narrower, in-scope version of the same request.
   - User offers a narrower ask that fits `$TICKET_CONTEXT` → treat it as
     the new `$OTHER_REQUEST`, re-run step 1.
   - User has none, or repeats the same out-of-scope ask → tell them it
     isn't supported yet, no mutation, continue to §C.
   - Never widens `allowed-tools` or fetches new data to satisfy the
     original ask.
   - The negotiation stays within `$TICKET_CONTEXT` at all times.

**§C Compose outcome:**
- Handled by §B.1 → an outcome naming what changed.
- Not supported by §B.2 → an outcome naming why, briefly.
- Aborted in §A → the "no action taken" outcome.
- Return control to `ticket-loop-subflow.md` §E.

**Failure/degradation contract:** every path — abort, unsupported, handled —
returns a composed outcome string. Unsupported requests are always
reported, never silently dropped or turned into an error.

---

## 3. Integration / wiring

**`ticket-loop-subflow.md` §B (Action Registry)** gains two new rows, after
"Push ticket(s)" and before "Exit":

| Action | Selectable via (examples) | Dispatch subflow |
|---|---|---|
| Set active ticket | "set ticket 2 as active", "make CSS-2664 active" | `set-active-ticket-subflow.md` |
| Other | (fallback — see §D) | `other-action-subflow.md` |

**`ticket-loop-subflow.md` §D (Dispatch)** is rewritten per the Design
decision above. The ambiguous-among-known-rows branch keeps its existing
"ask directly, re-loop" behavior unchanged.

The old unqualified "unmatched reply: ask a clarifying question" clause is
replaced. It becomes: a confident zero-row match invokes
`other-action-subflow.md` instead.

The exact wording is drafted directly into the file during execution. It
preserves §D's existing "no re-running all of §C" clause.

**`ticket-loop-subflow.md` §C (Present)** needs no edit. Step 4's wording is
already generic over row count, so the two new rows appear in the menu on
their own. This satisfies AC4 without any text change, confirmed in §0
above.

**Sections A and E** of `ticket-loop-subflow.md` stay untouched. That
file's own contract says later steps extend the action set only via §B.
This step's §D edit is scoped narrowly to the fallback branch alone.

**`skills/references/references-toc.md`** gains two new rows for the two
new subflow files. Both sit after the `push-ticket-subflow.md` row and
before `exit-ticket-loop-subflow.md`. This mirrors §B's own new row order.

**`skills/hb-ticket-discuss.md`** is deliberately not edited this time.
Unlike steps 2-5, this step's ticket names no change here.

"Other" is an internal escape hatch, not a primary action worth the
top-line wording. `allowed-tools` needs no change either, since neither new
action calls any tool.

No configuration, build wiring, or dependency-manifest changes apply — this
repo's skill layer has none of those.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/set-active-ticket-subflow.md` | **new** — full Set-active action subflow (§2.1) |
| `skills/references/other-action-subflow.md` | **new** — full Other action subflow (§2.2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — two new Action Registry rows (§B); §D fallback rewritten (§3); Sections A, C, E untouched |
| `skills/references/references-toc.md` | **edit** — two new rows |
| `.hb/facts.md` | **edit (conditional)** — only if this step's own facts-write-subflow pass finds a candidate fact that passes the gate |

No dependency manifest or lockfile exists in this repo's skill layer.
`skills/hb-ticket-discuss.md` is intentionally absent from this table; see
§3 for why.

---

## 5. Tests

No automated harness exists — this is a markdown-procedure repo, per every
prior execution summary here. Coverage is static/structural checks plus
dry-run trace, matching that convention.

**Structural (grep/read-checkable):**
- Action Registry table in `ticket-loop-subflow.md` has 8 data rows (6
  existing plus 2 new), plus header and separator.
- Both new rows are present, positioned between Push and Exit.
- `set-active-ticket-subflow.md` has exactly 2 `####` sections (A-B).
- `other-action-subflow.md` has exactly 3 `####` sections (A-C).
- `git diff --stat` for the six untouched subflows plus
  `hb-ticket-discuss.md` shows no output.
- `git diff` for `ticket-loop-subflow.md` touches only §B (table) and §D
  (dispatch prose); §A, §C, §E stay byte-unchanged.
- The two new TOC rows sit immediately after the `push-ticket-subflow.md`
  row.
- **Reuse guard**: neither new file references `Bash` or `hb-sdk`, matching
  sibling subflows.
- **No-file-write guard**: neither new file references `Write`, `mkdir`,
  or `TARGET_PATH`.

**Dry-run traces (exercised when `/hb-ticket-discuss` is run):**
- Positional set-active, in range: 3 entries, "set ticket 2" → the 2nd
  entry becomes active, prior one unset.
- Positional set-active, out of range: 2 entries, "set ticket 5 as active"
  → told out of range, re-asked.
- Named set-active, unambiguous: "make CSS-2664 active" matches one entry
  → resolved and applied.
- Named set-active, ambiguous: two entries share a substring → numbered
  list scoped to it, user picks one.
- Named set-active, zero match: reference names a ticket not present →
  asked to clarify, never guessed.
- Bare set-active, no reference: "make it active" → asked which ticket.
- Set-active on empty context: told, no mutation.
- Set-active never touches content: `$TARGET.content` is byte-identical,
  only `active` flags change.
- Other, in-context request: "reformat PROJ-123" → entry resolved, content
  reformatted, change reported.
- Other, out-of-scope request, no narrower ask offered: needs an external
  call or new data.
  - Constraint explained, narrower ask requested, user declines/repeats
    → told not supported, `$TICKET_CONTEXT` unchanged.
- Other, out-of-scope request, negotiated down: initial ask needs an
  external call.
  - User's follow-up fits `$TICKET_CONTEXT` → performed directly, change
    reported.
- Other, vague trigger: utterance too vague to act on → asked what the
  user would like to do, reply re-evaluated.
- §D ambiguous-among-known-rows still asks directly: could mean Clear or
  Push → direct ask, re-loop, not Other.
- §D confident zero-match routes to Other: matches none of the eight rows
  → dispatched to `other-action-subflow.md`.
- Load/Describe/Breakdown/Clear/Push/Exit non-regression: steps 1-5's
  dry-run traces stay unaffected.

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A for this markdown repo;
   structural checks below are authoritative.
2. **Scope check** — `git status --short` shows exactly the 4 files in §4,
   plus `.hb/facts.md` if changed.
3. **Action Registry rows** — §B has 8 rows: Load, Describe, Breakdown,
   Clear, Push, Set active ticket, Other, Exit.
4. **§D rewrite correctness** — both branches exist: ambiguous-among-known
   unchanged, zero-match dispatches Other.
5. **New subflow shape** — both files open with a blockquote and "Caller
   contract.", end with a failure contract line.
   - `set-active-ticket-subflow.md` has 2 `####` sections,
     `other-action-subflow.md` has 3.
6. **`hb-ticket-discuss.md` unchanged** — `git diff` shows no hunks there
   at all.
7. **Per-AC checks** — read both new files end-to-end and confirm AC1.2,
   AC1.3, and AC2.2 each hold as specified.
8. **Non-regression** — `git diff --stat` for the seven files in §5's
   first structural check shows no changes.
9. **TOC rows** — `references-toc.md` has 2 new rows, positioned between
   Push and Exit's subflow rows.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Set active ticket action added, dispatching to `set-active-ticket-subflow.md` | §3 (row); §2.1 (file) | |
| 1.1 — selectable via positional and by-name phrasings | §2.1 §A steps 2-3 | |
| 1.2 — semantic match; ambiguous/zero → ask, never auto-select | §2.1 §A steps 2-4 | Covers positional out-of-range too |
| 1.3 — mutates only `active`, never `content` | §2.1 §B steps 1-3 | |
| 2 — Other action added, dispatching to `other-action-subflow.md` | §3 (row + §D rewrite); §2.2 (file) | See Design decision |
| 2.1 — prompts the user for what they'd like to do | §2.2 §A | |
| 2.2 — handles lightweight in-context requests; otherwise reports unsupported | §2.2 §B | Negotiates toward an in-scope version before falling back to unsupported |
| 3 — both subflows follow existing shape; no edits to the six existing action files | §2.1, §2.2 shape; §0.2 / §5 non-regression | |
| 4 — `ticket-loop-subflow.md` §C lists both new actions | §3 (no-edit rationale) | Verified in §6 check 3 |

---

## 8. Out of scope (per ticket)

- Editing any of the six existing action subflow files — excluded by AC3.
- Updating `hb-ticket-discuss.md`'s wording to list the two new actions —
  not required by this step's ACs; see §3.
- Any external or tool-backed operation inside `other-action-subflow.md` —
  AC2.2 scopes it to in-context data.
- Auto-selecting a target for Set-active with no reference — AC1.2 allows
  no single-entry carve-out.
