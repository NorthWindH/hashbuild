# Background

Step-1 of this task (`northwind/hb-016`) wired `hb-sdk facts read` into the
planning skills named in the parent ticket's AC2 — `hb-task-step-plan` and
`hb-task-plan` — but only the read side. Step-2 and step-4 later extended
execution and review-addressing with the write-after half of the pattern:
re-read the store, correct stale facts, and record newly discovered ones. The
planning skills never got that write-after half, so facts discovered or
invalidated during planning (as opposed to execution or review) are lost
instead of being captured. This step brings both planning skills up to the
same read-before/write-after pattern already used by execution and review.

---

# Acceptance Criteria

1. `hb-task-step-plan.md`'s Steps include a step, after generating/updating
   `plan.md` and before its commit, that:
    1. re-reads the current facts store (`hb-sdk facts read`);
    2. removes or corrects any facts discovered to be stale or incorrect
       while planning this step, via `hb-sdk facts write`;
    3. adds new facts discovered while planning only when they are likely to
       matter for future planning/execution/review, weighed against the size
       guidance from step-0 (target <= 100 lines, hard max 1000 lines, <= 120
       chars/line).
2. `hb-task-plan.md`'s Steps include an analogous step after gap analysis /
   breakdown and before any resulting commit, following the same
   read-then-write-if-needed pattern as AC1.
3. Any facts-store changes made by either skill are included in the relevant
   commit, per `committing.md`.
4. When the facts store is empty or missing (per step-0's `read` contract),
   both skills proceed unaffected — no error, no blocking prompt.

---

# Out of scope

- Planning-time reads before generating output — already covered by step-1.
- Execution-time or review-addressing writes — already covered by step-2 and
  step-4.
