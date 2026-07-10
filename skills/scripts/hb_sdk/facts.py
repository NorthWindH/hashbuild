"""Facts store subcommands for hb-sdk."""

import argparse
from pathlib import Path
from typing import Any

from .common import path_hb_asserted, path_hb_facts, progress


def write_facts(content: str) -> Path:
    """Overwrite the facts store with `content`. Returns the path written."""
    path_hb_asserted()
    p = path_hb_facts()
    progress(f"writing facts to {p.absolute()} ...")
    p.write_text(content)
    return p


def read_facts() -> str:
    """Return the facts store's exact contents, or "" if it does not exist."""
    p = path_hb_facts()
    if not p.exists():
        return ""
    return p.read_text()


def cmd_facts_write(args: argparse.Namespace) -> None:
    write_facts(args.content)


def cmd_facts_read(args: argparse.Namespace) -> None:
    print(read_facts(), end="")


def def_cli_facts(subs: Any) -> None:
    p_facts = subs.add_parser("facts", help="Facts store operations")
    facts_subs = p_facts.add_subparsers(dest="facts_command", metavar="<action>")
    facts_subs.required = True

    p_write = facts_subs.add_parser("write", help="Overwrite the facts store with new content")
    p_write.add_argument("content", metavar="<content>")
    p_write.set_defaults(func=cmd_facts_write)

    p_read = facts_subs.add_parser("read", help="Print the current facts store contents")
    p_read.set_defaults(func=cmd_facts_read)
