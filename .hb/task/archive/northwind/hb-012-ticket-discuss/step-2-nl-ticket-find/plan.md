# Step 2 Plan — Natural-language Jira target resolution in `hb-ticket-discuss`

Today (after step 1 + review), `/hb-ticket-discuss` asks the user to choose "create new /
update existing / no" and then resolves each required field one at a time through sequential
prompts. The **motivating case** — a user who types "update the auth refactor story in MOBILE"
and wants to skip the field-by-field interrogation — fails: Step 3's menu requires a formal
choice, Step 4 then asks for each field in sequence (project, type, summary for create; or
just the issue key for update) without ever querying Jira from the description. This is the
**general class**: any case where the user already knows the target naturally (project name,
issue name, or issue key) is forced through redundant prompts. Scope boundary: **one file
changes** (`skills/hb-ticket-discuss.md`) — the shared subflow, sibling skills, and the push
tool calls are untouched. Externally observable effect once this lands: the user describes the
target once in plain English; the agent resolves it against the live Jira, presents the
resolved field set for confirmation, and loops on decline — no field-by-field interrogation.

Source ticket: `./ticket.md`. Builds on the **shipped + reviewed** work from step 1
(`skills/hb-ticket-discuss.md` — Steps 1–6 including the review loop in Step 2,
capability-first MCP detection in Step 3, and platform-agnostic push instructions in Step 4).
This plan targets the file as it exists **now** (post step-1 review, confirmed by reading the
file in full during planning).

> **Design decision — NL resolution is a separate new Step 4; the push call is preserved
> unchanged as new Step 5.** The ticket's out-of-scope clause: "Implementing the actual
> `createJiraIssue` / `editJiraIssue` call — that is step 1; this step only resolves and
> confirms the field values." The cleanest factoring is: insert a new Step 4 (NL resolution
> + confirmation loop) between Step 3 (detect + collect) and the renumbered Step 5 (push).
> Step 5 receives pre-resolved `$JIRA_FIELDS` and just calls the tool — no resolution logic.
> This preserves the step-1 push contract exactly. See §1 and §7.

---

## 0. Current-state facts (verified during planning)

Confirmed by reading the files, not assumed:

- **Skill as shipped (post step-1 review)** — `skills/hb-ticket-discuss.md` (read in full).
  Six steps: 1 help, 2 generate+review loop, 3 detect+offer 3-way menu, 4 field-by-field
  resolution → push call, 5 fallback emit, 6 prompt user. Frontmatter: `name`,
  `argument-hint: "[--help]"`, `description` (mentions Jira push + stdout fallback).
- **`allowed-tools` as of now** (file line 10, multiline YAML block — 9 entries):
  six `/tmp` grants + three MCP tools:
  `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources`,
  `mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects`,
  `mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata`.
  `createJiraIssue` and `editJiraIssue` are **intentionally absent** (STEP-1-REVIEW-1:
  write ops require explicit permission prompts — correct safety posture; unchanged here).
- **Step 3 current wording** (detected by capability; offers "create new / update existing /
  no" as a 3-way menu). This is what changes — the offer becomes a NL prompt.
- **Step 4 current wording** — for create: resolves `cloudId` → `projectKey` →
  `issueTypeName` → `summary` sequentially, then calls the create tool; for update: prompts
  directly for `issueIdOrKey`, then calls the edit tool. Resolution and push are in the same
  step. This step splits them.
- **Missing tools for NL resolution** (verified in the session's deferred tool list):
  - `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql` — JQL search for finding
    issues matching a description.
  - `mcp__claude_ai_Atlassian_Rovo__getJiraIssue` — retrieve a specific issue by key (when
    the user supplies an explicit key in their NL description).
  Both are **read-only** — consistent with REVIEW-1 rationale (pre-approve read-only
  discovery; prompt for write ops). Added to `allowed-tools`.
- **No automated harness** — markdown-procedure repo (confirmed by step-0 and step-1
  execution summaries). Verification is static/structural.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| "create a Task in Northwind backend" | 3-way menu + sequential prompts | NL parsed → project via `getVisibleJiraProjects` → type via `getJiraProjectIssueTypesMetadata` → summary proposed → confirm |
| "update the auth refactor story in MOBILE" | 3-way menu, then prompt for key | NL parsed → JQL search → match presented → confirm |
| "update MOBILE-412" (explicit key) | same as above | NL parsed, key extracted → `getJiraIssue(MOBILE-412)` → confirm title → proceed |
| Ambiguous (multiple project/issue matches) | not applicable | numbered list presented; user picks (AC 7) |
| Unresolved field (can't infer, not in search) | prompted directly | surfaced as unresolved, prompted explicitly (AC 6) |
| Decline resolved set | not applicable | refine description (re-resolve) or supply exact values (AC 5) |
| "no" / MCP absent / `--help` / generate | unchanged | unchanged |
| Push call (`createJiraIssue` / `editJiraIssue`) | in Step 4 | preserved verbatim in new Step 5 |

Kind of change: **additive/refactor** — new Step 4 inserted; current Steps 4/5/6 renumbered
to 5/6/7 with content unchanged. Push calls unmodified.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| `--help` | Step 1 stops | Step 1 untouched |
| Ticket generation + review loop | Step 2 (subflow + loop) | Step 2 untouched |
| Jira push call | Step 4 calls create/edit tool | Preserved verbatim as new Step 5 |
| Stdout fallback emit | Step 5 | Preserved verbatim as new Step 6 |
| Prompt user | Step 6 branches on `$JIRA` | Preserved as new Step 7; unchanged |
| `$JIRA` state machine | {create, update, declined, unavailable, pushed} | All values preserved; `$JIRA_FIELDS` is additive |

Additive on net. Risk limited to: (a) NL resolution correctly routes to create vs update path
and (b) resolved `$JIRA_FIELDS` are correctly passed to push — both verifiable by reading
the skill. The push call itself cannot regress because it is copied verbatim.

---

## 1. Design overview

Insert a **NL resolution + confirmation loop** as new Step 4, between detect/collect (Step 3)
and push (new Step 5). Control flow:

```
Step 3: detect MCP → if available, prompt for NL description (or "no")
Step 4: NL Resolution Loop:
  parse $NL_DESC → infer path (create/update) + partial fields
  query Jira to fill remaining fields
  handle ambiguous → present choices; unresolved → prompt
  present resolved field set
  on confirm → set $JIRA_FIELDS, break
  on decline → refine description (re-enter) or supply exact values (confirm, break)
Step 5: Push — call create/edit tool with $JIRA_FIELDS (resolution-free)
Step 6: Fallback emit (unchanged)
Step 7: Prompt user (unchanged)
```

**Step 3 modification:** Replace the 3-way "create new / update existing / no" menu with a
request for a NL description. "no" remains valid and routes to fallback.

**Step 4 — NL resolution precedence:**

| Resolution tier | Trigger | Action |
|---|---|---|
| Explicit issue key (`[A-Z]+-[0-9]+` in NL) | update intent, key found | `getJiraIssue(key)` → confirm title/status |
| NL-described issue (no explicit key) | update intent, no key | `searchJiraIssuesUsingJql` with derived JQL → present matches |
| NL-described project/type (create) | create intent | `getVisibleJiraProjects` match → `getJiraProjectIssueTypesMetadata` → propose summary |
| Unresolved field | required field can't be inferred | surface explicitly, prompt — never guess |
| Ambiguous | multiple project or issue matches | numbered list; user picks — never auto-select |

```
precedence: explicit key ≥ JQL search match ≥ project/type lookup ≥ unresolved prompt
(tie-break: prefer most specific match; equal confidence → present choices)
```

**`$JIRA_FIELDS` structure passed to Step 5:**
- create: `{path: "create", cloudId, projectKey, issueTypeName, summary}`
- update: `{path: "update", cloudId, issueIdOrKey}`

**Alternatives considered and rejected:**
- *Keep the 3-way menu + add NL only for update issue-search* — the ticket's motivating case
  is NL for the whole target (create path too); a partial NL path leaves create mechanical.
  Rejected.
- *Single combined "detect + NL resolve" step* — conflates MCP detection (may exit to
  fallback) with the resolution loop (may iterate); cleaner as two steps. Rejected.
- *Use `getTeamworkGraphContext`* — designed for relationship/connection reasoning between
  Atlassian entities, not for straightforward project/issue lookup. Overkill here. Rejected.
- *Re-add `createJiraIssue`/`editJiraIssue` to `allowed-tools`* — STEP-1-REVIEW-1
  established the write-op safety posture; that decision is unchanged. Rejected.

---

## 2. `skills/hb-ticket-discuss.md` — specification

One changed unit: the skill file.

### 2.1 Frontmatter

- **`allowed-tools`** — *refactor (extend)*. Append two new read-only tools to the existing
  nine entries (preserving all six `/tmp` grants and the three original discovery tools):
  ```
  mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql
  mcp__claude_ai_Atlassian_Rovo__getJiraIssue
  ```
  Does **not** add `createJiraIssue`/`editJiraIssue` (write ops — per REVIEW-1).
- `name`, `argument-hint`, `description` — **unchanged** (no new arguments; the NL input is
  still interactive).

### 2.2 Steps (final shape: 7 steps)

| # | Step | Status |
|---|---|---|
| 1 | Help check | **unchanged** |
| 2 | Generate standalone ticket + review loop | **unchanged** |
| 3 | Detect Jira MCP & collect NL description | **modified** (was: 3-way menu) |
| 4 | NL resolution & confirmation loop | **new** |
| 5 | Push to Jira (primary path) | **renumbered** from 4; push call preserved verbatim |
| 6 | Emit ticket (fallback / no-push path) | **renumbered** from 5; content unchanged |
| 7 | Prompt user | **renumbered** from 6; content unchanged |

**Step 3 (modified) — Detect Jira MCP & collect NL description.** Contract:
- Detection logic (by capability, Rovo as example, graceful absent-path) — **unchanged**.
- If unavailable: `$JIRA = unavailable`, skip to Step 6. **Unchanged.**
- If available: ask the user to describe the Jira target in natural language, and tell
  them the resolved details will be shown for confirmation before anything is created or
  updated. Examples to include in the prompt:
  "create a Task in the MOBILE project for the auth refactor", "update MOBILE-412",
  "update the login epic in BACKEND". "no" remains valid → `$JIRA = declined`, skip to
  Step 6. Otherwise store description as `$NL_DESC` and continue to Step 4.
- The old "create new / update existing / no" menu is **removed**.

**Step 4 (new) — NL Resolution & Confirmation Loop.** Contract:

```
Loop until user accepts or aborts:

  A. PARSE $NL_DESC:
     - Determine path: create intent (create/new/add/file a …) or update intent
       (update/edit/change/find/fix …).
     - Extract any partial fields mentioned:
       - Issue key pattern [A-Z]+-[0-9]+ → explicit issueIdOrKey candidate
       - Project name or key fragment → projectKey candidate
       - Issue type name (Story, Task, Bug, Epic …) → issueTypeName candidate
       - Summary / title text → summary candidate
       - Site name or URL → cloudId candidate

  B. RESOLVE cloudId:
     - Call the MCP's list-accessible-sites tool.
       (Atlassian Rovo example: mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources)
     - If exactly one site: use it. If multiple: prompt user to choose.

  C. RESOLVE remaining fields by path:

     [Create path]
     - projectKey:
       - If project candidate in NL → filter getVisibleJiraProjects by name match.
         Unambiguous → use it. Multiple matches → numbered list, user picks.
         No matches / not mentioned → prompt user to choose from full project list.
       - (Atlassian Rovo example: mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects)
     - issueTypeName:
       - If type candidate in NL → match against getJiraProjectIssueTypesMetadata for the
         resolved project. Unambiguous → use it. Multiple / unclear → present list.
         Not mentioned → propose "Task" and confirm.
       - (Atlassian Rovo example: mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata)
     - summary:
       - If clearly stated in NL → extract and propose for confirmation.
         Otherwise → propose a concise title, confirm. Never silently guessed (AC 6).

     [Update path]
     - If explicit key in NL ([A-Z]+-[0-9]+):
       → Call the MCP's get-issue tool to retrieve the issue and confirm its title/status.
         (Atlassian Rovo example: mcp__claude_ai_Atlassian_Rovo__getJiraIssue)
       → Resolved: issueIdOrKey = the extracted key.
     - If no explicit key:
       → Derive a JQL query from the NL description (e.g. project = "MOBILE" AND
         text ~ "auth refactor" ORDER BY updated DESC).
       → Call the MCP's JQL search tool.
         (Atlassian Rovo example: mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql)
       → 1 match → present key + title for confirmation.
       → Multiple matches → numbered list, user picks. (Never auto-select — AC 7)
       → 0 matches → tell the user, prompt for a key or a more specific description.

  D. PRESENT resolved field set:
     - Create: "Resolved: CREATE in <projectKey> as <issueTypeName> — '<summary>'"
     - Update: "Resolved: UPDATE <issueKey> — '<issue title>'"
     Ask: "Does this look right?"

  E. USER RESPONSE:
     - Accept → set $JIRA_FIELDS = resolved set,
                set $JIRA = "create" or "update", break loop.
     - Refine description → update $NL_DESC, go to A.
     - Supply exact values → accept the values the user provides as $JIRA_FIELDS,
       present for final confirmation, on accept break loop.
     - Abort → set $JIRA = "declined", skip to Step 6.
```

Failure / degradation contract:
- If a query tool errors → surface the error, prompt user to supply that field directly
  (never dead-end).
- If 0 JQL matches and user cannot resolve → offer to abort (`$JIRA = "declined"` → Step 6).

**Step 5 (renumbered, push preserved) — Push to Jira (primary path).** Contract:
- Only when `$JIRA ∈ {create, update}`. Uses `$JIRA_FIELDS` set by Step 4. No resolution.
- `$JIRA_FIELDS.path = create` → call the MCP's create-issue tool with `cloudId`,
  `projectKey`, `issueTypeName`, `summary`, `description` = full `$WRITTEN_TICKET` content,
  `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`.)
- `$JIRA_FIELDS.path = update` → call the MCP's edit-issue tool with `cloudId`,
  `issueIdOrKey`, `fields: { description: <full $WRITTEN_TICKET content> }`,
  `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__editJiraIssue`.)
- On success: `$JIRA = "pushed"`, report issue key and browse URL.
- On failure: surface error verbatim, fall through to Step 6.

**Steps 6 and 7** — renumbered only; content identical to current Steps 5 and 6.

### 2.3 Reference files / `## Output`

- `## Inputs`, `## Reference Files` (toc injection), `## Output` — **unchanged**.

---

## 3. Integration / wiring

- **Only `skills/hb-ticket-discuss.md` changes.**
- Steps 1–2 are byte-unchanged.
- Step 5's push call text is taken verbatim from current Step 4 — resolution logic removed
  (extracted to new Step 4), not deleted.
- `interactive-ticket-subflow.md`, `hb-task-create.md`, `hb-task-step-add.md`, and
  everything under `references/` and `scripts/` are **untouched**.
- No manifest, lockfile, build config, or new reference file. No new dependency.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-ticket-discuss.md` | **edit** — extend `allowed-tools` (+2 read-only search tools); modify Step 3 (3-way menu → NL prompt); add new Step 4 (NL resolution + confirmation loop); renumber current Steps 4→5, 5→6, 6→7 (content of new 5/6/7 unchanged except renumbering). `## Inputs`, `## Reference Files`, `## Output`, Steps 1–2 untouched. |

No other files. No manifest or lockfile changes.

---

## 5. Tests

No automated harness (markdown-procedure repo). Coverage is static/structural +
runtime-interactive.

**Structural (grep/read-checkable):**
- `allowed-tools` contains all 5 MCP tools (3 original + 2 new search tools) and all 6
  `/tmp` grants; does NOT add `createJiraIssue`/`editJiraIssue` (write ops).
- Skill has exactly Steps 1–7 after the edit; Steps 1–2 text unchanged from step-1-review.
- Step 3 no longer contains "create new / update existing / no" as a literal menu; instead
  prompts for NL description.
- Step 4 contains: `$NL_DESC`, `searchJiraIssuesUsingJql`, `getJiraIssue`, create/update
  path resolution logic, ambiguity → numbered list, unresolved → explicit prompt,
  confirmation loop with refine/exact-values branches.
- Step 5 push call: capability-first language + Rovo example parenthetical (preserved from
  STEP-1-REVIEW-4).
- **REST guard**: `grep -niE 'rest|curl|/rest/api' skills/hb-ticket-discuss.md` → nothing.
- **Reuse guard**: `grep 'interactive-ticket-subflow' skills/hb-ticket-discuss.md` shows
  Step 2 still references the subflow (not inlined).

**Runtime-interactive (exercised when `/hb-ticket-discuss` is invoked):**
- **Create NL happy path**: "create a Bug in PROJECT" → resolves projectKey + issueTypeName →
  proposes summary → confirm → pushed (AC 1, 2, 2a–2c).
- **Update by explicit key**: "update PROJECT-123" → `getJiraIssue` → confirm title →
  accept → pushed (AC 2d).
- **Update by NL description**: "update the auth refactor story in MOBILE" → JQL search →
  match presented → accept → pushed (AC 2d).
- **Ambiguous project**: multiple `getVisibleJiraProjects` matches → list presented, user
  picks (AC 7).
- **Ambiguous issue**: JQL returns multiple matches → list presented, user picks (AC 7).
- **Unresolved summary**: no summary inferable → prompted explicitly (AC 6).
- **Decline + refine**: decline resolved set → refined description → re-resolve (AC 5a).
- **Decline + exact values**: decline → supply exact values directly → confirm → proceed (AC 5b).
- **"no"** from Step 3 → `$JIRA = declined` → fallback emit (unchanged).
- **MCP absent** → fallback emit (unchanged).
- **Non-regression**: `--help` and generate (Steps 1–2) unchanged; push call in Step 5 same.

---

## 6. Verification (after implementation)

1. **No automated build/test gate** — N/A (markdown repo). Structural checks are authoritative.
2. **Scope check** — `git status --short` shows only `M skills/hb-ticket-discuss.md` (plus
   `.hb/` artifacts for this step). Nothing under `references/`, `scripts/`, or sibling
   skills changed.
3. **REST guard** — `grep -niE 'rest|curl|/rest/api|https?://[^ )]*api' skills/hb-ticket-discuss.md`
   returns nothing.
4. **`allowed-tools` completeness** — `grep -n 'allowed-tools' skills/hb-ticket-discuss.md`
   shows 6 `/tmp` grants + 5 MCP tools (3 original + `searchJiraIssuesUsingJql` +
   `getJiraIssue`). Confirm `createJiraIssue`/`editJiraIssue` are **absent** (intentional).
5. **Step 3 NL prompt** — read Step 3: no "create new / update existing / no" literal menu;
   instructs the agent to ask for a NL description; "no" still routes to fallback.
6. **Step 4 NL resolution** — read Step 4 and confirm: `$NL_DESC` variable; parse/infer
   create vs update; both explicit-key and JQL-search paths for update; both project-match
   and type-match paths for create; ambiguity → choice list; unresolved → explicit prompt;
   confirmation loop with refine + exact-values + abort branches.
7. **Step renumbering** — Steps 1–7 present; Step 5 push language is capability-first with
   Rovo parenthetical (preserved from STEP-1-REVIEW-4).
8. **Non-regression** — Steps 1–2 text unchanged; subflow still referenced (`grep
   'interactive-ticket-subflow' skills/hb-ticket-discuss.md` → Step 2 hit only).

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — accepts NL specifying some/all/none of required fields | §2.2 Step 3 (collects NL), Step 4 (partial fields OK — unresolved fields prompted) | |
| 2 — resolves via Jira MCP, not guessing | §2.2 Step 4 — queries `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`, `searchJiraIssuesUsingJql`, `getJiraIssue` | |
| 2a — described project → real `projectKey` | §2.2 Step 4 create path: `getVisibleJiraProjects` name-filter + match | |
| 2b — described type → valid `issueTypeName` | §2.2 Step 4 create path: `getJiraProjectIssueTypesMetadata` | |
| 2c — site → concrete `cloudId` | §2.2 Step 4: `getAccessibleAtlassianResources` (unchanged from step-1) | |
| 2d — described issue → concrete `issueIdOrKey` | §2.2 Step 4 update path: explicit key → `getJiraIssue`; described → `searchJiraIssuesUsingJql` | |
| 3 — presents resolved field set for confirmation | §2.2 Step 4 block D: resolved set shown before any create/update | |
| 4 — accept path: resolved values flow to push | §2.2 Step 4 block E accept: sets `$JIRA_FIELDS`; Step 5 uses `$JIRA_FIELDS` | |
| 5a — decline + refine NL → re-resolve | §2.2 Step 4 block E "Refine description" branch | |
| 5b — decline + exact values | §2.2 Step 4 block E "Supply exact values" branch | |
| 6 — unresolved fields prompted, never fabricated | §2.2 Step 4 block C: "surface explicitly, prompt" rule; summary never silently guessed | |
| 7 — ambiguous matches → choice list, not auto-select | §2.2 Step 4 block C: multiple matches → numbered list | |
| 8 — consistent with step 1 conventions; no raw Jira REST | §4 (one file changed), §6.3 (REST grep), §6.8 (reuse guard); platform-agnostic language preserved from STEP-1-REVIEW-4 | |

---

## 8. Out of scope (per ticket)

- **The actual `createJiraIssue` / `editJiraIssue` push calls** — step-1; Step 5 of this
  plan preserves them unchanged.
- **NL interpretation of the ticket body/description** — only the push *target* fields are
  resolved from NL; the ticket content is always `$WRITTEN_TICKET` verbatim.
- **Bidirectional sync / importing Jira issues back into hashbuild tickets** — not in scope.
- **Raw Jira REST API integration path** — not in scope.
- **Adding `createJiraIssue`/`editJiraIssue` to `allowed-tools`** — intentionally excluded
  per STEP-1-REVIEW-1's write-op safety posture.
- **Extracting a shared NL-resolve subflow** — only one caller; deferred (same precedent as
  step-1 §8 on `jira-push-subflow`).
