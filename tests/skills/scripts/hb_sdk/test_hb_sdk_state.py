"""Tests for hb-sdk state subcommands."""

import json
import subprocess
from pathlib import Path

from helpers import init, state_record, state_show

# ── state record — happy path ───────────────────────────────────────────────

STATE_FILE_NAME = ".state.ignore.json"
STATE_FILE_HB_PATH = Path(".hb") / STATE_FILE_NAME


def test_state_record_writes_json_file(tmp_path: Path) -> None:
    init(tmp_path)
    state_record(tmp_path, skill="hb-task-create", outcome="success", timestamp="2026-01-01T00:00:00Z")
    data = json.loads((tmp_path / STATE_FILE_HB_PATH).read_text())
    assert data == {
        "skill": "hb-task-create",
        "outcome": "success",
        "timestamp": "2026-01-01T00:00:00Z",
        "task": None,
        "step": None,
    }


def test_state_record_with_task_and_step(tmp_path: Path) -> None:
    init(tmp_path)
    state_record(
        tmp_path,
        skill="hb-task-step-plan",
        outcome="success",
        timestamp="2026-01-01T00:00:00Z",
        task="northwind/hb-014",
        step="0",
    )
    data = json.loads((tmp_path / STATE_FILE_HB_PATH).read_text())
    assert data["task"] == "northwind/hb-014"
    assert data["step"] == "0"


# ── state record — overwrite semantics (AC2) ────────────────────────────────


def test_state_record_overwrites_prior_record(tmp_path: Path) -> None:
    init(tmp_path)
    state_record(tmp_path, skill="skill-a", outcome="success", timestamp="2026-01-01T00:00:00Z")
    state_record(tmp_path, skill="skill-b", outcome="failure", timestamp="2026-01-02T00:00:00Z")
    data = json.loads((tmp_path / STATE_FILE_HB_PATH).read_text())
    assert data["skill"] == "skill-b"
    assert data["outcome"] == "failure"


# ── state record — no .hb/ ───────────────────────────────────────────────────


def test_state_record_no_hb(tmp_path: Path) -> None:
    result = state_record(
        tmp_path, skill="skill-a", outcome="success", timestamp="2026-01-01T00:00:00Z", ok=False
    )
    assert ".hb/" in result.stderr


# ── state record — missing required flags ───────────────────────────────────


def test_state_record_requires_skill(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_record(tmp_path, outcome="success", timestamp="2026-01-01T00:00:00Z", ok=False)
    assert result.returncode != 0


def test_state_record_requires_outcome(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_record(tmp_path, skill="skill-a", timestamp="2026-01-01T00:00:00Z", ok=False)
    assert result.returncode != 0


def test_state_record_requires_timestamp(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_record(tmp_path, skill="skill-a", outcome="success", ok=False)
    assert result.returncode != 0


# ── state show — happy path, JSON (default) ─────────────────────────────────


def test_state_show_json_after_record(tmp_path: Path) -> None:
    init(tmp_path)
    state_record(tmp_path, skill="skill-a", outcome="success", timestamp="2026-01-01T00:00:00Z")
    result = state_show(tmp_path)
    data = json.loads(result.stdout)
    assert data["skill"] == "skill-a"
    assert data["outcome"] == "success"
    assert data["timestamp"] == "2026-01-01T00:00:00Z"


def test_state_show_json_absent(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_show(tmp_path)
    assert json.loads(result.stdout) == {}


# ── state show — markdown ────────────────────────────────────────────────────


def test_state_show_md_after_record(tmp_path: Path) -> None:
    init(tmp_path)
    state_record(tmp_path, skill="skill-a", outcome="success", timestamp="2026-01-01T00:00:00Z")
    result = state_show(tmp_path, format="md")
    assert "skill-a" in result.stdout
    assert "success" in result.stdout
    assert "2026-01-01T00:00:00Z" in result.stdout


def test_state_show_md_absent(tmp_path: Path) -> None:
    init(tmp_path)
    result = state_show(tmp_path, format="md")
    assert result.stdout.strip() == "No recorded state."


# ── state show — no .hb/ ─────────────────────────────────────────────────────


def test_state_show_no_hb(tmp_path: Path) -> None:
    result = state_show(tmp_path, ok=False)
    assert ".hb/" in result.stderr


# ── AC8/AC9 — git-status non-tracking end-to-end proof ───────────────────────


def test_state_json_not_reported_by_git_status(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    init(tmp_path)
    state_record(tmp_path, skill="skill-a", outcome="success", timestamp="2026-01-01T00:00:00Z")
    result = subprocess.run(
        ["git", "status", "--short"], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert STATE_FILE_NAME not in result.stdout
