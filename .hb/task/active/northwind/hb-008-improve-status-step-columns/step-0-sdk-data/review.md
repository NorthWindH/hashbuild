# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 | ✅ Addressed — deleted unused `sp1` variable |
| STEP-0-REVIEW-2 |            |
| STEP-0-REVIEW-3 |            |

---

## Notes

### STEP-0-REVIEW-1: Unused sp1 variable in test_summarize_task_count_fields_mixed

- **file(s):** `tests/skills/scripts/test_hb-sdk.py` (`test_summarize_task_count_fields_mixed`)
- `sp1` is assigned but never accessed in the test body; consider deleting it.
- **source:** `TODO REVIEW` in commit `24985c3` — delete comment from source file after addressing

**Resolution:** Deleted both the `TODO REVIEW` comment and the `sp1 = base / "step-1"` assignment. Step-1 needed no file manipulation in this test (the comment `# step-1: ticketed` already explained that), so the variable was truly dead code. All 129 tests pass after removal.

**Disposition: Addressed**

---

### STEP-0-REVIEW-2: review.md format in tests doesn't match actual format

- **file(s):** `tests/skills/scripts/test_hb-sdk.py` (around `TODO REVIEW` marker, `test_summarize_steps_needs_review_includes_executed_and_review_open` and related tests)
- The review.md content written inline in tests (raw table string `| ID | Status | Description |...`) doesn't match the real review.md format produced by `hb-task-step-review-init`. All tests that test review.md parsing should use the actual review.md format. Also update hb-sdk itself if it currently parses the old format — the only format that needs to be supported going forward is the real one.
- **source:** `TODO REVIEW` in commit `24985c3` — delete comment from source file after addressing

---

### STEP-0-REVIEW-3: hb-sdk should be refactored into a Python module

- **file(s):** `tests/skills/scripts/test_hb-sdk.py` (end of file); `scripts/hb-sdk`
- The test file has grown past 1000 lines and hb-sdk itself is ~1000 lines — both are getting unwieldy. Refactor hb-sdk into a Python module `hb_sdk/` adjacent to the current `hb-sdk` script, with `__init__.py` and `__main__.py`. Add a per-command-tree `.py` file inside `hb_sdk/`. Split the test file into `tests/skills/scripts/hb_sdk/test_hb_sdk_<command>.py` files (one per command tree); any tests that don't fit a command tree can stay in the original file; drop the original file if it becomes empty.
- **source:** `TODO REVIEW` in commit `24985c3` — delete comment from source file after addressing

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
