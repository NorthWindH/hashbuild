"""Tests for hb-sdk init command."""

from pathlib import Path

from helpers import init, run


def test_init_creates_hb_dir(tmp_path: Path) -> None:
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()
    assert (tmp_path / ".hb" / ".gitkeep").exists()


def test_init_idempotent(tmp_path: Path) -> None:
    init(tmp_path)
    init(tmp_path)
    assert (tmp_path / ".hb").is_dir()


def test_init_fails_without_hb(tmp_path: Path) -> None:
    result = run(["task", "create", "hasan/abc-1"], tmp_path, ok=False)
    assert ".hb/ directory not found" in result.stderr
