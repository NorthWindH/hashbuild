# Step 5 Plan — Push ticket(s) action

`hb-ticket-discuss`'s loop (shipped in steps 1-4) offers Load, Describe,
Breakdown, and Clear — none of them can send a ticket anywhere outside the
conversation. The **motivating case**: a user has drafted or loaded one or
more tickets into context and says "push this to Jira" (or "push PROJ-123 and
PROJ-124", or "push all tickets") — today no Action Registry row recognizes
that; the only Jira-push logic that ever existed lived in this skill's
single-shot Steps 3-8 before the step-1 loop restructuring deleted them
outright (`c74ec90`'s commit message: "today's Jira push/NL-resolution/Idea-
link content was removed rather than left dormant... recoverable via git
history for step-5"). This step adds the fifth action, **Push ticket(s)**,
covering the **general class** of sending any subset of tickets currently
held in context (one, several named, all, or a defaulted single ticket) to
Jira, one at a time, reusing the pre-restructuring push procedure unchanged
in substance. Scope boundary: **additive only** — a new subflow file plus a
targeted `allowed-tools` fix (see Design decision below); it introduces no
new integration, and per AC5 a pushed ticket is never removed from context.
Externally observable effect once this lands: saying "push the active
ticket", "push PROJ-123 and PROJ-124", or "push all tickets" at any loop
iteration walks the resolved ticket(s) one at a time through the existing
Jira create/update (+ optional Epic→Idea link) flow, reports each outcome,
and leaves every pushed ticket in context afterward.

Source ticket: `./ticket.md`. Builds on the **shipped** Load/Describe/
Breakdown/Clear/Exit actions and loop skeleton (`skills/hb-ticket-discuss.md`,
`skills/references/ticket-loop-subflow.md`,
`skills/references/load-ticket-subflow.md`,
`skills/references/describe-ticket-subflow.md`,
`skills/references/breakdown-ticket-subflow.md`,
`skills/references/clear-ticket-subflow.md`,
`skills/references/exit-ticket-loop-subflow.md`) — all read in full during
planning, current as of commit `cb86e9b` (the last commit to touch any of
these files; repo HEAD is also `cb86e9b`). This plan targets that code as it
exists **now**, plus the deleted pre-restructuring push logic recovered from
`git show 7bd2c42:skills/hb-ticket-discuss.md` (old Steps 3-8, the last
commit before `c74ec90`'s restructuring deleted them).

> **Design decision — fix the `allowed-tools` gap now, since AC7 requires it,
> even though it predates this task.** Verified by reading every commit that
> ever touched `hb-ticket-discuss.md`'s frontmatter (`738235c` through
> `cb86e9b`): the `allowed-tools` block has **never** listed
> `createJiraIssue`, `editJiraIssue`, or `createIssueLink`, not even in the
> pre-restructuring version (`7bd2c42`) whose Steps 5-6 called all three. That
> gap is a pre-existing oversight from `hb-012`, not something step-1 through
> step-4 introduced. AC7 for *this* step reads "the `allowed-tools`
> frontmatter... still lists exactly the Jira MCP tools this procedure calls
> (unchanged from today, since no new integrations are introduced)" — the
> procedure this step reintroduces calls those three tools, so satisfying "lists
> exactly the tools this procedure calls" requires adding them now; "unchanged
> from today" refers to the *set of external systems* involved (still just
> Jira via the same MCP, no new integration), not to leaving the frontmatter
> line-for-line untouched. This plan's §3 adds all three. See §7 (AC7).

---

## 0. Current-state facts (verified during planning)

- **`skills/references/ticket-loop-subflow.md`** (74 lines, read in full): §A
  (lines 12-26) defines the ticket entry as `{ id_or_summary, content, active
  }` with an explicit extensibility note that later steps may attach
  *additional* optional fields without revisiting this file. §B (Action
  Registry, lines 28-40) has exactly 5 rows today: Load, Describe, Breakdown,
  Clear, Exit — in that order, matching the task ticket's AC numbering
  (Load=AC4, Describe=AC5, Breakdown=AC6, Clear=AC7, **Push=AC8**, Exit=AC9 —
  Push belongs between Clear and Exit). §D (Dispatch, lines 54-61): "invoke
  the matched action's dispatch subflow, passing `$TICKET_CONTEXT` by
  reference (the callee mutates it in place)" — no other formal parameter;
  the triggering utterance is already visible in conversation.
- **`skills/references/clear-ticket-subflow.md`** (68 lines, read in full):
  established the target-*set* resolution precedent this step reuses
  directly — §A's algorithm (whole-context "all" request > named
  reference(s), split and matched independently, zero/multiple-match handling
  identical to `breakdown-ticket-subflow.md` > "the active ticket" alone >
  ask-user). This step's own §A follows the identical posture, with one
  addition Clear doesn't need: a *default-to-single-or-active* branch (AC1.1),
  since Push (unlike Clear) is commonly invoked right after Describe/Load with
  a bare "push" and no explicit target name.
- **`skills/references/breakdown-ticket-subflow.md`** (74 lines) and
  **`skills/references/load-ticket-subflow.md`** (100 lines): confirm the
  "never guess" posture for ambiguous/zero-match named references (numbered
  list / re-prompt) that §A below reuses verbatim for Push's named-reference
  case.
- **`skills/references/describe-ticket-subflow.md`** (21 lines) and
  **`skills/references/exit-ticket-loop-subflow.md`** (16 lines): both
  confirm `$TICKET_CONTEXT`'s `{id_or_summary, content, active}` fields are
  the only ones they read — this step adds an optional `pushResult` field per
  the extensibility note; neither file needs to change since neither iterates
  over unknown fields.
- **`skills/hb-ticket-discuss.md`** (56 lines, read in full): `allowed-tools`
  (frontmatter, lines 12-24) — 6 `/tmp`-scoped Read/Write/Edit grants + **5**
  Atlassian Rovo tools (`getAccessibleAtlassianResources`,
  `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`,
  `searchJiraIssuesUsingJql`, `getJiraIssue`) — confirmed via
  `git log -p --follow` that this exact 5-tool Jira list has never changed
  across any commit, including `7bd2c42` (pre-restructuring, when Steps 5-6
  already called `createJiraIssue`/`editJiraIssue`/`createIssueLink` without
  those three being granted). `description:` (frontmatter) and the body prose
  at line 28 both read "...a menu of next actions (e.g. describe, load,
  breakdown, clear, exit) selectable via natural language" — the two-location
  pattern updated each time a prior action shipped (steps 2-4); this step adds
  "push" to both, following that exact precedent.
- **`skills/references/references-toc.md`** (23 rows, read in full): rows for
  `ticket-loop-subflow.md` through `exit-ticket-loop-subflow.md` appear
  consecutively, mirroring the Action Registry's own row order.
- **Recovered pre-restructuring push logic** (`git show
  7bd2c42:skills/hb-ticket-discuss.md`, old Steps 3-8, read in full): Step 3
  (detect Jira MCP by capability + collect NL description), Step 4 (lettered
  A-E NL resolution & confirmation loop: parse intent/fields, resolve
  `cloudId` via `getAccessibleAtlassianResources`, resolve remaining
  create/update fields, present resolved set, loop on
  accept/refine/supply-exact/abort), Step 5 (push via
  `createJiraIssue`/`editJiraIssue`, using `$WRITTEN_TICKET`'s full content as
  `description`; on success store `issueKey` alias; on failure fall through to
  emit), Step 6 (Epic-only Idea-link offer via `createIssueLink`, guarded on
  `issueTypeName === "Epic"`), Step 7 (emit ticket fallback, skipped when
  pushed), Step 8 (final prompt). AC2 requires this procedure to run "unchanged
  in substance" per targeted ticket — this plan's §2 §B reproduces it 1:1,
  substituting `$TARGET.content` (an in-memory entry field) for
  `$WRITTEN_TICKET` (a `/tmp` file path), since Push operates on tickets
  already held in `$TICKET_CONTEXT`, never a file.
- **This step's own `ticket.md`** (AC1-7, read in full): confirms multi-target
  looping is **sequential, never concurrent** (AC3, "out of scope" bullet),
  and that a pushed ticket is never implicitly cleared from context (AC5).
- **No automated test harness** — markdown-procedure repo (confirmed by every
  prior step-0 through step-4 execution summary in this task). Verification
  is structural grep + dry-run trace, matching established convention.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "push the active ticket" (1 ticket in context, unmarked or active) | Not recognized — no Push action exists | §A defaults to that one ticket (AC1.1) → §B runs the full push procedure on it |
| "push" (bare, >1 ticket in context, one marked active) | Not recognized | §A defaults to the active entry (AC1.1) |
| "push" (bare, >1 ticket in context, none active) | Not recognized | §A asks "Which ticket(s) would you like to push?" |
| "push PROJ-123 and PROJ-124" (both present, unambiguous) | Not recognized | §A resolves both via two independent matches → §C loops both sequentially |
| "push all tickets" (3 in context) | Not recognized | §A resolves all 3 → §C processes them one at a time, with a continue/stop checkpoint between each |
| No Jira MCP connected | N/A | §B.1 tells the user, emits the ticket for copy-paste (unchanged degradation contract) |
| Pushed issue type is Epic | N/A | §B.4 offers the Idea-link step exactly as the recovered pre-restructuring flow did |
| User says "stop" mid-batch (2+ remaining targets) | N/A | §C breaks the loop; untouched targets remain in `$TICKET_CONTEXT`, reported as not-attempted in §D |
| Ticket's presence in `$TICKET_CONTEXT` after a push | N/A | Unchanged — Push never adds/removes an entry or touches `active` (AC5); it may attach an optional `pushResult` field |
| Load, Describe, Breakdown, Clear, Exit | Unchanged | Unchanged — Sections A/C/D/E and all four existing action subflows untouched |
| `hb-ticket-discuss.md` `allowed-tools` | 6 `/tmp` grants + 5 Jira tools | 6 `/tmp` grants + **8** Jira tools (+`createJiraIssue`, `editJiraIssue`, `createIssueLink`) — see Design decision |

Kind of change: **additive only**. New Action Registry row + new subflow file
+ new TOC row + 3 new tool grants (fixing a pre-existing gap, not a new
integration) + a one-word text tweak in two existing prose locations. No
existing row, section, or action's behavior changes.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Load / Describe / Breakdown / Clear dispatch | §B rows 1-4 → their own subflow files | Files untouched; §B gains one row, existing rows keep their text |
| Exit dispatch | §B row 5 → `exit-ticket-loop-subflow.md` | File untouched |
| §A ticket-entry model `{id_or_summary, content, active}` | 3 required fields, plus optional `source`/`parent` | Push only ever *reads* `content`/`id_or_summary` and attaches an additive optional `pushResult` — it introduces no required field, so it cannot violate the extensibility note |
| §C present-state / §D dispatch / §E log+continue | Unchanged control flow | Push is invoked exactly like the other four: matched via NL, mutates `$TICKET_CONTEXT` by reference (optional-field-only here), returns an outcome string for §E to log |
| Membership / active-flag mutation | N/A (no such action touches these on push) | AC5 explicitly forbids implicit clearing — §B.6/§C never call `$TICKET_CONTEXT.remove` or reassign `active` |
| Existing 5 Jira read-tools (`getAccessibleAtlassianResources` etc.) | Used by Load and now also by Push's §B.2 | Same tools, same calls — Push's NL-resolution loop reuses them exactly as the recovered pre-restructuring Step 4 did; Load's own usage is untouched |

Purely additive; the only new risk is the new subflow's own correctness
(target-set default/resolution, per-ticket procedure fidelity to the
recovered flow, sequential loop with early-stop, `allowed-tools` completeness)
— covered in §5/§6 below.

---

## 1. Design overview

One new action, dispatched like Load/Describe/Breakdown/Clear, that resolves
a *set* of targets (generalizing Clear's §A with a new default-to-single/
active branch), then walks each target sequentially through the recovered
pre-restructuring push procedure, tracking a per-ticket outcome:

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

**Target-set resolution generalizes Clear's, plus one new default branch:**
`clear-ticket-subflow.md` §A has no "bare word with no target named" default
beyond "ask the user" — Clear has no reason to guess since removal is
destructive. Push's AC1.1 explicitly wants a default for the common
case (bare "push" right after Describe/Load), so §A below adds that branch
ahead of the final ask-user fallback:

```
precedence:  "all" request  >  named reference(s) (one or more)  >
             bare "push" + exactly one entry in context  >
             bare "push" + an unambiguous active entry  >  ask-user
(tie-break inside "named references": identical to clear-ticket-subflow.md
 §A step 4 — matched independently per reference, never guess)
```

**No up-front bulk confirmation gate** (unlike Clear's count-based confirm):
AC2 already requires each ticket's own NL-resolution loop (§B.2) to end with
an explicit "Does this look right?" accept before anything is created or
updated — that per-ticket confirmation *is* the safety gate Push needs.
Adding a second, redundant "confirm pushing N tickets?" prompt ahead of §C
would duplicate that gate without the ticket asking for it (unlike Clear,
whose AC5 explicitly calls for a count-based confirm because deletion has no
per-item recovery step of its own).

**Sequential loop with an explicit continue/stop checkpoint** (AC3): the
checkpoint is placed *between* completed tickets, not by watching for an
ad-hoc "stop" utterance mid-ticket — a mid-flight "stop" during, say, §B.2's
own NL-resolution loop would be ambiguous (is the user aborting only that
one ticket's field resolution, or the whole batch?). An explicit "continue to
the next ticket, `<label>`?" question after each ticket's own procedure fully
resolves removes that ambiguity and gives the user one unambiguous place to
say stop.

**`pushResult` is additive, never structural**: Push is the first ticket-loop
action that mutates `$TICKET_CONTEXT` without adding, removing, or
re-activating an entry — it only ever attaches an optional bookkeeping field
to an existing entry (per `ticket-loop-subflow.md` §A's extensibility note),
consistent with AC5's "Push does not implicitly clear it."

**Alternatives considered and rejected:**
- *Resolve `cloudId` once per Push invocation and reuse it across every
  target* — rejected: AC2 requires the procedure to run "unchanged in
  substance" per ticket; caching `cloudId` across tickets is a behavior
  change (and an unnecessary one — `getAccessibleAtlassianResources` typically
  resolves to a single site without re-prompting, so the cost is negligible).
- *Add a bulk "confirm pushing N tickets?" gate before §C, mirroring Clear* —
  rejected: see the Design overview note above; the ticket's own AC2
  confirmation loop is the gate, and inventing a second one isn't asked for
  by any AC.
- *Let the user interrupt mid-ticket with a free-floating "stop" instead of
  an explicit between-ticket checkpoint* — rejected: ambiguous scope (which
  loop is being stopped — the NL-resolution sub-loop or the batch?); an
  explicit checkpoint after each ticket fully resolves removes the ambiguity
  and matches AC3's "stopping before processing the next" wording precisely.
- *Leave `allowed-tools` at its current 5-tool list, since "unchanged from
  today" could be read literally* — rejected: see the Design decision above;
  the procedure this step ships calls 3 tools not currently granted, so
  "lists exactly the tools this procedure calls" (AC7) requires adding them.

---

## 2. `push-ticket-subflow.md` — specification

**New file.** One subflow, four lettered top-level sections (A resolve target
set, B per-ticket push procedure, C multi-target loop, D compose outcome),
matching the opening-blockquote + "Caller contract." + lettered-sections
shape already used by `clear-ticket-subflow.md`, `breakdown-ticket-
subflow.md`, and `load-ticket-subflow.md`. Numbered steps inside each
section, mirroring `load-ticket-subflow.md`'s §B/§C/§D internal numbering
(no further `####` nesting).

**Caller contract:**
- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out) — mutated only
  via an additive, optional `pushResult` field attached per pushed/emitted
  entry; never added-to, removed-from, or re-activated by this subflow
- (implicit) the user's triggering utterance — already in conversation
  context, not a formal parameter (mirrors Load/Breakdown/Clear's own
  precedent)

**§A Resolve target set** — algorithm:
1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to push."
   → return outcome `"Push: no tickets in context."` (no calls, no
   mutation).
2. Utterance requests the whole context ("push all," "push everything," or
   an equivalent) → `$TARGETS` = every entry in `$TICKET_CONTEXT`, in its
   existing order. Continue to §C.
3. Utterance names one or more tickets (by id/summary): identical algorithm
   to `clear-ticket-subflow.md` §A step 4 — split into distinct named
   references, semantic-match each against every entry's `id_or_summary`
   (zero matches → ask and re-match that one reference; multiple matches →
   numbered list scoped to that reference, user picks, never auto-select;
   one match → include). `$TARGETS` = the deduplicated union across all
   references. Continue to §C.
4. Utterance names no ticket and does not request "all" (e.g. "push", "push
   it", "push this ticket"):
   1. `$TICKET_CONTEXT` has exactly one entry → `$TARGETS` = `[that entry]`
      (AC1.1's "one ticket in context" default), regardless of its `active`
      flag.
   2. Else, exactly one entry has `active: true` → `$TARGETS` = `[that
      entry]` (AC1.1's "unambiguous active ticket" default).
   3. Else (multiple entries, none active) → ask the user "Which ticket(s)
      would you like to push?" and re-run this §A against the reply.
   Continue to §C once resolved via 4.1 or 4.2.

**§B Per-ticket push procedure** — invoked once per `$TARGET` by §C. Returns
a result record `{ status: "pushed" | "copy-paste", issueKey?, browseUrl?,
ideaLinked? }` for that one ticket; never mutates `$TICKET_CONTEXT`
membership or `active`.

1. **Detect Jira MCP & collect NL description** (recovered `7bd2c42` Step 3,
   verbatim, labeled per-ticket): look for a connected MCP tool capable of
   creating a Jira issue, discovered by capability (Atlassian Rovo example:
   `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`).
   - Not found → `$JIRA` = `unavailable`; tell the user no Jira-capable MCP
     was detected; skip to step 5.
   - Found → ask the user to describe the Jira target in NL for *this*
     ticket, naming it by `$TARGET.id_or_summary` in the prompt so a
     multi-target run stays distinguishable (e.g. "For 'PROJ-123: fix
     auth', describe the Jira target..."). "no"/decline → `$JIRA` =
     `declined`, skip to step 5. Otherwise → `$NL_DESC`, continue to step 2.
2. **NL resolution & confirmation loop** (recovered `7bd2c42` Step 4,
   verbatim, lettered A-E): parse `$NL_DESC` into create/update intent and
   candidate fields; resolve `cloudId` via
   `getAccessibleAtlassianResources`; resolve remaining fields per path
   (`getVisibleJiraProjects` / `getJiraProjectIssueTypesMetadata` for
   create; `getJiraIssue` / `searchJiraIssuesUsingJql` for update, also
   capturing `issueTypeName`); present the resolved set and ask "Does this
   look right?"; loop on accept (→ `$JIRA_FIELDS`, `$JIRA` =
   create/update, continue step 3) / refine (return to parse) / supply-exact
   (accept user-given values, confirm, then continue step 3) / abort (→
   `$JIRA` = `declined`, skip to step 5). Any query-tool error → surface
   verbatim, prompt the user to supply that field directly — never
   dead-ends.
3. **Push to Jira** (recovered `7bd2c42` Step 5, verbatim, substituting
   `$TARGET.content` for `$WRITTEN_TICKET`): create path calls
   `createJiraIssue` with `cloudId`, `projectKey`, `issueTypeName`,
   `summary`, `description` = `$TARGET.content`, `contentFormat:
   "markdown"`; update path calls `editJiraIssue` with `cloudId`,
   `issueIdOrKey`, `fields: { description: $TARGET.content }`,
   `contentFormat: "markdown"`.
   - Success → `$JIRA` = `pushed`; report the issue key + browse URL; store
     `$JIRA_FIELDS.issueKey` (create path: the returned key; update path:
     alias of `issueIdOrKey`). Continue to step 4.
   - Failure (auth, permission, invalid field, etc.) → surface the error
     verbatim; fall through to step 5.
4. **Offer Jira Idea link (Epic only)** (recovered `7bd2c42` Step 6,
   verbatim): guard on `$JIRA = pushed` **and** `$JIRA_FIELDS.issueTypeName
   === "Epic"`; otherwise proceed directly to step 5. Offer the link; on
   yes, resolve `$IDEA_REF` (explicit key, bare number + project prompt, or
   unrecognized → re-prompt/abort-as-decline) and call `createIssueLink`
   with `cloudId`, `type: "Polaris work item link"`, `inwardIssue` =
   `$JIRA_FIELDS.issueKey`, `outwardIssue` = the resolved Idea key
   (direction never reversed). Success → confirm both keys, set
   `$IDEA_LINKED` = the Idea key. Failure → surface verbatim, state the
   already-pushed issue is unaffected, no retry/rollback. Either way,
   continue to step 5.
5. **Emit ticket (fallback)** (recovered `7bd2c42` Step 7, verbatim,
   substituting `$TARGET.content` for `$WRITTEN_TICKET`): reached when
   `$JIRA` ∈ {`unavailable`, `declined`} or after a step-3 failure. Skipped
   when `$JIRA = pushed`. Print `$TARGET.content` in a fenced block for
   copy-paste; state this is the standalone ticket held in context — no
   `.hb/` write. When `$JIRA = unavailable`, additionally state that no Jira
   MCP was available.
6. **Compose result**:
   - `$JIRA = pushed` → `{ status: "pushed", issueKey: $JIRA_FIELDS.issueKey,
     browseUrl: <from step 3>, ideaLinked: $IDEA_LINKED or null }`.
   - Otherwise → `{ status: "copy-paste" }`.
   Attach as `$TARGET.pushResult` (additive optional field per
   `ticket-loop-subflow.md` §A's extensibility note). Return the result to
   §C.

**§C Multi-target loop** — algorithm:
1. `|$TARGETS| > 1` → announce the resolved set before starting ("About to
   push N ticket(s), one at a time: `<label1>`, `<label2>`, ..."). `|
   $TARGETS| == 1` → skip the announcement.
2. `$PUSH_RESULTS` = `[]`.
3. For each `$TARGET` in `$TARGETS`, **in order, one at a time (never
   concurrent, per AC3)**:
   1. Run §B for `$TARGET`; append `{ label: $TARGET.id_or_summary, result:
      <§B's returned result> }` to `$PUSH_RESULTS`.
   2. If `$TARGET` is not the last entry in `$TARGETS` **and** `|$TARGETS| >
      1`: ask "Continue to the next ticket, '`<next label>`'? (yes to
      continue, or say stop)."
      - Stop/decline → break out of this loop; every not-yet-processed
        target remains in `$TICKET_CONTEXT`, untouched.
      - Continue/yes → proceed to the next target.
4. Continue to §D once the loop ends (exhausted, or stopped early per 3.2).

**§D Compose return outcome**:
1. For each entry in `$PUSH_RESULTS`, compose a line: `pushed` →
   `"<label>: pushed as <issueKey> (<browseUrl>)"`, appending `", linked to
   Idea <ideaKey>"` when `ideaLinked` is set; `copy-paste` → `"<label>:
   emitted for copy-paste (no Jira push)"`.
2. If §C stopped early: additionally list every not-yet-attempted target's
   label.
3. Present the full summary to the user.
4. Return outcome string `"Push: N of M ticket(s) processed (<per-ticket
   breakdown>)."` (`M` = `|$TARGETS|`, `N` = `|$PUSH_RESULTS|`) for
   `ticket-loop-subflow.md` §E to log.

**Failure/degradation contract**: §A's empty-context and default-ambiguous
cases return without invoking §B at all (no mutation, no calls). Within §B,
every branch (no MCP, decline, query-tool error, push error, idea-link
error) mirrors the recovered pre-restructuring flow's own contract exactly —
never dead-ends, always falls through to step 5 (emit). §C's stop path
leaves `$TICKET_CONTEXT` and its untouched entries exactly as they were — no
partial per-ticket mutation, since a target only gains `pushResult` once its
own §B run fully completes (step 6).

---

## 3. Integration / wiring

- **`ticket-loop-subflow.md` §B (Action Registry)** — one new row added:

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Push ticket(s) | "push this", "push PROJ-123 and PROJ-124", "push all tickets" | `push-ticket-subflow.md` |

  Inserted after the existing "Clear ticket(s)" row and before "Exit"
  (matching the task ticket's own AC ordering: Clear=AC7, Push=AC8,
  Exit=AC9). **Sections A, C, D, E of `ticket-loop-subflow.md` are not
  touched** — per that file's own contract ("Later steps extend this
  skill's action set only via §B").
- **`skills/hb-ticket-discuss.md`**:
  - `allowed-tools` gains 3 lines, appended after the existing 5 Jira tools:
    `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`,
    `mcp__claude_ai_Atlassian_Rovo__editJiraIssue`,
    `mcp__claude_ai_Atlassian_Rovo__createIssueLink` — see Design decision.
    The 6 `/tmp`-scoped Read/Write/Edit grants are untouched (Push writes no
    file).
  - `description:` (frontmatter) and the body prose both change "(e.g.
    describe, load, breakdown, clear, exit)" → "(e.g. describe, load,
    breakdown, clear, push, exit)" — matching how steps 2-4 updated the same
    two locations when each prior action shipped. No `Steps` section change
    — Push is reachable purely through the Action Registry, like the other
    four actions.
- **`skills/references/references-toc.md`** — one new row for
  `push-ticket-subflow.md`, placed directly after the
  `clear-ticket-subflow.md` row and before `exit-ticket-loop-subflow.md`
  (mirroring the Action Registry's new ordering).
- No configuration, build wiring, or dependency-manifest changes — this
  repo's skill layer has none.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/push-ticket-subflow.md` | **new** — full Push action subflow (§A-D as specified in §2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — one new Action Registry row (§B); Sections A, C, D, E untouched |
| `skills/hb-ticket-discuss.md` | **edit** — `allowed-tools` gains 3 Jira tool lines; `description:` and body-prose example-actions list gain "push"; `Steps` section untouched |
| `skills/references/references-toc.md` | **edit** — one new row for `push-ticket-subflow.md` |
| `.hb/facts.md` | **edit** — prune the now-redundant `hb-015/step-5: re-author Jira push logic deleted...` fact (superseded by this plan.md, its intended reader), per §6 below |

No dependency manifest or lockfile in this repo's skill layer.

---

## 5. Tests

No automated harness (markdown-procedure repo, confirmed by every prior
execution summary in this task). Coverage is static/structural + dry-run
trace, matching the established convention from steps 0-4.

**Structural (grep/read-checkable):**
- `grep -n "Push ticket(s)" skills/references/ticket-loop-subflow.md` →
  exactly one Action Registry row, positioned between Clear and Exit; the
  other four rows' text unchanged.
- `grep -c "^####" skills/references/push-ticket-subflow.md` → 4 (§A-D).
- `git diff --stat -- skills/references/load-ticket-subflow.md
  skills/references/describe-ticket-subflow.md
  skills/references/breakdown-ticket-subflow.md
  skills/references/clear-ticket-subflow.md
  skills/references/exit-ticket-loop-subflow.md
  skills/references/breakdown-subflow.md` → no output (all six untouched).
- `grep -n "mcp__claude_ai_Atlassian_Rovo__" skills/hb-ticket-discuss.md |
  wc -l` → 8 (5 existing + 3 new); `grep -n "createJiraIssue\|editJiraIssue\|
  createIssueLink" skills/hb-ticket-discuss.md` → each appears exactly once,
  inside `allowed-tools`.
- `grep -n "clear, push, exit" skills/hb-ticket-discuss.md` → 2 matches
  (frontmatter `description:` + body prose).
- `grep -n "push-ticket-subflow" skills/references/references-toc.md` →
  exactly one row, positioned between the `clear-ticket-subflow.md` and
  `exit-ticket-loop-subflow.md` rows.
- **No-file-write guard**: `grep -n "Write(\|Edit(\|^Bash"
  skills/references/push-ticket-subflow.md` → no matches (Push only reads
  `$TARGET.content` already in memory and calls MCP tools/stdout — no
  filesystem access, unlike Load/Describe/Breakdown).
- **Reuse-fidelity check**: `git show 7bd2c42:skills/hb-ticket-discuss.md`
  diffed by eye against §2 §B steps 1-5 — every field name (`cloudId`,
  `projectKey`, `issueTypeName`, `summary`, `issueIdOrKey`, `issueKey`) and
  tool name matches the recovered version; only `$WRITTEN_TICKET` →
  `$TARGET.content` and per-ticket labeling in step 1's prompt differ.

**Dry-run traces (exercised when `/hb-ticket-discuss` is run):**
- **Single-ticket default**: exactly one entry in context, user says "push"
  → §A step 4.1 resolves `$TARGETS` = `[that entry]` → §C skips the
  announcement (count == 1) → §B runs once → §D reports one outcome.
- **Active-ticket default**: 2+ entries, one `active: true`, user says
  "push it" → §A step 4.2 resolves the active entry.
- **Ambiguous bare push**: 2+ entries, none active, user says "push" → §A
  step 4.3 asks "Which ticket(s) would you like to push?"
- **Multiple named targets**: "push PROJ-123 and PROJ-124," both present and
  unambiguous → §A resolves both via two independent matches → §C announces
  the set, runs §B for the first, asks to continue, runs §B for the second.
- **"Push all," 3 tickets**: §A step 2 resolves all 3 → §C loop runs
  sequentially with two continue-checkpoints.
- **Stop mid-batch**: 3 targets, user says "stop" after ticket 1 completes →
  §C breaks; tickets 2-3 remain in `$TICKET_CONTEXT`, untouched; §D reports
  1 processed + 2 not-attempted.
- **No Jira MCP connected**: §B.1 sets `$JIRA = unavailable`, tells the
  user, skips to §B.5 (emits `$TARGET.content` for copy-paste) — ticket
  stays in context (AC5), `pushResult = { status: "copy-paste" }` attached.
- **Push declined mid-NL-resolution**: §B.2 abort branch → `$JIRA =
  declined` → §B.5 emits fallback.
- **Push failure (create/update tool error)**: §B.3 failure branch →
  surfaces error verbatim → falls through to §B.5 — never dead-ends.
- **Epic push → Idea link accepted**: §B.3 succeeds, `issueTypeName ===
  "Epic"` → §B.4 offers, user supplies a bare number → prompts for project,
  combines key, calls `createIssueLink`, confirms both keys → `pushResult
  .ideaLinked` set.
- **Epic push → Idea link declined/failed**: §B.4's No branch or
  `createIssueLink` error → both fall through to §B.5/§B.6 with
  `ideaLinked` unset; already-pushed issue unaffected.
- **Non-Epic push**: §B.4 guard fails → straight to §B.5/§B.6, no Idea
  prompt at all.
- **Ticket remains in context after push**: post-push, `$TICKET_CONTEXT`
  still contains the entry (AC5); only `pushResult` was added.
- **Load/Describe/Breakdown/Clear/Exit non-regression**: dry-run traces from
  steps 1-4's execution summaries re-verified unaffected — Push reads
  existing entries and adds only an optional field, touching no other
  subflow's logic.

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A (markdown repo); structural
   checks below are authoritative.
2. **Scope check** — `git status --short` shows exactly the 4 files in §4
   (plus this step's own `.hb/task/...` artifacts).
3. **Action Registry row** — `ticket-loop-subflow.md` §B has exactly 6 rows
   (Load, Describe, Breakdown, Clear, Push, Exit) in that order; Sections
   A/C/D/E byte-unchanged (`git diff` shows only the §B table hunk).
4. **New subflow shape** — `push-ticket-subflow.md` opens with a `>`
   blockquote + "Caller contract." line, has exactly 4 `####` sections
   (A-D), and ends with a "Failure/degradation contract" line — matching
   sibling subflow shape.
5. **`allowed-tools` completeness** — `git diff -- skills/hb-ticket-
   discuss.md` shows exactly one hunk adding the 3 Jira tool lines (no
   removal of the existing 5, no change to the 6 `/tmp` grants) plus the
   two wording hunks.
6. **Per-AC checks** — read `push-ticket-subflow.md` end-to-end and confirm
   each of the ticket's ACs is textually satisfied (full mapping in §7
   below); specifically confirm: §A never auto-selects on an ambiguous
   named reference or an ambiguous bare-"push" default; §B reproduces the
   recovered Steps 3-7 with no substantive change beyond the
   file→in-memory-content substitution; §C is explicitly sequential with a
   named stop mechanism; §D reports every ticket's outcome including
   not-attempted ones on an early stop.
7. **Non-regression** — `git diff --stat` for `load-ticket-subflow.md`,
   `describe-ticket-subflow.md`, `breakdown-ticket-subflow.md`,
   `clear-ticket-subflow.md`, `exit-ticket-loop-subflow.md`,
   `breakdown-subflow.md` shows no changes.
8. **TOC row** — `references-toc.md` has exactly one new row for
   `push-ticket-subflow.md`, correctly pointing at the new file's path,
   positioned between the Clear and Exit rows.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Push ticket(s) action added to menu, NL-selectable | §3 (Action Registry row) | |
| 1.1 — single named ticket, or "the active ticket" default (bare "push" + 1 in context, or unambiguous active) | §2 §A steps 3-4 | |
| 1.2 — several named tickets in one request | §2 §A step 3 (split references, match each) | |
| 1.3 — all tickets currently in context | §2 §A step 2 | |
| 2.1 — Jira MCP detected by capability; graceful fallback when absent | §2 §B step 1 | |
| 2.2 — NL description → resolution → confirmation loop, unchanged | §2 §B step 2 | Recovered `7bd2c42` Step 4 verbatim |
| 2.3 — push (create/update); report key/URL on success; fall through to copy-paste on failure | §2 §B step 3, step 5 | |
| 2.4 — Epic → offer Idea-link exactly as today | §2 §B step 4 | Recovered `7bd2c42` Step 6 verbatim |
| 3 — sequential looping, not concurrent; stops early on request; unprocessed tickets remain untouched | §2 §C | |
| 4 — per-ticket outcome tracked and summarized once batch finishes or stops | §2 §B step 6, §D | |
| 5 — ticket remains in context after push; not implicitly cleared | §1 (Design overview, `pushResult` note); §2 §B step 6 | Clearing stays a separate action (Clear, already shipped) |
| 6 — logic lives in its own subflow file(s); TOC updated | §2 (new file `push-ticket-subflow.md`); §3 (TOC row) | |
| 7 — `allowed-tools` lists exactly the Jira MCP tools this procedure calls | §3 (3 new tool lines) | See Design decision — pre-existing gap fixed now |

---

## 8. Out of scope (per ticket)

- New MCP/source integrations beyond the Jira push flow that already existed
  pre-restructuring — this step re-adds `createJiraIssue`/`editJiraIssue`/
  `createIssueLink` to `allowed-tools` to match what that flow always called,
  not a new integration.
- Any change to the Idea-linking direction or semantics (`createIssueLink`
  with `inwardIssue` = Epic, `outwardIssue` = Idea) — carried over verbatim
  from the recovered `7bd2c42` Step 6.
- Concurrent/parallel pushing of multiple tickets — sequential only (§2 §C).
