"""Tests for hb-sdk summarize command."""

import json
import os
from pathlib import Path

from helpers import (
    archive_path,
    init,
    summarize,
    task_archive,
    task_create,
    task_path,
    task_step_add,
)


def test_summarize_not_initialized(tmp_path: Path) -> None:
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["initialized"] is False
    assert data["active_tasks"] == []
    assert data["archive"]["count"] == 0
    assert data["archive"]["recent"] == []


def test_summarize_initialized_no_tasks(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["initialized"] is True
    assert data["active_tasks"] == []
    assert data["archive"]["count"] == 0


def test_summarize_active_task_no_steps(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert len(data["active_tasks"]) == 1
    t = data["active_tasks"][0]
    assert t["author"] == "hasan"
    assert t["task_id"] == "abc-1"
    assert t["task_folder"] == "abc-1"
    assert t["total_steps"] == 0
    assert t["steps"] == []
    assert t["steps_skeleton"] == 0
    assert t["steps_needs_review"] == []
    assert t["steps_needs_work"] == []
    assert t["next_pending_step"] is None


def test_summarize_task_has_ticket(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["active_tasks"][0]["has_ticket"] is False

    ticket = tmp_path / "t.md"
    ticket.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-2", ticket=ticket)
    result2 = summarize(tmp_path)
    data2 = json.loads(result2.stdout)
    abc2 = next(t for t in data2["active_tasks"] if t["task_id"] == "abc-2")
    assert abc2["has_ticket"] is True


def test_summarize_task_with_flavor(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    t = data["active_tasks"][0]
    assert t["task_id"] == "abc-1"
    assert t["task_folder"] == "abc-1-add-login"


def test_summarize_step_files(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    step = data["active_tasks"][0]["steps"][0]
    assert step["name"] == "step-0"
    assert step["has_ticket"] is True  # default ticket written by step add
    assert step["has_plan"] is False
    assert step["has_execution"] is False

    # add plan.md
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    result2 = summarize(tmp_path)
    step2 = json.loads(result2.stdout)["active_tasks"][0]["steps"][0]
    assert step2["has_plan"] is True
    assert step2["has_execution"] is False

    # add execution file
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result3 = summarize(tmp_path)
    step3 = json.loads(result3.stdout)["active_tasks"][0]["steps"][0]
    assert step3["has_execution"] is True


def test_summarize_steps_pending_execution(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")

    step0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")

    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    t = data["active_tasks"][0]
    assert t["total_steps"] == 3
    assert t["steps_ticketed"] == 2
    assert t["steps_needs_work"] == ["step-1", "step-2"]
    assert t["next_pending_step"] == "step-1"


def test_summarize_all_steps_executed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")

    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    t = data["active_tasks"][0]
    assert t["steps_executed"] == 1
    assert t["steps_needs_review"] == ["step-0"]
    assert t["next_pending_step"] is None


def test_summarize_next_pending_step_with_flavor(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1", flavor="scaffold")
    task_step_add(tmp_path, "hasan/abc-1", flavor="wire-auth")

    step0 = task_path(tmp_path, "hasan", "abc-1") / "step-0-scaffold"
    (step0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")

    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["active_tasks"][0]["next_pending_step"] == "step-1-wire-auth"


def test_summarize_multiple_active_tasks(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    task_create(tmp_path, "northwind/xyz-10")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert len(data["active_tasks"]) == 3
    ids = [(t["author"], t["task_id"]) for t in data["active_tasks"]]
    assert ("hasan", "abc-1") in ids
    assert ("hasan", "abc-2") in ids
    assert ("northwind", "xyz-10") in ids


def test_summarize_archive_count(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    task_archive(tmp_path, "hasan/abc-1")

    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["archive"]["count"] == 1
    assert len(data["active_tasks"]) == 1

    task_archive(tmp_path, "hasan/abc-2")
    result2 = summarize(tmp_path)
    data2 = json.loads(result2.stdout)
    assert data2["archive"]["count"] == 2
    assert data2["active_tasks"] == []


def test_summarize_last_archived_by_mtime(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    task_archive(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-2")

    # force abc-2 to appear older so abc-1 wins
    p = archive_path(tmp_path, "hasan", "abc-2")
    os.utime(p, (1_000_000, 1_000_000))

    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["archive"]["recent"][0]["task_id"] == "abc-1"


def test_summarize_last_archived_strips_flavor(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    task_archive(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    recent = data["archive"]["recent"]
    assert recent[0]["task_id"] == "abc-1"
    assert recent[0]["task_folder"] == "abc-1-add-login"


def test_summarize_task_path_is_absolute(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    p = Path(data["active_tasks"][0]["task_path"])
    assert p.is_absolute()
    assert p.is_dir()


# ── step status field ──────────────────────────────────────────────────────────


def test_summarize_step_status_skeleton(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "ticket.md").unlink()
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "skeleton"
    assert step["has_review"] is False


def test_summarize_step_status_ticketed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "ticketed"


def test_summarize_step_status_planned(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "plan.md").write_text("# plan")
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "planned"


def test_summarize_step_status_executed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "executed"


def test_summarize_step_status_review_open(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n| STEP-0-REVIEW-1 |  |\n"
    )
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "review-open"
    assert step["has_review"] is True


def test_summarize_step_status_reviewed_all_closed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n"
        "| STEP-0-REVIEW-1 | ✅ Addressed — fixed |\n"
        "| STEP-0-REVIEW-2 | ⏭️ Deferred — later |\n"
    )
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "reviewed"


def test_summarize_step_status_reviewed_no_rows(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text("# Review\n\nNo issues found.\n")
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "reviewed"


def test_summarize_step_status_review_case_insensitive(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n"
        "| STEP-0-REVIEW-1 | ✅ Addressed — fixed |\n"
    )
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "reviewed"


def test_summarize_step_status_review_mixed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (step_path / "review.md").write_text(
        "# Step 0 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n"
        "| STEP-0-REVIEW-1 | ✅ Addressed — fixed |\n"
        "| STEP-0-REVIEW-2 |  |\n"
    )
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["status"] == "review-open"


def test_summarize_step_has_review_false_without_file(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    step_path = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (step_path / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = summarize(tmp_path)
    step = json.loads(result.stdout)["active_tasks"][0]["steps"][0]
    assert step["has_review"] is False
    assert step["status"] == "executed"


# ── active-task count and list fields ─────────────────────────────────────────


def test_summarize_task_count_fields_all_zero(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert t["steps_skeleton"] == 0
    assert t["steps_ticketed"] == 0
    assert t["steps_planned"] == 0
    assert t["steps_executed"] == 0
    assert t["steps_review_open"] == 0
    assert t["steps_reviewed"] == 0
    assert t["steps_needs_review"] == []
    assert t["steps_needs_work"] == []


def test_summarize_task_count_fields_mixed(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")

    # create 6 steps via SDK so each has a ticket
    for _ in range(6):
        task_step_add(tmp_path, "hasan/abc-1")

    base = task_path(tmp_path, "hasan", "abc-1")
    sp0 = base / "step-0"
    sp2 = base / "step-2"
    sp3 = base / "step-3"
    sp4 = base / "step-4"
    sp5 = base / "step-5"

    # step-0: skeleton — remove ticket so no files remain
    (sp0 / "ticket.md").unlink()
    # step-1: ticketed — already has ticket only; no changes needed
    # step-2: planned
    (sp2 / "plan.md").write_text("# plan")
    # step-3: executed
    (sp3 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    # step-4: review-open
    (sp4 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (sp4 / "review.md").write_text(
        "# Step 4 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n| STEP-4-REVIEW-1 |  |\n"
    )
    # step-5: reviewed
    (sp5 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (sp5 / "review.md").write_text(
        "# Step 5 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n| STEP-5-REVIEW-1 | ✅ Addressed — x |\n"
    )

    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert t["steps_skeleton"] == 1
    assert t["steps_ticketed"] == 1
    assert t["steps_planned"] == 1
    assert t["steps_executed"] == 1
    assert t["steps_review_open"] == 1
    assert t["steps_reviewed"] == 1


def test_summarize_steps_needs_review_includes_executed_and_review_open(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    sp0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    sp1 = task_path(tmp_path, "hasan", "abc-1") / "step-1"
    (sp0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (sp1 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    (sp1 / "review.md").write_text(
        "# Step 1 Review\n\n## Status\n\n| ID | Resolution |\n| --- | --- |\n| STEP-1-REVIEW-1 |  |\n"
    )
    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert "step-0" in t["steps_needs_review"]
    assert "step-1" in t["steps_needs_review"]


def test_summarize_steps_needs_work_includes_skeleton_ticketed_planned(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    # create 3 steps via SDK so each has a ticket
    for _ in range(3):
        task_step_add(tmp_path, "hasan/abc-1")

    base = task_path(tmp_path, "hasan", "abc-1")
    # step-0: skeleton — remove ticket
    (base / "step-0" / "ticket.md").unlink()
    # step-1: ticketed — already has ticket, no changes needed
    # step-2: planned
    (base / "step-2" / "plan.md").write_text("# plan")

    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert "step-0" in t["steps_needs_work"]
    assert "step-1" in t["steps_needs_work"]
    assert "step-2" in t["steps_needs_work"]


def test_summarize_steps_needs_review_empty_when_none_qualify(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert t["steps_needs_review"] == []


def test_summarize_steps_needs_work_empty_when_none_qualify(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    sp0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (sp0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = summarize(tmp_path)
    t = json.loads(result.stdout)["active_tasks"][0]
    assert t["steps_needs_work"] == []


# ── archive recent ─────────────────────────────────────────────────────────────


def test_summarize_archive_recent_empty_when_no_archives(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path)
    data = json.loads(result.stdout)
    assert data["archive"]["recent"] == []


def test_summarize_archive_recent_single_entry(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    recent = json.loads(result.stdout)["archive"]["recent"]
    assert len(recent) == 1
    assert set(recent[0].keys()) >= {"author", "task_id", "task_folder"}


def test_summarize_archive_recent_sorted_by_mtime_desc(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-2")
    task_archive(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-2")

    # force abc-2 to appear older so abc-1 wins
    p = archive_path(tmp_path, "hasan", "abc-2")
    os.utime(p, (1_000_000, 1_000_000))

    result = summarize(tmp_path)
    recent = json.loads(result.stdout)["archive"]["recent"]
    assert recent[0]["task_id"] == "abc-1"


def test_summarize_archive_recent_max_five(tmp_path: Path) -> None:
    init(tmp_path)
    for i in range(1, 8):
        task_create(tmp_path, f"hasan/abc-{i}")
        task_archive(tmp_path, f"hasan/abc-{i}")
    result = summarize(tmp_path)
    recent = json.loads(result.stdout)["archive"]["recent"]
    assert len(recent) == 5


def test_summarize_archive_recent_task_folder_includes_flavor(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    task_archive(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    recent = json.loads(result.stdout)["archive"]["recent"]
    assert recent[0]["task_folder"] == "abc-1-add-login"
    assert recent[0]["task_id"] == "abc-1"


def test_summarize_archive_recent_author_field(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path)
    recent = json.loads(result.stdout)["archive"]["recent"]
    assert recent[0]["author"] == "hasan"


# ── --format flag ──────────────────────────────────────────────────────────────


def test_summarize_format_default_is_json(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path)
    json.loads(result.stdout)  # must not raise


def test_summarize_format_json_explicit(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="json")
    data = json.loads(result.stdout)
    assert "initialized" in data
    assert "active_tasks" in data
    assert "archive" in data


def test_summarize_format_md_returns_non_json(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="md")
    try:
        json.loads(result.stdout)
        raise AssertionError("expected non-JSON output")
    except json.JSONDecodeError:
        pass


def test_summarize_format_invalid_exits_nonzero(tmp_path: Path) -> None:
    result = summarize(tmp_path, format="xml", ok=False)
    assert result.returncode != 0


def test_summarize_format_md_not_initialized(tmp_path: Path) -> None:
    result = summarize(tmp_path, format="md")
    assert "`.hb/` not found" in result.stdout


def test_summarize_format_md_initialized(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="md")
    assert "`.hb/` initialized" in result.stdout


def test_summarize_format_md_no_active_tasks_section_absent(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="md")
    assert "## Active Tasks" not in result.stdout


def test_summarize_format_md_active_task_in_table(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "hasan/abc-1" in result.stdout


def test_summarize_format_md_count_dash_when_zero(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "| — |" in result.stdout


def test_summarize_format_md_count_nonzero(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "| 1 |" in result.stdout


def test_summarize_format_md_needs_review_in_details(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_step_add(tmp_path, "hasan/abc-1")
    sp0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (sp0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = summarize(tmp_path, format="md")
    assert "Needs review" in result.stdout


def test_summarize_format_md_archive_section_present(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "## Archive" in result.stdout


def test_summarize_format_md_archive_section_absent(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="md")
    assert "## Archive" not in result.stdout


def test_summarize_format_md_next_action_not_initialized(tmp_path: Path) -> None:
    result = summarize(tmp_path, format="md")
    assert "## Next Action" in result.stdout
    assert "/hb-init" in result.stdout


def test_summarize_format_md_next_action_no_tasks(tmp_path: Path) -> None:
    init(tmp_path)
    result = summarize(tmp_path, format="md")
    assert "/hb-task-create" in result.stdout


def test_summarize_format_md_next_action_task_no_ticket(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "ticket.md" in result.stdout


def test_summarize_format_md_next_action_step_needs_plan(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    result = summarize(tmp_path, format="md")
    assert "/hb-task-step-plan" in result.stdout


def test_summarize_format_md_next_action_step_needs_execution(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    sp0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (sp0 / "plan.md").write_text("# plan")
    result = summarize(tmp_path, format="md")
    assert "/hb-task-step-execute" in result.stdout


def test_summarize_format_md_next_action_all_steps_executed(tmp_path: Path) -> None:
    init(tmp_path)
    ticket_file = tmp_path / "t.md"
    ticket_file.write_text("# ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket_file)
    task_step_add(tmp_path, "hasan/abc-1")
    sp0 = task_path(tmp_path, "hasan", "abc-1") / "step-0"
    (sp0 / "plan.md").write_text("# plan")
    (sp0 / "execution-2026-01-01T00-00-00+0000.md").write_text("# exec")
    result = summarize(tmp_path, format="md")
    assert "Review this step" in result.stdout
    assert "Add more steps" in result.stdout
    assert "Update the plan" in result.stdout
    assert "Archive the task" in result.stdout
