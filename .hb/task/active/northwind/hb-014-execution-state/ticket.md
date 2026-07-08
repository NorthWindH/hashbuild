# Background

Today, after each `hb-*` skill finishes, the user must remember or re-derive what to run next (`hb-status` can suggest actions, but nothing is persisted about the specific action just taken). hashbuild should track and persist the last executed action so it can reliably tell the user — or itself — what to do next, based on where a task or step actually left off.

---

# Acceptance Criteria

1. hashbuild persists a record of the last executed action (which skill ran, against which task/step, and its outcome) after each relevant `hb-*` skill completes.
2. After a task is created, the recommended next action is to `/clear` then plan the task into steps (`hb-task-plan`).
3. After steps are created for a task, the recommended next action is to `/clear` then plan the next unplanned step (`hb-task-step-plan`).
4. After a step is planned, the recommended next action is to `/clear` then execute that step (`hb-task-step-execute`).
5. After a step is executed, the recommended next action offers a choice: loop through reviewing and addressing review items (`hb-task-step-review-init` / `hb-task-step-review-address`), or move on to the next step.
6. After all steps for a task have been executed (and reviewed, if applicable), the recommended next action offers a choice: add more steps, update the plan, or archive the task.
7. The persisted state survives across separate conversations/sessions (i.e. it is stored in `.hb/`, not in-memory or conversation-scoped).
