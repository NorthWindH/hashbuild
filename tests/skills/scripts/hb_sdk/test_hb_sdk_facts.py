"""Tests for hb-sdk facts subcommands."""

from pathlib import Path

from helpers import facts_read, facts_write, init, run

# ── facts read — missing file ────────────────────────────────────────────────


def test_facts_read_missing_file_returns_empty(tmp_path: Path) -> None:
    init(tmp_path)
    result = facts_read(tmp_path)
    assert result.stdout == ""


def test_facts_read_no_hb_at_all_returns_empty(tmp_path: Path) -> None:
    result = facts_read(tmp_path)
    assert result.stdout == ""


# ── facts write — creates file (AC3.1/AC3.2, AC6.2) ─────────────────────────


def test_facts_write_creates_file_when_absent(tmp_path: Path) -> None:
    init(tmp_path)
    facts_write(tmp_path, "hello")
    assert (tmp_path / ".hb" / "facts.md").read_text() == "hello"


def test_facts_write_no_hb_dies(tmp_path: Path) -> None:
    result = facts_write(tmp_path, "hello", ok=False)
    assert result.returncode != 0
    assert ".hb/" in result.stderr


# ── facts write/read — round trip and overwrite (AC3.1, AC6.3) ──────────────


def test_facts_write_then_read_round_trips_exactly(tmp_path: Path) -> None:
    init(tmp_path)
    content = "- fact one\n- fact two, no trailing newline"
    facts_write(tmp_path, content)
    result = facts_read(tmp_path)
    assert result.stdout == content


def test_facts_write_overwrites_prior_content(tmp_path: Path) -> None:
    init(tmp_path)
    facts_write(tmp_path, "A")
    facts_write(tmp_path, "B")
    result = facts_read(tmp_path)
    assert result.stdout == "B"


# ── facts write — missing required arg ──────────────────────────────────────


def test_facts_write_requires_content_arg(tmp_path: Path) -> None:
    init(tmp_path)
    result = run(["facts", "write"], tmp_path, ok=False)
    assert result.returncode != 0
