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

1. Read `$WRITTEN_TICKET` and display its full content inside a fenced block.
2. Ask the user: "Does this ticket look right? Reply **yes** to continue, or describe any changes."
3. If the user replies **yes** (or an equivalent affirmation): break — proceed to Step 3.
4. Otherwise: treat the reply as corrections. Re-run only Sections C (Transform) and D (Write) of the subflow, incorporating the user's feedback into the derived content. Then return to step 1 of this loop.

### 3. Detect Jira MCP & offer to push

- Look for a connected MCP tool capable of **creating a Jira issue**. Discover it by capability — check available tools for one that creates Jira issues. On Claude Code with the Atlassian Rovo MCP connected, that tool is `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`; the exact name may differ on other platforms.
- If **no such tool is found**: set `$JIRA` = `unavailable` and skip to Step 5, additionally telling the user that no Jira-capable MCP was detected and they can connect one (e.g. the Atlassian Rovo MCP on Claude Code) and re-run if they want to push. This is the graceful path — absence of the MCP must never raise an error.
- If a tool is found: ask the user — "Push this ticket to Jira? (create new / update existing / no)".
  - "no" → set `$JIRA` = `declined`, go to Step 5.
  - "create new" → set `$JIRA` = `create`, continue to Step 4.
  - "update existing" → set `$JIRA` = `update`, continue to Step 4.

### 4. Push to Jira (primary path)

Only when `$JIRA` ∈ {`create`, `update`}.

- **Resolve `cloudId`** — use the MCP's list-accessible-sites tool to enumerate connected Atlassian sites. (On Claude Code with Atlassian Rovo MCP: `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources`; exact name may differ on other platforms.) If exactly one site is accessible, use it; otherwise prompt the user to choose. (If the user supplied a site URL, its hostname may be passed directly per the tool's guidance.)
- **If `$JIRA` = `create`:**
  - Resolve `projectKey` — use the MCP's list-projects tool to offer choices and confirm. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects`.)
  - Resolve `issueTypeName` — use the MCP's issue-type-metadata tool to offer valid types; default to `Task`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata`.)
  - Resolve `summary` — propose a concise summary line and confirm, or prompt. The summary is **not** determinable from the ticket body, so it is never silently guessed.
  - Call the MCP's create-issue tool with `cloudId`, `projectKey`, `issueTypeName`, `summary`, `description` = the full content of `$WRITTEN_TICKET`, and `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`.)
- **If `$JIRA` = `update`:**
  - Prompt for the target `issueIdOrKey` (e.g. `PROJ-123`).
  - Call the MCP's edit-issue tool with `cloudId`, `issueIdOrKey`, `fields: { description: <full content of $WRITTEN_TICKET> }`, and `contentFormat: "markdown"`. (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__editJiraIssue`.)
- **On success:** set `$JIRA` = `pushed` and report the resulting issue **key and browse URL** to the user.
- **On failure** (auth, permission, invalid field, etc.): surface the error verbatim, then **fall through to Step 5** so the user still gets the copy-paste ticket — the skill never dead-ends.

### 5. Emit ticket (fallback / no-push path)

Reached when `$JIRA` ∈ {`unavailable`, `declined`} or after a Step 4 failure. **Skipped** when `$JIRA` = `pushed`.

- Read `$WRITTEN_TICKET` and print its full content to stdout inside a fenced block so the user can copy-paste it.
- State that this is the standalone ticket — no `.hb/` task or step folder was created.
- When `$JIRA` = `unavailable`, additionally state that **no Jira MCP was available, so the ticket is emitted for copy-paste**.

### 6. Prompt user

- **If `$JIRA` = `pushed`:** confirm the Jira issue key and browse URL, and that nothing was written to `.hb/`.
- **Otherwise:** tell the user:

  > Standalone ticket is ready above — copy-paste it wherever you need it. Nothing was written to `.hb/`.

## Output

On a successful push, report the Jira issue key and browse URL. Otherwise print the generated ticket content and the scratch path. If any step fails, surface the error verbatim to the caller.
