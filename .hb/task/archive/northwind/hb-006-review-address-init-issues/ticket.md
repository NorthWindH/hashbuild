# Background

`/hb-task-step-review-address` (step 3) invokes the `hb-task-step-review-init` skill when `review.md` does not yet exist. This cross-skill invocation causes two bugs:

**Bug 1 — context loss.** When `review-address` invokes `review-init` as a sub-skill, the agent treats it as an independent skill invocation with its own entry/exit behaviour. `review-init` ends with a user notification that says to fill in review items then re-run `review-address` — the exact opposite of what the agent should do (continue executing `review-address`). The result is that the agent either stops prematurely or floods the user with conflicting messages before stopping unexpectedly.

**Bug 2 — TODO REVIEW scan misses its target commit.** `review-init` creates a commit for the new `review.md` file (step 6). By default, `review-address` scans only `HEAD` (1 commit) for `TODO REVIEW` markers. After the `review-init` commit, `HEAD` is the `review.md` creation commit, not the commit containing `TODO REVIEW` comments — so the scan finds nothing.

Both bugs share a root cause: `review-init` is designed as a standalone skill with side effects (user notification, commit) that are inappropriate when called as a subflow from `review-address`.

**Proposed fix:** Extract the file-creation logic from `review-init` into a shared subflow reference file (e.g. `references/review-init-subflow.md`) that both skills include via the existing `!` dynamic injection mechanism. The standalone `review-init` skill calls the subflow then adds its own notification and commit steps. `review-address` inlines the subflow directly (no notification, no commit) before continuing to step 4.

---

# Acceptance Criteria

## A. Subflow extraction

1. A new shared subflow file exists at `skills/references/review-init-subflow.md` containing the `review.md` file-creation logic (current `review-init` steps 2–4: resolve step folder, check for existing `review.md`, write the file).
2. `hb-task-step-review-init.md` is updated to reference the subflow file via `!` injection and adds its own notification (step 5) and commit (step 6) steps after it — standalone behaviour is unchanged.
3. `hb-task-step-review-address.md` step 3 is updated to inline the subflow via `!` injection instead of invoking the `review-init` skill.

## B. Bug 1 fixed — no context loss

4. When `review-address` is run and `review.md` does not exist, the agent creates `review.md` and continues immediately to step 4 (TODO REVIEW scan) without prompting the user or stopping.
5. The `review-init` notification message ("fill in review items, then run `/hb-task-step-review-address`…") does **not** appear during a `review-address` run.

## C. Bug 2 fixed — TODO REVIEW scan targets the right commit

6. When `review-address` creates `review.md` as part of its own flow (via the subflow), no intermediate commit is created for `review.md` before the TODO REVIEW scan runs.
7. The TODO REVIEW scan (step 4) therefore targets the correct `HEAD` commit — the one that contains `TODO REVIEW` markers — not a `review.md` creation commit.

## D. Standalone `review-init` behaviour preserved

8. Running `/hb-task-step-review-init` directly still:
    1. creates `review.md` with the placeholder structure,
    2. shows the user notification (including README-1 and README-2),
    3. creates a commit for `review.md`.
9. `review-init` is still idempotent — running it when `review.md` already exists reports "nothing to do" and stops.

---

# Out of scope

- Changes to the TODO REVIEW scan logic itself (step 4 of `review-address`) beyond removing the off-by-one caused by the extra commit.
- The `--commits N` flag default value — the fix removes the need to change it.
- Any other `review-address` steps beyond step 3.
- Changes to the `hb-sdk` scripts or commit tooling.
