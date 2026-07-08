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


def test_init_adds_state_json_to_gitignore(tmp_path: Path) -> None:
    init(tmp_path)
    assert ".hb/state.json" in (tmp_path / ".gitignore").read_text().splitlines()


def test_init_twice_does_not_duplicate_gitignore_entry(tmp_path: Path) -> None:
    init(tmp_path)
    init(tmp_path)
    lines = (tmp_path / ".gitignore").read_text().splitlines()
    assert lines.count(".hb/state.json") == 1


def test_init_preserves_existing_gitignore_content(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules\n")
    init(tmp_path)
    lines = (tmp_path / ".gitignore").read_text().splitlines()
    assert "node_modules" in lines
    assert ".hb/state.json" in lines
