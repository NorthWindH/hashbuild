"""Tests for hb-sdk commit write-message-file commands."""

from pathlib import Path

from helpers import commit_write_message_file, init, run, task_create


def test_commit_write_message_file_basic(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", short="add login page")
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "abc-1: add login page\n"


def test_commit_write_message_file_with_step(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task-step", task="hasan/abc-1", step=2, short="add login page"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: add login page\n"


def test_commit_write_message_file_with_long(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", short="add login page", long="needed for auth flow"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: add login page\n\nneeded for auth flow\n"


def test_commit_wmf_plain_basic(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", short="init hb")
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.read_text() == "hb: init hb\n"


def test_commit_wmf_plain_with_long(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", short="x", long="y")
    path = Path(result.stdout.strip())
    assert path.read_text() == "hb: x\n\ny\n"


def test_commit_wmf_plain_rejects_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", task="hasan/abc-1", short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_plain_rejects_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "plain", step=0, short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_task_requires_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task", short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_task_rejects_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", step=2, short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_task_step_requires_task(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task-step", step=2, short="x", ok=False)
    assert "--task" in result.stderr


def test_commit_wmf_task_step_requires_step(tmp_path: Path) -> None:
    result = commit_write_message_file(tmp_path, "task-step", task="hasan/abc-1", short="x", ok=False)
    assert "--step" in result.stderr


def test_commit_wmf_no_mode_errors(tmp_path: Path) -> None:
    result = run(
        ["commit", "write-message-file", "--task", "hasan/abc-1", "--short", "x"], tmp_path, ok=False
    )
    assert result.returncode != 0


def test_commit_wmf_task_with_tag(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", tag="step-add", short="add routes"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: (step-add) add routes\n"


def test_commit_wmf_task_without_tag_unchanged(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", short="add routes")
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1: add routes\n"


def test_commit_wmf_task_step_with_tag(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task-step", task="hasan/abc-1", step=2, tag="step-plan", short="write plan"
    )
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: (step-plan) write plan\n"


def test_commit_wmf_task_step_without_tag_unchanged(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task-step", task="hasan/abc-1", step=2, short="write plan")
    path = Path(result.stdout.strip())
    assert path.read_text() == "abc-1/step-2: write plan\n"


def test_commit_wmf_plain_rejects_tag(tmp_path: Path) -> None:
    result = run(
        ["commit", "write-message-file", "plain", "--tag", "foo", "--short", "x"], tmp_path, ok=False
    )
    assert result.returncode != 0


def test_commit_wmf_invalid_tag_uppercase(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(tmp_path, "task", task="hasan/abc-1", tag="Foo", short="x", ok=False)
    assert result.returncode != 0
    assert "invalid" in result.stderr


def test_commit_wmf_invalid_tag_underscore(tmp_path: Path) -> None:
    init(tmp_path)
    task_create(tmp_path, "hasan/abc-1")
    result = commit_write_message_file(
        tmp_path, "task", task="hasan/abc-1", tag="foo_bar", short="x", ok=False
    )
    assert result.returncode != 0
    assert "invalid" in result.stderr
