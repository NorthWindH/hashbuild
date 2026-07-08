# Background

With `hb-sdk state record`/`show` persisting the last-executed action (prior steps), hashbuild still has no shared logic that turns "what just happened" plus "what the task/step tree currently looks like" into "what to do next." Today `hb_sdk/summarize.py`'s `_next_action` (summarize.py:140-172) derives a next-action string purely by re-inspecting file existence on disk — it works for the file-presence cases it covers, but it does not implement the exact lifecycle rules the task ticket requires (AC 3.1–3.5), and it is not reusable by anything other than `summarize`'s markdown renderer (it returns a pre-joined string, not structured data).

Task ticket AC 3 pins down five lifecycle stages precisely:

1. After a task is created → recommend `/clear` then `hb-task-plan`.
2. After steps are created for a task → recommend `/clear` then `hb-task-step-plan` on the next unplanned step.
3. After a step is planned → recommend `/clear` then `hb-task-step-execute` on that step.
4. After a step is executed → offer a **choice**: review loop (`hb-task-step-review-init`/`hb-task-step-review-address`) or move to the next step.
5. After all steps executed (and reviewed, if applicable) → offer a **choice**: add more steps, update the plan, or archive the task.

AC 5 further requires that existing consumers (`hb-status`'s `summarize`) source next-action data from this new logic rather than duplicating it.

---

# Goal

A single `hb-sdk` module computes the recommended next action (including the AC 3.4/3.5 branching choices) from the persisted last-executed-action record plus current task/step file state, exposed via a CLI command, and `summarize.py` is refactored to consume it instead of its own `_next_action`.

---

# Acceptance Criteria

## A. Next-action derivation module

1. A new `hb_sdk/next_action.py` module exposes a function that takes the current `state.py` record (may be absent) and the per-task/step status data already computed by `_summarize_task`/`_build_data` (summarize.py:109-137), and returns a structured result (not a pre-formatted string) containing at least: a `stage` identifier, a human-readable `message`, and — for the two branching stages — a list of `choices`, each with a label and the corresponding skill invocation.
2. The five stages map to the exact rules in Background, verified with these canonical cases:
    1. Task has `ticket.md`, zero steps → stage recommends `/clear` then `hb-task-plan <ref>`.
    2. Task has ≥1 step, at least one step has `ticket.md` but none has `plan.md` → stage recommends `/clear` then `hb-task-step-plan <ref>/<next-unplanned-step>`.
    3. A step has `plan.md` but no `execution-*.md` → stage recommends `/clear` then `hb-task-step-execute <ref>/<step>`.
    4. A step has an `execution-*.md` and either no `review.md` or a `review.md` with open items → stage offers the choice between reviewing (`hb-task-step-review-init`/`hb-task-step-review-address`) and moving to the next step.
    5. All steps have `execution-*.md`, and any that have `review.md` have no open items → stage offers the choice between adding steps (`hb-task-plan`/`hb-task-step-add`), updating the plan, or archiving (`hb-task-archive`).
3. When no active tasks exist, the module returns the existing "start a new task" guidance (parity with current `_next_action` behavior for that case, summarize.py:146-147).
4. `hb-sdk state next-action [--format json|md]` prints the derived result for the currently active task(s) needing attention.

## B. Refactor existing consumer

5. `hb_sdk/summarize.py`'s `_next_action` (or its call sites in `_render_md`) is replaced with a call into the new `hb_sdk/next_action.py` logic — no next-action derivation logic remains duplicated inline in `summarize.py`.
6. `hb-sdk summarize --format md`'s "Next Action" section output is equivalent in content to before for the cases that existed previously (task with no ticket, no steps, per-step ticket/plan/execution gaps), and additionally reflects the new AC 3.4/3.5 branching choices where applicable.
7. `hb-sdk summarize --format json` continues to include enough per-task/step fields for the new module to operate (no regression to the existing JSON schema fields consumed elsewhere).

## C. Verification

8. Manually exercise `hb-sdk state next-action` against a fixture task at each of the five stages (using the existing archived tasks under `.hb/task/archive/` as reference shapes, or a scratch task) and confirm the returned stage/message/choices match the rule for that stage.

---

# Out of scope

- The new `hb-flow` skill that presents this data conversationally and handles natural-language navigation — deferred to the next step.
- Changing how/when skills call `hb-sdk state record` — already delivered in the prior step.
- Any change to the existing "S/T/P/E/RO/R" table rendering in `_render_md` beyond the Next Action section.
