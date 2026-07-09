"""hb-sdk init command."""

import argparse
import typing
from pathlib import Path

from .common import ensure_gitignore_entry, exists_or_do, path_hb, path_hb_git_keep, progress, report_paths


def cmd_init(args: argparse.Namespace) -> None:
    progress(f"initializing hashbuild (hb) framework directory at {path_hb().absolute()}")
    paths = list[Path]()
    paths.append(exists_or_do(path_hb(), lambda p: p.mkdir(parents=True, exist_ok=True)))
    paths.append(exists_or_do(path_hb_git_keep(), lambda p: p.touch(exist_ok=True)))

    # TODO REVIEW when gitignore gets updated, it should be added to paths list so the updated path can be reported
    ensure_gitignore_entry()

    progress("init done; created hashbuild (hb) framework directory")
    report_paths(paths)


def def_cli_init(subs: typing.Any) -> None:
    p_init = subs.add_parser("init", help="Initialize hashbuild in project directory (idempotent)")
    p_init.set_defaults(func=cmd_init)
