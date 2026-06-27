"""Tests for hb-sdk idea subcommands."""

import json
from pathlib import Path

from helpers import idea_add, idea_remove, idea_set_content, idea_show, init

# ── idea add ──────────────────────────────────────────────────────────────────


def test_idea_add_basic(tmp_path: Path) -> None:
    init(tmp_path)
    result = idea_add(tmp_path, "alice", "first idea")
    assert result.stdout.strip() == "alice/0"
    ideas_file = tmp_path / ".hb" / "idea" / "alice" / "ideas.json"
    assert ideas_file.exists()
    data = json.loads(ideas_file.read_text())
    assert len(data["ideas"]) == 1
    assert data["ideas"][0]["content"] == "first idea"
    shown = json.loads(idea_show(tmp_path, "alice/0").stdout)
    assert shown["index"] == 0
    assert shown["content"] == "first idea"


def test_idea_add_sequential_indices(tmp_path: Path) -> None:
    init(tmp_path)
    r0 = idea_add(tmp_path, "alice", "idea 0")
    r1 = idea_add(tmp_path, "alice", "idea 1")
    r2 = idea_add(tmp_path, "alice", "idea 2")
    assert r0.stdout.strip() == "alice/0"
    assert r1.stdout.strip() == "alice/1"
    assert r2.stdout.strip() == "alice/2"
    shown = json.loads(idea_show(tmp_path, "alice").stdout)
    assert len(shown) == 3


def test_idea_add_creates_parent_dir(tmp_path: Path) -> None:
    init(tmp_path)
    assert not (tmp_path / ".hb" / "idea" / "alice").exists()
    idea_add(tmp_path, "alice", "some idea")
    assert (tmp_path / ".hb" / "idea" / "alice").is_dir()


def test_idea_add_no_hb(tmp_path: Path) -> None:
    result = idea_add(tmp_path, "alice", "some idea", ok=False)
    assert ".hb/" in result.stderr


# ── idea remove ───────────────────────────────────────────────────────────────


def test_idea_remove_basic(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "idea 0")
    idea_add(tmp_path, "alice", "idea 1")
    idea_remove(tmp_path, "alice/0")
    ideas_file = tmp_path / ".hb" / "idea" / "alice" / "ideas.json"
    assert ideas_file.exists()
    data = json.loads(ideas_file.read_text())
    assert len(data["ideas"]) == 1
    assert data["ideas"][0]["content"] == "idea 1"


def test_idea_remove_shifts_indices(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "idea 0")
    idea_add(tmp_path, "alice", "idea 1")
    idea_add(tmp_path, "alice", "idea 2")
    idea_remove(tmp_path, "alice/1")
    shown = json.loads(idea_show(tmp_path, "alice").stdout)
    assert len(shown) == 2
    assert shown[0]["index"] == 0
    assert shown[0]["content"] == "idea 0"
    assert shown[1]["index"] == 1
    assert shown[1]["content"] == "idea 2"


def test_idea_remove_out_of_range(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "idea 0")
    result = idea_remove(tmp_path, "alice/99", ok=False)
    assert result.returncode != 0
    assert "error" in result.stderr
    data = json.loads((tmp_path / ".hb" / "idea" / "alice" / "ideas.json").read_text())
    assert len(data["ideas"]) == 1


def test_idea_remove_no_hb(tmp_path: Path) -> None:
    result = idea_remove(tmp_path, "alice/0", ok=False)
    assert ".hb/" in result.stderr


# ── idea show ─────────────────────────────────────────────────────────────────


def test_idea_show_all_no_ideas(tmp_path: Path) -> None:
    init(tmp_path)
    result = idea_show(tmp_path)
    data = json.loads(result.stdout)
    assert data == []


def test_idea_show_all_multiple_authors(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "alice's idea")
    idea_add(tmp_path, "bob", "bob's idea")
    result = idea_show(tmp_path)
    data = json.loads(result.stdout)
    assert len(data) == 2
    authors = {entry["author"] for entry in data}
    assert authors == {"alice", "bob"}


def test_idea_show_author(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "only alice")
    idea_add(tmp_path, "bob", "bob's idea")
    result = idea_show(tmp_path, "alice")
    data = json.loads(result.stdout)
    assert len(data) == 1
    assert data[0]["content"] == "only alice"
    assert "author" not in data[0]


def test_idea_show_author_empty(tmp_path: Path) -> None:
    init(tmp_path)
    result = idea_show(tmp_path, "alice")
    data = json.loads(result.stdout)
    assert data == []


def test_idea_show_single(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "target idea")
    result = idea_show(tmp_path, "alice/0")
    data = json.loads(result.stdout)
    assert data["index"] == 0
    assert data["content"] == "target idea"


def test_idea_show_single_not_found(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "some idea")
    result = idea_show(tmp_path, "alice/99", ok=False)
    assert result.returncode != 0
    assert "error" in result.stderr


def test_idea_show_no_hb(tmp_path: Path) -> None:
    result = idea_show(tmp_path, ok=False)
    assert ".hb/" in result.stderr


# ── idea set-content ──────────────────────────────────────────────────────────


def test_idea_set_content_basic(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "original content")
    idea_set_content(tmp_path, "alice/0", "new content")
    result = idea_show(tmp_path, "alice/0")
    data = json.loads(result.stdout)
    assert data["content"] == "new content"
    assert data["index"] == 0


def test_idea_set_content_not_found(tmp_path: Path) -> None:
    init(tmp_path)
    idea_add(tmp_path, "alice", "some idea")
    result = idea_set_content(tmp_path, "alice/99", "new content", ok=False)
    assert result.returncode != 0
    assert "error" in result.stderr


def test_idea_set_content_no_hb(tmp_path: Path) -> None:
    result = idea_set_content(tmp_path, "alice/0", "content", ok=False)
    assert ".hb/" in result.stderr
