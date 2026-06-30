# Step 1 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-1-REVIEW-1 | ✅ Assessed — write-op permission prompts are intentional; no change needed |
| STEP-1-REVIEW-2 |            |
| STEP-1-REVIEW-3 |            |
| STEP-1-REVIEW-4 |            |

---

## Notes

### STEP-1-REVIEW-1: allowed-tools dropped createJiraIssue and editJiraIssue — confirm intent

- **file(s):** `skills/hb-ticket-discuss.md` (frontmatter `allowed-tools`)
- The allowed-tools list was reformatted for readability and `mcp__claude_ai_Atlassian_Rovo__createJiraIssue` and `mcp__claude_ai_Atlassian_Rovo__editJiraIssue` were dropped. Confirm this removal was intentional and that the skill can still operate correctly without these permissions declared.
- **source:** `TODO REVIEW` in commit `db456e9` — delete comment from source file after addressing

**Resolution:** Intentional and correct. `createJiraIssue` and `editJiraIssue` are write operations on an external system — requiring an explicit permission prompt for them is the right safety posture. The remaining pre-approved entries (`getAccessibleAtlassianResources`, `getVisibleJiraProjects`, `getJiraProjectIssueTypesMetadata`) are read-only discovery calls and low-risk to pre-approve. This removal is also consistent with the platform-agnostic direction being pursued in items 3 and 4: once those are resolved the remaining Atlassian-specific entries may also be cleaned up (the tool names won't be known at skill-authoring time). No code change needed.

---

### STEP-1-REVIEW-2: Step 2 should loop until user is satisfied with the ticket

- **file(s):** `skills/hb-ticket-discuss.md` (Step 2)
- Step 2 currently moves on to push after the first ticket interpretation. Instead it should loop — show the generated ticket and ask if the user is happy; if not, accept corrections and re-interpret before proceeding to Step 3.
- **source:** `TODO REVIEW` in commit `db456e9` — delete comment from source file after addressing

---

### STEP-1-REVIEW-3: Step 3 "In this environment" wording is confusing when MCP is absent

- **file(s):** `skills/hb-ticket-discuss.md` (Step 3 — Detect Jira MCP & offer to push)
- The phrase "In this environment that tool is `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`" is confusing to an agent that runs without that MCP. Reword to guide the agent to discover a capable MCP by capability (e.g. "find an MCP that can create Jira issues; if running on Claude Code with the Atlassian Rovo MCP, that tool is `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`"), and add a fallback: if no such MCP is found, prompt the user to enable one.
- **source:** `TODO REVIEW` in commit `db456e9` — delete comment from source file after addressing

---

### STEP-1-REVIEW-4: Step 4 Jira push instructions hard-code exact Atlassian Rovo tool names

- **file(s):** `skills/hb-ticket-discuss.md` (Step 4 — Jira Push)
- Several instructions in Step 4 name exact `mcp__claude_ai_Atlassian_Rovo__*` tool names (e.g. `getAccessibleAtlassianResources`, `getVisibleJiraProjects`). This assumes a specific MCP server. Reword each instruction to be platform-agnostic, then mention the exact Atlassian Rovo tool name as an example (e.g. "on Claude Code with Atlassian Rovo MCP, use `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources`").
- **source:** `TODO REVIEW` in commit `db456e9` — delete comment from source file after addressing

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
