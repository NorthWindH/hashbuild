"""Plan document (plan.md) linting subcommands for hb-sdk."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import die

MAX_SENTENCE_CHARS = 120
MAX_SENTENCES_PER_PARAGRAPH = 3
MAX_SENTENCES_PER_BULLET = 1

_FENCE_RE = re.compile(r"^```")
_BULLET_MARKER_RE = re.compile(r"^[-*]\s+")
_NUMBERED_MARKER_RE = re.compile(r"^\d+\.\s+")
_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9`"*_])')


@dataclass(eq=True)
class LintViolation:
    line: int
    kind: str  # "sentence-length" | "paragraph-length" | "bullet-length"
    message: str


def _is_exempt(stripped: str) -> bool:
    """Tables and headings are exempt from the prose limits (diagrams are exempt via fencing)."""
    return not stripped or stripped.startswith("|") or stripped.startswith("#")


def _starts_new_block(stripped: str) -> bool:
    """A blockquote, bullet, or numbered-list marker always starts a new logical block."""
    return bool(
        stripped.startswith(">") or _BULLET_MARKER_RE.match(stripped) or _NUMBERED_MARKER_RE.match(stripped)
    )


def _classify(stripped: str) -> tuple[bool, str]:
    """Return (is_bullet, content) for a block-starting line, stripping its lead-in marker(s)."""
    if stripped.startswith(">"):
        stripped = stripped.lstrip(">").strip()
    is_bullet = bool(_BULLET_MARKER_RE.match(stripped) or _NUMBERED_MARKER_RE.match(stripped))
    content = _BULLET_MARKER_RE.sub("", stripped, count=1)
    content = _NUMBERED_MARKER_RE.sub("", content, count=1)
    return is_bullet, content


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [p for p in _SENTENCE_SPLIT_RE.split(text) if p.strip()]


def _iter_blocks(text: str) -> list[tuple[int, bool, str]]:
    """Group lines into logical blocks (paragraphs or bullets), joining soft-wrapped
    continuation lines. Fenced code blocks, table rows, and headings are dropped
    entirely. Returns `(start_line, is_bullet, content)` per block.
    """
    lines = text.splitlines()
    n = len(lines)
    blocks: list[tuple[int, bool, str]] = []
    in_fence = False
    i = 0

    while i < n:
        stripped = lines[i].strip()

        if _FENCE_RE.match(stripped):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence or _is_exempt(stripped):
            i += 1
            continue

        start_line = i + 1
        is_bullet, first_content = _classify(stripped)
        parts = [first_content] if first_content else []
        i += 1

        while i < n:
            next_stripped = lines[i].strip()
            if not next_stripped or _FENCE_RE.match(next_stripped) or _is_exempt(next_stripped):
                break
            if _starts_new_block(next_stripped):
                break
            parts.append(next_stripped)
            i += 1

        content = " ".join(p for p in parts if p)
        if content:
            blocks.append((start_line, is_bullet, content))

    return blocks


def lint_plan_text(text: str) -> list[LintViolation]:
    """Check `text` against plan-template.md's prose limits: at most
    `MAX_SENTENCES_PER_PARAGRAPH` sentences per paragraph (or
    `MAX_SENTENCES_PER_BULLET` per bullet/numbered item), each sentence at most
    `MAX_SENTENCE_CHARS` characters. Soft-wrapped continuation lines are joined
    before counting. Fenced code blocks (diagrams), table rows, and headings
    are exempt.
    """
    violations: list[LintViolation] = []
    for start_line, is_bullet, content in _iter_blocks(text):
        sentences = _split_sentences(content)
        cap = MAX_SENTENCES_PER_BULLET if is_bullet else MAX_SENTENCES_PER_PARAGRAPH
        if len(sentences) > cap:
            violations.append(
                LintViolation(
                    start_line,
                    "bullet-length" if is_bullet else "paragraph-length",
                    f"{len(sentences)} sentences (max {cap})",
                )
            )
        for sentence in sentences:
            if len(sentence) > MAX_SENTENCE_CHARS:
                violations.append(
                    LintViolation(
                        start_line,
                        "sentence-length",
                        f"sentence is {len(sentence)} chars (max {MAX_SENTENCE_CHARS}): {sentence!r}",
                    )
                )
    return violations


def lint_plan_file(path: Path) -> list[LintViolation]:
    if not path.exists():
        die(f"error: file not found: {path}")
    return lint_plan_text(path.read_text())


def cmd_plan_lint(args: argparse.Namespace) -> None:
    path = Path(args.path)
    violations = lint_plan_file(path)
    if not violations:
        print(f"{path}: OK — no sentence/paragraph/bullet-length violations")
        return

    for v in violations:
        print(f"{path}:{v.line}: {v.kind}: {v.message}")
    die(f"error: {len(violations)} violation(s) found in {path}")


def def_cli_plan(subs: Any) -> None:
    p_plan = subs.add_parser("plan", help="Plan document (plan.md) operations")
    plan_subs = p_plan.add_subparsers(dest="plan_command", metavar="<action>")
    plan_subs.required = True

    p_lint = plan_subs.add_parser(
        "lint", help="Check a plan.md's prose against sentence/paragraph/bullet-length limits"
    )
    p_lint.add_argument("path", metavar="<path>", help="Path to the plan.md file to check")
    p_lint.set_defaults(func=cmd_plan_lint)
