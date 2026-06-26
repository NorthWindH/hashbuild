# Step 0 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-0-REVIEW-1 | ✅ Addressed — new step 4 added to skill; description, CTA, and README updated |
| STEP-0-REVIEW-2 | ✅ Addressed — deleted TODO REVIEW comment from references-toc.md |
| STEP-0-REVIEW-3 |            |

---

## Notes

### STEP-0-REVIEW-1: Add uncommitted file scanning to hb-task-step-review-address — ADDRESSED

- **file(s):** `skills/hb-task-step-review-address.md` (step 4 — scan commits for TODO REVIEW comments)
- In addition to scanning commits, when `--no-todo-scan` is not provided, the skill should also scan files that have been changed but not committed for `TODO REVIEW` comments. If found, the user should be asked whether to commit those files before continuing the flow. If accepted, commit the changed files containing `TODO REVIEW` comments, then continue; if declined, just continue.
- **source:** `TODO REVIEW` in commit `4895b102d24203269a5fcfdf64a57842aebbdcfe` — delete comment from source file after addressing

**Resolution:** Added a new **step 4 — Scan working tree for TODO REVIEW comments** to `hb-task-step-review-address.md`, inserted before the existing commit-scan step (renumbered 4→5 through 9→10). The new step: runs `git status --short` to find uncommitted changed files, greps each for `TODO REVIEW`, and if any are found, prompts the user to commit them before the commit-scan step runs. Propagated the change to all call-to-action sites:

| file | change |
|------|--------|
| `skills/hb-task-step-review-address.md` | new step 4; frontmatter description updated; `--no-todo-scan` description updated; intro paragraph updated |
| `skills/hb-task-step-review-init.md` | CTA updated: mentions committed _and_ uncommitted |
| `skills/hb-task-step-execute.md` | CTA updated: "committed or uncommitted" |
| `skills/references/README.md` | Option A updated to mention uncommitted files and the commit-offer prompt |

The `TODO REVIEW` comment itself was deleted from `skills/hb-task-step-review-address.md` and replaced with the new step 4 text.

---

### STEP-0-REVIEW-2: Test review message — delete comment from references-toc.md — ADDRESSED

- **file(s):** `skills/references/references-toc.md` (bottom of file)
- This is a test review message left as a `TODO REVIEW` comment. It should be addressed by going through the normal review address flow, then deleted.
- **source:** `TODO REVIEW` in commit `4895b102d24203269a5fcfdf64a57842aebbdcfe` — delete comment from source file after addressing

**Resolution:** Deleted the `<!-- TODO REVIEW this is a test review message; go through the normal review address flow then address it by deleting this comment -->` line from the bottom of `skills/references/references-toc.md`. This was a self-referential test item verifying the review-address flow works end to end — successfully exercised.

---

### STEP-0-REVIEW-3: Update step 10 call-to-action to mention uncommitted TODO REVIEW comments

- **file(s):** `skills/hb-task-step-review-address.md` (step 10 — Prompt user)
- The call-to-action prompt at the end of the skill still says "add and commit more TODO REVIEW comments" — it should be updated to say "committed or uncommitted" to match the new working-tree scanning feature added in STEP-0-REVIEW-1.
- **source:** `TODO REVIEW` in commit `2a7b26ae84d91052d1256f74d3df04735dee2d37` — delete comment from source file after addressing

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
