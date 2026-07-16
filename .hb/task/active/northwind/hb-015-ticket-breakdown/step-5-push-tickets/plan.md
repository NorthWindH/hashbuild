# Step 5 Plan — Push ticket(s) action

## Motivation

- `hb-ticket-discuss`'s loop (steps 1-4) offers Load, Describe, Breakdown, Clear.
- None of them can send a ticket outside the conversation.
- Motivating case: user has ticket(s) in context and says "push this to Jira" or "push all tickets."
- No Action Registry row recognizes that today.
- The only Jira-push logic that ever existed lived in this skill's single-shot Steps 3-8.
- The step-1 loop restructuring (`c74ec90`) deleted them outright.
- That commit's message says the content was "removed rather than left dormant."
- It also says the content is "recoverable via git history for step-5."
- This step adds a fifth action, **Push ticket(s)**.
- It sends any subset of in-context tickets — one, several named, all, or a default single ticket — to Jira.
- It processes them one at a time, reusing the pre-restructuring push procedure unchanged in substance.

**Scope — additive only:**
- A new subflow file, plus a targeted `allowed-tools` fix (see Design decision below).
- No new integration is introduced.
- Per AC5, a pushed ticket is never removed from context.

**Observable effect once shipped:**
- Saying "push the active ticket," "push PROJ-123 and PROJ-124," or "push all tickets" triggers it.
- It walks the resolved ticket(s) through the existing Jira create/update flow.
- That flow includes an optional Epic→Idea link step.
- It reports each outcome and leaves every pushed ticket in context.

## Source & inputs

- Source ticket: `./ticket.md`.
- Builds on the shipped Load/Describe/Breakdown/Clear/Exit actions and loop skeleton (all read in full):
  - `skills/hb-ticket-discuss.md`
  - `skills/references/ticket-loop-subflow.md`
  - `skills/references/load-ticket-subflow.md`
  - `skills/references/describe-ticket-subflow.md`
  - `skills/references/breakdown-ticket-subflow.md`
  - `skills/references/clear-ticket-subflow.md`
  - `skills/references/exit-ticket-loop-subflow.md`
- Current as of commit `cb86e9b` (last commit touching any of these files; repo HEAD matches).
- Also targets the deleted pre-restructuring push logic.
- That logic was recovered from `git show 7bd2c42:skills/hb-ticket-discuss.md` (old Steps 3-8).
- `7bd2c42` is the commit right before `c74ec90` deleted them.

> **Design decision — fix the `allowed-tools` gap now, since AC7 requires it, even though it predates this task.**
> - The `allowed-tools` block has never listed `createJiraIssue`, `editJiraIssue`, or `createIssueLink`.
> - Verified across every commit touching `hb-ticket-discuss.md`'s frontmatter (`738235c`–`cb86e9b`).
> - True even in `7bd2c42` (pre-restructuring), whose Steps 5-6 already called all three.
> - This is a pre-existing oversight from `hb-012`, not something steps 1-4 introduced.
> - AC7 requires `allowed-tools` to list "exactly the Jira MCP tools this procedure calls."
> - The procedure this step reintroduces calls those three tools.
> - They must be added now to satisfy that wording.
> - AC7's "unchanged from today" refers to the *set of external systems* (still just Jira).
> - It does not mean leaving the frontmatter untouched line-for-line.
> - §3 below adds all three; see §7 (AC7 traceability).

---

## 0. Current-state facts (verified during planning)

- **`ticket-loop-subflow.md`** (74 lines):
  - §A defines the ticket entry as `{ id_or_summary, content, active }`.
  - It is extensible with optional fields per its own note.
  - §B (Action Registry) has 5 rows today: Load, Describe, Breakdown, Clear, Exit.
  - That order matches the ticket's AC numbering.
  - Push (AC8) belongs between Clear (AC7) and Exit (AC9).
  - §D (Dispatch) passes `$TICKET_CONTEXT` by reference.
  - No other formal parameter exists.
- **`clear-ticket-subflow.md`** (68 lines):
  - Set this step's target-resolution precedent.
  - Precedence: "all" > named reference(s), matched independently > "the active ticket" alone > ask-user.
  - This step's §A adds one branch Clear doesn't need: default-to-single-or-active (AC1.1).
  - Push is commonly invoked bare, right after Describe/Load, unlike Clear.
- **`breakdown-ticket-subflow.md`** (74 lines) and **`load-ticket-subflow.md`** (100 lines):
  - Confirm the "never guess" posture for ambiguous/zero-match references.
  - §A below reuses that posture verbatim for Push's named-reference case.
- **`describe-ticket-subflow.md`** (21 lines) and **`exit-ticket-loop-subflow.md`** (16 lines):
  - Both read only `{id_or_summary, content, active}`.
  - This step's new optional `pushResult` field needs no change here.
- **`hb-ticket-discuss.md`** (56 lines):
  - `allowed-tools` has 6 `/tmp` grants and 5 Jira tools today:
    - `getAccessibleAtlassianResources`
    - `getVisibleJiraProjects`
    - `getJiraProjectIssueTypesMetadata`
    - `searchJiraIssuesUsingJql`
    - `getJiraIssue`
  - That 5-tool list has never changed (`git log -p --follow`), even pre-restructuring.
  - `description:` and body prose both list actions "(e.g. describe, load, breakdown, clear, exit)."
  - Both were updated at each prior action's ship, per steps 2-4's precedent.
  - This step adds "push" to both.
- **`references-toc.md`** (23 rows): rows mirror the Action Registry's order; this step adds one row.
- **Recovered pre-restructuring push logic** (`7bd2c42`, old Steps 3-8):
  - Step 3: detect Jira MCP by capability + collect NL description.
  - Step 4 (A-E): parse intent/fields, resolve `cloudId`, resolve remaining fields, confirm.
  - Step 4 loops on accept/refine/supply-exact/abort.
  - Step 5: push via `createJiraIssue`/`editJiraIssue` using `$WRITTEN_TICKET` as `description`.
  - Step 5 stores `issueKey` on success; falls through to emit on failure.
  - Step 6: Epic-only Idea-link offer via `createIssueLink`.
  - Step 7: emit-ticket fallback, skipped when pushed.
  - Step 8: final prompt.
  - AC2 requires this "unchanged in substance" per targeted ticket.
  - §2 §B reproduces it 1:1, substituting `$TARGET.content` (in-memory) for `$WRITTEN_TICKET` (a file path).
- **This step's `ticket.md`** (AC1-7):
  - Multi-target looping is sequential, never concurrent (AC3).
  - A pushed ticket is never implicitly cleared from context (AC5).
- **No automated test harness** — markdown-procedure repo.
  - Verification is structural grep + dry-run trace, matching every prior step's convention.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "push the active ticket" (1 ticket in context) | Not recognized | §A defaults to it (AC1.1) → §B runs the push procedure |
| "push" (bare, >1 ticket, one active) | Not recognized | §A defaults to the active entry (AC1.1) |
| "push" (bare, >1 ticket, none active) | Not recognized | §A asks which ticket(s) |
| "push PROJ-123 and PROJ-124" (both present) | Not recognized | §A resolves both → §C loops sequentially |
| "push all tickets" (3 in context) | Not recognized | §A resolves all 3 → §C processes one at a time, with checkpoints |
| No Jira MCP connected | N/A | §B.1 tells the user, emits for copy-paste (unchanged degradation contract) |
| Pushed issue type is Epic | N/A | §B.4 offers the Idea-link step, as before |
| User says "stop" mid-batch | N/A | §C breaks; untouched targets stay in context, reported as not-attempted |
| Ticket's context membership after a push | N/A | Unchanged — Push never adds/removes/reactivates (AC5) |
| Load, Describe, Breakdown, Clear, Exit | Unchanged | Unchanged |
| `allowed-tools` | 5 Jira tools | 8 Jira tools (+3) — see Design decision |

- Kind of change: **additive only**.
- New Action Registry row, subflow file, TOC row, 3 tool grants (fixing a pre-existing gap), and a prose tweak.
- No existing behavior changes.

### 0.2 Non-regression proof

| Case | Why it can't change |
|---|---|
| Load / Describe / Breakdown / Clear / Exit dispatch | Their files are untouched; §B gains one row only |
| §A ticket-entry model | Push only reads `content`/`id_or_summary`, adds an optional field |
| §C/§D/§E control flow | Push dispatches like the other four actions; no shared-file logic changes |
| Membership / active-flag mutation | AC5 forbids implicit clearing; §B/§C never call `remove` or reassign `active` |
| Existing 5 Jira read-tools | Same tools, same calls, reused by Push's §B.2 exactly as Load already does |

Only new risk is the new subflow's own correctness — covered in §5/§6.

---

## 1. Design overview

- One new action, dispatched like Load/Describe/Breakdown/Clear.
- It resolves a target *set*, generalizing Clear's §A with a new default branch.
- It then walks each target sequentially through the recovered push procedure.
- It tracks a per-ticket outcome throughout.

```
Action Registry (ticket-loop-subflow.md §B) — new row:
  Push ticket(s) → push-ticket-subflow.md

push-ticket-subflow.md:
  §A Resolve target set ("all" → every entry; named reference(s) → NL match
     per reference, numbered-list on ambiguity, ask on zero-match; bare
     "push" with no name/"all" → default to the sole entry, or the active
     entry if >1 exist, else ask; nothing recognized → ask and re-run §A)
       │
       ▼
  §C Multi-target loop (sequential; announce the set when |targets| > 1;
     for each target: run §B, then — if more targets remain — ask to
     continue or stop; stop leaves remaining targets untouched)
       │              ▲
       ▼              │ (per target)
  §B Per-ticket push procedure (recovered pre-restructuring Steps 3-7,
     unchanged in substance, operating on $TARGET.content):
     B.1 detect Jira MCP + collect NL description (or unavailable/declined)
     B.2 NL resolution & confirmation loop (lettered A-E, verbatim)
     B.3 push (create/update) — success sets $JIRA=pushed + issueKey/browseUrl
     B.4 Epic-only Idea-link offer (guarded)
     B.5 emit-ticket fallback (skipped when pushed)
     B.6 compose this ticket's result, attach as $TARGET.pushResult
       │
       ▼
  §D Compose return outcome (per-ticket summary + any not-attempted targets)
```

**Target-set resolution** generalizes Clear's, plus one new default branch:

```
precedence:  "all" request  >  named reference(s) (one or more)  >
             bare "push" + exactly one entry in context  >
             bare "push" + an unambiguous active entry  >  ask-user
(tie-break inside "named references": identical to clear-ticket-subflow.md
 §A step 4 — matched independently per reference, never guess)
```

- Clear has no bare-word default, since deletion shouldn't guess.
- Push's AC1.1 wants one for the common bare-"push" case.

**Key design calls:**
- **No up-front bulk confirm gate.**
  - Each ticket's own §B.2 "Does this look right?" loop is the safety gate.
  - A second batch-level confirm would duplicate it without any AC asking for it.
- **Sequential loop with an explicit continue/stop checkpoint** (AC3).
  - Placed *between* completed tickets, not watched for mid-ticket.
  - A mid-flight "stop" during §B.2's own loop would be ambiguous.
  - An explicit post-ticket question removes that ambiguity.
- **`pushResult` is additive, never structural.**
  - Push only ever attaches an optional bookkeeping field.
  - It never adds, removes, or reactivates a `$TICKET_CONTEXT` entry (AC5).

**Alternatives rejected:**
- *Cache `cloudId` across targets* — AC2 requires the procedure to run "unchanged in substance" per ticket.
  - Caching is a behavior change, and the query is cheap to repeat.
- *Bulk "confirm pushing N tickets?" gate mirroring Clear* — no AC asks for a second gate.
  - The per-ticket AC2 confirmation already is the gate.
- *Free-floating mid-ticket "stop" instead of a between-ticket checkpoint* — ambiguous scope.
  - The explicit checkpoint matches AC3's wording precisely.
- *Leave `allowed-tools` at 5 tools, reading "unchanged from today" literally* — see Design decision.
  - The procedure this step ships calls 3 ungranted tools, so AC7 requires adding them.

---

## 2. `push-ticket-subflow.md` — specification

- New file, four lettered sections: A resolve targets, B per-ticket push, C multi-target loop, D compose outcome.
- Matches the sibling subflows' blockquote + "Caller contract." + lettered-sections shape.

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out).
  - Mutated only via an additive, optional `pushResult` field.
  - Never added-to, removed-from, or re-activated.
- The user's triggering utterance — already in conversation, not a formal parameter.

**§A Resolve target set:**
1. Context empty → tell the user, return `"Push: no tickets in context."`
   - No calls, no mutation.
2. "All"/"everything" request → `$TARGETS` = every entry, in order.
   - Continue to §C.
3. Named ticket(s): identical algorithm to Clear's §A step 4.
   - Split into distinct references, match each against every entry's `id_or_summary`.
   - Zero matches → ask/re-match; multiple → numbered list, never auto-select; one → include.
   - `$TARGETS` = deduplicated union across all references.
   - Continue to §C.
4. Bare "push"/"push it"/"push this ticket" (no name, no "all"):
   1. Exactly one entry in context → `$TARGETS` = `[that entry]` (AC1.1).
   2. Else exactly one entry has `active: true` → `$TARGETS` = `[that entry]` (AC1.1).
   3. Else → ask "Which ticket(s) would you like to push?" and re-run §A against the reply.

**§B Per-ticket push procedure:**
- Invoked once per `$TARGET` by §C.
- Returns `{ status: "pushed" | "copy-paste", issueKey?, browseUrl?, ideaLinked? }`.
- Never touches `$TICKET_CONTEXT` membership or `active`.

1. **Detect Jira MCP & collect NL description** (recovered `7bd2c42` Step 3, verbatim, per-ticket):
   - Not found → `$JIRA = unavailable`; tell the user; skip to step 5.
   - Found → ask the user to describe the target for *this* ticket.
   - Name the ticket by `id_or_summary` so a multi-target run stays distinguishable.
   - Decline → `$JIRA = declined`, skip to step 5.
   - Otherwise → `$NL_DESC`, continue.
2. **NL resolution & confirmation loop** (recovered Step 4, verbatim, A-E):
   - Parse `$NL_DESC`, resolve `cloudId` via `getAccessibleAtlassianResources`.
   - Resolve remaining fields per path: create uses `getVisibleJiraProjects`/`getJiraProjectIssueTypesMetadata`.
   - Update uses `getJiraIssue`/`searchJiraIssuesUsingJql`, also capturing `issueTypeName`.
   - Present the resolved set, ask "Does this look right?"
   - Loop on accept/refine/supply-exact/abort.
   - Query-tool errors surface verbatim; never dead-end.
3. **Push to Jira** (recovered Step 5, verbatim, `$TARGET.content` in place of `$WRITTEN_TICKET`):
   - Create path calls `createJiraIssue`; update path calls `editJiraIssue` with `fields.description`.
   - Success → `$JIRA = pushed`, report key + URL, store `issueKey`.
   - Failure → surface error, fall through to step 5.
4. **Offer Jira Idea link, Epic only** (recovered Step 6, verbatim):
   - Guard on `$JIRA = pushed` and `issueTypeName === "Epic"`.
   - On yes, resolve the Idea key and call `createIssueLink`.
   - `inwardIssue` is the Epic; `outwardIssue` is the Idea; direction never reversed.
   - Failure doesn't affect the already-pushed issue.
5. **Emit ticket fallback** (recovered Step 7, verbatim):
   - Reached on `unavailable`/`declined`/failure.
   - Skipped when pushed.
   - Prints `$TARGET.content` for copy-paste; no `.hb/` write.
6. **Compose result:**
   - Pushed → `{status, issueKey, browseUrl, ideaLinked}`; else → `{status: "copy-paste"}`.
   - Attach as `$TARGET.pushResult` (additive, optional).
   - Return to §C.

**§C Multi-target loop:**
1. `|$TARGETS| > 1` → announce the set before starting.
   - Else skip the announcement.
2. For each `$TARGET`, in order, never concurrent (AC3):
   1. Run §B; append `{label, result}` to `$PUSH_RESULTS`.
   2. Not the last target and `|$TARGETS| > 1` → ask "Continue to the next ticket?"
      - Stop/decline breaks the loop.
      - Untouched targets stay in `$TICKET_CONTEXT`.
3. Continue to §D once the loop ends (exhausted or stopped early).

**§D Compose return outcome:**
1. Per result: pushed → `"<label>: pushed as <issueKey> (<browseUrl>)"` (+ Idea link if set).
   - Copy-paste → `"<label>: emitted for copy-paste (no Jira push)"`.
2. On early stop, also list not-yet-attempted targets.
3. Present the summary.
4. Return `"Push: N of M ticket(s) processed (<breakdown>)."` for §E to log.

**Failure/degradation contract:**
- §A's empty-context and default-ambiguous cases return without invoking §B.
- No mutation, no calls happen in those cases.
- Every §B branch mirrors the recovered flow's contract exactly.
- Branches: no MCP, decline, query error, push error, idea-link error.
- Every branch never dead-ends; it always falls through to step 5.
- §C's stop path leaves `$TICKET_CONTEXT` exactly as it was.
- A target only gains `pushResult` once its own §B run fully completes.

---

## 3. Integration / wiring

- **`ticket-loop-subflow.md` §B** — one new row, between Clear and Exit (matching AC7/AC8/AC9 order):

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Push ticket(s) | "push this", "push PROJ-123 and PROJ-124", "push all tickets" | `push-ticket-subflow.md` |

  Sections A, C, D, E are not touched, per that file's own contract.
- **`hb-ticket-discuss.md`**:
  - `allowed-tools` gains 3 lines: `createJiraIssue`, `editJiraIssue`, `createIssueLink`.
  - See Design decision above.
  - The 6 `/tmp` grants are untouched — Push writes no file.
  - `description:` and body prose: "(e.g. describe, load, breakdown, clear, exit)" → "(..., push, exit)."
  - `Steps` section untouched — Push is reachable purely through the Action Registry, like the others.
- **`references-toc.md`** — one new row for `push-ticket-subflow.md`, between Clear's and Exit's rows.
- No configuration, build wiring, or dependency-manifest changes — this repo's skill layer has none.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/push-ticket-subflow.md` | **new** — full Push action subflow (§A-D per §2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — one new Action Registry row; A/C/D/E untouched |
| `skills/hb-ticket-discuss.md` | **edit** — `allowed-tools` +3 Jira tools; description/prose +"push" |
| `skills/references/references-toc.md` | **edit** — one new row for `push-ticket-subflow.md` |
| `.hb/facts.md` | **edit** — prune the now-redundant "re-author Jira push logic deleted" fact |

No dependency manifest or lockfile in this repo's skill layer.

---

## 5. Tests

- No automated harness (markdown-procedure repo).
- Coverage is static/structural + dry-run trace, matching the established convention from steps 0-4.

**Structural (grep/read-checkable):**
- `grep -n "Push ticket(s)" ticket-loop-subflow.md` → exactly one row, between Clear and Exit.
- `grep -c "^####" push-ticket-subflow.md` → 4 (§A-D).
- `git diff --stat` on the five other subflow files + `breakdown-subflow.md` → no output (untouched).
- `grep -n "mcp__claude_ai_Atlassian_Rovo__" hb-ticket-discuss.md | wc -l` → 8 (5 existing + 3 new).
- `grep -n "clear, push, exit" hb-ticket-discuss.md` → 2 matches (frontmatter + body prose).
- `grep -n "push-ticket-subflow" references-toc.md` → exactly one row, correctly positioned.
- **No-file-write guard**: `grep -n "Write(\|Edit(\|^Bash" push-ticket-subflow.md` → no matches.
- **Reuse-fidelity**: diff `7bd2c42:hb-ticket-discuss.md` by eye against §2 §B.
  - Every field/tool name matches.
  - Only `$WRITTEN_TICKET` → `$TARGET.content` and per-ticket labeling differ.

**Dry-run traces (exercised via `/hb-ticket-discuss`):**
- Single-ticket default; active-ticket default; ambiguous bare "push" (asks).
- Multiple named targets; "push all" with 3 tickets.
- Stop mid-batch (partial processed, rest untouched).
- No Jira MCP connected → copy-paste fallback, ticket stays in context.
- Push declined mid-resolution; push failure (tool error) → both fall through to emit, never dead-end.
- Epic push → Idea link accepted; Epic push → Idea link declined/failed; non-Epic push (no Idea prompt).
- Ticket remains in context after push (only `pushResult` added).
- Load/Describe/Breakdown/Clear/Exit non-regression, re-verified against steps 1-4's own traces.

---

## 6. Verification (after implementation)

1. No automated build/test gate — structural checks below are authoritative.
2. `git status --short` shows exactly the 4 files in §4 (plus this step's own `.hb/task/...` artifacts).
3. `ticket-loop-subflow.md` §B has exactly 6 rows in order; A/C/D/E byte-unchanged.
4. `push-ticket-subflow.md` opens with blockquote + "Caller contract.", has 4 `####` sections.
   - It ends with a "Failure/degradation contract" line.
5. `git diff -- hb-ticket-discuss.md` shows one hunk adding 3 Jira tool lines (no removals).
   - Plus two wording hunks.
6. Read `push-ticket-subflow.md` end-to-end; confirm every AC is textually satisfied (§7 below).
7. `git diff --stat` on the five untouched sibling subflows + `breakdown-subflow.md` shows no changes.
8. `references-toc.md` has exactly one new row, correctly positioned between Clear and Exit.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Push action added to menu, NL-selectable | §3 (Action Registry row) | |
| 1.1 — single/active-default (bare "push") | §2 §A steps 3-4 | |
| 1.2 — several named tickets in one request | §2 §A step 3 | |
| 1.3 — all tickets in context | §2 §A step 2 | |
| 2.1 — Jira MCP detected by capability; graceful fallback | §2 §B step 1 | |
| 2.2 — NL description → resolution → confirmation, unchanged | §2 §B step 2 | Recovered Step 4 verbatim |
| 2.3 — push; report key/URL; fall through on failure | §2 §B steps 3, 5 | |
| 2.4 — Epic → Idea-link offer, exactly as today | §2 §B step 4 | Recovered Step 6 verbatim |
| 3 — sequential, not concurrent; stops early on request | §2 §C | |
| 4 — per-ticket outcome tracked and summarized | §2 §B step 6, §D | |
| 5 — ticket stays in context after push | §1 (design note); §2 §B step 6 | Clearing is Clear's job |
| 6 — logic in its own subflow file(s); TOC updated | §2 (new file); §3 (TOC row) | |
| 7 — `allowed-tools` lists exactly the tools this procedure calls | §3 (3 new tool lines) | See Design decision |

---

## 8. Out of scope (per ticket)

- New MCP/source integrations beyond the Jira push flow that already existed pre-restructuring.
- Any change to Idea-linking direction/semantics — carried over verbatim from the recovered Step 6.
- Concurrent/parallel pushing of multiple tickets — sequential only (§2 §C).
