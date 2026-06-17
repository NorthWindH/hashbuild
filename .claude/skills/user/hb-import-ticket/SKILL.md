---
name: hb-import-ticket
description: "Import an existing ticket (Jira, Linear, GitHub Issue, plain text, paste, or any other format) as a hashbuild task. Use whenever the user provides ticket content or a reference and wants it tracked as a task — even if they just paste text or say 'make a task from this'. Optionally breaks the ticket into steps. Invokes hb-task-create and optionally hb-step-create."
---

# hb-import-ticket

Parse a ticket in any format and create the corresponding task record.

## Supported input formats

- **Jira** — exported JSON, plain text with summary/description/acceptance criteria fields
- **Linear** — exported markdown, URL reference
- **GitHub Issue** — markdown body, issue URL
- **Plain paste** — any free-form text the user provides
- **Structured fields** — title + description typed directly

If given a URL (not a file path), ask the user to paste the ticket content instead — don't fetch URLs.

## Steps

1. **Parse the ticket**: extract title, description, acceptance criteria, and source reference. Use your best judgment when fields don't map cleanly — preserve all meaningful content.

2. **Show extracted fields** and confirm: "Here's what I extracted — does this look right?"

3. **Ask about breakdown**: "Should I break this into steps now? If you have sub-tickets, paste them; otherwise I'll create the task without steps."

4. **Create task**: apply `hb-task-create` with extracted content. Set source ticket field to the original reference.

5. **If breaking into steps**: apply `hb-import-steps` for the sub-tickets, passing the newly created task ID.

6. **Report**: task ID, path, and number of steps created (if any).

## Parsing heuristics

- "Summary" / "Title" → task title
- "Description" / "Details" / "Body" → task description  
- "Acceptance Criteria" / "Done When" / "Definition of Done" → acceptance criteria
- "Key" / "ID" / issue number → source ticket reference

When a ticket has child items (subtasks in Jira, sub-issues in GitHub, child issues in Linear), treat them as candidate steps but confirm with the user first.
