# Step 2 Plan — Load ticket action (file / Jira / web sources)

`hb-ticket-discuss`'s loop (shipped in step-1) currently offers only Describe and
Exit. The **motivating case**: a user runs `/hb-ticket-discuss` and says "load the
ticket from PROJ-123" (or "load this file as a ticket", or "pull in the ticket at
this URL") — today none of these are recognized; the loop's Action Registry has no
entry for them and the user is forced to redescribe the ticket from scratch via
Describe. This step adds a third action, **Load ticket**, covering the **general
class** of pulling an *existing* ticket (from a text file, a connected Jira MCP, or
a fetchable URL) into the loop's context instead of authoring one interactively.
Scope boundary: **additive only** — one new subflow file, one new Action Registry
row, one new TOC row, and a frontmatter tool-grant extension on the skill file;
`ticket-loop-subflow.md` Sections A/C/D/E, `describe-ticket-subflow.md`,
`exit-ticket-loop-subflow.md`, and `interactive-ticket-subflow.md` are all
unchanged. Externally observable effect once this lands: saying "load the ticket
from <source>" at any loop iteration adds that ticket to context as the active
entry, without leaving the loop.

Source ticket: `./ticket.md`. Builds on the **shipped** loop skeleton from step-1
(`skills/hb-ticket-discuss.md`, `skills/references/ticket-loop-subflow.md`,
`skills/references/describe-ticket-subflow.md`,
`skills/references/exit-ticket-loop-subflow.md`) — read in full during planning,
current as of commit `c74ec90`. This plan targets that code as it exists now.

> **Design decision — reuse `interactive-ticket-subflow.md` §C's transform rules
> only, not its whole guarded flow; reuse the Jira push flow's *update-path*
> resolution algorithm only, not its create path.** `interactive-ticket-subflow.md`
> §A/§B assume an interactive "please describe the ticket" prompt already
> happened — Load's raw material is file/issue/page content, not a fresh user
> description, so only §C (Rule 1 transcribe / Rule 2 derive) and §D's write-step
> *shape* are reused (ticket AC 2.1 says "same rules as ... Section C", not "same
> subflow"). Similarly, the pre-step-1 Jira push flow's NL-resolution loop (full
> text recovered via `git show 7bd2c42:skills/hb-ticket-discuss.md`, deleted from
> the live file per step-1's execution deviation) had both a *create* path
> (resolve project/type/summary) and an *update* path (resolve an existing issue
> by key or JQL search). Load only ever reads an existing issue, so it mirrors the
> **update path** only (§7-C below) — never creates. See §1 and the
> AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- **`skills/hb-ticket-discuss.md`** (57 lines, read in full): 3 Steps (Help check /
  Initialize loop / Inject loop subflow), no inlined action logic. Frontmatter
  `allowed-tools` (lines 12-24): 6 `/tmp` Read/Write/Edit grants +
  `mcp__claude_ai_Atlassian_Rovo__{getAccessibleAtlassianResources,
  getVisibleJiraProjects, getJiraProjectIssueTypesMetadata,
  searchJiraIssuesUsingJql, getJiraIssue}`. No `Read`/`Write`/`Edit` grant for
  paths outside `/tmp`, no `WebFetch`, no `Bash(find *)`.
- **`skills/references/ticket-loop-subflow.md`** (73 lines, read in full):
  §A defines the ticket entry as `{ id_or_summary, content, active }` with an
  explicit **extensibility note** (line 24-27): "Later steps may attach
  *additional* optional fields to an entry for their own bookkeeping — that is
  additive, not a redefinition, and doesn't require revisiting this subflow."
  §B (Action Registry) currently has exactly 2 rows: Describe ticket, Exit. §D
  (Dispatch) invokes "the matched action's dispatch subflow, passing
  `$TICKET_CONTEXT` and `$TICKET_SEQ` by reference" — no other variable is
  formally threaded; the user's triggering utterance is already visible in the
  same conversation, so an action needing to parse it (Load does) does not
  require a new formal parameter.
- **`skills/references/describe-ticket-subflow.md`** (23 lines): precedent for
  subflow shape — opening blockquote, "Caller contract.", numbered Behavior,
  "Failure/degradation contract" closing line. Uses scratch path
  `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` (incrementing `$TICKET_SEQ` first),
  derives `$id_or_summary` from the Background section's first clause (~8 words),
  unsets `active` on all existing entries before appending the new one as active.
- **`skills/references/interactive-ticket-subflow.md`** §C (Transform step,
  lines 25-49): Rule 1 (near-perfect match → transcribe verbatim, minimal
  conforming adjustments) / Rule 2 (freeform → derive Background / Acceptance
  Criteria / Out of scope per the table at lines 43-47). §D (Write step,
  lines 51-73): delete `$TARGET_PATH/ticket.md` if it exists, then write the
  three-section structure.
- **Jira MCP tools already granted** (verified against
  `hb-ticket-discuss.md` frontmatter): `getAccessibleAtlassianResources` (site/
  `cloudId` resolution), `searchJiraIssuesUsingJql`, `getJiraIssue` — exactly the
  three tools Load's Jira path needs. `getVisibleJiraProjects` and
  `getJiraProjectIssueTypesMetadata` are create-path-only (needed by the future
  Push step, not Load) and are already present too — **no Jira tool-grant change
  needed for this step.**
- **No `Read`/`WebFetch`/glob-capable `Bash` grant exists** for the File/Web
  sources. Precedent for a broad `Read` grant in this repo:
  `skills/hb-task-plan.md` frontmatter (`allowed-tools: ... Read Write`,
  unrestricted path) — reading arbitrary repo/ticket files during planning.
  Precedent for glob-style file discovery: `skills/hb-task-plan.md`'s
  `Bash(find *)` grant. No existing skill in this repo uses `WebFetch` — Load's
  web source is the first; it must be added.
- **No automated test harness** — markdown-procedure repo (confirmed by every
  prior step-0/step-1 execution summary in this task). Verification is
  structural grep + dry-run trace, matching established convention.
- **The pre-step-1 Jira flow's exact update-path wording** (git-recoverable,
  not present in the live file) — from `git show
  7bd2c42:skills/hb-ticket-discuss.md`, old Step 4's *update* branch: explicit
  key (`[A-Z]+-[0-9]+`) → `getJiraIssue`, confirm title/status; no key → derive a
  JQL query from the NL description → `searchJiraIssuesUsingJql`; 1 match → use
  it; multiple → numbered list, user picks (never auto-select); 0 matches → tell
  the user, ask for a key or a more specific description. This is the pattern
  ticket AC 2.2 requires Load to mirror.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "load the ticket from PROJ-123" | Not recognized — no Load action exists | Jira path: `getJiraIssue(PROJ-123)` → transform → added to context, active |
| "load the login epic from MOBILE" (no key) | Not recognized | Jira path: JQL search → 1 match → transform → added, active |
| "load this file: /tmp/draft.md" | Not recognized | File path: read → transform (Rule 1 or 2) → added, active |
| "pull in the ticket at https://…" | Not recognized | Web path: fetch → transform → added, active |
| Glob matches several files / JQL returns several issues | N/A | Numbered list presented; user picks — never auto-selected (AC 6) |
| File not found / Jira MCP absent / fetch fails | N/A | Error/absence surfaced; loop menu resumes; no partial entry added (AC 5) |
| Describe, Exit | Unchanged | Unchanged — Sections A/C/D/E and both existing subflows untouched |

Kind of change: **additive only**. New Action Registry row + new subflow file +
new TOC row + frontmatter tool-grant extension. No existing row, section, or file
is edited in a way that changes its behavior.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Describe ticket dispatch | `ticket-loop-subflow.md` §B row 1 → `describe-ticket-subflow.md` | File untouched; Action Registry gains a row, existing rows keep their text |
| Exit dispatch | §B row 2 → `exit-ticket-loop-subflow.md` | File untouched |
| §A ticket-entry model `{id_or_summary, content, active}` | 3 required fields | Load only *appends* an optional `source` field per §A's own extensibility note (line 24-27) — not a redefinition; Describe/Exit never read `source`, so they're unaffected |
| §C present-state / §D dispatch / §E log+continue | Unchanged control flow | Load is invoked exactly like Describe (matched via NL, mutates `$TICKET_CONTEXT`/`$TICKET_SEQ` by reference, returns an outcome string for §E to log) — no change to the cycle itself |
| Jira tool grants (5 existing entries) | Present, unused until step-5 | Unchanged — Load reuses 3 of the 5 read-only; none are removed or altered |

Purely additive — no table entry changes an existing behavior, so this is a
low-regression-risk step; the only new risk is the new subflow's own
correctness, covered in §5/§6 below.

---

## 1. Design overview

One new action, dispatched like Describe/Exit but with three internal source
branches that converge on a single finalize step:

```
Action Registry (ticket-loop-subflow.md §B) — new row:
  Load ticket → load-ticket-subflow.md

load-ticket-subflow.md:
  §A Classify source (file | jira | web | ask-if-unclear)
       │
       ├─ file source ──► §B (find/read) ─┐
       ├─ jira source ──► §C (capability check → update-path resolution) ─┤
       └─ web source  ──► §D (capability check → fetch) ─┘
                                                          │
                                                          ▼
                                              §E Finalize (transform, write
                                              scratch, read back, derive
                                              id_or_summary, append to
                                              $TICKET_CONTEXT as active)
```

**Source precedence / ambiguity:** §A classifies by pattern-matching the user's
triggering utterance (file path/glob syntax → file; `[A-Z]+-[0-9]+` or explicit
"Jira"/issue-description phrasing → jira; `https?://` → web). If none match
clearly, ask the user which source they mean — never guess (mirrors the Jira
push flow's own "never silently guessed" posture, carried into this design).

```
precedence: explicit pattern match (file glob / issue key / URL) ≥ ask-user
(tie-break: if the utterance matches two patterns at once — e.g. a URL that also
looks like a file path — ask the user to disambiguate; do not guess)
```

**Failure/degradation is uniform across all three sources**: any failure inside
§B/§C/§D returns directly to the loop menu (via §E's own contract, not the
finalize path) without adding a partial entry — see the Failure/degradation
contract at the end of the new file.

**Alternatives considered and rejected:**
- *Thread the user's utterance as an explicit `$USER_REQUEST` caller-contract
  variable, updating `ticket-loop-subflow.md` §D's wording* — rejected: the
  utterance is already visible in the same conversation the subflow executes in;
  formalizing it as a passed variable would touch §D, which step-1 explicitly
  scoped as not-to-change when adding actions. No behavior is gained.
- *Reuse `interactive-ticket-subflow.md`'s full guarded flow (§A-D) for Load* —
  rejected: §A/§B assume a fresh interactive prompt ("please describe..."); Load
  has no such prompt, it has file/issue/page content as input. Forcing Load
  through the guard clause would require inventing sentinel flag values with no
  real caller-contract meaning. Reusing only §C's rules (as the ticket itself
  specifies) is the precise, minimal reuse.
- *Mirror the Jira push flow's create path too, in case the referenced issue
  doesn't exist yet* — rejected: Load's contract (AC 4) is "load a ticket from a
  source"; a non-existent Jira issue is a resolution failure (0 matches), not a
  reason to create one. Ticket's own out-of-scope explicitly reserves Push
  (create/update) for step-5.
- *A single unified "fetch remote thing" helper shared by Jira-get and
  web-fetch* — rejected: the two have unrelated capability-detection and error
  shapes (MCP tool discovery vs. `WebFetch` availability); forcing a shared
  helper for two call sites is premature abstraction for no reuse benefit.

---

## 2. `load-ticket-subflow.md` — specification

**New file.** One subflow, five lettered sections (A classify, B file, C jira, D
web, E finalize), matching the opening-blockquote + "Caller contract." +
lettered-sections shape already used by `ticket-loop-subflow.md` and the
pre-step-1 Jira flow.

**Caller contract** (unchanged shape from `describe-ticket-subflow.md`):
- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- `$TICKET_SEQ` — mutable integer counter (in/out)
- (implicit) the user's triggering utterance — already in conversation context,
  not a formal parameter (see §1 alternatives-rejected)

**§A Classify source** — pattern-match the utterance into `$SOURCE ∈ {file,
jira, web}`; ask the user to disambiguate if no pattern matches or two match
at once. Never guess.

**§B File source** — algorithm:
1. Resolve the named path/glob. Zero matches → tell the user, return to loop
   menu (no entry added). Multiple matches → numbered list, user picks (never
   auto-select). One match → use it.
2. Read the resolved file; read failure → surface error verbatim, return to
   loop menu.
3. `$RAW_CONTENT` = file's full text → continue to §E.

**§C Jira source** — algorithm (mirrors the recovered pre-step-1 update path,
read-only, no create branch):
1. Capability check: discover a connected MCP tool that can read a Jira issue by
   key or by JQL search (Atlassian Rovo example already granted:
   `getJiraIssue` / `searchJiraIssuesUsingJql`; site resolution via
   `getAccessibleAtlassianResources`). None found → tell the user, suggest
   connecting one, return to loop menu.
2. Explicit key in the utterance → call the get-issue tool directly.
3. No explicit key → derive a JQL query from the description → call the JQL
   search tool. 0 matches → tell the user, ask for a key or a more specific
   description, return to loop menu if still unresolved. 1 match → use it.
   Multiple → numbered list of key + title, user picks (never auto-select).
4. Any tool error → surface verbatim, return to loop menu.
5. `$RAW_CONTENT` = resolved issue's `description` field (fallback: summary/
   title if description is empty); `$ISSUE_KEY` / `$ISSUE_TITLE` captured →
   continue to §E.

**§D Web source** — algorithm:
1. Capability check: is a URL-fetching tool (`WebFetch`) available in this
   session? Not available → tell the user, return to loop menu.
2. Fetch the named URL. Failure (network/HTTP/unparseable) → surface verbatim,
   return to loop menu.
3. `$RAW_CONTENT` = fetched page's extracted main text → continue to §E.

**§E Finalize** — algorithm (shared by all three sources):
1. Transform `$RAW_CONTENT` via `interactive-ticket-subflow.md` §C's Rule 1
   (transcribe) / Rule 2 (derive) — applied as written there, not re-derived.
2. Increment `$TICKET_SEQ`; `$TARGET_PATH` =
   `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` (same convention as
   `describe-ticket-subflow.md`).
3. Write step mirroring `interactive-ticket-subflow.md` §D's file structure:
   delete `$TARGET_PATH/ticket.md` if present, write the transformed content.
4. Read back `$TARGET_PATH/ticket.md` as `$content` (keeps the entry
   self-contained, per §A's provenance rule in `ticket-loop-subflow.md`).
5. Derive `$id_or_summary`: Jira source → `"$ISSUE_KEY: $ISSUE_TITLE"` (embeds
   the identifier per AC 4); file/web source → Background's first clause,
   truncated to ~8 words (same rule as `describe-ticket-subflow.md`).
6. Unset `active` on every existing `$TICKET_CONTEXT` entry, append
   `{ id_or_summary: $id_or_summary, content: $content, active: true, source:
   { type: $SOURCE, ref: <path | issue key | url> } }`. `source` is an
   additive, optional field per `ticket-loop-subflow.md` §A's extensibility
   note — Describe/Exit ignore it safely.
7. Return outcome string `"Loaded ticket: $id_or_summary (from $SOURCE)"`.

**Failure/degradation contract**: every §B/§C/§D failure branch returns to the
loop menu without mutating `$TICKET_CONTEXT`/`$TICKET_SEQ` and without an error
— the returned outcome string instead describes the failure (e.g. `"Load ticket
failed: <reason>"`) so `ticket-loop-subflow.md` §E still logs the attempt. No
partial or malformed entry is ever appended (AC 5).

---

## 3. Integration / wiring

- **`ticket-loop-subflow.md` §B (Action Registry)** — one new row added:

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Load ticket | "load the ticket from PROJ-123", "load this file as a ticket", "pull in the ticket at this URL" | `load-ticket-subflow.md` |

  Inserted before the existing "Describe ticket" row (matching the task
  ticket's own AC ordering: Load = AC 4, Describe = AC 5), so the table reads in
  the same order later steps will extend it. **Sections A, C, D, E of
  `ticket-loop-subflow.md` are not touched** — per that file's own line 3-5
  contract ("Later steps extend this skill's action set only via §B").
- **`skills/hb-ticket-discuss.md` frontmatter** — `allowed-tools` gains 3 new
  grants: `Read` (unrestricted path — precedent: `hb-task-plan.md`), `WebFetch`,
  `Bash(find *)` (precedent: `hb-task-plan.md`'s identical grant, for glob/path
  discovery). The 5 existing Jira MCP grants and 6 `/tmp` grants are unchanged.
  `description:` gains "load" as a third example action alongside "describe,
  exit". No Steps-section change — Help check / Initialize loop / Inject loop
  subflow are unchanged; Load is reachable purely through the Action Registry.
- **`skills/references/references-toc.md`** — one new row for
  `load-ticket-subflow.md`, placed directly after the `ticket-loop-subflow.md`
  row and before `describe-ticket-subflow.md` (mirroring the Action Registry's
  new ordering).
- No configuration, build wiring, or dependency-manifest changes — this repo's
  skill layer has none.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/load-ticket-subflow.md` | **new** — full Load action subflow (§A-E as specified in §2) |
| `skills/references/ticket-loop-subflow.md` | **edit** — one new Action Registry row (§B); Sections A, C, D, E untouched |
| `skills/hb-ticket-discuss.md` | **edit** — frontmatter `allowed-tools` (+`Read`, +`WebFetch`, +`Bash(find *)`); `description:` example-actions list gains "load"; Steps section untouched |
| `skills/references/references-toc.md` | **edit** — one new row for `load-ticket-subflow.md` |
| `.hb/facts.md` | **edit (conditional)** — record the git-recoverable-Jira-flow fact discovered during this planning pass (see step 6 of the skill's own process); only written if it changes the composed content |

No dependency manifest or lockfile in this repo's skill layer.

---

## 5. Tests

No automated harness (markdown-procedure repo, confirmed by every prior
execution summary in this task). Coverage is static/structural + dry-run trace,
matching the established convention from steps 0 and 1.

**Structural (grep/read-checkable):**
- `grep -n "Load ticket" skills/references/ticket-loop-subflow.md` → exactly one
  Action Registry row; Describe/Exit rows' text unchanged.
- `grep -c "^####" skills/references/load-ticket-subflow.md` → 5 (§A-E).
- `grep -n "interactive-ticket-subflow" skills/references/load-ticket-subflow.md`
  → references §C's rules, does not duplicate Rule 1/Rule 2 text inline.
- `grep -n "allowed-tools" -A 15 skills/hb-ticket-discuss.md` → contains `Read`,
  `WebFetch`, `Bash(find *)`, plus all 5 pre-existing Jira tools and 6 `/tmp`
  grants (nothing removed).
- `grep -n "load-ticket-subflow" skills/references/references-toc.md` → exactly
  one row.
- **Reuse guard**: `grep -n "hb-sdk\|^Bash" skills/references/load-ticket-subflow.md`
  → no matches (pure conversational state + tool calls, no SDK/shell side
  effects inlined, matching `ticket-loop-subflow.md`'s own convention).
- **Non-regression**: `git diff --stat -- skills/references/describe-ticket-subflow.md
  skills/references/exit-ticket-loop-subflow.md skills/references/interactive-ticket-subflow.md`
  → no output.

**Dry-run traces (per source, exercised when `/hb-ticket-discuss` is run):**
- **File happy path**: "load this file: /tmp/draft.md" → §A classifies file →
  §B finds one match, reads it, content already has Background/AC headers →
  Rule 1 transcribe → §E writes/reads back/derives `id_or_summary` from
  Background → entry appended, active.
- **File freeform**: same but `/tmp/draft.md` is unstructured prose → Rule 2
  derive → same finalize path.
- **File glob, multiple matches**: "load the tickets in drafts/*.md" → §B
  presents a numbered list → user picks one → continues as single-file path.
- **File not found**: → §B tells the user, returns to loop menu, no entry
  added, `$TICKET_SEQ` unchanged.
- **Jira explicit key**: "load the ticket from PROJ-123" → §C capability check
  passes → `getJiraIssue(PROJ-123)` → `$RAW_CONTENT`/`$ISSUE_KEY`/`$ISSUE_TITLE`
  set → §E → `id_or_summary` = `"PROJ-123: <title>"`.
- **Jira NL, one match**: "load the login epic from MOBILE" → JQL search → 1
  match → same as above.
- **Jira NL, multiple matches**: JQL search returns 3 → numbered list, user
  picks → continues as single-issue path.
- **Jira MCP absent**: capability check fails → told, returns to loop menu.
- **Web happy path**: "pull in the ticket at https://example.com/ticket" → §D
  capability check passes → fetch succeeds → §E.
- **Web unavailable**: `WebFetch` not available this session → told, returns to
  loop menu.
- **Ambiguous utterance**: "load PROJ-123.md" (looks like both a file and a
  Jira-key-shaped string) → §A asks the user to disambiguate rather than
  guessing.
- **Multiple Load calls, active-flag exclusivity**: second Load call increments
  `$TICKET_SEQ` again (fresh scratch path), unsets `active` on the first loaded
  entry before appending the second as active — traced correct, same mechanism
  `describe-ticket-subflow.md` already uses.
- **Describe/Exit non-regression**: both dry-run traces from step-1's execution
  summary re-verified unaffected (no shared state touched by Load's new
  `source` field).

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A (markdown repo); structural checks
   below are authoritative.
2. **Scope check** — `git status --short` shows exactly the 4 files in §4 (plus
   `.hb/facts.md` only if step 6 of the skill's own process changed it, and this
   step's own `.hb/task/...` artifacts).
3. **Action Registry row** — `ticket-loop-subflow.md` §B has exactly 3 rows
   (Load, Describe, Exit); Sections A/C/D/E byte-unchanged (`git diff` shows
   only the §B table hunk).
4. **New subflow shape** — `load-ticket-subflow.md` opens with a `>` blockquote
   + "Caller contract." line, has exactly 5 `####` sections (A-E), and ends with
   a "Failure/degradation contract" line — matching sibling subflow shape.
5. **`allowed-tools` completeness** — read `hb-ticket-discuss.md` frontmatter;
   confirm `Read`, `WebFetch`, `Bash(find *)` present; confirm all 5 pre-existing
   Jira tools and 6 `/tmp` grants still present (nothing dropped).
6. **Per-AC checks** — read `load-ticket-subflow.md` end-to-end and confirm each
   of the ticket's ACs is textually satisfied (full mapping in §7 below);
   specifically confirm: numbered-list-on-ambiguity appears in both §B and §C
   (never auto-select), and every §B/§C/§D branch's failure path states "return
   to the loop menu" with no entry added.
7. **Non-regression** — `git diff --stat` for `describe-ticket-subflow.md`,
   `exit-ticket-loop-subflow.md`, `interactive-ticket-subflow.md` shows no
   changes.
8. **TOC row** — `references-toc.md` has exactly one new row for
   `load-ticket-subflow.md`, correctly pointing at the new file's path.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — Load action added, selectable via NL | §3 (Action Registry row); §2 §A (classify by pattern, never guess) | |
| 2 — supports loading from file / MCP / web | §2 §B (file), §C (jira), §D (web) | |
| 2.1 — file: read + transform via `interactive-ticket-subflow.md` §C rules | §2 §B step 3 → §E step 1 | Reuses rules only, not the whole guarded flow — see Design decision |
| 2.2 — MCP (Jira): discover-by-capability + resolution, never auto-select | §2 §C (mirrors recovered update-path algorithm, §0's "current-state facts") | Read-only; no create path (out of scope) |
| 2.3 — web access when available | §2 §D (capability check → fetch) | First `WebFetch` use in this repo's skill layer |
| 3 — loaded ticket added to context, becomes active | §2 §E steps 6 | Same active-flag-exclusivity mechanism as Describe |
| 4 — recallable by NL summary/content and by identifier (e.g. Jira key) | §2 §E steps 5-6 (`id_or_summary` embeds the Jira key; optional `source` field records path/key/url) | Additive field per `ticket-loop-subflow.md` §A's extensibility note — no redefinition |
| 5 — graceful degradation, no partial/malformed entry, no crash | §2 §B/§C/§D failure branches; §2 closing Failure/degradation contract | |
| 6 — ambiguous/multi-match → numbered list, never auto-selected | §2 §B step 1, §C step 3 | |
| 7 — action's logic in its own subflow file; TOC updated | §2 (new file `load-ticket-subflow.md`); §3 (TOC row) | |

---

## 8. Out of scope (per ticket)

- Breakdown, Clear, and Push actions — later steps (3, 4, 5 of this task).
- New MCP/source integrations beyond what's already available to the agent
  harness (Jira via Atlassian Rovo, local files, web fetch via `WebFetch`) —
  this step wires Load to existing means only.
- Any change to `hb-task-plan` or the shared breakdown subflow.
- The Jira **create** path (new issue) — Load only ever reads an existing issue;
  creating/updating a Jira issue remains step-5's Push action.
- Re-adding the deleted pre-step-1 Jira push/NL-resolution/Idea-link Steps
  verbatim — that recovery is step-5's job (flagged in step-1's execution
  summary); this step only reuses its *update-path resolution pattern* in
  adapted, read-only form for Load.
