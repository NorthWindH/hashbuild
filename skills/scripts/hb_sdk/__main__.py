"""hb-sdk CLI entry point."""

import argparse

from .commit import def_cli_commit
from .init_cmd import def_cli_init
from .summarize import def_cli_summarize
from .task import def_cli_task


def main() -> None:
    parser = argparse.ArgumentParser(prog="hb-sdk", description="Hashbuild SDK CLI")
    subs = parser.add_subparsers(dest="command", metavar="<command>")
    subs.required = True

    def_cli_init(subs)
    def_cli_task(subs)
    def_cli_summarize(subs)
    def_cli_commit(subs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
