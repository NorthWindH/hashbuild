"""Idea subcommands for hb-sdk."""

import argparse
import json
from pathlib import Path

from .common import die, path_hb_asserted


def path_idea_dir(author: str) -> Path:
    return path_hb_asserted() / "idea" / author


def path_idea_file(author: str) -> Path:
    return path_hb_asserted() / "idea" / author / "ideas.json"


# TODO REVIEW
# - find all function definitions in this file
# - ensure that every function definition has full type annotations on args and return values

# TODO REVIEW add type annotations to return types below


def _load_idea_file(author: str) -> dict:
    p = path_idea_file(author)
    if not p.exists():
        return {"ideas": []}
    return json.loads(p.read_text())


def _save_idea_file(author: str, data: dict) -> None:
    d = path_idea_dir(author)
    d.mkdir(parents=True, exist_ok=True)
    (d / "ideas.json").write_text(json.dumps(data, indent=2) + "\n")


def _parse_idea_ref(ref: str) -> tuple[str, int]:
    if "/" not in ref:
        die(f"error: invalid idea ref '{ref}'; expected '<author>/<index>'")
    author, _, idx_str = ref.rpartition("/")
    try:
        idx = int(idx_str)
    except ValueError:
        die(f"error: invalid idea ref '{ref}'; index must be an integer")
    if idx < 0:
        die(f"error: invalid idea ref '{ref}'; index must be non-negative")
    return author, idx


def cmd_idea_add(args: argparse.Namespace) -> None:
    data = _load_idea_file(args.author)
    data["ideas"].append({"content": args.content})
    _save_idea_file(args.author, data)
    print(f"{args.author}/{len(data['ideas']) - 1}")


def cmd_idea_remove(args: argparse.Namespace) -> None:
    author, idx = _parse_idea_ref(args.idea_ref)
    data = _load_idea_file(author)
    ideas = data["ideas"]
    if idx >= len(ideas):
        die(f"error: idea {args.idea_ref} not found; index {idx} out of range (have {len(ideas)})")
    ideas.pop(idx)
    _save_idea_file(author, data)


def cmd_idea_show(args: argparse.Namespace) -> None:
    target = args.target
    hb_path = path_hb_asserted()

    if target is None:
        results = []
        idea_root = hb_path / "idea"
        if idea_root.exists():
            for f in sorted(idea_root.glob("*/ideas.json")):
                author = f.parent.name
                file_data = json.loads(f.read_text())
                for i, entry in enumerate(file_data["ideas"]):
                    results.append({"index": i, "author": author, **entry})
        print(json.dumps(results, indent=2))
    elif "/" in target:
        author, idx = _parse_idea_ref(target)
        data = _load_idea_file(author)
        ideas = data["ideas"]
        if idx >= len(ideas):
            die(f"error: idea {target} not found; index {idx} out of range (have {len(ideas)})")
        print(json.dumps({"index": idx, **ideas[idx]}, indent=2))
    else:
        author = target
        data = _load_idea_file(author)
        results = [{"index": i, **entry} for i, entry in enumerate(data["ideas"])]
        print(json.dumps(results, indent=2))


def cmd_idea_set_content(args: argparse.Namespace) -> None:
    author, idx = _parse_idea_ref(args.idea_ref)
    data = _load_idea_file(author)
    ideas = data["ideas"]
    if idx >= len(ideas):
        die(f"error: idea {args.idea_ref} not found; index {idx} out of range (have {len(ideas)})")
    ideas[idx]["content"] = args.new_content
    _save_idea_file(author, data)


def def_cli_idea(subs: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    p_idea = subs.add_parser("idea", help="Idea operations")
    idea_subs = p_idea.add_subparsers(dest="idea_command", metavar="<action>")
    idea_subs.required = True

    p_add = idea_subs.add_parser("add", help="Add a new idea")
    p_add.add_argument("author")
    p_add.add_argument("content")
    p_add.set_defaults(func=cmd_idea_add)

    p_rm = idea_subs.add_parser("remove", help="Remove an idea by ref")
    p_rm.add_argument("idea_ref", metavar="<author>/<index>")
    p_rm.set_defaults(func=cmd_idea_remove)

    p_show = idea_subs.add_parser("show", help="Show ideas")
    p_show.add_argument("target", nargs="?", default=None, metavar="[<author>[/<index>]]")
    p_show.set_defaults(func=cmd_idea_show)

    p_sc = idea_subs.add_parser("set-content", help="Update idea content")
    p_sc.add_argument("idea_ref", metavar="<author>/<index>")
    p_sc.add_argument("new_content")
    p_sc.set_defaults(func=cmd_idea_set_content)
