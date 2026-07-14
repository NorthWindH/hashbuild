"""Tests for `install`'s /hb-flow SessionStart hook patching."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

INSTALL = Path(__file__).parents[1] / "install"

HB_FLOW_HOOK_MATCHER = "startup|clear"
HB_FLOW_HOOK_COMMAND = "[ -d .hb ] && echo 'hashbuild: run /hb-flow to see where things left off.'; true"


def run_install(home: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(INSTALL), "--harness", "claude", *extra_args],
        cwd=home,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(home)},
    )
    assert result.returncode == 0, result.stderr
    return result


def make_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    return home


def read_settings(home: Path) -> dict[str, Any]:
    return json.loads((home / ".claude" / "settings.json").read_text())


def test_fresh_install_adds_hook(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    run_install(home)

    groups = read_settings(home)["hooks"]["SessionStart"]
    assert len(groups) == 1
    group = groups[0]
    assert group["matcher"] == HB_FLOW_HOOK_MATCHER
    assert group["hooks"] == [{"type": "command", "command": HB_FLOW_HOOK_COMMAND}]


def test_install_is_idempotent(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    run_install(home)
    result = run_install(home)

    assert "already present" in result.stdout
    groups = read_settings(home)["hooks"]["SessionStart"]
    assert len(groups) == 1
    assert len(groups[0]["hooks"]) == 1


def test_install_appends_into_existing_matcher_group(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    settings_path = home / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": HB_FLOW_HOOK_MATCHER,
                            "hooks": [{"type": "command", "command": "echo 'other hook'"}],
                        }
                    ]
                }
            }
        )
    )

    run_install(home)

    groups = read_settings(home)["hooks"]["SessionStart"]
    assert len(groups) == 1
    commands = {h["command"] for h in groups[0]["hooks"]}
    assert commands == {"echo 'other hook'", HB_FLOW_HOOK_COMMAND}


def test_uninstall_removes_hook_cleanly(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    run_install(home)
    run_install(home, "--uninstall")

    settings = read_settings(home)
    assert "hooks" not in settings


def test_uninstall_does_not_disturb_unrelated_hooks(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    settings_path = home / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo pre"}]}
                    ],
                    "SessionStart": [
                        {"matcher": "startup", "hooks": [{"type": "command", "command": "echo startup-only"}]}
                    ],
                }
            }
        )
    )
    before = read_settings(home)["hooks"]

    run_install(home)
    run_install(home, "--uninstall")

    after = read_settings(home)["hooks"]
    assert after == before


def test_install_confirm_prompt_shows_hook_diff(tmp_path: Path) -> None:
    home = make_home(tmp_path)
    result = run_install(home)

    assert "The following hook will be added" in result.stdout
    assert HB_FLOW_HOOK_MATCHER in result.stdout
    assert HB_FLOW_HOOK_COMMAND in result.stdout


def test_hook_command_silent_outside_hb_dir(tmp_path: Path) -> None:
    no_hb_dir = tmp_path / "no-hb"
    no_hb_dir.mkdir()
    result = subprocess.run(
        ["bash", "-c", HB_FLOW_HOOK_COMMAND],
        cwd=no_hb_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_command_prints_reminder_inside_hb_dir(tmp_path: Path) -> None:
    has_hb_dir = tmp_path / "has-hb"
    (has_hb_dir / ".hb").mkdir(parents=True)
    result = subprocess.run(
        ["bash", "-c", HB_FLOW_HOOK_COMMAND],
        cwd=has_hb_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "hashbuild: run /hb-flow to see where things left off.\n"
