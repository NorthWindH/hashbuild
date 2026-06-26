"""Tests for skills/scripts/hb-sdk"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SDK = Path(__file__).parents[3] / "skills" / "scripts" / "hb-sdk"

DEFAULT_TICKET = "# Background\n\n- \n\n# Acceptance Criteria\n\n1. \n"


def run(args: list[str], cwd: Path, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SDK), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if ok:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
    return result


def init(cwd: Path) -> None:
    run(["init"], cwd)


def task_create(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["task", "create", name]
    if ticket := kwargs.get("ticket"):
        args += ["--ticket", str(ticket)]
    if kwargs.get("ticket_overwrite"):
        args.append("--ticket-overwrite")
    return run(args, cwd, ok=kwargs.get("ok", True))


def task_step_add(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["task", "step", "add", name]
    if flavor := kwargs.get("flavor"):
        args += ["--flavor", flavor]
    if ticket := kwargs.get("ticket"):
        args += ["--ticket", str(ticket)]
    if kwargs.get("ticket_overwrite"):
        args.append("--ticket-overwrite")
    return run(args, cwd, ok=kwargs.get("ok", True))


def task_archive(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["task", "archive", name], cwd, ok=kwargs.get("ok", True))


def task_unarchive(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["task", "unarchive", name], cwd, ok=kwargs.get("ok", True))


def task_path_cmd(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["task", "path", name], cwd, ok=kwargs.get("ok", True))


def task_step_list(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["task", "step", "list", name], cwd, ok=kwargs.get("ok", True))


def summarize(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["summarize"], cwd, ok=kwargs.get("ok", True))


def commit_write_message_file(cwd: Path, mode: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["commit", "write-message-file", mode]
    if task := kwargs.get("task"):
        args += ["--task", task]
    if (step := kwargs.get("step")) is not None:
        args += ["--step", str(step)]
    if short := kwargs.get("short"):
        args += ["--short", short]
    if long := kwargs.get("long"):
        args += ["--long", long]
    if tag := kwargs.get("tag"):
        args += ["--tag", tag]
    return run(args, cwd, ok=kwargs.get("ok", True))


def hb(cwd: Path) -> Path:
    return cwd / ".hb"


def task_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "active" / author / folder


def archive_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "archive" / author / folder


def task_json(cwd: Path, author: str, folder: str) -> dict[str, Any]:
    p = task_path(cwd, author, folder) / ".hb-task.json"
    return json.loads(p.read_text())


# ── init ──────────────────────────────────────────────────────────────────────


def test_init_creates_hb_dir(tmp_path: Path) -> None:
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()
    assert (tmp_path / ".hb" / ".gitkeep").exists()


def test_init_idempotent(tmp_path: Path) -> None:
    init(tmp_path)
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()


def test_init_fails_without_hb(tmp_path: Path) -> None:
    result = run(["task", "create", "hasan/abc-1"], tmp_path, ok=False)
    assert ".hb/ directory not found" in result.stderr


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
    # resolve by task_id alone
    task_archive(tmp_path, "hasan/abc-1")
    assert archive_path(tmp_path, "hasan", "abc-1-some-flavor").is_dir()


# ── task unarchive ───────────────────────────────────────────────────────────


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


# ── task path ────────────────────────────────────────────────────────────────


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


@pytest.fixture()
def task1(tmp_path: Path) -> Path:
    """Initialized repo with one task ready for steps."""
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    return tmp_path


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


# ── commit write-message-file ─────────────────────────────────────────────────


def test_commit_write_message_file_basic(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", short="add login page")
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "abc-1: add login page\n"


def test_commit_write_message_file_with_step(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task-step", task="hasan/abc-1", step=2, short="add login page"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: add login page\n"


def test_commit_write_message_file_with_long(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", short="add login page", long="needed for auth flow"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: add login page\n\nneeded for auth flow\n"


def test_commit_wmf_plain_basic(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", short="init hb")
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "hb: init hb\n"


def test_commit_wmf_plain_with_long(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", short="x", long="y")
    path = Path(result.stdout.strip())
    assert path.read_text() == "hb: x\n\ny\n"


def test_commit_wmf_plain_rejects_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", task="hasan/abc-1", short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_plain_rejects_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", step=0, short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_task_requires_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task", short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_task_rejects_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", step=2, short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_task_step_requires_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task-step", step=2, short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_task_step_requires_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task-step", task="hasan/abc-1", short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_no_mode_errors(tmp_path: Path) -> None:
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--short", "x"], tmp_path, ok=False
    )
    assert result.returncode != 0


def test_commit_wmf_task_with_tag(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", tag="step-add", short="add routes"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: (step-add) add routes\n"


def test_commit_wmf_task_without_tag_unchanged(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", short="add routes")
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: add routes\n"


def test_commit_wmf_task_step_with_tag(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task-step", task="hasan/abc-1", step=2, tag="step-plan", short="write plan"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: (step-plan) write plan\n"


def test_commit_wmf_task_step_without_tag_unchanged(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task-step", task="hasan/abc-1", step=2, short="write plan")
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: write plan\n"


def test_commit_wmf_plain_rejects_tag(tmp_path: Path) -> None:
    result = run(
        ["commit", "write-message-file", "plain", "--tag", "foo", "--short", "x"], tmp_path, ok=False
    )
    assert result.returncode != 0


def test_commit_wmf_invalid_tag_uppercase(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", tag="Foo", short="x", ok=False)
    assert result.returncode != 0
    assert "invalid" in result.stderr


def test_commit_wmf_invalid_tag_underscore(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", tag="foo_bar", short="x", ok=False
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr


# ── summarize ─────────────────────────────────────────────────────────────────


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


# TODO REVIEW this test file has become larger than 1000 lines; hb-sdk itself is ~1000 lines.
# it's time to refactor hb-sdk into modules.
# since we're assuming existence of python3, refactor as follows:
# - move and refactor content of hb-sdk into python module hb_sdk/ located adjacent to existing hb-sdk
# - add a __init__.py file to new hb_sdk folder
# - add a __main__.py file to new hb_sdk folder that acts as main for the module
# - create a .py file within hb_sdk for top-level command tree
# - refactor test_hb-sdk:
#   - create folder tests/skills/scripts/hb_sdk
#   - in that folder, create one test_hb_sdk_*.py file for each command tree
#   - any top-level tests that don't fit into a command tree test can remain in tests/skills/scripts/test_hb-sdk
#   - if no such tests, drop tests/skills/scripts/test_hb-sdk
