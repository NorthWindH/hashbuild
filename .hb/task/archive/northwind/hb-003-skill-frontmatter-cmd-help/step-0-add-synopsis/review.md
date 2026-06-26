# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 | ✅ Addressed — added `argument-hint` to all 11 skills; `arguments` added to 9 positional-arg skills; TODO REVIEW comment deleted from `hb-init.md` |

---

## Notes

### STEP-0-REVIEW-1: Populate `arguments` and `argument-hint` frontmatter fields for all skills — ADDRESSED

- **file(s):** `skills/hb-init.md` (frontmatter block); applies to all 11 skills in `skills/`
- The reviewer requests populating the `arguments` and `argument-hint` frontmatter fields (per the Claude skills frontmatter reference at `https://code.claude.com/docs/en/skills#frontmatter-reference`) in `hb-init.md` and all other skills in this directory.
- **source:** `TODO REVIEW` in commit `1731a91` — delete comment from source file after addressing

**Resolution:** Added `argument-hint` to all 11 skills (`hb-init`, `hb-status`, `hb-task-archive`, `hb-task-create`, `hb-task-plan`, `hb-task-step-add`, `hb-task-step-execute`, `hb-task-step-plan`, `hb-task-step-review-address`, `hb-task-step-review-init`, `hb-task-unarchive`). The value matches the synopsis argument surface (minus the command name) already established in step-0, e.g. `"[--help] <author/task-id/step-n>"`.

For `arguments`: added to the 9 skills that have a primary positional argument (`task_id` for task-scoped skills, `step_ref` for step-scoped skills). Omitted for `hb-init` and `hb-status`, which accept no positional args. The hb-* skills use their own SDK-based argument parsing rather than `$name` substitution, so `arguments` is primarily declarative metadata here.

The two `# TODO REVIEW` comment lines were deleted from `skills/hb-init.md`.

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
