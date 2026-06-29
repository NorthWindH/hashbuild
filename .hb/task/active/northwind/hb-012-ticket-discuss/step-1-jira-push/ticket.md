# Background

Step 0 scaffolded `hb-ticket-discuss` so it generates a standalone ticket and
emits it to stdout. This step adds the Jira push, completing task acceptance
criterion 4 and the remainder of criterion 5.

The push uses the connected Atlassian (Jira) MCP — creating or updating a Jira
issue with the generated ticket as the issue description — and falls back to the
existing stdout copy-paste output when no Jira MCP is available. The raw Jira
REST API path is deliberately not pursued: it duplicates the MCP and adds
credential management.

---

# Acceptance Criteria

1. After the ticket is generated, the skill offers to push it to Jira.
2. Primary path: when an Atlassian (Jira) MCP is connected, the skill
   creates or updates a Jira issue using the generated ticket content as the
   issue description.
    1. The skill resolves the necessary issue fields (e.g. project, issue type,
       summary) by prompting the user when they are not otherwise determinable,
       rather than guessing silently.
    2. On success, the skill reports the resulting issue key / URL to the user.
3. Fallback path: when no Jira MCP is available, the skill emits the ticket
   content for copy-paste (the stdout behavior from step 0 is preserved) and
   tells the user the MCP was unavailable.
4. The skill detects MCP availability gracefully — absence of the Atlassian MCP
   leads to the fallback, not an error.
5. The raw Jira REST API is **not** used anywhere in the skill.
6. The skill remains consistent with sibling `hb-*` conventions established in
   step 0 (help flag, inputs table, reference files, step structure), with the
   new Jira behavior documented in its inputs/steps.

---

# Out of scope

- Implementing a raw Jira REST API integration path.
- Bidirectional sync or pulling existing Jira issues back into hashbuild
  tickets.
- Changes to the `hb-task-create` / `hb-task-step-add` interactive flows.
