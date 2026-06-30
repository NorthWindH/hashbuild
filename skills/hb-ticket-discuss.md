---
name: hb-ticket-discuss
argument-hint: "[--help]"
description: >
  /hb-ticket-discuss [--help]

  Run hashbuild's interactive ticket-creation flow to produce a standalone ticket
  (not attached to any task or step), then offer to push the ticket to a connected
  Jira (Atlassian MCP), falling back to stdout copy-paste. Makes no .hb/ writes.
allowed-tools: >
  Write(//tmp/*)
  Write(//private/tmp/*)
  Read(//tmp/*)
  Read(//private/tmp/*)
  Edit(//tmp/*)
  Edit(//private/tmp/*)
  mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources
  mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects
  mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata
  mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql
  mcp__claude_ai_Atlassian_Rovo__getJiraIssue
---

# hb-ticket-discuss

Run the interactive ticket-creation flow to produce a standalone `ticket.md` at a scratch path and print it for copy-paste — no task or step folder is created.

## Inputs

| Parameter              | Required | Description                |
| ---------------------- | -------- | -------------------------- |
| `help`, `--help`, `-h` | no       | Print help and exit.       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Generate standalone ticket

- Set `$TARGET_PATH` = `/tmp` (scratch; the generated ticket is standalone — it lives only here and is never moved into `.hb/`).
- Follow [${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](references/interactive-ticket-subflow.md) with:
  - `$TARGET_PATH` = `/tmp`
  - `$TICKET_SUPPLIED` = `false`
  - `$NO_INTERACTIVE` = `false`

  The subflow writes `ticket.md` to `/tmp/ticket.md`.
- Set `$WRITTEN_TICKET` = `/tmp/ticket.md`.

**Review loop** — repeat until the user is satisfied:

1. Read `$WRITTEN_TICKET` and display its full content as formatted markdown (not a fenced block).
2. Ask the user: "Does this ticket look right? Reply **yes** to continue, or describe any changes."
3. If the user replies **yes** (or an equivalent affirmation): break — proceed to Step 3.
4. Otherwise: treat the reply as corrections. Re-run only Sections C (Transform) and D (Write) of the subflow, incorporating the user's feedback into the derived content. Then return to step 1 of this loop.

### 3. Detect Jira MCP & collect NL description

- Look for a connected MCP tool capable of **creating a Jira issue**. Discover it by capability — check available tools for one that creates Jira issues. On Claude Code with the Atlassian Rovo MCP connected, that tool is `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`; the exact name may differ on other platforms.
- If **no such tool is found**: set `$JIRA` = `unavailable` and skip to Step 6, additionally telling the user that no Jira-capable MCP was detected and they can connect one (e.g. the Atlassian Rovo MCP on Claude Code) and re-run if they want to push. This is the graceful path — absence of the MCP must never raise an error.
- If a tool is found: ask the user to describe the Jira target in natural language, and tell them the resolved details will be shown for confirmation before anything is created or updated. Examples: "create a Task in the MOBILE project for the auth refactor", "update MOBILE-412", "update the login epic in BACKEND".
  - "no" → set `$JIRA` = `declined`, go to Step 6.
  - Otherwise: store the description as `$NL_DESC` and continue to Step 4.

### 4. NL resolution & confirmation loop

Loop until the user accepts the resolved field set or aborts.

**A. Parse `$NL_DESC`:**
- Determine intent path: **create** (keywords: create, new, add, file a …) or **update** (update, edit, change, find, fix …).
- Extract partial fields:
  - Issue key pattern `[A-Z]+-[0-9]+` → explicit `issueIdOrKey` candidate.
  - Project name or key fragment → `projectKey` candidate.
  - Issue type name (Story, Task, Bug, Epic …) → `issueTypeName` candidate.
  - Summary / title text → `summary` candidate.
  - Site name or URL → `cloudId` candidate.

**B. Resolve `cloudId`:**
- Call the MCP's list-accessible-sites tool. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources`.)
- Exactly one site → use it. Multiple → prompt user to choose.

**C. Resolve remaining fields by path:**

*Create path:*
- **`projectKey`:** If a project candidate was extracted, filter `getVisibleJiraProjects` by name match. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects`.) Unambiguous → use it. Multiple matches → present numbered list, user picks. No match or not mentioned → prompt the user to choose from the full project list.
- **`issueTypeName`:** If a type candidate was extracted, match against `getJiraProjectIssueTypesMetadata` for the resolved project. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata`.) Unambiguous → use it. Multiple or unclear → present list. Not mentioned → propose "Task" and confirm.
- **`summary`:** If clearly stated in `$NL_DESC` → extract and propose for confirmation. Otherwise → propose a concise title and confirm. Never silently guessed (unresolved → prompt explicitly).

*Update path:*
- **Explicit key** (`[A-Z]+-[0-9]+` found in NL): call the MCP's get-issue tool to retrieve the issue and confirm its title and status. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getJiraIssue`.) Resolved: `issueIdOrKey` = extracted key.
- **No explicit key**: derive a JQL query from the NL description (e.g. `project = "MOBILE" AND text ~ "auth refactor" ORDER BY updated DESC`). Call the MCP's JQL search tool. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql`.) 1 match → present key + title for confirmation. Multiple matches → numbered list, user picks — **never auto-select**. 0 matches → tell the user, prompt for a key or a more specific description.

Failure / degradation: if any query tool errors → surface the error verbatim and prompt the user to supply that field directly. Never dead-end.

**D. Present resolved field set:**
- Create: `Resolved: CREATE in <projectKey> as <issueTypeName> — '<summary>'`
- Update: `Resolved: UPDATE <issueKey> — '<issue title>'`

Ask: "Does this look right?"

**E. User response:**
- **Accept** → set `$JIRA_FIELDS` = resolved set, set `$JIRA` = `"create"` or `"update"`, break loop.
- **Refine description** → update `$NL_DESC`, return to A.
- **Supply exact values** → accept the values the user provides as `$JIRA_FIELDS`, present for final confirmation, on accept break loop.
- **Abort** → set `$JIRA` = `"declined"`, skip to Step 6.

### 5. Push to Jira (primary path)

Only when `$JIRA` ∈ {`create`, `update`}. Uses `$JIRA_FIELDS` set by Step 4 — no field resolution in this step.

- **If `$JIRA_FIELDS.path` = `create`:**
  - Call the MCP's create-issue tool with `cloudId`, `projectKey`, `issueTypeName`, `summary`, `description` = the full content of `$WRITTEN_TICKET`, and `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`.)
- **If `$JIRA_FIELDS.path` = `update`:**
  - Call the MCP's edit-issue tool with `cloudId`, `issueIdOrKey`, `fields: { description: <full content of $WRITTEN_TICKET> }`, and `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__editJiraIssue`.)
- **On success:** set `$JIRA` = `pushed` and report the resulting issue **key and browse URL** to the user.
- **On failure** (auth, permission, invalid field, etc.): surface the error verbatim, then **fall through to Step 6** so the user still gets the copy-paste ticket — the skill never dead-ends.

### 6. Emit ticket (fallback / no-push path)

Reached when `$JIRA` ∈ {`unavailable`, `declined`} or after a Step 5 failure. **Skipped** when `$JIRA` = `pushed`.

- Read `$WRITTEN_TICKET` and print its full content to stdout inside a fenced block so the user can copy-paste it.
- State that this is the standalone ticket — no `.hb/` task or step folder was created.
- When `$JIRA` = `unavailable`, additionally state that **no Jira MCP was available, so the ticket is emitted for copy-paste**.

### 7. Prompt user

- **If `$JIRA` = `pushed`:** confirm the Jira issue key and browse URL, and that nothing was written to `.hb/`.
- **Otherwise:** tell the user:

  > Standalone ticket is ready above — copy-paste it wherever you need it. Nothing was written to `.hb/`.

## Output

On a successful push, report the Jira issue key and browse URL. Otherwise print the generated ticket content and the scratch path. If any step fails, surface the error verbatim to the caller.
