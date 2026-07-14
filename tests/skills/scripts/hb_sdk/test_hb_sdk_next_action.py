"""Tests for hb-sdk state next-action."""

import json
from pathlib import Path

from helpers import (
    init,
    state_next_action,
    state_record,
    task_create,
    task_path,
    task_step_add,
)

# ── not initialized / no active tasks (AC 3) ─────────────────────────────────


def test_next_action_not_initialized(tmp_path: Path) -> None:
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert len(entries) == 1
    assert entries[0]["task"] is None
    assert entries[0]["stage"] == "not_initialized"
    assert "/hb-init" in entries[0]["message"]


def test_next_action_no_active_tasks(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "no_active_tasks"
    assert "/hb-task-create" in entries[0]["message"]


# ── no_ticket ─────────────────────────────────────────────────────────────────


def test_next_action_task_no_ticket(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["task"] == "hasan/abc-1"
    assert entries[0]["stage"] == "no_ticket"
    assert "ticket.md" in entries[0]["message"]


# ── step_needs_ticket ─────────────────────────────────────────────────────────


def test_next_action_step_needs_ticket(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "ticket.md").unlink()
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "step_needs_ticket"


# ── plan_task (AC 2.1) ────────────────────────────────────────────────────────


def test_next_action_stage_plan_task(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "plan_task"
    assert entries[0]["invocation"] == "/hb-task-plan hasan/abc-1"
    assert "/clear" in entries[0]["message"]


# ── plan_step (AC 2.2) ────────────────────────────────────────────────────────


def test_next_action_stage_plan_step(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "plan_step"
    assert entries[0]["invocation"] == "/hb-task-step-plan hasan/abc-1/step-0"
    assert "/clear" in entries[0]["message"]


def test_next_action_stage_plan_step_picks_earliest(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    base = task_path(tmp_path, "hasan", "abc-1")
    (base / "step-0" / "plan.md").write_text("# plan")
    (base / "step-0" / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (base / "step-0" / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n"
        "| STEP-0-REVIEW-1 | ✅ Addressed — fixed |\n"
    )
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "plan_step"
    assert entries[0]["invocation"] == "/hb-task-step-plan hasan/abc-1/step-1"


# ── execute_step (AC 2.3) ─────────────────────────────────────────────────────


def test_next_action_stage_execute_step(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "execute_step"
    assert entries[0]["invocation"] == "/hb-task-step-execute hasan/abc-1/step-0"
    assert "/clear" in entries[0]["message"]


# ── review_or_next (AC 2.4) ───────────────────────────────────────────────────


def test_next_action_stage_review_or_next_no_review_file(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "review_or_next"
    choices = entries[0]["choices"]
    assert len(choices) == 4
    assert choices[0]["label"] == "Review this step"
    assert "/hb-task-step-review-address" in choices[0]["invocation"]
    labels = [c["label"] for c in choices]
    assert "Add more steps" in labels
    assert "Update the plan" in labels
    assert "Archive the task" in labels


def test_next_action_stage_review_or_next_open_review(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n| STEP-0-REVIEW-1 |  |\n"
    )
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "review_or_next"
    choices = entries[0]["choices"]
    assert "/hb-task-step-review-address" in choices[0]["invocation"]


def test_next_action_stage_review_or_next_has_next_step(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    base = task_path(tmp_path, "hasan", "abc-1")
    step0 = base / "step-0"
    (step0 / "plan.md").write_text("# plan")
    (step0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "review_or_next"
    choices = entries[0]["choices"]
    assert len(choices) == 2
    assert choices[0]["label"] == "Review this step"
    assert choices[1]["label"] == "Move to the next step (run `/clear` first)"
    assert choices[1]["invocation"] == "/hb-task-step-plan hasan/abc-1/step-1"


# ── steps_complete (AC 2.5) ───────────────────────────────────────────────────


def test_next_action_stage_steps_complete(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n"
        "| STEP-0-REVIEW-1 | ✅ Addressed — fixed |\n"
    )
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["stage"] == "steps_complete"
    choices = entries[0]["choices"]
    assert len(choices) == 3
    labels = [c["label"] for c in choices]
    assert labels == ["Add more steps", "Update the plan", "Archive the task"]
    assert "Review this step" not in labels


# ── ordering by state (AC 1's use of the persisted record) ───────────────────


def test_next_action_orders_state_task_first(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    state_record(tmp_path, skill="hb-task-step-execute", outcome="success", task="hasan/abc-2")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["task"] == "hasan/abc-2"


def test_next_action_state_unknown_task_no_reorder(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    state_record(tmp_path, skill="hb-task-step-execute", outcome="success", task="hasan/does-not-exist")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["task"] == "hasan/abc-1"
    assert entries[1]["task"] == "hasan/abc-2"


def test_next_action_no_state_default_order(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    assert entries[0]["task"] == "hasan/abc-1"
    assert entries[1]["task"] == "hasan/abc-2"


# ── --format ───────────────────────────────────────────────────────────────────


def test_next_action_format_default_is_json(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_next_action(tmp_path)
    json.loads(result.stdout)  # must not raise


def test_next_action_format_md_renders_message(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = state_next_action(tmp_path, format="md")
    assert "executed — review it or move on" in result.stdout
    assert "Review this step" in result.stdout
    assert "Add more steps" in result.stdout


# ── invariant: exactly one of invocation/choices set (except global fallbacks) ─


def test_next_action_invariant_one_of_invocation_or_choices(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = state_next_action(tmp_path, format="json")
    entries = json.loads(result.stdout)
    for e in entries:
        assert e["message"]
        assert (e["invocation"] is None) != (e["choices"] is None)
