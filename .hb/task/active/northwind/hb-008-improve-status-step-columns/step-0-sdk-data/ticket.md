# Background

The task (hb-008) requires `hb-sdk summarize` to emit richer step and archive data so the status report can show per-lifecycle counts and recent archive history. This step implements the data layer only. Step 1 consumes the new JSON to update the template and skill instructions.

Specifically: add a `status` field to each step object (one of six lifecycle values), derive six count fields and two name-list fields on each active task, and replace the `archive.last_archived` scalar with an `archive.recent` array of up to 5 entries.

---

# Acceptance Criteria

## Step status field

1. `_StepInfo` gains a `has_review` bool: true when a file named `review.md` exists in the step folder.
2. Each step object in the JSON output gains a `status` field with one of six values, computed in priority order:
   - `reviewed` — has a review file and all parsed status-table items are closed (status in {`addressed`, `deferred`}), or the review file exists but contains no status-table rows
   - `review-open` — has a review file with at least one item whose status is not `addressed` or `deferred`
   - `executed` — has at least one `execution-*.md` file; no review file present
   - `planned` — has `plan.md`; no execution file present
   - `ticketed` — has `ticket.md`; no plan, no execution
   - `skeleton` — none of the above
3. Review-file parsing: scan `review.md` for Markdown table rows whose second pipe-delimited column matches a status value (case-insensitive). Any row with a status not in {`addressed`, `deferred`} counts as open.

## Active-task count and list fields

4. `active_tasks[]` gains six integer count fields derived from step statuses: `steps_skeleton`, `steps_ticketed`, `steps_planned`, `steps_executed`, `steps_review_open`, `steps_reviewed`.
5. `active_tasks[]` gains two string-array fields:
   - `steps_needs_review` — step folder names (e.g. `step-1-add-form`) where status is `executed` or `review-open`
   - `steps_needs_work` — step folder names where status is `skeleton`, `ticketed`, or `planned`
6. `next_pending_step` continues to point to the first step with no `execution-*.md` file (no change to existing logic).
7. The old `steps_pending_execution` and `steps_with_ticket` fields are removed from the JSON output.

## Archive section

8. The archive JSON changes from `{ "count": int, "last_archived": str | null }` to `{ "count": int, "recent": [...] }`.
9. `recent` is an array of up to 5 entries, sorted by folder mtime descending, each with `{ "author": str, "task_id": str, "task_folder": str }` where `task_folder` includes the flavor (e.g. `hb-004-interactive-ticket-creation`).
10. When `.hb/` is absent, the uninitialized JSON uses `"recent": []` instead of `"last_archived": null`.

---

# Out of scope

- Updating the status template or `hb-status.md` skill (step 1)
- Adding review detection to any other skill or command
- Changing how review files are structured or authored
