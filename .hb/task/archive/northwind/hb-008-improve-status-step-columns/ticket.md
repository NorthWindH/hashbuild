# Background

The current `/hb-status` Active Tasks table reports coarse step counts (pending execution, with ticket) that don't show where each step actually sits in its lifecycle. A step moves through distinct stages — skeleton → ticketed → planned → executed → review-open → reviewed — and collapsing that into two counts forces the user to dig into each task folder to understand what needs attention. Separately, the archive section only surfaces the single most-recently-archived task and strips its flavor, making recent history hard to scan.

---

# Acceptance Criteria

## A. Step lifecycle stages in `hb-sdk summarize`

1. Each step object in `active_tasks[].steps` gains a `status` field with one of six values, computed by `hb-sdk`:
    1. `skeleton` — no ticket, no plan, no execution, no review file
    2. `ticketed` — has ticket; no plan, no execution
    3. `planned` — has plan; no execution
    4. `executed` — has execution; no review file present
    5. `review-open` — has a review file with at least one item whose status is not `addressed`, `deferred`, or a closed equivalent
    6. `reviewed` — has a review file and all items are closed (addressed or deferred), or the review file exists but contains no items
2. `active_tasks[]` gains six count fields derived from step statuses: `steps_skeleton`, `steps_ticketed`, `steps_planned`, `steps_executed`, `steps_review_open`, `steps_reviewed`.
3. `active_tasks[]` gains two name-list fields, each an array of step folder names (e.g. `step-1-add-form`):
    1. `steps_needs_review` — steps whose status is `executed` or `review-open` (done but not fully reviewed)
    2. `steps_needs_work` — steps whose status is `skeleton`, `ticketed`, or `planned` (not yet executed)
4. `next_pending_step` continues to point to the first step that has not yet been executed (no `execution-*.md`).

## B. Active Tasks table in status template and `hb-status` output

1. The Active Tasks table is replaced with columns: Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total.
2. Each count cell shows `—` when the count is zero (not `0`), to reduce visual noise.
3. The `steps_pending_execution` and `steps_with_ticket` columns are removed from both the template and the SDK output.
4. Below each task row, two indented lists are rendered (each omitted when empty):
    1. **Needs review** — step folder names from `steps_needs_review` (status `executed` or `review-open`)
    2. **Needs work** — step folder names from `steps_needs_work` (status `skeleton`, `ticketed`, or `planned`)

## C. Archive section — last 5 tasks with flavor

1. `hb-sdk summarize` returns `archive.recent` as an array of up to 5 entries, each with `author`, `task_id`, and `task_folder` (which includes the flavor, e.g. `hb-004-interactive-ticket-creation`).
2. The `archive.last_archived` scalar field is removed; `archive.recent[0]` replaces it.
3. The Archive section in the status template renders `recent` as a small table or bulleted list showing `author/task_folder` for each entry; the section is omitted when `archive.recent` is empty.

## D. Consistency

1. The `hb-status` skill instructions are updated to reference the new JSON fields and table columns.
2. The status template `## Next Action` decision tree remains logically correct under the new column names (references to `steps_pending_execution` and `steps_with_ticket` are updated to match the new fields).

---

# Out of scope

- Changes to the Next Action decision tree logic beyond renaming fields to match the new schema
- Modifying any skill other than `hb-status` (template + skill instructions) and `hb-sdk`
- Changing how review files are structured or authored
- Surfacing per-step status breakdowns in the status report (counts per task are sufficient)
