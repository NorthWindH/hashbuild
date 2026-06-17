---
name: hb-import-steps
description: "Import sub-tickets or a list of steps into an existing hashbuild task. Use when the user provides sub-tickets, a breakdown list, child issues, or says 'add these steps to task X' / 'break this down into steps'. Invokes hb-step-create for each step."
---

# hb-import-steps

Import one or more steps into an existing task.

## Steps

1. **Identify the target task**: ask if not clear from context. Show available active tasks via `query_tasks.py list` if the user is unsure.

2. **Parse the input**: steps may arrive as:
   - A list of sub-tickets (any format — same parsing heuristics as hb-import-ticket)
   - A numbered or bulleted list of titles
   - Free-form text describing multiple pieces of work

   For each item, extract: title, description (if present), and source sub-ticket reference.

3. **Show the parsed steps** in order and confirm: "I found N steps — does this order look right? Any to add or remove?"

4. **Create steps in order**: for each step, apply `hb-step-create` with the parsed content. Steps are numbered sequentially from the current max step in the task.

5. **Report**: list of created step IDs and paths.

## Ordering

Preserve the input order — the user's ordering is intentional. If ordering is ambiguous (e.g., unordered set of sub-tickets), surface the ambiguity and ask.

## Notes

Steps don't need plans yet — plan creation is a separate workflow (`hb-plan-step`).
It's fine to create steps without descriptions; the user can flesh them out later.
