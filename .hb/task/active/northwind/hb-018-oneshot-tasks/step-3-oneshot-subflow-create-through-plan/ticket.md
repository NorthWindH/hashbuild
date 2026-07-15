# Background

`northwind/hb-018-oneshot-tasks` requires a new, dedicated "oneshot guided subflow" — documented as its own reference file, the same way `breakdown-subflow.md` and `interactive-ticket-subflow.md` are — that walks a user through create → plan → execute → review → archive as one continuous loop with stop-or-continue checkpoints, triggered by `--oneshot` on `hb-task-create` (and its equivalent surfaced through `hb-flow`).

By this point in the task, step-1 (`task-create-prefix-form`) has already wired `hb-sdk task create`'s `--oneshot` flag and prefix resolution. This step and its sibling (step-5) implement the subflow itself, split at the natural midpoint of the checkpoint list (task ticket §C AC 10): this step covers checkpoints 1–7 (task creation through plan confirmation); step-5 covers the rest (checkpoints 8–11: execution through archive).

# Goal

Author the oneshot guided subflow reference doc through its plan-confirmation checkpoint, and wire it into `hb-task-create`'s `--oneshot` mode (and `hb-flow`'s equivalent) as a distinct flow from the normal single-shot task-create path.

# Acceptance Criteria

1. `--oneshot` on `hb-task-create` (and its equivalent surfaced through `hb-flow`) triggers a new, dedicated subflow reference file, distinct from the normal single-shot task-create flow.
2. The subflow proceeds through these checkpoints, each an explicit stop-or-continue prompt to the user:
    1. Create the task as usual (interactive or non-interactive ticket creation).
    2. Present the created ticket, take any requested updates, confirm.
    3. Prompt: continue to planning, or stop here (task remains a normal task, resumable later via `/clear` + `/hb-flow`).
    4. If continuing: evaluate whether the ticket looks like it fits in one step, using existing step-sizing guidance.
        1. If it looks too big for one step: warn the user and require an explicit "continue anyway" before proceeding; otherwise direct them to stop and run normal `hb-task-plan` instead.
    5. If continuing: create exactly one step, seeding the step's ticket from the task's own ticket content.
    6. Plan that step.
    7. Present the plan, take any requested updates, loop until confirmed.
3. Stopping at checkpoint 3 or 4 leaves the task in a valid state consumable by the existing (non-oneshot) `hb-task-*` skills — no partial/inconsistent state (e.g. an orphaned step folder, a half-written ticket).
4. Stopping after checkpoint 7 (plan confirmed, not yet executed) leaves the task/step resumable via the normal `hb-task-step-execute` flow (this is where step-5 picks up).
5. Tests or worked examples cover: continuing through all 7 checkpoints to a confirmed plan; stopping at checkpoint 3; stopping at checkpoint 4 (declining "continue anyway" after an oversize warning); the oversize warning firing correctly for a multi-step-sized ticket and not firing for a right-sized one.

# Out of scope

- Checkpoints 8–11 (execute, review, archive) — step-5.
- The prefix-sequence engine and `task create` flag wiring — step-0 and step-1 (already complete).
- The `hb-prefix-*` skills — step-2 (already complete).
