---
name: hb-plan-step
description: "Create a detailed execution plan for a task step. Use whenever the user wants to plan a step, says 'plan STEP-X', 'how should we approach step N', or asks for a plan before implementing. Reads step.md for context, produces plan.md via hb-plan-create."
---

# hb-plan-step

Produce a concrete, actionable execution plan for one step.

## Steps

1. **Identify step**: resolve task ID and step ID from context or user input. Read `tasks/active/<task_id>/steps/<step_id>/step.md` for the step description.

2. **Read task context**: read `tasks/active/<task_id>/task.md` to understand the broader goal.

3. **Explore relevant codebase**: read files, run searches as needed to understand the current state. A good plan is grounded in what exists — don't plan in a vacuum.

4. **Draft the plan**: compose plan content per the `hb-plan-create` template:
   - Objective (one sentence)
   - Approach (chosen strategy and rationale)
   - Numbered execution steps (concrete enough to follow without ambiguity)
   - Files to modify/create
   - Tests required
   - Risks/considerations

5. **Review with user**: share the draft plan and ask if anything needs adjusting before committing.

6. **Persist**: apply `hb-plan-create` with the finalized content.

7. **Report**: confirm plan written, show path.

## What makes a good plan

- Each execution step is small enough to do in one focused action
- Files to modify are listed specifically (path + why), not vaguely ("update the auth module")
- Risks name concrete failure modes, not generic concerns
- Tests section says what to check, not just "write tests"
