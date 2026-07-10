# Background

`README.md` documents every other hb-* skill (the Skills table and the "Getting started" lifecycle walkthrough) but has no mention of `hb-ticket-discuss` at all — not in the skills table, and not as a usage section, since it predates this task's loop rewrite and previously lived outside the task/step lifecycle the "Getting started" section walks through. Once the loop, Describe, Breakdown, and Push actions land (earlier steps in this task), the README should explain how to use the skill and show it working end to end.

---

# Acceptance Criteria

1. `hb-ticket-discuss` is added as a row in the Skills table (`## Skills`), with a one-line description consistent with the other rows.
2. A new section documents `hb-ticket-discuss`, placed after "Getting started" (it operates outside the task/step lifecycle those steps walk through) and before "Lifecycle":
    1. Explains what the skill is for: a persistent, multi-turn loop for discussing, creating, breaking down, managing, and pushing tickets that are not yet attached to a task or step.
    2. Explains the context model in plain terms: any number of tickets can be held across the conversation, at most one is active, and each iteration shows the active ticket, the count, and the ids of tickets in context.
    3. Lists the available actions (Load, Describe, Breakdown, Clear, Push, Exit) with a one-line description of each, consistent with how other skills are described elsewhere in the README.
3. The section includes a simple, concrete usage example walking through **create → breakdown → push**:
    1. Start the loop with `/hb-ticket-discuss`.
    2. Use **Describe ticket** to create one ticket via natural language, showing an example prompt/response that results in it becoming the active ticket.
    3. Use **Breakdown ticket** on that ticket, showing an example where a gap is found and one or more child tickets are proposed, confirmed, and added to context.
    4. Use **Push ticket(s)** to push a ticket (e.g. one of the children) to Jira, showing an example resolved field set and a successful push result (issue key + browse URL).
    5. The example is illustrative prose/sample dialogue, not a literal transcript requirement — it should read naturally alongside the tone of the rest of the README's "Getting started" walkthrough.
4. The example and section correctly reflect the actual behavior implemented in the loop-skeleton, breakdown-action, and push-tickets steps of this task (no aspirational or inaccurate claims) — cross-checked against those steps' final `hb-ticket-discuss.md` and subflow files once implemented.
5. Existing README sections (Getting started, Lifecycle, File structure) are left otherwise unchanged — this step only adds the skills-table row and the new section.

---

# Out of scope

- Any change to `hb-ticket-discuss.md` or its subflows — this step is documentation-only.
- Documenting the Load ticket action's every source in exhaustive detail — the action list entry and the worked example are enough; deep mechanics belong to the skill's own reference files, not the README.
