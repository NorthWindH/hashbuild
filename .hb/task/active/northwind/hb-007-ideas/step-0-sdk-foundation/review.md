# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 | ✅ Addressed — added `argparse.Namespace` to 4 `cmd_*` args and `_SubParsersAction` to `def_cli_idea`; removed TODO comment |

---

## Notes

### STEP-0-REVIEW-1: Missing type annotations in idea.py — ADDRESSED

- **file(s):** `skills/scripts/hb_sdk/idea.py` (all functions)
- All functions in this file lack type annotations on arguments and return values. Add full type annotations throughout the file.
- **source:** `TODO REVIEW` in commit `bcb9e1e98da9483e7a2b3214f16b6b7618fb4957` — delete comment from source file after addressing

**Resolution:** Investigated which functions were missing annotations. Five functions already had complete signatures (`path_idea_dir`, `path_idea_file`, `_load_idea_file`, `_save_idea_file`, `_parse_idea_ref`). Four `cmd_*` functions were missing `args` type; `def_cli_idea` was missing `subs` type. Changes made:
- Added `import argparse`
- Added `args: argparse.Namespace` to `cmd_idea_add`, `cmd_idea_remove`, `cmd_idea_show`, `cmd_idea_set_content`
- Added `subs: "argparse._SubParsersAction[argparse.ArgumentParser]"` to `def_cli_idea` (quoted to avoid runtime resolution of the private type)
- Removed the `TODO REVIEW` comment and its surrounding blank lines

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
