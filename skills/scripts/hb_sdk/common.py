"""Shared utilities, constants, and types for hb-sdk."""

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


def progress(msg: str) -> None:
    _err(msg)


def die(msg: str) -> typing.NoReturn:
    _err(msg)
    sys.exit(1)


def _progress_already_exists(p: Path) -> None:
    progress(f"{p.absolute()} already exists")


def exists_or_do(p: Path, f: Callable[[Path], typing.Any]) -> Path:
    if p.exists():
        _progress_already_exists(p)
    else:
        progress(f"creating {p.absolute()} ...")
        f(p)

        if not p.exists():
            die(f"error: failed to create {p.absolute()}")

    return p


def path_hb() -> Path:
    return Path.cwd() / ".hb"


def path_hb_git_keep() -> Path:
    return path_hb() / ".gitkeep"


def path_hb_asserted() -> Path:
    p = path_hb()
    if not p.exists():
        die(
            "error: .hb/ directory not found"
            f"; expected to find .hb/ directory at {p.absolute()}"
            f"; current working directory is {Path.cwd().absolute()}"
            "; use /hb-init if first time or change directory to project directory where .hb/ directory exists"
        )

    return p


def path_task_ticket(task_path: Path) -> Path:
    return task_path / "ticket.md"


def path_step_ticket(step_path: Path) -> Path:
    return step_path / "ticket.md"


def path_project_gitignore() -> Path:
    return Path.cwd() / ".gitignore"


def path_hb_state() -> Path:
    return path_hb() / ".state.ignore.json"


def ensure_gitignore_entry() -> Path:
    """Idempotently append the hb state file's path to the project .gitignore.

    The entry is anchored to the repo root (leading `/`) so it matches only
    the top-level state file, not any same-named file in a subdirectory.
    Creates the file if absent. No-ops if a line matching the entry verbatim
    already exists (exact line match, not substring). Returns the .gitignore
    path either way, so callers can report it as an affected path.
    """
    entry = "/" + str(path_hb_state().relative_to(Path.cwd()))
    p = path_project_gitignore()
    if p.exists():
        text = p.read_text()
        if entry in text.splitlines():
            progress(f"{entry} already present in {p.absolute()}")
            return p
        if text and not text.endswith("\n"):
            text += "\n"
        p.write_text(text + entry + "\n")
    else:
        p.write_text(entry + "\n")
    return p


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


def parse_task_name(name: str) -> TaskName:
    m = TASK_NAME_RE.match(name)
    if not m:
        die(
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


def find_matching_task_folders(tn: TaskName) -> Sequence[tuple[Path, TaskName]]:
    """Collect list of matching paths by task author and task_id"""

    out = list[tuple[Path, TaskName]]()
    for a in (TASK_FOLDER_ACTIVE, TASK_FOLDER_ARCHIVE):
        path_base = path_hb_asserted() / "task" / a
        if not path_base.exists():
            continue

        for p_author in path_base.iterdir():
            for p_task in p_author.iterdir():
                tn_other = parse_task_name(p_author.name + "/" + p_task.name)
                if tn_other.author == tn.author and tn_other.task_id == tn.task_id:
                    out.append((p_task, tn_other))

    return sorted(out)
