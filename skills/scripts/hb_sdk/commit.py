"""hb-sdk commit write-message-file commands."""

import argparse
import tempfile
import typing

from .common import TAG_RE, die, parse_task_name


def _commit_write_message_file(subject: str, long: str | None) -> None:
    message = subject + "\n"
    if long:
        message += "\n" + long + "\n"
    fd, path = tempfile.mkstemp(prefix="hb-commit-", suffix=".txt")
    with open(fd, "w") as f:
        f.write(message)
    print(path)


def _validate_tag(tag: str) -> None:
    if not TAG_RE.match(tag):
        die(
            f"error: invalid --tag value '{tag}'\n"
            "  must match [a-z][a-z0-9]*(-[a-z0-9]+)*\n"
            "  (lowercase letters and digits, hyphens allowed between segments)"
        )


def cmd_commit_wmf_plain(args: argparse.Namespace) -> None:
    _commit_write_message_file(f"hb: {args.short}", args.long)


def cmd_commit_wmf_task(args: argparse.Namespace) -> None:
    tn = parse_task_name(args.task)
    if args.tag:
        _validate_tag(args.tag)
        _commit_write_message_file(f"{tn.task_id}: ({args.tag}) {args.short}", args.long)
    else:
        _commit_write_message_file(f"{tn.task_id}: {args.short}", args.long)


def cmd_commit_wmf_task_step(args: argparse.Namespace) -> None:
    tn = parse_task_name(args.task)
    if args.tag:
        _validate_tag(args.tag)
        _commit_write_message_file(f"{tn.task_id}/step-{args.step}: ({args.tag}) {args.short}", args.long)
    else:
        _commit_write_message_file(f"{tn.task_id}/step-{args.step}: {args.short}", args.long)


def def_cli_commit(subs: typing.Any) -> None:
    p_commit = subs.add_parser("commit", help="Commit operations")
    commit_subs = p_commit.add_subparsers(dest="commit_command", metavar="<action>")
    commit_subs.required = True

    p_wmf = commit_subs.add_parser(
        "write-message-file", help="Write commit message to a temp file; prints path"
    )
    wmf_subs = p_wmf.add_subparsers(dest="wmf_mode", metavar="<mode>")
    wmf_subs.required = True

    p_plain = wmf_subs.add_parser("plain", help="SDK-level commit (no task)")
    p_plain.add_argument("--short", required=True, metavar="<desc>", help="One-line description")
    p_plain.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_plain.set_defaults(func=cmd_commit_wmf_plain)

    p_task = wmf_subs.add_parser("task", help="Task-level commit")
    p_task.add_argument("--task", required=True, metavar="<task>", help="Fully-qualified task name")
    p_task.add_argument("--short", required=True, metavar="<desc>", help="One-line description")
    p_task.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_task.add_argument("--tag", metavar="<tag>", help="Optional lifecycle tag; injected as (tag) in subject")
    p_task.set_defaults(func=cmd_commit_wmf_task)

    p_task_step = wmf_subs.add_parser("task-step", help="Step-level commit")
    p_task_step.add_argument("--task", required=True, metavar="<task>", help="Fully-qualified task name")
    p_task_step.add_argument("--step", required=True, type=int, metavar="<n>", help="Step number")
    p_task_step.add_argument("--short", required=True, metavar="<desc>", help="One-line description")
    p_task_step.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_task_step.add_argument(
        "--tag", metavar="<tag>", help="Optional lifecycle tag; injected as (tag) in subject"
    )
    p_task_step.set_defaults(func=cmd_commit_wmf_task_step)
