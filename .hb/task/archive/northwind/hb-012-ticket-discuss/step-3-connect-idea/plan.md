# Step 3 Plan — Offer Epic→Idea linking in `hb-ticket-discuss`

Today (after steps 0–2), `/hb-ticket-discuss` pushes a generated ticket to Jira via
`createJiraIssue`/`editJiraIssue` and reports the resulting issue key/URL — full stop. The
**motivating case** — a user who just pushed a new **Epic** and needs it traced back to the
Jira **Idea** it originated from — fails: there is no path from a successful push to a
`createIssueLink` call, so the user must leave the flow and link manually in Jira's UI (and,
per the ticket's background, get the link **direction** wrong is easy to do since
`createIssueLink`'s `inwardIssue`/`outwardIssue` semantics are non-obvious and were only
empirically verified in a prior session). This is the **general class**: any successful
Epic push (create or update) that should offer to close the loop back to its originating
Idea. Scope boundary: **one file changes** (`skills/hb-ticket-discuss.md`) — no new
`allowed-tools` grants, since the sole new tool call (`createIssueLink`) is a write op and
follows the same require-a-prompt posture already established for `createJiraIssue`/
`editJiraIssue` (STEP-1-REVIEW-1). Externally observable effect once this lands: after a
successful Epic push, the skill asks whether to link it to an existing Idea, resolves the
supplied reference to a full issue key, and calls `createIssueLink` with the
ticket-verified-correct direction (Epic = `inwardIssue`, Idea = `outwardIssue`) — and for any
non-Epic push, or any decline, nothing changes.

Source ticket: `./ticket.md`. Builds on the **shipped** work from steps 0–2
(`skills/hb-ticket-discuss.md` — 7 steps: help → generate+review → detect+collect NL → NL
resolution+confirm loop → push → fallback emit → prompt). This plan targets that file as it
exists **now** (140 lines, read in full during planning).

> **Design decision — link as a step appended after push succeeds, not a field collected
> during info-gathering.** The ticket explicitly leaves this open (AC 1.1). The deciding
> fact: `createIssueLink` needs a **real** Epic issue key, and for the create path that key
> does not exist until `createJiraIssue` (Step 5) returns it — asking "which Idea?" any
> earlier risks asking a question that becomes moot if the push fails, and would force
> resolution logic into Step 5, which step 2's design deliberately kept push-only/
> resolution-free (see step-2 plan §1 design decision). Appending a new Step 6 *after* Step 5
> keeps that separation intact: Step 6 only ever runs once a real issue key is in hand. The
> one piece of state this requires that doesn't already exist: the **issue type name** for
> the *update* path (the create path already carries `issueTypeName` in `$JIRA_FIELDS` per
> step 2) — added to Step 4's update-path resolution using data both its tool calls already
> return, at no extra API cost. See §1 and §7.

---

## 0. Current-state facts (verified during planning)

Confirmed by reading `skills/hb-ticket-discuss.md` in full, not assumed:

- **Frontmatter `allowed-tools`** (lines 10–22) grants six `/tmp` Read/Write/Edit patterns
  plus five **read-only** Atlassian Rovo MCP tools: `getAccessibleAtlassianResources`,
  `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`, `searchJiraIssuesUsingJql`,
  `getJiraIssue`. `createJiraIssue` and `editJiraIssue` are **deliberately absent** — per
  STEP-1-REVIEW-1 (step-1 review.md), write ops on Jira require an explicit runtime
  permission prompt rather than being pre-approved. This is the precedent this plan follows
  for `createIssueLink` (also a write op).
- **Step 4 — NL resolution & confirmation loop** (lines 70–110). Block C's *Create path*
  (lines 89–92) resolves `projectKey`, **`issueTypeName`**, and `summary` — `issueTypeName`
  is already a first-class resolved field here. Block C's *Update path* (lines 94–96) only
  resolves `issueIdOrKey`:
  - Explicit-key bullet (line 95): "call the MCP's get-issue tool to retrieve the issue and
    confirm its title and status... Resolved: `issueIdOrKey` = extracted key." No issue-type
    capture today.
  - No-explicit-key bullet (line 96): JQL search, 1 match → confirm key + title; multiple →
    numbered list; 0 → prompt. No issue-type capture today.
  - Per the step-2 plan, the *update* `$JIRA_FIELDS` shape is `{path: "update", cloudId,
    issueIdOrKey}` — **no `issueTypeName`**.
- **Tool schemas — verified live** (loaded via ToolSearch during planning):
  - `mcp__claude_ai_Atlassian_Rovo__getJiraIssue` — when `fields` is omitted, **defaults
    include `issuetype`**. The explicit-key bullet's existing call already returns the type;
    it is just not being captured into `$JIRA_FIELDS` today.
  - `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` — same default-fields
    behavior; `issuetype` is already present in every match the no-explicit-key bullet
    already fetches.
  - `mcp__claude_ai_Atlassian_Rovo__createIssueLink` — required: `cloudId`, `inwardIssue`,
    `outwardIssue`, `type` (link-type **name**, e.g. `"Duplicate"`, `"Blocks"`); optional
    `comment`, `contentFormat`. No lookup call is required when the type name is already
    known — matches the ticket's already-verified `"Polaris work item link"`.
  - `mcp__claude_ai_Atlassian_Rovo__getIssueLinkTypes` exists (lists link types) but is
    unneeded: the ticket's background table already verifies the exact type string and
    direction live; adding a discovery call here would be unused ceremony (see §1 rejected
    alternatives).
- **Step 5 — Push to Jira** (lines 112–121). On success (line 120): "set `$JIRA` = `pushed`
  and report the resulting issue **key and browse URL**" — the key is reported to the user
  but **not persisted to a named field** on `$JIRA_FIELDS` for reuse by a later step.
- **Step 6 — Emit ticket (fallback)** (lines 123–129): reached when `$JIRA` ∈ {`unavailable`,
  `declined`} or after a Step-5 failure; **skipped when `$JIRA` = `pushed`**. This means: the
  only branch where a real Jira issue exists to link is exactly the branch where this emit
  step is skipped — the new idea-link step belongs between Push and this Emit step.
- **Step 7 — Prompt user** (lines 131–136): branches only on `$JIRA` = `pushed` vs. not.
- **No build/test harness** exists (confirmed by step-0/1/2 execution summaries) — skills are
  markdown procedures; verification is static/structural + runtime-interactive.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| Push succeeds, resolved type = Epic | reports key/URL, done | additionally asks to link to a Jira Idea; on accept, resolves the reference and calls `createIssueLink` (Epic=`inwardIssue`, Idea=`outwardIssue`) |
| Push succeeds, resolved type ≠ Epic | reports key/URL, done | **unchanged** — no idea-linking prompt/step occurs (AC 5) |
| Idea-link offered, user declines | n/a | ticket/issue already created/updated — unaffected; skill proceeds (AC 2) |
| Idea-link offered, user supplies full key (`EO-32`) | n/a | used directly as `outwardIssue` |
| Idea-link offered, user supplies bare number (`32`) | n/a | user is asked which project it belongs to (never silently guessed, matching Step 4's existing resolution philosophy), combined into a full key |
| `createIssueLink` fails (bad key, API error, permission) | n/a | error surfaced verbatim; the already-created/updated ticket is **not** discarded or rolled back (AC 6) |
| Push declined / MCP unavailable / push fails | fallback emit, no linking possible | **unchanged** — no Epic issue exists yet, so no idea-link step runs |
| `--help`, generate, detect+collect, resolution loop (Steps 1–4 create path) | unchanged | **unchanged** |

Kind of change: **additive** — one new step (new Step 6) inserted after Push; the *update*
path in Step 4 gains one additional captured field (`issueTypeName`) using data its existing
calls already return; Step 5 gains one additional captured field (`issueKey`) using data it
already has at the point it reports success. No existing field, call, or branch is removed.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| `--help` | Step 1 stops | untouched |
| Generate + review loop | Step 2 | untouched |
| Detect MCP + collect NL | Step 3 | untouched |
| Create-path field resolution | Step 4 Block C create bullets | untouched — `issueTypeName` capture already exists there |
| Update-path key resolution | Step 4 Block C update bullets | **extended, not replaced** — the same tool calls run; only one additional field is read from their existing response and stored |
| Push call semantics (`createJiraIssue`/`editJiraIssue` args) | Step 5 | untouched — only the post-success bookkeeping (`$JIRA_FIELDS.issueKey`) is added |
| Fallback emit | Step 6 (current) → Step 7 (renumbered) | content byte-identical; only renumbered and given a new upstream neighbor |
| Prompt user | Step 7 (current) → Step 8 (renumbered) | content unchanged except one additive bullet for the idea-link outcome |

Additive on net. The only risk that can only be *verified*, not proven: that the Epic/
non-Epic guard correctly gates the new step so non-Epic pushes see zero behavior change —
deferred to a concrete check in §6.

---

## 1. Design overview

Insert a new **Step 6 — Offer Jira Idea link (Epic only)** between the existing Push (current
Step 5) and Emit-fallback (current Step 6, renumbered to 7) steps. Precedence of outcomes:

| Tier | Trigger | Result | New? |
|---|---|---|---|
| 1 — Offer | `$JIRA` = `pushed` **and** `$JIRA_FIELDS.issueTypeName` = `"Epic"` | ask to link; resolve reference; call `createIssueLink` | ✅ new |
| 2 — Skip (not an Epic) | `$JIRA` = `pushed` **and** type ≠ `"Epic"` | no prompt, no step (AC 5) | ✅ new (guard only) |
| 3 — Skip (nothing to link) | `$JIRA` ∈ {`unavailable`, `declined`} or Step-5 failure | no prompt, no step — no Jira issue exists | reuses existing precedence from Step 5/6 |

```
guard:  $JIRA == "pushed"  AND  $JIRA_FIELDS.issueTypeName == "Epic"
        (exact string match — issueTypeName is always a canonical Jira type name already
         resolved via metadata/lookup in Step 4, never raw NL text, so no fuzzy match needed)
```

Within Tier 1, reference resolution and the link call:

```
ask:      "This is a Jira Epic. Link it to an existing Jira Idea?" → no → skip (AC 2)
resolve:  full key  [A-Z]+-[0-9]+           → use directly (AC 3)
          bare number  ^[0-9]+$             → ask which project → "<PROJECT>-<number>" (AC 3)
          neither                            → re-prompt for a valid key/number, or abort → skip
link:     createIssueLink(cloudId, type="Polaris work item link",
                           inwardIssue=<Epic key>, outwardIssue=<Idea key>)   (AC 4)
on fail:  surface error verbatim; ticket/issue already created/updated — unaffected (AC 6)
```

**Alternatives considered and rejected:**
- *Collect the idea reference during info-gathering (Step 4), before push* — rejected (see
  top-of-plan design decision): the create path has no real Epic key yet at that point, and
  it would re-introduce resolution logic into the push step, which step 2 deliberately kept
  resolution-free.
- *Store the idea reference as a Jira field/label instead of a formal link* — rejected: AC 4
  explicitly mandates `createIssueLink` with type `"Polaris work item link"`, not a field.
- *Infer the Idea's project from the Epic's project* — rejected: the ticket's own verified
  example pairs `CSS-2649` (Epic) with `EO-32` (Idea) — different projects. Guessing would
  risk linking the wrong issue; matches the "never silently guess" precedent already set in
  Step 4's field resolution.
- *Pre-validate the resolved Idea key with `getJiraIssue` before linking* — rejected: adds a
  tool call and a new `allowed-tools` consideration for no behavior change — `createIssueLink`
  itself surfaces an invalid-reference or API error just as well, and AC 6 only requires the
  failure be *surfaced*, not pre-empted.
- *Call `getIssueLinkTypes` to resolve the link-type name/id dynamically* — rejected: the
  ticket's background already verifies the exact type string and direction live in this
  environment; a discovery call here is unused ceremony for a value that's already known and
  ticket-mandated.
- *Add `createIssueLink` to `allowed-tools`* — rejected: it is a write op on an external
  system, matching the exact rationale STEP-1-REVIEW-1 gave for excluding `createJiraIssue`/
  `editJiraIssue` (explicit permission prompt is the correct safety posture).

---

## 2. `skills/hb-ticket-discuss.md` — specification

One changed unit: the skill file. Three edits (Step 4 extension, Step 5 extension, new Step
6) plus renumbering of the last two steps.

### 2.1 Frontmatter

- **`allowed-tools`, `name`, `argument-hint`** — **unchanged**. No new tool is pre-granted
  (see §1 rejected alternatives) and no new CLI argument is introduced (the offer is
  interactive, matching the skill's existing character).
- **`description`** — *refactor (extend)*. Keep the usage-first first line
  (`/hb-ticket-discuss [--help]`); extend the closing prose to additionally mention: "and,
  when the pushed ticket is a Jira Epic, offers to link it to an existing Jira Idea."

### 2.2 Steps (final shape: 8 steps)

| # | Step | Status |
|---|---|---|
| 1 | Help check | **unchanged** |
| 2 | Generate standalone ticket + review loop | **unchanged** |
| 3 | Detect Jira MCP & collect NL description | **unchanged** |
| 4 | NL resolution & confirmation loop | **extended** (update path gains `issueTypeName` capture) |
| 5 | Push to Jira (primary path) | **extended** (gains `issueKey` capture on success) |
| 6 | Offer Jira Idea link (Epic only) | **new** |
| 7 | Emit ticket (fallback / no-push path) | **renumbered** from 6; content unchanged |
| 8 | Prompt user | **renumbered** from 7; one additive bullet |

**Step 4 (extended) — Block C, Update path.** Add issue-type capture to both existing
bullets, using data their existing calls already return (no new tool call):
- Explicit-key bullet: after "Resolved: `issueIdOrKey` = extracted key," add: "also capture
  the retrieved issue's type name (`fields.issuetype.name`) as `issueTypeName`."
- No-explicit-key bullet: after the user confirms a match, add: "also capture the confirmed
  match's issue type name as `issueTypeName`."
- **`$JIRA_FIELDS` update-path shape becomes**: `{path: "update", cloudId, issueIdOrKey,
  issueTypeName}` (extends the step-2 shape by one field). The create-path shape (`{path:
  "create", cloudId, projectKey, issueTypeName, summary}`) is **unchanged** — it already
  carries `issueTypeName`.

**Step 5 (extended) — on success.** After "set `$JIRA` = `pushed` and report the resulting
issue key and browse URL," add: "also store the issue key as `$JIRA_FIELDS.issueKey`" —
for the create path this is the key `createJiraIssue` returned; for the update path this is
simply `$JIRA_FIELDS.issueIdOrKey` (no new call, just an alias so Step 6 has one uniform
field to read regardless of path). Everything else in Step 5 (the create/update call
arguments, the failure/fall-through-to-emit contract) is **unchanged**.

**Step 6 (new) — Offer Jira Idea link (Epic only).** Contract:
- **Guard**: only run when `$JIRA` = `pushed` **and** `$JIRA_FIELDS.issueTypeName` exactly
  equals `"Epic"`. Otherwise: no prompt, no step — proceed directly to Step 7 (AC 5; also
  covers the case where push was declined/unavailable/failed, since `$JIRA` ≠ `pushed`
  there).
- **Offer**: ask the user: "This is a Jira Epic. Would you like to link it to an existing
  Jira Idea?"
  - **No** → skip linking entirely; proceed to Step 7 (AC 2 — the already-pushed ticket is
    unaffected).
  - **Yes** → prompt: "Provide the Idea's issue key (e.g. `PROJ-123`) or its bare number
    (e.g. `123`)." Capture as `$IDEA_REF`.
- **Resolve `$IDEA_REF` to a full Jira issue key** (AC 3):
  - Matches `[A-Z]+-[0-9]+` → use directly as the Idea key.
  - Matches `^[0-9]+$` (bare number only) → ask the user which project the Idea belongs to
    (e.g. "Which project is Idea #`<n>` in?"); never silently guessed — the ticket's own
    verified example shows the Idea can live in a different project than the Epic. Combine
    as `<PROJECT>-<n>`.
  - Matches neither → tell the user the format wasn't recognized; re-prompt for a valid key
    or bare number, or let the user abort (treated as declining — same as "No" above).
- **Call `createIssueLink`** (AC 4) with: `cloudId` = `$JIRA_FIELDS.cloudId`, `type` =
  `"Polaris work item link"`, `inwardIssue` = `$JIRA_FIELDS.issueKey` (the Epic),
  `outwardIssue` = the resolved Idea key. This direction is the one the ticket's background
  verified live as correct — never reversed.
- **On success**: confirm to the user that the Epic is now linked to the Idea, naming both
  keys.
- **Failure / degradation contract** (AC 6): if `createIssueLink` errors (invalid Idea
  reference, permission, API error) → surface the error verbatim; explicitly state that the
  already-created/updated ticket/issue is unaffected — no retry, no rollback. Proceed to
  Step 7.

**Step 7 (renumbered, unchanged content)** — Emit ticket (fallback / no-push path). Same
guard as before (`$JIRA` ∈ {`unavailable`, `declined`} or Step-5 failure; skipped when
`$JIRA` = `pushed`) — Step 6 sits strictly between Push and this step and does not alter its
guard.

**Step 8 (renumbered, one additive bullet)** — Prompt user. Existing branches (`pushed` vs.
not) unchanged; add: "If an idea link was created in Step 6, additionally confirm the Idea
key it was linked to. If linking was declined or failed, no additional mention is needed
beyond what Step 6 already surfaced."

### 2.3 Reference files / `## Output`

- `## Inputs`, `## Reference Files` (toc injection) — **unchanged**.
- `## Output` — extend one line: on a successful idea link, additionally report the linked
  Idea key; on a failed link attempt, the verbatim error was already surfaced in Step 6 (no
  duplicate reporting needed here).

---

## 3. Integration / wiring

- **Only `skills/hb-ticket-discuss.md` changes.** Steps 1–3 are byte-unchanged.
- Step 4's edit is additive within the existing update-path bullets (no restructuring).
- Step 5's edit is additive at the existing "on success" bullet (no change to the
  create/update call arguments or the failure/fall-through contract).
- New Step 6 is inserted; current Steps 6–7 renumber to 7–8 with content otherwise
  unchanged (Step 8 gains one bullet).
- `interactive-ticket-subflow.md`, `references-toc.md`, `skill-help.md`, `hb-task-create.md`,
  `hb-task-step-add.md`, and everything under `references/` and `scripts/` are **untouched**.
- No manifest, lockfile, build config, or new reference file. No new dependency. No
  `allowed-tools` change (see §1).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-ticket-discuss.md` | **edit** — extend `description`; extend Step 4's update-path bullets (+`issueTypeName` capture); extend Step 5's success bullet (+`issueKey` capture); insert new Step 6 (offer + resolve + `createIssueLink`); renumber current Steps 6→7, 7→8 (Step 8 gains one bullet); extend `## Output`. `## Inputs`, `## Reference Files`, `allowed-tools`, `name`, `argument-hint`, Steps 1–3 stay untouched. |

No other file changes. No dependency manifest or lockfile exists or changes.

---

## 5. Tests

No automated harness exists (markdown-procedure repo) — same posture as steps 0–2. Coverage
is static/structural + runtime-interactive.

**Structural (grep/read-checkable):**
- `allowed-tools` (lines 10–22) is byte-unchanged — `createIssueLink` does **not** appear
  there (write op, requires runtime prompt, per §1).
- Skill has exactly Steps 1–8 after the edit; Steps 1–3 text byte-unchanged from step 2.
- Step 4's update-path bullets mention `issueTypeName` capture; the create-path bullets are
  unchanged (already had it).
- Step 5's success bullet mentions `$JIRA_FIELDS.issueKey`.
- Step 6 exists between Push and Emit, and contains: the Epic-only guard (`issueTypeName ==
  "Epic"`), the full-key regex `[A-Z]+-[0-9]+`, the bare-number handling, `"Polaris work item
  link"`, `inwardIssue`/`outwardIssue` assignment matching Epic=inward/Idea=outward, and a
  failure bullet stating the ticket is not rolled back.
- **Reversed-direction guard**: `grep -A2 -i 'inwardIssue' skills/hb-ticket-discuss.md`
  shows the Epic bound to `inwardIssue`, never the Idea (AC 4 — the ticket's own table shows
  the reversed pairing is wrong).
- **REST guard**: `grep -niE 'rest|curl|/rest/api' skills/hb-ticket-discuss.md` → nothing.
- **Reuse guard**: `grep 'interactive-ticket-subflow' skills/hb-ticket-discuss.md` still
  shows the Step 2 reference only.

**Runtime-interactive (exercised when `/hb-ticket-discuss` is invoked):**
- **Epic create + link happy path**: create an Epic → push succeeds → offered to link → full
  key supplied → `createIssueLink` called with correct direction → confirmation shown (AC 1,
  3, 4).
- **Epic update + link happy path**: update an existing Epic → push succeeds → `issueTypeName`
  correctly captured from Step 4's update path → offered to link → accept.
- **Bare number resolution**: supply a bare number → prompted for project → combined key used
  (AC 3).
- **Decline**: offered → "no" → ticket/issue unaffected, skill proceeds (AC 2).
- **Non-Epic push**: create/update a Story/Task/Bug → push succeeds → **no** idea-link
  prompt appears at all (AC 5).
- **Link failure**: supply an invalid/nonexistent Idea key → `createIssueLink` errors →
  error surfaced verbatim → ticket/issue still intact, skill proceeds to Step 8 (AC 6).
- **Push declined / MCP unavailable / push failure**: unchanged — fallback emit, no idea-link
  step runs (no Jira issue exists to link).
- **Non-regression**: `--help`, generate+review, detect+collect, and Step 4's create-path
  resolution behave exactly as before.

---

## 6. Verification (after implementation)

1. **No build/test gate** — N/A (markdown repo); structural checks are authoritative.
2. **Scope check** — `git status --short` shows only `M skills/hb-ticket-discuss.md` (plus
   this step's `plan.md`/execution artifacts under `.hb/`). Nothing under `references/`,
   `scripts/`, or sibling skills changed.
3. **`allowed-tools` unchanged** — diff lines 10–22 against the pre-edit file; byte-identical.
4. **AC 5 guard** — read Step 6: the guard is `$JIRA == "pushed" AND issueTypeName ==
   "Epic"`; for any other `$JIRA` value or any non-Epic type, Step 6 does not prompt.
5. **AC 4 direction** — read Step 6's `createIssueLink` call: `inwardIssue` is bound to the
   Epic's key (`$JIRA_FIELDS.issueKey`), `outwardIssue` to the resolved Idea key, `type` =
   `"Polaris work item link"` — matching the ticket's verified-correct row, never the
   verified-wrong reversed row.
6. **AC 3 resolution** — read Step 6: full-key pattern used directly; bare-number path
   prompts for a project before combining; unrecognized input re-prompts or aborts (never
   silently guessed).
7. **AC 2 optionality** — read Step 6's "No" branch and the Step-5→Step-7 skip path: ticket
   creation/update completion (Step 5) never depends on Step 6's outcome.
8. **AC 6 failure contract** — read Step 6's failure bullet: error surfaced verbatim, no
   rollback language, flow proceeds to Step 8.
9. **Live demonstration** (requires a connected Atlassian MCP with an Epic issue type and an
   existing Idea): run `/hb-ticket-discuss`, push a new Epic, accept the idea-link offer with
   a real Idea key, and confirm the resulting link's direction in Jira matches
   Epic=inward/Idea=outward.
10. **Non-regression** — diff Steps 1–3 against the pre-edit file: identical; Step 4's
    create-path bullets identical; Step 5's push-call arguments identical; renumbered Step 7
    (emit) content identical to the pre-edit Step 6.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — offered to link when Epic | §1 Tier table, §2.2 Step 6 guard + offer | |
| 1.1 — design decision documented (step vs. field) | top-of-plan design decision, §1 rejected alternatives | chose "additional step appended after push" |
| 2 — linking optional, doesn't block ticket completion | §2.2 Step 6 "No" branch, §0.2 non-regression | Step 5's push contract is untouched by Step 6 |
| 3 — reference resolves to a full key (full key or bare number) | §1 resolve block, §2.2 Step 6 resolution bullets | bare number never silently guessed — prompts for project |
| 4 — `createIssueLink`, type `"Polaris work item link"`, Epic=inward/Idea=outward | §2.2 Step 6 call spec, §6.5, §5 reversed-direction guard | matches ticket's verified-correct row |
| 5 — non-Epic → no prompt/step | §1 Tier 2, §2.2 Step 6 guard, §6.4 | |
| 6 — failure surfaced, ticket not discarded/rolled back | §2.2 Step 6 failure contract, §0.2, §6.8 | Step 5's success already persisted the ticket before Step 6 runs |

---

## 8. Out of scope (per ticket)

- **Creating a new Jira Idea** — this step only links to an **existing** Idea; no
  `createJiraIssue` call for Ideas.
- **Linking issue types other than Epic to an Idea** — the guard in Step 6 is Epic-only by
  design (AC 5).
- **Unlinking or editing an existing Epic↔Idea link** — not built here.
- **Pre-validating the Idea reference via `getJiraIssue`** — rejected in §1; `createIssueLink`
  surfaces invalid references itself.
- **Dynamic link-type discovery via `getIssueLinkTypes`** — rejected in §1; the type string is
  already ticket-verified.
- **Adding `createIssueLink` to `allowed-tools`** — intentionally excluded, matching the
  write-op safety posture from STEP-1-REVIEW-1.
