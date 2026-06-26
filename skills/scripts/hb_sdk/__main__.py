"""hb-sdk CLI entry point."""

import argparse

# TODO REVIEW this file is importing private symbols (_def_*); fix so that these symbols are public (ie def_*).
# Do the same for all other cases in hb_sdk where a .py module is importing a private symbol from another .py module.
from .commit import _def_cli_commit
from .init_cmd import _def_cli_init
from .summarize import _def_cli_summarize
from .task import _def_cli_task


def main() -> None:
    parser = argparse.ArgumentParser(prog="hb-sdk", description="Hashbuild SDK CLI")
    subs = parser.add_subparsers(dest="command", metavar="<command>")
    subs.required = True

    _def_cli_init(subs)
    _def_cli_task(subs)
    _def_cli_summarize(subs)
    _def_cli_commit(subs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
