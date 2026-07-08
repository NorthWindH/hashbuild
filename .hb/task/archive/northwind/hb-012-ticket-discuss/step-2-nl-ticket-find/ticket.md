# Background

Step 1 added the Jira push to `hb-ticket-discuss`: a create path that requires
`cloudId`, `projectKey`, `issueTypeName`, and `summary`, and an update path that
requires `cloudId` and `issueIdOrKey` (see step-1 `plan.md` §0 / §2). Step 1 resolves
those fields **one at a time** — prompting the user and offering choices from the Jira
metadata tools field-by-field. That is correct but mechanical: the user answers a
sequence of narrow questions instead of stating their intent once.

This step makes field resolution conversational. The user describes the Jira target in
**natural language** — supplying some, all, or none of the required fields (e.g. "create
a Task in the Northwind backend project" or "update the login epic") — and the agent
**queries Jira to resolve that description into concrete field values**, then presents
the resolved set back for confirmation before anything is created or updated.

The motivating case: a user types "update the auth refactor story in MOBILE"; the agent
queries Jira, resolves it to a concrete `cloudId` + issue key (e.g. `MOBILE-412`),
presents that back, and on acceptance feeds those exact values into the step-1 push —
no field-by-field interrogation.

---

# Goal

Let the user specify the Jira push target in natural language; have the agent resolve it
against the live Jira (via the connected Atlassian MCP), present the resolved field set,
and proceed only on explicit confirmation — with a refine-or-supply-exact loop on
decline.

---

# Acceptance Criteria

1. The skill accepts a natural-language description of the Jira target in which the user
   may specify **some, all, or none** of the fields step 1 requires (site/cloud, project,
   issue type, summary for create; or which existing issue to update).
2. The agent **resolves the natural language into concrete field values by querying the
   connected Jira MCP** — it does not guess:
    1. a described project resolves to a real `projectKey` (via the projects metadata tool);
    2. a described issue type resolves to a valid `issueTypeName` for that project (via the
       issue-type metadata tool);
    3. the site resolves to a concrete `cloudId`;
    4. for the update path, the described existing issue is located (by key, or by
       searching Jira) and resolved to a concrete `issueIdOrKey`.
3. After resolution, the agent **presents the resolved field set back to the user** for
   confirmation before any create or update is performed.
4. **Accept path:** if the user accepts, the resolved values are exactly what the step-1
   push proceeds with.
5. **Decline path:** if the user declines, they can either
    1. refine the natural-language description and have the agent re-resolve, or
    2. supply exact field values directly;

   the resolve → present → confirm loop repeats until the user accepts or aborts.
6. Fields the natural language does **not** determine are surfaced as unresolved and
   prompted for (consistent with step 1's "never silently guess" rule) — never fabricated.
7. **Ambiguous** matches (e.g. a description matching more than one project or issue) are
   presented as a choice for the user to disambiguate, not auto-selected silently.
8. The behavior remains consistent with step 1 and sibling `hb-*` conventions, with the
   new natural-language resolution documented in the skill's inputs/steps; the raw Jira
   REST API is **not** used.

---

# Out of scope

- Implementing the actual `createJiraIssue` / `editJiraIssue` call — that is step 1; this
  step only resolves and confirms the field values that the step-1 push consumes.
- Natural-language interpretation of the ticket **body/description** — the description is
  the generated ticket content; this step concerns the target **fields** only.
- Bidirectional sync or importing existing Jira issues back into hashbuild tickets.
- Any raw Jira REST API integration path.
