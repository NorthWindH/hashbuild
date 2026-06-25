# Hashbuild Status

<!--
  STATUS TEMPLATE — a status report is a concise, at-a-glance snapshot of the
  current .hb workspace. Fill each section from the live filesystem. Use the
  exact step folder name (e.g. `step-1-add-form`) when a step has a flavor;
  plain `step-N` otherwise. Omit the Archive section if there are no archived
  tasks. Omit the Active Tasks section if there are no active tasks.
-->

## Initialization

<!--
  Exactly one of the two lines below. Remove the other.
-->

`.hb/` initialized

`.hb/` not found — run `/hb-init` to set up

---

## Active Tasks

<!--
  One subsection per active task, in filesystem order (author → task_id).
  For each step, "pending execution" means the step folder exists but contains
  no `execution-*.md` file.
-->

### `<author>/<task_id>`

<!--
  Repeat this block for each active task. Replace placeholders with real values.
-->

|                         |             |
| ----------------------- | ----------- |
| Steps                   | `<total>`   |
| Steps pending execution | `<count>`   |
| Next step to execute    | `<step_id>` |

---

## Archive

|                |                      |
| -------------- | -------------------- |
| Archived tasks | `<count>`            |
| Last archived  | `<author>/<task_id>` |

<!--
  Last archived: the task folder under task/archive/ with the most recent
  modification time, identified as author/task_id (no flavor). Omit the row
  if the archive is empty.
-->

---

## Next Action

<!--
  One concise sentence or bullet telling the user what to do next.

  Decision tree (pick the first that applies):
  - .hb not initialized (ie does not exist) → run /hb-init
  - any active task with no ticket.md → add ticket.md to it with Background and Acceptance Criteria (summarize ticket-template.md and present to user)
  - any active task with ticket.md but no steps or no steps that have ticket.md → /hb-task-plan or /hb-task-step-add with manually created tickets (summarize ticket-template.md and present to user) or manually add ticket.md to existing steps
  - any active task has a step with no ticket.md → run /hb-task-step-add or
    write ticket.md for that step
  - any active task has a step with ticket.md but no plan.md → run
    /hb-task-step-plan for that step
  - any active task has a step with plan.md but no execution-*.md → run
    /hb-task-step-execute for that step
  - all steps of an active task have executions → consider archiving with
    /hb-task-archive or adding the next step with /hb-task-step-add or /hb-task-plan
  - no active tasks → start a new task with /hb-task-create
-->

<one-sentence recommended action>
