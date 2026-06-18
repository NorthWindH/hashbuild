---
name: hb-execute-step
description: "Execute a planned task step by following its plan.md. Use whenever the user says 'execute step X', 'implement STEP-X', 'do step N', or 'let's work on this step'. Requires plan.md to exist. Saves execution artifacts to the step's execution/ directory."
---

# hb-execute-step

Follow plan.md and implement the step.

## Precondition

`plan.md` must exist for the step. If missing, stop and invoke `hb-plan-step` first.

## Steps

1. **Load context**:
   - Read `tasks/active/<task_id>/steps/<step_id>/plan.md`
   - Read `tasks/active/<task_id>/task.md` (overall goal)
   - Read `tasks/active/<task_id>/steps/<step_id>/step.md` (step description)

2. **Execute the plan**: follow the numbered execution steps in plan.md. For each step:
   - Make the change
   - Note any deviation from the plan (unexpected state, better approach found, etc.)

3. **Handle deviations**: if you need to deviate from the plan materially, pause and explain why before continuing. Don't silently diverge.

4. **Save execution notes**: after completing, write a brief `tasks/active/<task_id>/steps/<step_id>/execution/notes.md`:
   - What was done
   - Any deviations from the plan and why
   - Open questions or follow-ups

5. **Update step status**: edit `step.md` — change `**Status:** planned` → `**Status:** needs-review`.

6. **Report**: summarize what was done, note any deviations, ask the user to review.

## Notes

Execution notes are for the human reviewer, not for logging every file edit. Keep them concise: what changed and what's worth noting.
