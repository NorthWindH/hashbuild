"""Shared utilities, constants, and types for hb-sdk."""

import json
import re
import sys
import typing
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# <author>/<task_id>[<task_extra>]
# task_id:    <prefix>-<num>   e.g. abc-123, PROJSLUG-456
# task_extra: -<slug>          slug chars: [a-z-]
TASK_NAME_RE = re.compile(r"^(?P<author>[^/]+)/(?P<task_id>[A-Za-z]+-\d+)(?P<task_extra>-[a-z][a-z-]*)?$")
STEP_EXTRA_RE = re.compile(r"^[a-z][a-z-]*$")
TAG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
TASK_FOLDER_ACTIVE = "active"
TASK_FOLDER_ARCHIVE = "archive"


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _progress(msg: str) -> None:
    _err(msg)


def _die(msg: str) -> typing.NoReturn:
    _err(msg)
    sys.exit(1)


def _progress_already_exists(p: Path) -> None:
    _progress(f"{p.absolute()} already exists")


def _exists_or_do(p: Path, f: Callable[[Path], typing.Any]) -> Path:
    if p.exists():
        _progress_already_exists(p)
    else:
        _progress(f"creating {p.absolute()} ...")
        f(p)

        if not p.exists():
            _die(f"error: failed to create {p.absolute()}")

    return p


def _path_hb() -> Path:
    return Path.cwd() / ".hb"


def _path_hb_git_keep() -> Path:
    return _path_hb() / ".gitkeep"


def _path_hb_asserted() -> Path:
    p = _path_hb()
    if not p.exists():
        _die(
            "error: .hb/ directory not found"
            f"; expected to find .hb/ directory at {p.absolute()}"
            f"; current working directory is {Path.cwd().absolute()}"
            "; use /hb-init if first time or change directory to project directory where .hb/ directory exists"
        )

    return p


def _path_task_ticket(task_path: Path) -> Path:
    return task_path / "ticket.md"


def _path_step_ticket(step_path: Path) -> Path:
    return step_path / "ticket.md"


def report_paths(paths: Iterable[Path]) -> None:
    print("=== affected paths: ===")
    for p in paths:
        print(p.absolute())


@dataclass(eq=True)
class TaskName:
    author: str
    task_id: str
    task_extra: str  # empty string if absent, otherwise without leading '-'

    def __str__(self) -> str:
        if self.task_extra:
            ex = f"-{self.task_extra}"
        else:
            ex = ""
        return f"{self.author}/{self.task_id}{ex}"


def _parse_task_name(name: str) -> TaskName:
    m = TASK_NAME_RE.match(name)
    if not m:
        _die(
            f"error: invalid task name '{name}'\n"
            f"  expected: <author>/<task_id>[<task_extra>]\n"
            f"  task_id:    <prefix>-<num>  (e.g. abc-123)\n"
            f"  task_extra: -<slug>         slug chars [a-z-]"
        )

    return TaskName(
        author=m.group("author"),
        task_id=m.group("task_id"),
        task_extra=(m.group("task_extra") or "").lstrip("-"),
    )


def _find_matching_task_folders(tn: TaskName) -> Sequence[tuple[Path, TaskName]]:
    """Collect list of matching paths by task author and task_id"""

    out = list[tuple[Path, TaskName]]()
    for a in (TASK_FOLDER_ACTIVE, TASK_FOLDER_ARCHIVE):
        path_base = _path_hb_asserted() / "task" / a
        if not path_base.exists():
            continue

        for p_author in path_base.iterdir():
            for p_task in p_author.iterdir():
                tn_other = _parse_task_name(p_author.name + "/" + p_task.name)
                if tn_other.author == tn.author and tn_other.task_id == tn.task_id:
                    out.append((p_task, tn_other))

    return sorted(out)
