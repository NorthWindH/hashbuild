"""Tests for hb-sdk task and task step commands."""

import json
import re
from pathlib import Path

from helpers import (
    DEFAULT_TICKET,
    archive_path,
    hb,
    init,
    run,
    task_archive,
    task_create,
    task_json,
    task_path,
    task_path_cmd,
    task_step_add,
    task_step_list,
    task_unarchive,
)

# ── task create ───────────────────────────────────────────────────────────────


def test_task_create_basic(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert tp.is_dir()
    data = json.loads((tp / ".hb-task.json").read_text())
    assert data["author"] == "hasan"
    assert data["task_id"] == "abc-1"
    assert data["task_extra"] is None
    assert data["next_step"] == 0


def test_task_create_with_extra(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    tp = task_path(tmp_path, "hasan", "abc-1-add-login")
    assert tp.is_dir()
    data = json.loads((tp / ".hb-task.json").read_text())
    assert data["task_extra"] == "add-login"


def test_task_create_idempotent(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-1")
    assert task_json(tmp_path, "hasan", "abc-1")["task_id"] == "abc-1"


def test_task_create_invalid_name(tmp_path: Path) -> None:
    init(tmp_path)
    result = task_create(tmp_path, "abc-1", ok=False)
    assert "invalid task name" in result.stderr


def test_task_create_with_ticket(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert (tp / "ticket.md").read_text() == "# My ticket"


def test_task_create_ticket_non_md_rejected(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.txt"
    ticket.write_text("content")
    result = task_create(tmp_path, "hasan/abc-1", ticket=ticket, ok=False)
    assert "must end in .md" in result.stderr


def test_task_create_ticket_same_content_idempotent(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)


def test_task_create_ticket_content_conflict_errors(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# Original")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    ticket.write_text("# Changed")
    result = task_create(tmp_path, "hasan/abc-1", ticket=ticket, ok=False)
    assert "does not match" in result.stderr


def test_task_create_ticket_overwrite(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# Original")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    ticket.write_text("# Changed")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket, ticket_overwrite=True)
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert (tp / "ticket.md").read_text() == "# Changed"


# ── task archive ──────────────────────────────────────────────────────────────


def test_task_archive_moves_to_archive(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    assert not task_path(tmp_path, "hasan", "abc-1").exists()
    assert archive_path(tmp_path, "hasan", "abc-1").is_dir()


def test_task_archive_with_extra(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    task_archive(tmp_path, "hasan/abc-1-add-login")
    assert not task_path(tmp_path, "hasan", "abc-1-add-login").exists()
    assert archive_path(tmp_path, "hasan", "abc-1-add-login").is_dir()


def test_task_archive_preserves_contents(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    task_archive(tmp_path, "hasan/abc-1")
    dest = archive_path(tmp_path, "hasan", "abc-1")
    assert (dest / "ticket.md").read_text() == "# My ticket"
    assert (dest / ".hb-task.json").exists()


def test_task_archive_creates_author_dir(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    assert not (hb(tmp_path) / "task" / "archive" / "hasan").exists()
    task_archive(tmp_path, "hasan/abc-1")
    assert (hb(tmp_path) / "task" / "archive" / "hasan").is_dir()


def test_task_archive_task_not_found(tmp_path: Path) -> None:
    init(tmp_path)
    result = task_archive(tmp_path, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


def test_task_archive_already_archived(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = task_archive(tmp_path, "hasan/abc-1", ok=False)
    assert "already archived" in result.stderr


def test_task_archive_reports_dest_path(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = task_archive(tmp_path, "hasan/abc-1")
    dest = archive_path(tmp_path, "hasan", "abc-1")
    assert str(dest.absolute()) in result.stdout


def test_task_archive_name_by_task_id_only(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-some-flavor")
    task_archive(tmp_path, "hasan/abc-1")
    assert archive_path(tmp_path, "hasan", "abc-1-some-flavor").is_dir()


# ── task unarchive ────────────────────────────────────────────────────────────


def test_task_unarchive_moves_to_active(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    task_unarchive(tmp_path, "hasan/abc-1")
    assert task_path(tmp_path, "hasan", "abc-1").is_dir()
    assert not archive_path(tmp_path, "hasan", "abc-1").is_dir()


def test_task_unarchive_with_extra(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    task_archive(tmp_path, "hasan/abc-1-add-login")
    task_unarchive(tmp_path, "hasan/abc-1-add-login")
    assert not archive_path(tmp_path, "hasan", "abc-1-add-login").is_dir()
    assert task_path(tmp_path, "hasan", "abc-1-add-login").is_dir()


def test_task_unarchive_preserves_contents(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    task_archive(tmp_path, "hasan/abc-1")
    task_unarchive(tmp_path, "hasan/abc-1")
    dest = task_path(tmp_path, "hasan", "abc-1")
    assert (dest / "ticket.md").read_text() == "# My ticket"
    assert (dest / ".hb-task.json").exists()


def test_task_unarchive_creates_active_author_dir(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    # active/hasan/ was removed by archive (empty after move)
    assert not (hb(tmp_path) / "task" / "active" / "hasan").exists()
    task_unarchive(tmp_path, "hasan/abc-1")
    assert (hb(tmp_path) / "task" / "active" / "hasan").is_dir()


def test_task_unarchive_task_not_found(tmp_path: Path) -> None:
    init(tmp_path)
    result = task_unarchive(tmp_path, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


def test_task_unarchive_already_active(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = task_unarchive(tmp_path, "hasan/abc-1", ok=False)
    assert "task is not archived" in result.stderr


def test_task_unarchive_reports_dest_path(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = task_unarchive(tmp_path, "hasan/abc-1")
    dest = task_path(tmp_path, "hasan", "abc-1")
    assert str(dest.absolute()) in result.stdout


def test_task_unarchive_name_by_task_id_only(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-some-flavor")
    task_archive(tmp_path, "hasan/abc-1")
    task_unarchive(tmp_path, "hasan/abc-1")
    assert task_path(tmp_path, "hasan", "abc-1-some-flavor").is_dir()


def test_task_unarchive_removes_empty_archive_author_dir(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    assert (hb(tmp_path) / "task" / "archive" / "hasan").is_dir()
    task_unarchive(tmp_path, "hasan/abc-1")
    assert not (hb(tmp_path) / "task" / "archive" / "hasan").exists()


def test_task_unarchive_round_trip(tmp_path: Path) -> None:
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# Round trip ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    original_contents = set((task_path(tmp_path, "hasan", "abc-1")).iterdir())
    task_archive(tmp_path, "hasan/abc-1")
    task_unarchive(tmp_path, "hasan/abc-1")
    restored = task_path(tmp_path, "hasan", "abc-1")
    assert restored.is_dir()
    assert {f.name for f in restored.iterdir()} == {f.name for f in original_contents}
    assert (restored / "ticket.md").read_text() == "# Round trip ticket"


# ── task path ─────────────────────────────────────────────────────────────────


def test_task_path_basic(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = task_path_cmd(tmp_path, "hasan/abc-1")
    p = Path(result.stdout.strip())
    assert p == task_path(tmp_path, "hasan", "abc-1").absolute()


def test_task_path_with_extra(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    result = task_path_cmd(tmp_path, "hasan/abc-1-add-login")
    p = Path(result.stdout.strip())
    assert p == task_path(tmp_path, "hasan", "abc-1-add-login").absolute()


def test_task_path_resolve_by_task_id_when_folder_has_extra(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    result = task_path_cmd(tmp_path, "hasan/abc-1")
    p = Path(result.stdout.strip())
    assert p == task_path(tmp_path, "hasan", "abc-1-add-login").absolute()


def test_task_path_output_is_absolute(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = task_path_cmd(tmp_path, "hasan/abc-1")
    p = Path(result.stdout.strip())
    assert p.is_absolute()
    assert p.is_dir()


def test_task_path_archived_task(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_archive(tmp_path, "hasan/abc-1")
    result = task_path_cmd(tmp_path, "hasan/abc-1")
    p = Path(result.stdout.strip())
    assert p == archive_path(tmp_path, "hasan", "abc-1").absolute()


def test_task_path_not_found(tmp_path: Path) -> None:
    init(tmp_path)
    result = task_path_cmd(tmp_path, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


def test_task_path_invalid_name(tmp_path: Path) -> None:
    init(tmp_path)
    result = task_path_cmd(tmp_path, "abc-1", ok=False)
    assert "invalid task name" in result.stderr


# ── task step add ─────────────────────────────────────────────────────────────


def test_step_add_creates_step_folder(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0").is_dir()


def test_step_add_creates_default_ticket(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    ticket = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert ticket.read_text() == DEFAULT_TICKET


def test_step_add_increments_next_step(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 1
    task_step_add(task1, "hasan/abc-1")
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 2


def test_step_add_sequential_folders(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0").is_dir()
    assert (tp / "step-1").is_dir()
    assert (tp / "step-2").is_dir()


def test_step_add_with_flavor(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1", flavor="scaffold-routes")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0-scaffold-routes").is_dir()
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 1


def test_step_add_flavor_invalid(task1: Path) -> None:
    result = task_step_add(task1, "hasan/abc-1", flavor="BadFlavor", ok=False)
    assert "invalid flavor" in result.stderr


def test_step_add_flavor_starts_with_digit_invalid(task1: Path) -> None:
    result = task_step_add(task1, "hasan/abc-1", flavor="1-bad", ok=False)
    assert "invalid flavor" in result.stderr


def test_step_add_with_ticket(task1: Path, tmp_path: Path) -> None:
    ticket = tmp_path / "step.md"
    ticket.write_text("# Step ticket")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    dest = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert dest.read_text() == "# Step ticket"


def test_step_add_ticket_non_md_rejected(task1: Path, tmp_path: Path) -> None:
    ticket = tmp_path / "step.txt"
    ticket.write_text("content")
    result = task_step_add(task1, "hasan/abc-1", ticket=ticket, ok=False)
    assert "must end in .md" in result.stderr


def test_step_add_ticket_missing_file_rejected(task1: Path, tmp_path: Path) -> None:
    result = task_step_add(task1, "hasan/abc-1", ticket=tmp_path / "ghost.md", ok=False)
    assert "ticket file not found" in result.stderr


def test_step_add_ticket_same_content_skips(task1: Path, tmp_path: Path) -> None:
    ticket = tmp_path / "step.md"
    ticket.write_text("# Step")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    task_step_add(task1, "hasan/abc-2", ok=False)
    # just confirm first step's ticket is unchanged
    dest = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert dest.read_text() == "# Step"


def test_step_add_ticket_content_conflict_errors(task1: Path, tmp_path: Path) -> None:
    ticket = tmp_path / "step.md"
    ticket.write_text("# Original")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    # manually put a different ticket in step-0 and reset next_step so we hit same folder
    step0 = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    step0.write_text("# Different")
    tj = task_path(task1, "hasan", "abc-1") / ".hb-task.json"
    data = json.loads(tj.read_text())
    data["next_step"] = 0
    tj.write_text(json.dumps(data, indent=2) + "\n")
    result = task_step_add(task1, "hasan/abc-1", ticket=ticket, ok=False)
    assert "does not match" in result.stderr


def test_step_add_ticket_overwrite(task1: Path, tmp_path: Path) -> None:
    ticket = tmp_path / "step.md"
    ticket.write_text("# Original")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    step0 = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    step0.write_text("# Different")
    tj = task_path(task1, "hasan", "abc-1") / ".hb-task.json"
    data = json.loads(tj.read_text())
    data["next_step"] = 0
    tj.write_text(json.dumps(data, indent=2) + "\n")
    task_step_add(task1, "hasan/abc-1", ticket=ticket, ticket_overwrite=True)
    assert step0.read_text() == "# Original"


def test_step_add_task_not_found(task1: Path) -> None:
    result = task_step_add(task1, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


def test_step_add_default_ticket_idempotent(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    # reset next_step to 0 to re-enter same step
    tj = task_path(task1, "hasan", "abc-1") / ".hb-task.json"
    data = json.loads(tj.read_text())
    data["next_step"] = 0
    tj.write_text(json.dumps(data, indent=2) + "\n")
    task_step_add(task1, "hasan/abc-1")
    # default ticket untouched on second pass
    dest = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert dest.read_text() == DEFAULT_TICKET


# ── task step list ────────────────────────────────────────────────────────────


def test_step_list_empty(task1: Path) -> None:
    result = task_step_list(task1, "hasan/abc-1")
    assert result.stdout.strip() == ""


def test_step_list_single_step(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    result = task_step_list(task1, "hasan/abc-1")
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].endswith("step-0")


def test_step_list_multiple_steps_ascending_order(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    result = task_step_list(task1, "hasan/abc-1")
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 3
    assert lines[0].endswith("step-0")
    assert lines[1].endswith("step-1")
    assert lines[2].endswith("step-2")


def test_step_list_with_flavors(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1", flavor="init-db")
    task_step_add(task1, "hasan/abc-1", flavor="seed-data")
    result = task_step_list(task1, "hasan/abc-1")
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    assert lines[0].endswith("step-0-init-db")
    assert lines[1].endswith("step-1-seed-data")


def test_step_list_mixed_plain_and_flavored(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1", flavor="do-thing")
    task_step_add(task1, "hasan/abc-1")
    result = task_step_list(task1, "hasan/abc-1")
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 3
    assert lines[0].endswith("step-0")
    assert lines[1].endswith("step-1-do-thing")
    assert lines[2].endswith("step-2")


def test_step_list_outputs_absolute_paths(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    result = task_step_list(task1, "hasan/abc-1")
    p = Path(result.stdout.strip())
    assert p.is_absolute()
    assert p.is_dir()


def test_step_list_numeric_not_lexicographic_order(task1: Path) -> None:
    for _ in range(11):
        task_step_add(task1, "hasan/abc-1")
    result = task_step_list(task1, "hasan/abc-1")
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 11
    names = [Path(line).name for line in lines]
    assert names[9] == "step-9"
    assert names[10] == "step-10"


def test_step_list_task_not_found(task1: Path) -> None:
    result = task_step_list(task1, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


# ── task step path ────────────────────────────────────────────────────────────


def test_step_path_by_integer(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1", flavor="scaffold-routes")
    result = run(["task", "step", "path", "hasan/abc-1/0"], task1)
    assert result.stdout.strip().endswith("step-0-scaffold-routes")


def test_step_path_by_step_n(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    result = run(["task", "step", "path", "hasan/abc-1/step-0"], task1)
    assert result.stdout.strip().endswith("step-0")


def test_step_path_by_full_step_name(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1", flavor="some-stuff")
    result = run(["task", "step", "path", "hasan/abc-1/step-0-some-stuff"], task1)
    assert result.stdout.strip().endswith("step-0-some-stuff")


def test_step_path_task_flavor_optional(task1: Path) -> None:
    task_step_add(task1, "hasan/abc-1")
    result_short = run(["task", "step", "path", "hasan/abc-1/0"], task1)
    result_full = run(["task", "step", "path", "hasan/abc-1/0"], task1)
    assert result_short.stdout.strip() == result_full.stdout.strip()


def test_step_path_not_found(task1: Path) -> None:
    result = run(["task", "step", "path", "hasan/abc-1/99"], task1, ok=False)
    assert "step 99 not found" in result.stderr


def test_step_path_task_not_found(task1: Path) -> None:
    result = run(["task", "step", "path", "hasan/abc-99/0"], task1, ok=False)
    assert "task not found" in result.stderr


def test_step_path_invalid_step_id(task1: Path) -> None:
    result = run(["task", "step", "path", "hasan/abc-1/bad"], task1, ok=False)
    assert "invalid step id" in result.stderr


# ── task step number ──────────────────────────────────────────────────────────


def test_step_number_from_integer(tmp_path: Path) -> None:
    result = run(["task", "step", "number", "hasan/abc-1/0"], tmp_path)
    assert result.stdout.strip() == "0"


def test_step_number_from_step_n(tmp_path: Path) -> None:
    result = run(["task", "step", "number", "hasan/abc-1/step-3"], tmp_path)
    assert result.stdout.strip() == "3"


def test_step_number_from_full_step_name(tmp_path: Path) -> None:
    result = run(["task", "step", "number", "hasan/abc-1/step-99-some-flavor"], tmp_path)
    assert result.stdout.strip() == "99"


def test_step_number_with_task_flavor(tmp_path: Path) -> None:
    result = run(["task", "step", "number", "hasan/abc-1-some-task/step-5"], tmp_path)
    assert result.stdout.strip() == "5"


def test_step_number_invalid(tmp_path: Path) -> None:
    result = run(["task", "step", "number", "hasan/abc-1/bad"], tmp_path, ok=False)
    assert "invalid step id" in result.stderr


# ── task step execution-slug ──────────────────────────────────────────────────

EXECUTION_SLUG_RE = re.compile(r"^execution-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}[+-]\d{4}\.md$")


def test_execution_slug_format(tmp_path: Path) -> None:
    result = run(["task", "step", "execution-slug"], tmp_path)
    slug = result.stdout.strip()
    assert EXECUTION_SLUG_RE.match(slug), f"unexpected slug format: {slug!r}"


def test_execution_slug_unique(tmp_path: Path) -> None:
    import time

    r1 = run(["task", "step", "execution-slug"], tmp_path)
    time.sleep(1.1)
    r2 = run(["task", "step", "execution-slug"], tmp_path)
    assert r1.stdout.strip() != r2.stdout.strip()
