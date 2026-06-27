"""hb-sdk summarize command."""

import argparse
import json
import re
import typing
from dataclasses import dataclass
from pathlib import Path

from .common import (
    TASK_FOLDER_ACTIVE,
    TASK_FOLDER_ARCHIVE,
    parse_task_name,
    path_hb,
)
from .task import list_step_folders

_SEPARATOR_RE = re.compile(r"^[-:]+$")


def _parse_review_open(review_path: Path) -> bool:
    """Return True if any Status-table row has an empty Resolution cell."""
    text = review_path.read_text()
    for line in text.splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 4:
            continue
        id_val = cols[1].lower()
        if not id_val or _SEPARATOR_RE.match(id_val) or id_val == "id":
            continue
        if not cols[2]:  # empty Resolution cell = open item
            return True
    return False


@dataclass
class _StepInfo:
    name: str
    has_ticket: bool
    has_plan: bool
    has_execution: bool
    has_review: bool
    review_open: bool

    @property
    def status(self) -> str:
        if self.has_review:
            return "review-open" if self.review_open else "reviewed"
        if self.has_execution:
            return "executed"
        if self.has_plan:
            return "planned"
        if self.has_ticket:
            return "ticketed"
        return "skeleton"


@dataclass
class _TaskInfo:
    author: str
    task_id: str
    task_folder: str
    task_path: Path
    has_ticket: bool
    steps: list["_StepInfo"]

    @property
    def steps_skeleton(self) -> int:
        return sum(1 for s in self.steps if s.status == "skeleton")

    @property
    def steps_ticketed(self) -> int:
        return sum(1 for s in self.steps if s.status == "ticketed")

    @property
    def steps_planned(self) -> int:
        return sum(1 for s in self.steps if s.status == "planned")

    @property
    def steps_executed(self) -> int:
        return sum(1 for s in self.steps if s.status == "executed")

    @property
    def steps_review_open(self) -> int:
        return sum(1 for s in self.steps if s.status == "review-open")

    @property
    def steps_reviewed(self) -> int:
        return sum(1 for s in self.steps if s.status == "reviewed")

    @property
    def steps_needs_review(self) -> list[str]:
        return [s.name for s in self.steps if s.status in ("executed", "review-open")]

    @property
    def steps_needs_work(self) -> list[str]:
        return [s.name for s in self.steps if s.status in ("skeleton", "ticketed", "planned")]

    @property
    def next_pending_step(self) -> str | None:
        for s in self.steps:
            if not s.has_execution:
                return s.name
        return None


def _summarize_task(task_path: Path, author: str) -> _TaskInfo:
    tn = parse_task_name(f"{author}/{task_path.name}")
    steps = list[_StepInfo]()
    for step_path in list_step_folders(task_path):
        has_execution = any(
            p.is_file() and p.name.startswith("execution-") and p.name.endswith(".md")
            for p in step_path.iterdir()
        )
        review_path = step_path / "review.md"
        has_review = review_path.is_file()
        review_open = _parse_review_open(review_path) if has_review else False
        steps.append(
            _StepInfo(
                name=step_path.name,
                has_ticket=(step_path / "ticket.md").exists(),
                has_plan=(step_path / "plan.md").exists(),
                has_execution=has_execution,
                has_review=has_review,
                review_open=review_open,
            )
        )
    return _TaskInfo(
        author=tn.author,
        task_id=tn.task_id,
        task_folder=task_path.name,
        task_path=task_path,
        has_ticket=(task_path / "ticket.md").exists(),
        steps=steps,
    )


def _next_action(data: dict) -> str:
    if not data["initialized"]:
        return "Run `/hb-init` to initialize the workspace."

    active_tasks = data["active_tasks"]

    for t in active_tasks:
        if not t["has_ticket"]:
            ref = f"{t['author']}/{t['task_folder']}"
            return f"Add `ticket.md` to `{ref}` with Background and Acceptance Criteria."

    for t in active_tasks:
        if t["has_ticket"] and (
            t["total_steps"] == 0 or not any(s["has_ticket"] for s in t["steps"])
        ):
            ref = f"{t['author']}/{t['task_folder']}"
            return f"Add steps to `{ref}` with `/hb-task-plan {ref}` or `/hb-task-step-add {ref}`."

    for t in active_tasks:
        for s in t["steps"]:
            if not s["has_ticket"]:
                ref = f"{t['author']}/{t['task_folder']}"
                return f"Add `ticket.md` to `{ref}/{s['name']}` or run `/hb-task-step-add {ref}`."

    for t in active_tasks:
        for s in t["steps"]:
            if s["has_ticket"] and not s["has_plan"]:
                ref = f"{t['author']}/{t['task_folder']}"
                return f"Run `/hb-task-step-plan {ref}/{s['name']}` to plan the next step."

    for t in active_tasks:
        for s in t["steps"]:
            if s["has_plan"] and not s["has_execution"]:
                ref = f"{t['author']}/{t['task_folder']}"
                return f"Run `/hb-task-step-execute {ref}/{s['name']}` to execute the plan."

    for t in active_tasks:
        if t["total_steps"] > 0 and all(s["has_execution"] for s in t["steps"]):
            ref = f"{t['author']}/{t['task_folder']}"
            return f"All steps executed for `{ref}` — review steps, archive task, or add more steps."

    if not active_tasks:
        return "Start a new task with `/hb-task-create <author/task-id>`."

    return "Review workspace state."


def _render_md(data: dict) -> str:
    def _cell(v: int) -> str:
        return "—" if v == 0 else str(v)

    lines: list[str] = []
    lines.append("# Hashbuild Status")
    lines.append("")
    lines.append("## Initialization")
    lines.append("")
    if data["initialized"]:
        lines.append("`.hb/` initialized")
    else:
        lines.append("`.hb/` not found — run `/hb-init` to set up")

    active_tasks = data["active_tasks"]
    if active_tasks:
        lines += ["", "---", "", "## Active Tasks", ""]
        lines.append("**Legend:**")
        lines.append("")
        lines.append("Step count in each status:")
        lines.append("")
        lines.append(
            "> S = Skeleton · T = Ticketed · P = Planned · E = Executed · RO = Review Open · R = Reviewed"
        )
        lines.append("")
        lines.append("| Task | Ticket | S | T | P | E | RO | R | Total |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for t in active_tasks:
            ref = f"{t['author']}/{t['task_folder']}"
            ticket = "✓" if t["has_ticket"] else "✗"
            lines.append(
                f"| `{ref}` | {ticket}"
                f" | {_cell(t['steps_skeleton'])}"
                f" | {_cell(t['steps_ticketed'])}"
                f" | {_cell(t['steps_planned'])}"
                f" | {_cell(t['steps_executed'])}"
                f" | {_cell(t['steps_review_open'])}"
                f" | {_cell(t['steps_reviewed'])}"
                f" | {t['total_steps']} |"
            )

        has_details = any(
            t["steps_needs_review"] or t["steps_needs_work"] for t in active_tasks
        )
        if has_details:
            lines.append("")
            lines.append("### Task Details")
            for t in active_tasks:
                needs_review = t["steps_needs_review"]
                needs_work = t["steps_needs_work"]
                if not needs_review and not needs_work:
                    continue
                ref = f"{t['author']}/{t['task_folder']}"
                lines.append("")
                lines.append(f"- `{ref}`:")
                if needs_review:
                    lines.append(
                        "  - **Needs review:** " + ", ".join(f"`{s}`" for s in needs_review)
                    )
                if needs_work:
                    lines.append(
                        "  - **Needs work:** " + ", ".join(f"`{s}`" for s in needs_work)
                    )

    archive = data["archive"]
    if archive["recent"]:
        lines += ["", "---", "", "## Archive", ""]
        lines.append(f"**Archived Tasks:** `{archive['count']}`")
        lines.append("")
        lines.append("**Recently Archived Tasks:**")
        lines.append("")
        for entry in archive["recent"]:
            lines.append(f"- `{entry['author']}/{entry['task_folder']}`")

    lines += ["", "---", "", "## Next Action", ""]
    lines.append(_next_action(data))

    return "\n".join(lines) + "\n"


def _build_data(hb: Path) -> dict:
    if not hb.exists():
        return {"initialized": False, "active_tasks": [], "archive": {"count": 0, "recent": []}}

    active_tasks = list[_TaskInfo]()
    active_base = hb / "task" / TASK_FOLDER_ACTIVE
    if active_base.exists():
        for author_dir in sorted(active_base.iterdir()):
            if not author_dir.is_dir():
                continue
            for task_dir in sorted(author_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                active_tasks.append(_summarize_task(task_dir, author_dir.name))

    archived_count = 0
    recent_entries: list[tuple[float, Path]] = []

    archive_base = hb / "task" / TASK_FOLDER_ARCHIVE
    if archive_base.exists():
        for author_dir in archive_base.iterdir():
            if not author_dir.is_dir():
                continue
            for task_dir in author_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                archived_count += 1
                recent_entries.append((task_dir.stat().st_mtime, task_dir))

    recent_entries.sort(key=lambda x: x[0], reverse=True)

    def _archive_entry(p: Path) -> dict[str, str]:
        tn = parse_task_name(f"{p.parent.name}/{p.name}")
        return {"author": tn.author, "task_id": tn.task_id, "task_folder": p.name}

    recent = [_archive_entry(p) for _, p in recent_entries[:5]]

    return {
        "initialized": True,
        "active_tasks": [
            {
                "author": t.author,
                "task_id": t.task_id,
                "task_folder": t.task_folder,
                "task_path": str(t.task_path.absolute()),
                "has_ticket": t.has_ticket,
                "total_steps": len(t.steps),
                "steps": [
                    {
                        "name": s.name,
                        "has_ticket": s.has_ticket,
                        "has_plan": s.has_plan,
                        "has_execution": s.has_execution,
                        "has_review": s.has_review,
                        "status": s.status,
                    }
                    for s in t.steps
                ],
                "steps_skeleton": t.steps_skeleton,
                "steps_ticketed": t.steps_ticketed,
                "steps_planned": t.steps_planned,
                "steps_executed": t.steps_executed,
                "steps_review_open": t.steps_review_open,
                "steps_reviewed": t.steps_reviewed,
                "steps_needs_review": t.steps_needs_review,
                "steps_needs_work": t.steps_needs_work,
                "next_pending_step": t.next_pending_step,
            }
            for t in active_tasks
        ],
        "archive": {
            "count": archived_count,
            "recent": recent,
        },
    }


def cmd_summarize(args: argparse.Namespace) -> None:
    data = _build_data(path_hb())
    if args.format == "md":
        print(_render_md(data))
    else:
        print(json.dumps(data, indent=2))


def def_cli_summarize(subs: typing.Any) -> None:
    p = subs.add_parser("summarize", help="Print workspace summary as JSON for status reporting")
    p.set_defaults(func=cmd_summarize)
    p.add_argument(
        "--format",
        choices=["json", "md"],
        default="json",
        help="Output format: json (default) or md (rendered markdown)",
    )
