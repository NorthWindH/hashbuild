# Step 1 Plan — Add Jira push to `hb-ticket-discuss`

Today `/hb-ticket-discuss` generates a standalone `ticket.md` at `/tmp/ticket.md`
and prints it to stdout for copy-paste (step 0, shipped). The **motivating case** —
a user who has just drafted a ticket and wants it to *become* a Jira issue without
leaving the flow — fails: there is no path from the generated ticket to Jira, so the
user must manually copy the stdout block into Jira's UI. This step closes that gap by
adding an offer-to-push interaction whose **primary path** creates/updates a Jira
issue through the connected Atlassian (Jira) MCP (the generated ticket as the issue
description) and whose **fallback path** is exactly the existing stdout emit. This is
the **general class**: completing task ACs 4 and the Jira remainder of 5. Headline
scope boundary: **one file changes** (`skills/hb-ticket-discuss.md`) — the shared
interactive subflow and its two sibling callers are untouched, and **no raw Jira REST
API** is introduced. Externally observable effect once this lands: after generating a
ticket the skill asks "push to Jira?", and on success reports a real issue key/URL.

Source ticket: `./ticket.md`. Builds on the **shipped** work from step 0
(`skills/hb-ticket-discuss.md` — the 4-step linear skill: help → generate via
subflow → emit → prompt) and the state it left behind (`allowed-tools` grants
`/tmp` Read/Write/Edit only; no SDK, no git). This plan targets that file as it
exists **now**.

> **Design decision — capability-based MCP discovery, not a hardcoded tool name.**
> The ticket's AC 4 ("detects MCP availability gracefully — absence leads to fallback,
> not an error") pulls against AC 2's need to name a concrete create/update tool. A
> skill that hardcodes `mcp__claude_ai_Atlassian_Rovo__createJiraIssue` works in *this*
> environment but breaks for any user whose Jira MCP is connected under a different
> server name. Resolution: the **skill body describes the capability** ("a connected
> Atlassian/Jira MCP tool that creates a Jira issue") and instructs the executing agent
> to discover it; the **canonical `mcp__claude_ai_Atlassian_Rovo__*` names are cited as
> the verified reference implementation** (§0) and pre-granted in `allowed-tools` as a
> permission optimization. The single guard that makes this correct: if no such tool is
> discoverable, the skill takes the fallback path — never errors (AC 4). See §1 (design)
> and §7 (AC traceability).

---

## 0. Current-state facts (verified during planning)

Confirmed by reading the files, not assumed:

- **Skill as shipped** — `skills/hb-ticket-discuss.md` (read in full). Frontmatter:
  `name: hb-ticket-discuss`, `argument-hint: "[--help]"`, usage-first `description`,
  and `allowed-tools: Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*)
  Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)` (line 9 — **no** SDK/git
  grant, **no** MCP grant). Body: `## Inputs`, `## Reference Files`
  (`!`cat …/references-toc.md``), `## Steps` with **Step 1** help check (delegates to
  `references/skill-help.md`, stops), **Step 2** generate (sets `$TARGET_PATH=/tmp`,
  injects `references/interactive-ticket-subflow.md`, sets `$WRITTEN_TICKET=/tmp/ticket.md`),
  **Step 3** emit (reads `$WRITTEN_TICKET`, prints fenced block; line 46 already names
  itself "the fallback output path step 1 will keep"), **Step 4** prompt; `## Output`.
- **The fallback already exists.** Step 0's Step 3 is verbatim the AC-3 fallback. This
  step does not invent stdout emit — it **reuses** it and gates it behind the no-MCP /
  no-push branch.
- **Subflow is reused untouched** — `skills/references/interactive-ticket-subflow.md`
  (read in full): guard → prompt → transform → write `$TARGET_PATH/ticket.md`. No side
  effects, no SDK. This step adds nothing to it (matches ticket out-of-scope).
- **Sibling conventions** — `skills/hb-task-create.md` (read in full) is the structural
  model: frontmatter shape, `## Inputs` table, `## Reference Files` toc injection,
  numbered `## Steps`, `## Output`. `hb-task-create`'s `allowed-tools` shows the
  established pattern of listing every tool family the skill calls.
- **Atlassian MCP tools — verified live in this environment** (schemas loaded via
  ToolSearch during planning). Exact names and required fields:

  | Tool | Required fields | Use |
  |---|---|---|
  | `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources` | (none) | resolve `cloudId` / list sites |
  | `mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects` | `cloudId` | list/confirm `projectKey` |
  | `mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata` | `cloudId`, `projectIdOrKey` | list valid `issueTypeName`s |
  | `mcp__claude_ai_Atlassian_Rovo__createJiraIssue` | `cloudId`, `projectKey`, `issueTypeName`, `summary` | **create** path (description optional; `contentFormat: "markdown"`) |
  | `mcp__claude_ai_Atlassian_Rovo__editJiraIssue` | `cloudId`, `issueIdOrKey`, `fields` | **update** path (set `fields.description`) |

  `createJiraIssue` accepts `description` as a Markdown string with
  `contentFormat: "markdown"` — so the generated ticket content drops in directly.
- **No build/test harness** exists in this repo (confirmed by step 0 execution summary;
  skills are markdown procedures). Verification is static/structural + runtime-interactive.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| Jira MCP present, user opts to create | no path to Jira; manual copy-paste | new issue created, description = ticket; key/URL reported |
| Jira MCP present, user opts to update | (same) | existing issue's description replaced; key/URL reported |
| Jira MCP present, user declines push | always printed stdout | ticket emitted to stdout for copy-paste |
| **No Jira MCP** | always printed stdout | ticket emitted to stdout **+ told MCP was unavailable** (unchanged behavior, clarified) |
| `--help` / generate steps | help stops; generate writes `/tmp/ticket.md` | **unchanged** |

Kind of change: **additive** — one new interaction branch plus widened `allowed-tools`.
No existing step's contract is removed; the stdout emit is preserved and re-homed under
the no-push branch.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| `--help` | delegates to `skill-help.md`, stops | Step 1 untouched |
| ticket generation | subflow writes `/tmp/ticket.md` | Step 2 untouched; subflow file untouched |
| stdout copy-paste | always printed | preserved verbatim as the fallback/no-push branch (AC 3) |
| sibling skills `hb-task-create` / `hb-task-step-add` | call subflow | not edited; subflow not edited |

The only behavior that *moves* is the stdout emit (from unconditional → no-push branch).
Risk it can only be **verified, not proven**: that the agent correctly detects a missing
MCP and degrades instead of erroring (AC 4) — deferred to a concrete check in §6.

---

## 1. Design overview

Insert the Jira interaction **after** generation (Step 2) and **before** the prompt.
The control flow is a precedence over three outcomes:

| Tier | Trigger | Result | New? |
|---|---|---|---|
| 1 — Push (primary) | Jira MCP discoverable **and** user opts to push | create or update issue via MCP; report key/URL | ✅ new |
| 2 — No-push fallback | Jira MCP discoverable but user declines | emit ticket to stdout for copy-paste | reuses step-0 emit |
| 3 — Unavailable fallback | no Jira MCP discoverable | emit ticket to stdout **+ state MCP unavailable** | reuses step-0 emit + note |

```
precedence:  MCP present + opt-in  >  MCP present + decline  >  MCP absent
             (tie-break: graceful — any failure/uncertainty falls right, never errors)
```

Within tier 1, a sub-choice (create vs update) and field resolution:

```
create:  resolve cloudId → projectKey → issueTypeName → summary → createJiraIssue(description=ticket, markdown)
update:  resolve cloudId → issueIdOrKey → editJiraIssue(fields.description=ticket, markdown)
```

Field-resolution rule (AC 2.1): each required field is **prompted for when not
determinable** — never silently guessed. `cloudId` is resolved from
`getAccessibleAtlassianResources` (auto-pick if exactly one site, else prompt);
`projectKey`/`issueTypeName` are offered from the metadata tools then confirmed;
`summary` is not derivable from the ticket's Background/AC/Out-of-scope shape, so it is
proposed-and-confirmed or prompted.

**Alternatives considered and rejected:**
- *Hardcode `mcp__…__createJiraIssue` in the skill body* — brittle across users with a
  differently-named Jira MCP; violates the spirit of AC 4. Rejected (see top-of-plan
  design decision).
- *Raw Jira REST API with credential handling* — explicitly forbidden by AC 5 and the
  ticket out-of-scope. Rejected.
- *Add a `--push` / `--jira-key` CLI flag* — adds surface area and an Inputs-table
  contract for a flow that is naturally interactive; the offer is a prompt, matching the
  skill's existing interactive character. Rejected (keep it conversational).
- *Always emit to stdout even on successful push* — redundant noise after a successful
  create; AC 2.2 only requires reporting the key/URL. Rejected (emit is the fallback,
  not unconditional).
- *Add a new shared `jira-push-subflow.md` reference* — only one skill uses it; a shared
  subflow earns its keep when ≥2 callers exist (cf. `interactive-ticket-subflow`).
  Rejected for now (keep inline; note as a future extraction in §8).

---

## 2. `skills/hb-ticket-discuss.md` — specification

One changed unit: the skill file. Mirror sibling idioms (numbered prose steps, no code).

### 2.1 Frontmatter

- **`allowed-tools`** — *refactor (extend)*. Append the five verified Jira tool names
  from §0 to the existing `/tmp` grants, on the same line:

  ```
  allowed-tools: Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*) mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata mcp__claude_ai_Atlassian_Rovo__createJiraIssue mcp__claude_ai_Atlassian_Rovo__editJiraIssue
  ```

  Contract: pre-authorizes the canonical Jira MCP tools so the happy path runs without a
  permission prompt. If a user's Jira MCP is named differently, the entries simply match
  nothing and the agent gets a normal permission prompt — **no failure** (graceful).
- **`description`** — *refactor (extend)*. Keep the usage-first first line
  (`/hb-ticket-discuss [--help]`); extend the prose to mention "then offers to push the
  ticket to a connected Jira (Atlassian MCP), falling back to stdout copy-paste."
- `name`, `argument-hint` — **unchanged** (no new args; the push is interactive).

### 2.2 Steps (final shape)

| # | Step | Status |
|---|---|---|
| 1 | Help check → `skill-help.md`, stop | **unchanged** |
| 2 | Generate standalone ticket (subflow → `/tmp/ticket.md`, set `$WRITTEN_TICKET`) | **unchanged** |
| 3 | Detect Jira MCP & offer to push | **new** |
| 4 | Push to Jira — primary path | **new** |
| 5 | Emit ticket — fallback / no-push path | refactor of step-0 Step 3 |
| 6 | Prompt user | refactor of step-0 Step 4 |

**Step 3 — Detect Jira MCP & offer to push.** Contract:
- Determine whether a connected Atlassian/Jira MCP tool capable of creating a Jira issue
  is available (in this environment: `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`;
  generally, discover the connected Jira MCP's create-issue tool).
- If **none available** → set `$JIRA=unavailable`, skip to Step 5 (AC 4: this is the
  graceful path, not an error).
- If available → ask the user: "Push this ticket to Jira? (create new / update existing
  / no)". Record the choice. "no" → set `$JIRA=declined`, go to Step 5. Otherwise set
  `$JIRA=create` or `$JIRA=update`, continue to Step 4.

**Step 4 — Push to Jira (primary).** Contract (only when `$JIRA ∈ {create, update}`):
- **Resolve `cloudId`** via `getAccessibleAtlassianResources`; if exactly one site, use
  it, else prompt the user to choose. (If the user supplied a site URL, its hostname may
  be passed directly per the tool's guidance.)
- **create**: resolve `projectKey` (offer choices via `getVisibleJiraProjects`, confirm),
  `issueTypeName` (offer via `getJiraProjectIssueTypesMetadata`, default `Task`), and
  `summary` (propose a concise line and confirm, or prompt — it is **not** determinable
  from the ticket body, so never silently guessed: AC 2.1). Call `createJiraIssue` with
  `cloudId`, `projectKey`, `issueTypeName`, `summary`, `description` = full
  `$WRITTEN_TICKET` content, `contentFormat: "markdown"`.
- **update**: prompt for the target `issueIdOrKey` (e.g. `PROJ-123`). Call `editJiraIssue`
  with `cloudId`, `issueIdOrKey`, `fields: { description: <ticket content> }`,
  `contentFormat: "markdown"`.
- **On success** (AC 2.2): report the resulting issue **key and browse URL** to the user.
- **Failure / degradation contract**: if a tool call errors (auth, permission, bad
  field), surface the error verbatim, then **fall through to Step 5** so the user still
  gets the copy-paste ticket — the skill never dead-ends.

**Step 5 — Emit ticket (fallback / no-push).** Reads `$WRITTEN_TICKET` and prints its
full content in a fenced block (verbatim from step-0 Step 3). Reached when
`$JIRA ∈ {unavailable, declined}` or after a Step-4 failure. When `$JIRA=unavailable`,
additionally state that **no Jira MCP was available, so the ticket is emitted for
copy-paste** (AC 3, AC 4). On a successful push (Step 4 reported a key/URL), this step is
**skipped**.

**Step 6 — Prompt user.** Branch the closing message: on successful push, confirm the
issue key/URL and that nothing was written to `.hb/`; otherwise keep the step-0 message
(standalone ticket above, copy-paste it; nothing written to `.hb/`).

### 2.3 Reference files / `## Output`

- `## Reference Files` (toc injection) — **unchanged** (the shared toc is not per-skill;
  no Jira-specific reference is added — see §1 rejected alternatives).
- `## Output` — extend one line: report the Jira issue key/URL when a push succeeded,
  else the emitted ticket + scratch path. Errors surfaced verbatim (unchanged contract).

---

## 3. Integration / wiring

- **Call site edited**: only inside `skills/hb-ticket-discuss.md` — Steps 3–6 replace the
  former Steps 3–4, and the frontmatter `allowed-tools`/`description` lines are extended.
- **Public/shared surfaces preserved**: `interactive-ticket-subflow.md`,
  `references-toc.md`, `skill-help.md`, `hb-task-create.md`, `hb-task-step-add.md`, and
  everything under `scripts/`, `references/`, and `.hb/` are **untouched** — keeping the
  two sibling subflow callers green and honoring the ticket out-of-scope.
- **No build/config/dependency wiring** changes: there is no manifest or lockfile; the
  skill is self-contained markdown. MCP tools are provided by the user's connected
  Atlassian server, not declared by this repo.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-ticket-discuss.md` | **edit** — extend `allowed-tools` (+5 Jira MCP tools) and `description`; replace Steps 3–4 with new Steps 3–6 (detect+offer → push → fallback emit → branched prompt); extend `## Output`. `## Inputs`, `## Reference Files`, Steps 1–2, `name`, `argument-hint` stay untouched. |

No other file changes. No dependency manifest or lockfile exists or changes. No new
reference file is added (toc unchanged).

---

## 5. Tests

No automated harness exists (markdown-procedure repo) — same posture as step 0. Coverage
is static/structural + runtime-interactive:

- **Structural (grep/read-checkable):**
  - Frontmatter `allowed-tools` contains the five `mcp__claude_ai_Atlassian_Rovo__*`
    entries **and** retains all six `/tmp` grants.
  - Body has exactly Steps 1–6 with the new headings; Step 1 (help) and Step 2 (generate
    via subflow) are byte-unchanged from step 0.
  - **Negative / guard**: `grep -niE 'rest|/rest/api|curl|http' skills/hb-ticket-discuss.md`
    returns nothing — no raw Jira REST path (AC 5).
  - **Reuse guard**: the skill still *references* `interactive-ticket-subflow.md` (link
    present), not an inlined copy.
- **Runtime-interactive (exercised when `/hb-ticket-discuss` is actually run):**
  - **Happy path — create**: generate → "create new" → resolve fields → `createJiraIssue`
    → key/URL reported (AC 2, 2.1, 2.2).
  - **Happy path — update**: generate → "update existing" → key → `editJiraIssue` →
    key/URL reported.
  - **No-push**: generate → "no" → stdout emit (Tier 2).
  - **Fallback (no MCP)**: in an environment with no Jira MCP, generate → stdout emit +
    "MCP unavailable" note, **no error** (AC 3, AC 4) — the load-bearing case for AC 4.
  - **Degradation**: a failing `createJiraIssue` (e.g. bad project) surfaces the error
    then falls through to stdout emit.
- **Non-regression**: `--help` and the generate step must behave exactly as step 0 (Steps
  1–2 unchanged); sibling skills unaffected (subflow untouched).

---

## 6. Verification (after implementation)

1. **No build/test gate** — N/A (markdown repo); structural checks are authoritative.
2. **Scope check** — `git status --short` shows only `M skills/hb-ticket-discuss.md`
   (and this step's `plan.md`/execution artifacts under `.hb/`). Nothing under
   `references/`, `scripts/`, or sibling skills changed.
3. **AC 5 (no REST)** — `grep -niE 'rest|curl|/rest/api|https?://[^ )]*api' skills/hb-ticket-discuss.md`
   returns nothing (URLs that appear, if any, are issue browse links in prose, not API
   calls — eyeball-confirm).
4. **AC 6 (conventions + allowed-tools)** —
   `grep -n 'allowed-tools' skills/hb-ticket-discuss.md` shows the six `/tmp` grants
   **and** the five `mcp__claude_ai_Atlassian_Rovo__*` tools on one line; `## Inputs`,
   `## Reference Files`, `## Steps`, `## Output` headings all present; Step 1 is the help
   check.
5. **AC 1/2/2.1/2.2 (offer + primary path)** — read the file: Step 3 offers the push;
   Step 4 resolves `cloudId`/`projectKey`/`issueTypeName`/`summary` by prompting when not
   determinable and calls `createJiraIssue`/`editJiraIssue`; success reports key/URL. For
   a live demonstration, run `/hb-ticket-discuss` against the connected Atlassian MCP and
   confirm a real issue is created with the ticket as its description.
6. **AC 3/4 (fallback + graceful detection)** — read the file: Step 3 routes a missing
   MCP to Step 5 (not an error); Step 5 emits stdout and states MCP unavailable.
   Live-confirm by running with the Jira MCP disconnected (or declining) and observing the
   copy-paste output with no error.
7. **Non-regression** — diff Steps 1–2 against step-0's Steps 1–2: identical; `--help`
   still stops.

(Interactive steps 5–6 are exercised at invocation time, as in step 0; the structural
checks plus the precedence guard in Step 3 back AC 4 without a live MCP outage.)

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — offers to push after generation | §1 Tier table, §2.2 Step 3 | offer is an interactive prompt |
| 2 — primary: create/update via MCP, ticket as description | §2.2 Step 4, §0 tool table | `createJiraIssue`/`editJiraIssue`, `description` = ticket, markdown |
| 2.1 — resolve fields by prompting, never silent guess | §1 field-resolution rule, §2.2 Step 4 | `summary` always confirmed/prompted |
| 2.2 — report issue key/URL on success | §2.2 Step 4, §6.5 | |
| 3 — fallback emit stdout (step-0 behavior preserved) | §1 Tier 3, §2.2 Step 5 | reuses step-0 emit verbatim |
| 4 — graceful detection, absence → fallback not error | top-of-plan design decision, §2.2 Step 3, §6.6 | precedence falls right on any uncertainty |
| 5 — no raw Jira REST API | §1 rejected alternatives, §5 negative grep, §6.3 | |
| 6 — consistent `hb-*` conventions + documented Jira behavior | §2.1–§2.3, §6.4 | mirrors `hb-task-create` shape |

---

## 8. Out of scope (per ticket)

- **Raw Jira REST integration / credential management** — forbidden by AC 5; MCP only.
- **Bidirectional sync / pulling existing Jira issues back into hashbuild tickets** —
  the update path only *writes* a description; it does not import.
- **Changes to `hb-task-create` / `hb-task-step-add` or the shared
  `interactive-ticket-subflow.md`** — reused as-is.
- **Extracting a shared `jira-push-subflow.md`** — deferred; justified only once a second
  caller needs it (flagged in §1, not built here).
- **Registering the skill** anywhere beyond its file existing in `skills/` — inherited
  from step 0's scope.
