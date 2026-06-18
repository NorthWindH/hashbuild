---
name: hb-complete-task
description: "Mark a task as done and archive it. Use when the user says 'mark task X as done', 'archive this task', 'complete TASK-NNN', or 'we're done with X'. Verifies all steps are complete before archiving. Invokes hb-task-archive."
---

# hb-complete-task

Close out a finished task and move it to archive.

## Steps

1. **Identify task**: resolve task ID from context or user input. Show active tasks if unclear.

2. **Check step completion**:
   - Run `query_tasks.py steps <task_id>` to list steps.
   - For each step, read `step.md` and check `**Status:**`.
   - If any step is not `complete`, list the incomplete steps and ask: "These steps aren't marked complete — archive anyway?"

3. **Verify acceptance criteria**: read `task.md` acceptance criteria. Ask the user to confirm each is met, or confirm all at once if they're confident.

4. **Archive**: apply `hb-task-archive` to move the task.

5. **Report**: confirm archive path and summarize what was completed.

## Notes

Archiving is not deletion — everything is preserved in `tasks/archive/`. It's safe to archive and revisit later.
