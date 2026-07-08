# Background

Today, after each `hb-*` skill finishes, the user must remember or re-derive what to run next (`hb-status` can suggest actions, but nothing is persisted about the specific action just taken). hashbuild should track and persist the last executed action so it can reliably tell the user — or itself — what to do next, based on where a task or step actually left off.

---

# Acceptance Criteria

1. hashbuild persists a record of the last executed action (which skill ran, against which task/step, and its outcome) after each relevant `hb-*` skill completes.
2. The persisted state survives across separate conversations/sessions (i.e. it is stored at `.hb/state.json`, not in-memory or conversation-scoped).
    1. `.hb/state.json` is excluded from git — the `hb-init` skill updates the project's `.gitignore` to include it (idempotently, alongside the existing `.hb/` structure setup), and no `hb-*` skill ever stages or commits it.
3. Based on the persisted last-executed-action, the recommended call to action is correct at every stage of a task's lifecycle:
    1. After a task is created, recommend `/clear` then plan the task into steps (`hb-task-plan`).
    2. After steps are created for a task, recommend `/clear` then plan the next unplanned step (`hb-task-step-plan`).
    3. After a step is planned, recommend `/clear` then execute that step (`hb-task-step-execute`).
    4. After a step is executed, offer a choice: loop through reviewing and addressing review items (`hb-task-step-review-init` / `hb-task-step-review-address`), or move on to the next step.
    5. After all steps for a task have been executed (and reviewed, if applicable), offer a choice: add more steps, update the plan, or archive the task.
4. A new skill (e.g. `hb-flow`) is added under `./skills/` that presents the current state (last-executed action and its recommended call to action) and drives the user through it.
    1. On invocation, it reports where the active task/step left off and what the recommended next action is, per the rules in AC 3.
    2. It understands natural-language navigation commands (e.g. "move on to the next step", "archive this task", "let's review", "update the plan") and maps them to the corresponding call to action, from any state a task/step can be in — not just the currently recommended one.
    3. It reuses `hb-sdk` for all state reads/derivations rather than re-implementing task/step traversal or status logic inline in the skill.
5. `hb-sdk` is extended as needed to support AC 1, 2, and 4 (e.g. persisting/reading the last-executed-action record, exposing it and the derived call to action programmatically) — existing `hb-sdk` commands/consumers (e.g. `hb-status`'s `summarize`) are updated to source next-action data from this new logic rather than duplicating it.
