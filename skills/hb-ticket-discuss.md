---
name: hb-ticket-discuss
argument-hint: "[--help]"
description: >
  /hb-ticket-discuss [--help]

  Run a persistent, multi-turn loop for drafting standalone tickets (not
  attached to any task or step). Holds any number of tickets in
  in-conversation context and, each iteration, presents a menu of next
  actions (e.g. describe, load, exit) selectable via natural language. Makes
  no .hb/ writes.
allowed-tools: >
  Write(//tmp/*)
  Write(//private/tmp/*)
  Read(//tmp/*)
  Read(//private/tmp/*)
  Edit(//tmp/*)
  Edit(//private/tmp/*)
  # TODO REVIEW review starts here:
  # These are overly broad permissions and they should be dropped.
  # Agent harness should not be allowed to read or web fetch ANY resource.
  # Any tool not listed here will simply be prompted upon attempt to use by agent / harness so dropping them here will NOT block actions in this skill.
  # Drop these overly broad tools from this listing.
  Read
  WebFetch
  # TODO REVIEW review ends here
  mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources
  mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects
  mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata
  mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql
  mcp__claude_ai_Atlassian_Rovo__getJiraIssue
---

# hb-ticket-discuss

Run a persistent, multi-turn loop for drafting standalone tickets — no task or step folder is created. Tickets accumulate in in-conversation context across iterations; each iteration presents the current state and a menu of next actions (e.g. describe, load, exit) selectable via natural language.

## Inputs

| Parameter              | Required | Description                |
| ---------------------- | -------- | -------------------------- |
| `help`, `--help`, `-h` | no       | Print help and exit.       |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Initialize loop

Set `$TICKET_CONTEXT` = `[]`, `$TICKET_SEQ` = `0`, `$ACTION_LOG` = `[]`.

### 3. Inject loop subflow

Follow [${CLAUDE_SKILL_DIR}/references/ticket-loop-subflow.md](references/ticket-loop-subflow.md), passing `$TICKET_CONTEXT`, `$TICKET_SEQ`, and `$ACTION_LOG` as its caller contract requires. This subflow runs the present → dispatch → loop-continue cycle until the user selects Exit, at which point it returns here and the skill ends.

## Output

On Exit, report the summary produced by `exit-ticket-loop-subflow.md` (tickets left in context, actions taken). If any step fails, surface the error verbatim to the caller.
