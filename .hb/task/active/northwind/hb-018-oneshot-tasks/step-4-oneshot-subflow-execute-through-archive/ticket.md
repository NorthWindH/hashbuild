# Background

Step-3 (`oneshot-subflow-create-through-plan`) authored the oneshot guided subflow reference doc through its plan-confirmation checkpoint (checkpoints 1–7 of task ticket §C AC 10). This step completes the same reference doc, adding the remaining checkpoints: execution, review, and archive-or-leave.

# Goal

Extend the oneshot guided subflow to cover execution through archival, completing the create → plan → execute → review → archive loop described in the task ticket.

# Acceptance Criteria

1. The subflow continues past step-3's plan-confirmation checkpoint (7) with these additional checkpoints, each an explicit stop-or-continue prompt to the user:
    8. Prompt: continue to execution, or stop here (resumable later via the normal `hb-task-step-execute` flow).
    9. If continuing: execute the step.
    10. After execution: gather review items (via `TODO REVIEW` comments or natural-language description), addressing each, looping until the user signals review is finished.
    11. Prompt: archive the task, or leave it as-is (still resumable via the normal per-task actions: add a step, more review, archive later, etc).
2. Stopping at checkpoint 8 leaves the task/step resumable via the normal `hb-task-step-execute` flow — no partial/inconsistent state.
3. Stopping at checkpoint 10 (mid-review) leaves the task/step resumable via the normal `hb-task-step-review-address` flow.
4. Declining to archive at checkpoint 11 leaves the task in a valid, normal active-task state — resumable via the existing per-task actions (add a step, continue review, archive later).
5. Confirming archive at checkpoint 11 results in the task being moved to `task/archive`, identical in effect to invoking `hb-task-archive` directly.
6. Across both halves of the subflow (this step and step-3), stopping at **any** checkpoint (1–11) leaves the task in a state consumable by the existing (non-oneshot) `hb-task-*` skills — no partial/inconsistent state anywhere in the full loop (task ticket §C AC 11).
7. Tests or worked examples cover: continuing through all remaining checkpoints to archival; stopping at checkpoint 8; stopping mid-review (checkpoint 10); declining archive at checkpoint 11; confirming archive at checkpoint 11.

# Out of scope

- Checkpoints 1–7 (create through plan) — step-3 (already complete).
- The prefix-sequence engine, `task create` flag wiring, and `hb-prefix-*` skills — step-0, step-1, step-2 (already complete).
