---
name: hb-new-task
description: "Create a new hashbuild task from scratch. Use this whenever the user wants to start a new piece of work, create a task, open a ticket, or track something new — even if they say 'let's work on X' without using the word 'task'. Invoke hb-task-create (api tier) to persist the task."
---

# hb-new-task

Workflow entry point: capture intent and create a task record.

## When this triggers

User starts new work: "create a task for...", "let's work on...", "I need to implement...", "new feature: ...", "add X to the backlog".

## Steps

1. **Gather required info** (ask if missing):
   - Title (short, action-oriented)
   - Description (what needs to be done and why)
   - Acceptance criteria (how we know it's done)
   - Source ticket reference (optional — Jira key, GitHub issue URL, Linear ID, etc.)

2. **Confirm** before creating — summarize the above and ask "Ready to create?"

3. **Create via api tier**: apply `hb-task-create` with the gathered info. The api skill handles ID generation and directory creation.

4. **Ask if steps are known**: "Do you have sub-tickets or steps to import now?" If yes, offer to continue with `hb-import-steps` or `hb-import-ticket`.

5. **Report**: output the task ID and path.

## Notes

Keep titles short and imperative: "Add OAuth login", not "Adding OAuth login support to the application".
Acceptance criteria should be bullet points, each independently verifiable.
