"""hb-sdk task and task step commands."""

import argparse
import json
import typing
from datetime import datetime, timezone
from pathlib import Path

from .common import (
    STEP_EXTRA_RE,
    TASK_FOLDER_ACTIVE,
    TASK_FOLDER_ARCHIVE,
    TaskName,
    _die,
    _exists_or_do,
    _find_matching_task_folders,
    _parse_task_name,
    _path_hb_asserted,
    _path_step_ticket,
    _path_task_ticket,
    _progress,
    report_paths,
)


def cmd_task_create(args: argparse.Namespace) -> None:
    paths = list[Path]()
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id; not adding or updating more:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    if len(matching_tasks) == 1:
        tn_existing = matching_tasks[0][1]
        if tn != tn_existing:
            _die(
                f"error: task already exists but components mismatched; existing: {tn_existing}, given: {tn}"
            )

    folder = tn.task_id + (f"-{tn.task_extra}" if tn.task_extra else "")

    task_path = _path_hb_asserted() / "task" / "active" / tn.author / folder
    task_json = task_path / ".hb-task.json"

    task_path.mkdir(parents=True, exist_ok=True)
    paths.append(task_path)

    data: typing.Any = None
    if task_json.exists():
        with open(task_json) as f:
            data = json.load(f)
    else:
        data = {
            "name": args.name,
            "author": tn.author,
            "task_id": tn.task_id,
            "task_extra": tn.task_extra or None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "next_step": 0,
        }

    if args.ticket:
        ticket_path = Path(args.ticket)
        if not ticket_path.exists():
            _die(f"error: ticket file not found: {args.ticket}")
        if ticket_path.suffix != ".md":
            _die(f"error: ticket file must end in .md: {args.ticket}")

        ticket_src = ticket_path.read_text()
        ticket_dest_path = _path_task_ticket(task_path)
        if not ticket_dest_path.exists():
            _progress("importing ticket ...")
            ticket_dest_path.write_text(ticket_src)
            data["ticket_written_at"] = datetime.now(timezone.utc).isoformat()
        else:
            _progress("task already has ticket; checking for content difference ...")
            ticket_dest = ticket_dest_path.read_text()
            if ticket_src != ticket_dest:
                if not args.ticket_overwrite:
                    _die(
                        f"error: source ticket at {ticket_path.absolute()} does not match "
                        f"current ticket at {ticket_dest_path.absolute()}"
                        "; to overwrite, supply --ticket-overwrite"
                    )

                _progress("ticket content has changed and --overwrite-ticket supplied; updating ...")
                ticket_dest_path.write_text(ticket_src)
                data["ticket_written_at"] = datetime.now(timezone.utc).isoformat()
            else:
                _progress("ticket has not changed, skipping ticket update")

        paths.append(ticket_dest_path)

    with open(task_json, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    paths.append(task_json)

    _progress("task create done")
    report_paths(paths)


def cmd_task_path(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {args.name}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    print(matching_tasks[0][0].absolute())


def cmd_task_archive(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {args.name}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    task_path, _ = matching_tasks[0]

    active_base = _path_hb_asserted() / "task" / TASK_FOLDER_ACTIVE
    try:
        task_path.relative_to(active_base)
    except ValueError:
        _die(f"error: task is already archived: {task_path.absolute()}")

    archive_author_dir = _path_hb_asserted() / "task" / TASK_FOLDER_ARCHIVE / tn.author
    archive_author_dir.mkdir(parents=True, exist_ok=True)

    dest = archive_author_dir / task_path.name
    if dest.exists():
        _die(f"error: destination already exists: {dest.absolute()}")

    paths = list[Path]()
    paths.append(task_path)

    active_author_dir = active_base / tn.author
    task_path.rename(dest)
    _progress(f"archived task to {dest.absolute()}")
    paths.append(dest)

    if active_author_dir.exists() and not any(active_author_dir.iterdir()):
        active_author_dir.rmdir()
        _progress(f"removed empty author directory: {active_author_dir.absolute()}")
        paths.append(active_author_dir)

    report_paths(paths)


def cmd_task_unarchive(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {args.name}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    task_path, _ = matching_tasks[0]

    archive_base = _path_hb_asserted() / "task" / TASK_FOLDER_ARCHIVE
    try:
        task_path.relative_to(archive_base)
    except ValueError:
        _die(f"error: task is not archived: {task_path.absolute()}")

    active_author_dir = _path_hb_asserted() / "task" / TASK_FOLDER_ACTIVE / tn.author
    active_author_dir.mkdir(parents=True, exist_ok=True)

    dest = active_author_dir / task_path.name
    if dest.exists():
        _die(f"error: destination already exists: {dest.absolute()}")

    paths = list[Path]()
    paths.append(task_path)

    archive_author_dir = archive_base / tn.author
    task_path.rename(dest)
    _progress(f"unarchived task to {dest.absolute()}")
    paths.append(dest)

    if archive_author_dir.exists() and not any(archive_author_dir.iterdir()):
        archive_author_dir.rmdir()
        _progress(f"removed empty author directory: {archive_author_dir.absolute()}")
        paths.append(archive_author_dir)

    report_paths(paths)


def _parse_step_ref(ref: str) -> tuple[TaskName, int]:
    parts = ref.rsplit("/", 1)
    if len(parts) != 2:
        _die(
            f"error: invalid step ref '{ref}'\n"
            f"  expected: <author>/<task_id>[-extra]/<step_n>\n"
            f"  step_n: integer, step-<n>, or step-<n>-<flavor>"
        )
    task_part, step_part = parts
    # accept: "0", "step-0", "step-0-some-flavor"
    n_str = step_part.removeprefix("step-").split("-")[0]
    try:
        step_n = int(n_str)
    except ValueError:
        _die(
            f"error: invalid step id '{step_part}' in '{ref}'\n"
            f"  expected: integer, step-<n>, or step-<n>-<flavor>"
        )
    tn = _parse_task_name(task_part)
    return tn, step_n


def _find_step_folder(task_path: Path, step_n: int) -> Path:
    prefix = f"step-{step_n}"
    matches = [
        p for p in task_path.iterdir() if p.is_dir() and (p.name == prefix or p.name.startswith(prefix + "-"))
    ]
    if len(matches) == 0:
        _die(f"error: step {step_n} not found in {task_path.absolute()}")
    if len(matches) > 1:
        _die(
            f"error: multiple step folders for step {step_n} in {task_path.absolute()}:\n"
            + "\n".join(str(m.absolute()) for m in sorted(matches))
        )
    return matches[0]


def _list_step_folders(task_path: Path) -> list[Path]:
    """Return all step-* directories sorted by step number ascending."""
    steps = list[tuple[int, Path]]()
    for p in task_path.iterdir():
        if not p.is_dir() or not p.name.startswith("step-"):
            continue
        n_str = p.name.removeprefix("step-").split("-")[0]
        try:
            steps.append((int(n_str), p))
        except ValueError:
            continue
    return [p for _, p in sorted(steps)]


def cmd_task_step_add(args: argparse.Namespace) -> None:
    paths = list[Path]()
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {args.name}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    task_path = matching_tasks[0][0]
    task_json = task_path / ".hb-task.json"

    if not task_json.exists():
        _die(f"error: task metadata not found: {task_json.absolute()}")

    with open(task_json) as f:
        data = json.load(f)

    step_n = data["next_step"]

    flavor = args.flavor
    if flavor is not None:
        if not STEP_EXTRA_RE.match(flavor):
            _die(f"error: invalid flavor '{flavor}'\n  slug allowed chars: [a-z-], must start with [a-z]")
        step_folder_name = f"step-{step_n}-{flavor}"
    else:
        step_folder_name = f"step-{step_n}"

    step_path = task_path / step_folder_name
    _exists_or_do(step_path, lambda p: p.mkdir(parents=True, exist_ok=True))
    paths.append(step_path)

    ticket_dest_path = _path_step_ticket(step_path)
    if args.ticket:
        ticket_path = Path(args.ticket)
        if not ticket_path.exists():
            _die(f"error: ticket file not found: {args.ticket}")
        if ticket_path.suffix != ".md":
            _die(f"error: ticket file must end in .md: {args.ticket}")

        ticket_src = ticket_path.read_text()
        if not ticket_dest_path.exists():
            _progress("importing ticket ...")
            ticket_dest_path.write_text(ticket_src)
        else:
            _progress("step already has ticket; checking for content difference ...")
            ticket_dest = ticket_dest_path.read_text()
            if ticket_src != ticket_dest:
                if not args.ticket_overwrite:
                    _die(
                        f"error: source ticket at {ticket_path.absolute()} does not match "
                        f"current ticket at {ticket_dest_path.absolute()}"
                        "; to overwrite, supply --ticket-overwrite"
                    )
                _progress("ticket content has changed and --ticket-overwrite supplied; updating ...")
                ticket_dest_path.write_text(ticket_src)
            else:
                _progress("ticket has not changed, skipping ticket update")
    else:
        _exists_or_do(
            ticket_dest_path,
            lambda p: p.write_text("# Background\n\n- \n\n# Acceptance Criteria\n\n1. \n"),
        )

    paths.append(ticket_dest_path)

    data["next_step"] = step_n + 1

    with open(task_json, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    paths.append(task_json)

    _progress("task step add done")
    report_paths(paths)


def cmd_task_step_path(args: argparse.Namespace) -> None:
    tn, step_n = _parse_step_ref(args.step_ref)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {tn.author}/{tn.task_id}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    task_path = matching_tasks[0][0]
    step_path = _find_step_folder(task_path, step_n)
    print(step_path.absolute())


def cmd_task_step_number(args: argparse.Namespace) -> None:
    _, step_n = _parse_step_ref(args.step_ref)
    print(step_n)


def cmd_task_step_list(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.name)

    matching_tasks = _find_matching_task_folders(tn)
    if len(matching_tasks) == 0:
        _die(f"error: task not found: {args.name}")
    if len(matching_tasks) > 1:
        _die(
            "error: found multiple existing tasks with same author/task_id:\n"
            + "\n".join(str(p.absolute()) for p, _ in matching_tasks)
        )

    task_path = matching_tasks[0][0]
    for step_path in _list_step_folders(task_path):
        print(step_path.absolute())


def cmd_task_step_execution_slug(args: argparse.Namespace) -> None:
    from datetime import datetime
    ts = datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S%z")
    print(f"execution-{ts}.md")


def _def_cli_task(subs: typing.Any) -> None:
    p_task = subs.add_parser("task", help="Task operations")
    task_subs = p_task.add_subparsers(dest="task_command", metavar="<action>")
    task_subs.required = True

    p_ta = task_subs.add_parser("archive", help="Archive a task (move from active to archive)")
    p_ta.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_ta.set_defaults(func=cmd_task_archive)

    p_tu = task_subs.add_parser("unarchive", help="Unarchive a task (move from archive to active)")
    p_tu.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_tu.set_defaults(func=cmd_task_unarchive)

    p_tp = task_subs.add_parser("path", help="Print absolute path of a task folder")
    p_tp.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_tp.set_defaults(func=cmd_task_path)

    p_tc: argparse.ArgumentParser = task_subs.add_parser(
        "create", help="Create or verify task skeleton (idempotent)"
    )
    p_tc.add_argument("--ticket", metavar="<path>", help="Seed task from this ticket file")
    p_tc.add_argument(
        "--ticket-overwrite",
        default=False,
        action="store_true",
        help="Overwrite ticket if it exists",
    )
    p_tc.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_tc.set_defaults(func=cmd_task_create)

    p_step = task_subs.add_parser("step", help="Step operations")
    step_subs = p_step.add_subparsers(dest="step_command", metavar="<action>")
    step_subs.required = True

    p_sa = step_subs.add_parser("add", help="Add next step folder to a task")
    p_sa.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_sa.add_argument("--flavor", metavar="<slug>", help="Optional step flavor suffix (slug chars: [a-z-])")
    p_sa.add_argument("--ticket", metavar="<path>", help="Seed step from this ticket file (.md)")
    p_sa.add_argument(
        "--ticket-overwrite",
        default=False,
        action="store_true",
        help="Overwrite ticket if it exists",
    )
    p_sa.set_defaults(func=cmd_task_step_add)

    p_sp = step_subs.add_parser("path", help="Print absolute path of a step folder")
    p_sp.add_argument(
        "step_ref",
        metavar="<step_ref>",
        help="Step reference: author/task_id[-extra]/<step_n> where step_n is an integer, step-<n>, or step-<n>-<flavor>",
    )
    p_sp.set_defaults(func=cmd_task_step_path)

    p_sn = step_subs.add_parser("number", help="Print the numeric step number from a step reference")
    p_sn.add_argument(
        "step_ref",
        metavar="<step_ref>",
        help="Step reference: author/task_id[-extra]/<step_n> where step_n is an integer, step-<n>, or step-<n>-<flavor>",
    )
    p_sn.set_defaults(func=cmd_task_step_number)

    p_sl = step_subs.add_parser(
        "list", help="List step folders in ascending step-number order; prints one absolute path per line"
    )
    p_sl.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
    p_sl.set_defaults(func=cmd_task_step_list)

    p_es = step_subs.add_parser(
        "execution-slug", help="Print an execution filename slug with local timestamp"
    )
    p_es.set_defaults(func=cmd_task_step_execution_slug)
