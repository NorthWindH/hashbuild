# Background

Hashbuild's interactive ticket-creation mode (the prompt → transform → write subflow shared by `hb-task-create` and `hb-task-step-add`) has proven useful for seeding task and step tickets. We want to leverage the same interactive flow in the abstract — for general planning and for drafting tickets that do **not** correspond to a hashbuild task or step. The deliverable is a new skill, `hb-ticket-discuss`, that runs interactive ticket mode to produce a standalone ticket and then offers a way to push that ticket's content into Jira.

---

# Acceptance Criteria

1. A new skill exists at `./skills/hb-ticket-discuss`.
2. The skill reuses the existing interactive ticket-creation subflow to generate a ticket (Background / Acceptance Criteria / Out of scope) from freeform user input.
3. The generated ticket is **standalone** — it is not written into a task or step folder and does not require an existing hashbuild task/step.
4. After the ticket is generated, the skill provides a way to set the ticket as the content of a Jira ticket. Recommended approach:
    1. Primary: create/update a Jira issue via the connected Atlassian (Jira) MCP, using the generated ticket as the issue description.
    2. Fallback: emit the ticket content for copy-paste (e.g. to stdout) when no Jira MCP is available.
    3. The raw Jira REST API is deliberately not pursued (duplicates the MCP and adds credential management).
5. The skill follows existing hashbuild skill conventions (help flag, reference files, skill structure) consistent with sibling `hb-*` skills.

---

# Out of scope

- Implementing the raw Jira REST API integration path.
- Bidirectional sync or pulling existing Jira issues back into hashbuild tickets.
- Changes to the existing `hb-task-create` / `hb-task-step-add` interactive flows beyond what is needed to share the subflow.
