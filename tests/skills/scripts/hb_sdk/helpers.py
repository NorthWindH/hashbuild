"""Shared test helpers for hb-sdk tests."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SDK = Path(__file__).parents[4] / "skills" / "scripts" / "hb-sdk"

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
    args = ["summarize"]
    if fmt := kwargs.get("format"):
        args += ["--format", fmt]
    return run(args, cwd, ok=kwargs.get("ok", True))


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


def idea_add(cwd: Path, author: str, content: str, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["idea", "add", author, content], cwd, ok=ok)


def idea_remove(cwd: Path, idea_ref: str, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["idea", "remove", idea_ref], cwd, ok=ok)


def idea_show(cwd: Path, target: str | None = None, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    args = ["idea", "show"]
    if target is not None:
        args.append(target)
    return run(args, cwd, ok=ok)


def idea_set_content(cwd: Path, idea_ref: str, new_content: str, *, ok: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["idea", "set-content", idea_ref, new_content], cwd, ok=ok)


def hb(cwd: Path) -> Path:
    return cwd / ".hb"


def task_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "active" / author / folder


def archive_path(cwd: Path, author: str, folder: str) -> Path:
    return hb(cwd) / "task" / "archive" / author / folder


def task_json(cwd: Path, author: str, folder: str) -> dict[str, Any]:
    p = task_path(cwd, author, folder) / ".hb-task.json"
    return json.loads(p.read_text())
