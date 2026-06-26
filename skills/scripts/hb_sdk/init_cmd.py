"""hb-sdk init command."""

import argparse
import typing
from pathlib import Path

from .common import _exists_or_do, _path_hb, _path_hb_git_keep, _progress, report_paths


def cmd_init(args: argparse.Namespace) -> None:
    _progress(f"initializing hashbuild (hb) framework directory at {_path_hb().absolute()}")
    paths = list[Path]()
    paths.append(_exists_or_do(_path_hb(), lambda p: p.mkdir(parents=True, exist_ok=True)))
    paths.append(_exists_or_do(_path_hb_git_keep(), lambda p: p.touch(exist_ok=True)))

    _progress("init done; created hashbuild (hb) framework directory")
    report_paths(paths)


def _def_cli_init(subs: typing.Any) -> None:
    p_init = subs.add_parser("init", help="Initialize hashbuild in project directory (idempotent)")
    p_init.set_defaults(func=cmd_init)
