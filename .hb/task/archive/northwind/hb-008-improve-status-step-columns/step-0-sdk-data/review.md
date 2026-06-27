# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 | ✅ Addressed — deleted unused `sp1` variable |
| STEP-0-REVIEW-2 | ✅ Addressed — updated hb-sdk parser + all tests to use 2-column format |
| STEP-0-REVIEW-3 | ✅ Addressed — hb-sdk refactored into hb_sdk/ module; tests split into 4 files |
| STEP-0-REVIEW-4 | ✅ Addressed — renamed `_def_cli_*` → `def_cli_*` across all four modules |
| STEP-0-REVIEW-5 | ✅ Addressed — renamed 10 private utility symbols in common.py + `_list_step_folders` in task.py |

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

**Resolution:** Two changes made:

1. **`skills/scripts/hb-sdk` — `_parse_review_open`**: Rewrote the parser to use the actual 2-column format (`| ID | Resolution |`). Old logic looked at the third column for keyword values ("open", "addressed", etc.). New logic: an empty `Resolution` cell indicates an open item; any non-empty value indicates a closed item. Also removed the now-unnecessary `REVIEW_CLOSED_STATUSES` constant.

2. **`tests/skills/scripts/test_hb-sdk.py`**: Updated 7 `review.md` write calls to use the actual format — `# Step N Review / ## Status / | ID | Resolution |` with emoji-prefixed resolution values (`✅ Addressed — ...`, `⏭️ Deferred — ...`) and empty cells for open items. The `TODO REVIEW` comment was also deleted.

All 129 tests pass.

**Disposition: Addressed**

---

### STEP-0-REVIEW-3: hb-sdk should be refactored into a Python module

- **file(s):** `tests/skills/scripts/test_hb-sdk.py` (end of file); `scripts/hb-sdk`
- The test file has grown past 1000 lines and hb-sdk itself is ~1000 lines — both are getting unwieldy. Refactor hb-sdk into a Python module `hb_sdk/` adjacent to the current `hb-sdk` script, with `__init__.py` and `__main__.py`. Add a per-command-tree `.py` file inside `hb_sdk/`. Split the test file into `tests/skills/scripts/hb_sdk/test_hb_sdk_<command>.py` files (one per command tree); any tests that don't fit a command tree can stay in the original file; drop the original file if it becomes empty.
- **source:** `TODO REVIEW` in commit `24985c3` — delete comment from source file after addressing

**Resolution:** Full refactoring done:

- **`skills/scripts/hb_sdk/`** (new module): `__init__.py`, `__main__.py` (CLI entry + `main()`), `common.py` (shared constants/utilities/TaskName), `init_cmd.py` (init command), `task.py` (all task + step commands), `summarize.py` (summarize command + `_parse_review_open`), `commit.py` (commit write-message-file commands).
- **`skills/scripts/hb-sdk`**: Reduced to a thin 5-line wrapper that adds the scripts dir to `sys.path` and calls `hb_sdk.__main__.main()`.
- **`tests/skills/scripts/hb_sdk/`** (new): `conftest.py` (sys.path + `task1` fixture), `helpers.py` (all shared test utilities), `test_hb_sdk_init.py`, `test_hb_sdk_task.py`, `test_hb_sdk_commit.py`, `test_hb_sdk_summarize.py`.
- **`tests/skills/scripts/test_hb-sdk.py`**: Deleted (all tests moved; no tests left without a command tree).
- 129 tests pass in the new structure; all are functionally equivalent to the originals.

**Disposition: Addressed**

---

### STEP-0-REVIEW-4: Private symbol imports in hb_sdk should be public

- **file(s):** `skills/scripts/hb_sdk/__main__.py` (around `TODO REVIEW` marker)
- `__main__.py` imports private symbols prefixed with `_def_` (e.g. `_def_cli_commit`, `_def_cli_init`, `_def_cli_summarize`, `_def_cli_task`). These should be renamed to remove the underscore prefix and be treated as public API. The same fix should be applied to all similar cross-module private-symbol imports across `hb_sdk/`.
- **source:** `TODO REVIEW` in commit `85ec3b6` — delete comment from source file after addressing

**Resolution:** Renamed the four CLI-definition functions from `_def_cli_*` to `def_cli_*` in their respective definition modules, and updated all references in `__main__.py`:

- `skills/scripts/hb_sdk/init_cmd.py`: `_def_cli_init` → `def_cli_init`
- `skills/scripts/hb_sdk/commit.py`: `_def_cli_commit` → `def_cli_commit`
- `skills/scripts/hb_sdk/summarize.py`: `_def_cli_summarize` → `def_cli_summarize`
- `skills/scripts/hb_sdk/task.py`: `_def_cli_task` → `def_cli_task`
- `skills/scripts/hb_sdk/__main__.py`: updated all four imports and call sites; deleted the `TODO REVIEW` comment

Grep for any remaining `_def_` usage found none after the rename. All 129 tests pass.

**Disposition: Addressed**

---

### STEP-0-REVIEW-5: Remaining private utility symbols in common.py and task.py exported as public API

- **file(s):** `skills/scripts/hb_sdk/common.py`, `skills/scripts/hb_sdk/task.py` (cross-module imports)
- STEP-0-REVIEW-4 surfaced the `_def_cli_*` pattern; the same underscore-prefix convention was applied to the utility layer in `common.py` (`_die`, `_progress`, `_exists_or_do`, `_path_hb*`, `_parse_task_name`, `_find_matching_task_folders`) and to `_list_step_folders` in `task.py`. All of these were imported across module boundaries, making the leading underscore misleading.

**Resolution:** Renamed all private utility symbols that are used by other modules in `hb_sdk/` to public names (removing the underscore prefix):

- `common.py` (definitions): `_progress` → `progress`, `_die` → `die`, `_exists_or_do` → `exists_or_do`, `_path_hb` → `path_hb`, `_path_hb_git_keep` → `path_hb_git_keep`, `_path_hb_asserted` → `path_hb_asserted`, `_path_task_ticket` → `path_task_ticket`, `_path_step_ticket` → `path_step_ticket`, `_parse_task_name` → `parse_task_name`, `_find_matching_task_folders` → `find_matching_task_folders`; also removed unused `import json`
- `task.py`: `_list_step_folders` → `list_step_folders`
- `init_cmd.py`, `task.py`, `summarize.py`, `commit.py`: updated all import sites accordingly

Grep for remaining `from .* import _` finds nothing. All 129 tests pass.

**Disposition: Addressed**

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
