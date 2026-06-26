# Background

This step implements the proposed fix for both bugs in `hb-task-step-review-address` (task ticket §Background). The root cause is that `review-address` calls `review-init` as a sub-skill, inheriting its side effects (user notification and intermediate commit) that are inappropriate in a subflow context.

The fix: extract the file-creation logic from `review-init` into a shared reference file (`skills/references/review-init-subflow.md`) that can be injected via `!` by both skills. `review-init` retains its standalone behaviour (subflow + notification + commit). `review-address` inlines the subflow directly (no notification, no commit) and then continues immediately to the TODO REVIEW scan.

Addresses task-level acceptance criteria A1–A3, B4–B5, C6–C7, D8–D9.

---

# Acceptance Criteria

1. A new file `skills/references/review-init-subflow.md` exists and contains the `review.md` file-creation logic (resolve step folder, check for existing `review.md`, write the file from the review template).
2. `skills/hb-task-step-review-init.md` references `review-init-subflow.md` via `!` injection and appends its own notification (step 5) and commit (step 6) steps — standalone behaviour is identical to today.
3. `skills/hb-task-step-review-address.md` step 3 inlines `review-init-subflow.md` via `!` injection instead of invoking the `review-init` skill.
4. When `review-address` runs and `review.md` does not exist, execution proceeds directly to the TODO REVIEW scan (step 4) after creating the file — no user notification is shown and no intermediate commit is created.
5. Running `/hb-task-step-review-init` standalone still creates `review.md`, shows the user notification, and creates a commit; running it when `review.md` already exists reports "nothing to do".

---

# Out of scope

- Changes to the TODO REVIEW scan logic (step 4 of `review-address`) beyond removing the off-by-one caused by the extra commit.
- The `--commits N` flag default value.
- Any other `review-address` steps beyond step 3.
- Changes to `hb-sdk` scripts or commit tooling.
