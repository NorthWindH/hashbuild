"""Tests for hb-sdk plan lint subcommand."""

from pathlib import Path

from helpers import plan_lint

# ── plan lint — clean input ─────────────────────────────────────────────────


def test_plan_lint_passes_single_sentence_bullet(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("# Title\n\n- One sentence bullet.\n- Another single-sentence bullet.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_passes_three_sentence_paragraph(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("One sentence. Two sentences. Three sentences.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_passes_on_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


# ── plan lint — sentence-length violations ──────────────────────────────────


def test_plan_lint_flags_sentence_over_120_chars(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    long_sentence = (
        "This is a very long sentence padded with many filler words to push it well past "
        "the one hundred and twenty character limit that this lint command enforces here."
    )
    assert len(long_sentence) > 120
    p.write_text(f"{long_sentence}\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "sentence-length" in result.stdout


def test_plan_lint_allows_sentence_at_exactly_120_chars(tmp_path: Path) -> None:
    sentence = ("x" * 118) + "y."
    assert len(sentence) == 120
    p = tmp_path / "plan.md"
    p.write_text(f"{sentence}\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


# ── plan lint — bullet-length violations (bullets cap at 1 sentence) ───────


def test_plan_lint_flags_bullet_with_2_sentences(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("- One sentence. Two sentences breaks it.\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "bullet-length" in result.stdout


def test_plan_lint_flags_numbered_item_with_2_sentences(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("1. One sentence. Two sentences breaks it.\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "bullet-length" in result.stdout


def test_plan_lint_allows_exactly_1_sentence_bullet(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("- Just one sentence here.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


# ── plan lint — paragraph-length violations (paragraphs cap at 3 sentences) ─


def test_plan_lint_flags_paragraph_with_4_sentences(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("One. Two. Three. Four breaks it.\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "paragraph-length" in result.stdout


# ── plan lint — soft-wrapped continuation lines are joined before counting ──


def test_plan_lint_joins_wrapped_bullet_before_checking_sentence_count(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("- One sentence that wraps onto\n  a second physical line, still one bullet.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_joins_wrapped_bullet_before_checking_sentence_length(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text(
        "- This single sentence is split across two physical lines but is still\n"
        "  one long logical sentence that in total exceeds the character limit here.\n"
    )
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "sentence-length" in result.stdout


def test_plan_lint_stops_joining_at_next_bullet(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("- First bullet.\n- Second bullet.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_stops_joining_at_blank_line(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("First paragraph.\n\nSecond paragraph.\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


# ── plan lint — exemptions ───────────────────────────────────────────────────


def test_plan_lint_exempts_fenced_code_blocks(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text(
        "```\nOne. Two. Three. Four. Five. This whole diagram block is exempt from every limit here.\n```\n"
    )
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_exempts_table_rows(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    long_cell = "y" * 200
    p.write_text(f"| col |\n|---|\n| {long_cell} |\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_exempts_headings(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    heading = "# " + ("z" * 200)
    p.write_text(heading + "\n")
    result = plan_lint(tmp_path, str(p))
    assert "OK" in result.stdout


def test_plan_lint_unwraps_blockquote_marker_as_paragraph(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("> One. Two. Three. Four breaks it even inside a blockquote.\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "paragraph-length" in result.stdout


def test_plan_lint_unwraps_blockquote_bullet_as_bullet(tmp_path: Path) -> None:
    p = tmp_path / "plan.md"
    p.write_text("> - One sentence. Two sentences breaks it.\n")
    result = plan_lint(tmp_path, str(p), ok=False)
    assert result.returncode != 0
    assert "bullet-length" in result.stdout


# ── plan lint — missing file ────────────────────────────────────────────────


def test_plan_lint_missing_file_dies(tmp_path: Path) -> None:
    result = plan_lint(tmp_path, str(tmp_path / "nope.md"), ok=False)
    assert result.returncode != 0
    assert "not found" in result.stderr
