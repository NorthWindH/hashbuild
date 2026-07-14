"""Shared next-action derivation: stage/message/choices for active tasks."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Choice:
    label: str
    invocation: str


@dataclass
class NextAction:
    stage: str
    message: str
    invocation: str | None = None
    choices: list[Choice] | None = None


# TODO REVIEW prefer /hb-task-step-review-address to /hb-task-step-review-init; init is only used in specialty scenarios when user needs a plain skeleton-only review.md file
def _resolve(steps: list[dict[str, Any]], ref: str, on_exhausted: str) -> NextAction:
    for i, s in enumerate(steps):
        if not s["has_ticket"]:
            return NextAction(
                stage="step_needs_ticket",
                message=f"Add `ticket.md` to `{ref}/{s['name']}` or run `/hb-task-step-add {ref}`.",
            )
        if not s["has_plan"]:
            inv = f"/hb-task-step-plan {ref}/{s['name']}"
            return NextAction(
                stage="plan_step",
                message=f"Run `/clear`, then `{inv}` to plan the next step.",
                invocation=inv,
            )
        if not s["has_execution"]:
            inv = f"/hb-task-step-execute {ref}/{s['name']}"
            return NextAction(
                stage="execute_step",
                message=f"Run `/clear`, then `{inv}` to execute the plan.",
                invocation=inv,
            )
        if not s["has_review"] or s["status"] == "review-open":
            review_inv = (
                f"/hb-task-step-review-init {ref}/{s['name']}"
                if not s["has_review"]
                else f"/hb-task-step-review-address {ref}/{s['name']}"
            )
            review_choice = Choice("Review this step", review_inv)
            move_on = _resolve(steps[i + 1 :], ref, on_exhausted="steps_complete")
            if move_on.invocation is not None:
                label = "Move to the next step"
                if "/clear" in move_on.message:
                    label += " (run `/clear` first)"
                rest = [Choice(label, move_on.invocation)]
            else:
                rest = move_on.choices or []
            return NextAction(
                stage="review_or_next",
                message=f"Step `{ref}/{s['name']}` is executed — review it or move on.",
                choices=[review_choice, *rest],
            )
    if on_exhausted == "plan_task":
        inv = f"/hb-task-plan {ref}"
        return NextAction(
            stage="plan_task",
            message=f"Run `/clear`, then `{inv}` to plan `{ref}` into steps.",
            invocation=inv,
        )
    return NextAction(
        stage="steps_complete",
        message=f"All steps for `{ref}` are executed and reviewed — add more steps, update the plan, or archive.",
        choices=[
            Choice("Add more steps", f"/hb-task-step-add {ref}"),
            Choice("Update the plan", f"/hb-task-plan {ref}"),
            Choice("Archive the task", f"/hb-task-archive {ref}"),
        ],
    )


def next_action_for_task(task: dict[str, Any]) -> NextAction:
    ref = f"{task['author']}/{task['task_folder']}"
    if not task["has_ticket"]:
        return NextAction(
            stage="no_ticket",
            message=f"Add `ticket.md` to `{ref}` with Background and Acceptance Criteria.",
        )
    on_exhausted = "plan_task" if not task["steps"] else "steps_complete"
    return _resolve(task["steps"], ref, on_exhausted=on_exhausted)


def compute_next_action(
    state: dict[str, Any] | None, data: dict[str, Any]
) -> list[tuple[str | None, NextAction]]:
    if not data["initialized"]:
        return [
            (
                None,
                NextAction(
                    stage="not_initialized",
                    message="Run `/hb-init` to initialize the workspace.",
                    invocation="/hb-init",
                ),
            )
        ]

    active = data["active_tasks"]
    if not active:
        return [
            (
                None,
                NextAction(
                    stage="no_active_tasks",
                    message="Start a new task with `/hb-task-create <author/task-id>`.",
                ),
            )
        ]

    entries = [(f"{t['author']}/{t['task_folder']}", next_action_for_task(t)) for t in active]
    wanted = state.get("task") if state else None
    if wanted is not None:
        idx = next((i for i, (ref, _) in enumerate(entries) if ref == wanted), None)
        if idx is not None and idx != 0:
            entries.insert(0, entries.pop(idx))
    return entries


def to_dict(ref: str | None, na: NextAction) -> dict[str, Any]:
    return {
        "task": ref,
        "stage": na.stage,
        "message": na.message,
        "invocation": na.invocation,
        "choices": (
            [{"label": c.label, "invocation": c.invocation} for c in na.choices]
            if na.choices is not None
            else None
        ),
    }


def render_md_lines(na: NextAction) -> list[str]:
    lines = [f"- {na.message}"]
    if na.choices:
        for c in na.choices:
            lines.append(f"  - {c.label}: `{c.invocation}`")
    return lines
