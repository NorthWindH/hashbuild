---
name: hb-plan-create
description: "[API] Atomic operation: write plan.md for a task step. Not user-facing — invoked by hb-plan-step after the plan content has been composed."
---

# hb-plan-create

Atomic: write a plan file for a step.

## Steps

1. Confirm step directory exists: `tasks/active/<task_id>/steps/<step_id>/`. If not, invoke hb-step-create first.
2. Write `tasks/active/<task_id>/steps/<step_id>/plan.md` using template below.
3. Update `step.md` status field: `pending` → `planned`.

## plan.md template

```markdown
# Execution Plan: <step_id>

**Task:** <task_id>
**Step:** <step_id>
**Created:** <ISO date>

## Objective

<one-sentence goal>

## Approach

<concise description of the chosen approach and why>

## Execution Steps

1. <step>
2. <step>
...

## Files to Modify / Create

- `<path>` — <reason>

## Tests Required

<what to verify after execution>

## Risks / Considerations

<edge cases, dependencies, blockers>
```
