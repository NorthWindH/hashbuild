"""Tests for skills/scripts/hb-sdk"""

import json
import subprocess
import sys
from pathlib import Path

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


def task_create(cwd: Path, name: str, **kwargs) -> subprocess.CompletedProcess[str]:
    args = ["task", "create", name]
    if ticket := kwargs.get("ticket"):
        args += ["--ticket", str(ticket)]
    if kwargs.get("ticket_overwrite"):
        args.append("--ticket-overwrite")
    return run(args, cwd, ok=kwargs.get("ok", True))


def task_step_add(cwd: Path, name: str, **kwargs) -> subprocess.CompletedProcess[str]:
    args = ["task", "step", "add", name]
    if flavor := kwargs.get("flavor"):
        args += ["--flavor", flavor]
    if ticket := kwargs.get("ticket"):
        args += ["--ticket", str(ticket)]
    if kwargs.get("ticket_overwrite"):
        args.append("--ticket-overwrite")
    return run(args, cwd, ok=kwargs.get("ok", True))


def hb(cwd: Path) -> Path:
    return cwd / ".hb"


def task_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "active" / author / folder


def task_json(cwd: Path, author: str, folder: str) -> dict:
    p = task_path(cwd, author, folder) / ".hb-task.json"
    return json.loads(p.read_text())


# ── init ──────────────────────────────────────────────────────────────────────


def test_init_creates_hb_dir(tmp_path):
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()
    assert (tmp_path / ".hb" / ".gitkeep").exists()


def test_init_idempotent(tmp_path):
    init(tmp_path)
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()


def test_init_fails_without_hb(tmp_path):
    result = run(["task", "create", "hasan/abc-1"], tmp_path, ok=False)
    assert ".hb/ directory not found" in result.stderr


# ── task create ───────────────────────────────────────────────────────────────


def test_task_create_basic(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert tp.is_dir()
    data = json.loads((tp / ".hb-task.json").read_text())
    assert data["author"] == "hasan"
    assert data["task_id"] == "abc-1"
    assert data["task_extra"] is None
    assert data["next_step"] == 0


def test_task_create_with_extra(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1-add-login")
    tp = task_path(tmp_path, "hasan", "abc-1-add-login")
    assert tp.is_dir()
    data = json.loads((tp / ".hb-task.json").read_text())
    assert data["task_extra"] == "add-login"


def test_task_create_idempotent(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    task_create(tmp_path, "hasan/abc-1")
    assert task_json(tmp_path, "hasan", "abc-1")["task_id"] == "abc-1"


def test_task_create_invalid_name(tmp_path):
    init(tmp_path)
    result = task_create(tmp_path, "abc-1", ok=False)
    assert "invalid task name" in result.stderr


def test_task_create_with_ticket(tmp_path):
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert (tp / "ticket").read_text() == "# My ticket"


def test_task_create_ticket_same_content_idempotent(tmp_path):
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# My ticket")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)


def test_task_create_ticket_content_conflict_errors(tmp_path):
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# Original")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    ticket.write_text("# Changed")
    result = task_create(tmp_path, "hasan/abc-1", ticket=ticket, ok=False)
    assert "does not match" in result.stderr


def test_task_create_ticket_overwrite(tmp_path):
    init(tmp_path)
    ticket = tmp_path / "ticket.md"
    ticket.write_text("# Original")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket)
    ticket.write_text("# Changed")
    task_create(tmp_path, "hasan/abc-1", ticket=ticket, ticket_overwrite=True)
    tp = task_path(tmp_path, "hasan", "abc-1")
    assert (tp / "ticket").read_text() == "# Changed"


# ── task step add ─────────────────────────────────────────────────────────────


@pytest.fixture()
def task1(tmp_path):
    """Initialized repo with one task ready for steps."""
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    return tmp_path


def test_step_add_creates_step_folder(task1):
    task_step_add(task1, "hasan/abc-1")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0").is_dir()


def test_step_add_creates_default_ticket(task1):
    task_step_add(task1, "hasan/abc-1")
    ticket = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert ticket.read_text() == DEFAULT_TICKET


def test_step_add_increments_next_step(task1):
    task_step_add(task1, "hasan/abc-1")
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 1
    task_step_add(task1, "hasan/abc-1")
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 2


def test_step_add_sequential_folders(task1):
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    task_step_add(task1, "hasan/abc-1")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0").is_dir()
    assert (tp / "step-1").is_dir()
    assert (tp / "step-2").is_dir()


def test_step_add_with_flavor(task1):
    task_step_add(task1, "hasan/abc-1", flavor="scaffold-routes")
    tp = task_path(task1, "hasan", "abc-1")
    assert (tp / "step-0-scaffold-routes").is_dir()
    assert task_json(task1, "hasan", "abc-1")["next_step"] == 1


def test_step_add_flavor_invalid(task1):
    result = task_step_add(task1, "hasan/abc-1", flavor="BadFlavor", ok=False)
    assert "invalid flavor" in result.stderr


def test_step_add_flavor_starts_with_digit_invalid(task1):
    result = task_step_add(task1, "hasan/abc-1", flavor="1-bad", ok=False)
    assert "invalid flavor" in result.stderr


def test_step_add_with_ticket(task1, tmp_path):
    ticket = tmp_path / "step.md"
    ticket.write_text("# Step ticket")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    dest = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert dest.read_text() == "# Step ticket"


def test_step_add_ticket_non_md_rejected(task1, tmp_path):
    ticket = tmp_path / "step.txt"
    ticket.write_text("content")
    result = task_step_add(task1, "hasan/abc-1", ticket=ticket, ok=False)
    assert "must end in .md" in result.stderr


def test_step_add_ticket_missing_file_rejected(task1, tmp_path):
    result = task_step_add(task1, "hasan/abc-1", ticket=tmp_path / "ghost.md", ok=False)
    assert "ticket file not found" in result.stderr


def test_step_add_ticket_same_content_skips(task1, tmp_path):
    ticket = tmp_path / "step.md"
    ticket.write_text("# Step")
    task_step_add(task1, "hasan/abc-1", ticket=ticket)
    result = task_step_add(task1, "hasan/abc-2", ok=False)
    # just confirm first step's ticket is unchanged
    dest = task_path(task1, "hasan", "abc-1") / "step-0" / "ticket.md"
    assert dest.read_text() == "# Step"


def test_step_add_ticket_content_conflict_errors(task1, tmp_path):
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


def test_step_add_ticket_overwrite(task1, tmp_path):
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


def test_step_add_task_not_found(task1):
    result = task_step_add(task1, "hasan/abc-99", ok=False)
    assert "task not found" in result.stderr


def test_step_add_default_ticket_idempotent(task1):
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


# ── commit write-message-file ─────────────────────────────────────────────────


def test_commit_write_message_file_basic(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--short", "add login page"],
        tmp_path,
    )
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "abc-1: add login page\n"


def test_commit_write_message_file_with_step(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--step", "2", "--short", "add login page"],
        tmp_path,
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: add login page\n"


def test_commit_write_message_file_with_long(tmp_path):
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = run(
        [
            "commit",
            "write-message-file",
            "--task",
            "hasan/abc-1",
            "--short",
            "add login page",
            "--long",
            "needed for auth flow",
        ],
        tmp_path,
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: add login page\n\nneeded for auth flow\n"
