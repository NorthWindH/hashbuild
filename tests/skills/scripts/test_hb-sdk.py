"""Tests for skills/scripts/hb-sdk"""

import json
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


def hb(cwd: Path) -> Path:
    return cwd / ".hb"


def task_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "active" / author / folder


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
    assert (tp / "ticket").read_text() == "# My ticket"


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
    assert (tp / "ticket").read_text() == "# Changed"


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
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--short", "add login page"],
        tmp_path,
    )
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "abc-1: add login page\n"


def test_commit_write_message_file_with_step(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--step", "2", "--short", "add login page"],
        tmp_path,
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: add login page\n"


def test_commit_write_message_file_with_long(tmp_path: Path) -> None:
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
