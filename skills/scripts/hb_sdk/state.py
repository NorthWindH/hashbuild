"""State persistence subcommands for hb-sdk."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import path_hb, path_hb_asserted, path_hb_state, progress
from .next_action import compute_next_action, render_md_lines, to_dict
from .summarize import build_data


def write_state(record: dict[str, str | None]) -> Path:
    """Overwrite state file with `record`. Returns the path written."""
    path_hb_asserted()
    p = path_hb_state()
    progress(f"writing state to {p.absolute()} ...")
    p.write_text(json.dumps(record, indent=2) + "\n")
    return p


def read_state() -> dict[str, str | None] | None:
    """Return the current record, or None if state file does not exist."""
    path_hb_asserted()
    p = path_hb_state()
    if not p.exists():
        return None
    return json.loads(p.read_text())


def cmd_state_record(args: argparse.Namespace) -> None:
    record: dict[str, Any] = {
        "skill": args.skill,
        "outcome": args.outcome,
        "timestamp": datetime.now().astimezone().isoformat(),
        "task": args.task,
        "step": args.step,
    }
    write_state(record)


def cmd_state_show(args: argparse.Namespace) -> None:
    record = read_state()
    if args.format == "md":
        if record is None:
            print("No recorded state.")
        else:
            lines = [
                f"Skill: {record.get('skill') or '—'}",
                f"Outcome: {record.get('outcome') or '—'}",
                f"Timestamp: {record.get('timestamp') or '—'}",
                f"Task: {record.get('task') or '—'}",
                f"Step: {record.get('step') or '—'}",
            ]
            print("\n".join(lines))
    else:
        print(json.dumps(record if record is not None else {}, indent=2))


def cmd_state_next_action(args: argparse.Namespace) -> None:
    state = read_state() if path_hb().exists() else None
    data = build_data(path_hb())
    entries = compute_next_action(state, data)
    if args.format == "md":
        for ref, na in entries:
            print("\n".join(render_md_lines(na)))
    else:
        print(json.dumps([to_dict(ref, na) for ref, na in entries], indent=2))


def def_cli_state(subs: Any) -> None:
    p_state = subs.add_parser("state", help="State persistence operations")
    state_subs = p_state.add_subparsers(dest="state_command", metavar="<action>")
    state_subs.required = True

    p_record = state_subs.add_parser("record", help="Record last-executed-action state")
    p_record.add_argument("--skill", required=True, metavar="<name>")
    p_record.add_argument("--outcome", required=True, metavar="<outcome>")
    p_record.add_argument("--task", metavar="<ref>")
    p_record.add_argument("--step", metavar="<ref>")
    p_record.set_defaults(func=cmd_state_record)

    p_show = state_subs.add_parser("show", help="Show current recorded state")
    p_show.add_argument("--format", choices=["json", "md"], default="json")
    p_show.set_defaults(func=cmd_state_show)

    p_na = state_subs.add_parser("next-action", help="Print derived next action for active task(s)")
    p_na.add_argument("--format", choices=["json", "md"], default="json")
    p_na.set_defaults(func=cmd_state_next_action)
