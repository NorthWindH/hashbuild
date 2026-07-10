# Background

Steps 1 and 2 of this task wired `hb-sdk facts read`/`write` into the planning
(`hb-task-step-plan`, `hb-task-plan`) and execution (`hb-task-step-execute`)
skills named in the parent ticket's AC2. `hb-task-step-review-address` is a
separate long-running loop — it reads context and makes code changes while
addressing review items — but was not among the skills named in the parent
ticket, so it does not yet consult or update the facts store. This step
extends the same read-before/write-after pattern to review addressing, so
facts discovered stale or newly learned while resolving a review item are
captured just as they would be during execution.

---

# Acceptance Criteria

1. `hb-task-step-review-address.md`'s Steps include a step, run before
   addressing each unresolved review item (9a/9b), that runs `hb-sdk facts
   read`, and the item-addressing step is instructed to take the returned
   facts into account.
2. After addressing a review item (9b) and before its commit (9e),
   `hb-task-step-review-address.md` includes a step that:
    1. re-reads the current facts store (`hb-sdk facts read`);
    2. removes or corrects any facts discovered to be stale or incorrect
       while addressing this item, via `hb-sdk facts write`;
    3. adds new facts discovered while addressing this item only when they
       are likely to matter for future planning/execution/review, weighed
       against the size guidance from step-0 (target <= 100 lines, hard max
       1000 lines, <= 120 chars/line).
3. Any facts-store changes made while addressing an item are included in
   that item's commit (9e), per `committing.md`.
4. When the facts store is empty or missing (per step-0's `read` contract),
   the skill proceeds unaffected — no error, no blocking prompt.

---

# Out of scope

- Reads/updates during review.md creation, normalisation, or status-table
  sync (steps 3, 5-8) — this step scopes facts handling to the per-item
  addressing loop (step 9) only.
- Planning-time or execution-time reads/updates — already covered by step-1
  and step-2.
