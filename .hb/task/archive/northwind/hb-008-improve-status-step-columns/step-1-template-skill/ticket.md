# Background

With the updated `hb-sdk summarize` JSON from step 0, this step updates the presentation layer: `skills/references/status-template.md` and `skills/hb-status.md`. The goal is to render the six lifecycle count columns, zero-as-dash, per-task step lists, and the new archive section, and to keep the skill's JSON schema docs and decision tree in sync with the new SDK output.

---

# Acceptance Criteria

## Status template — Active Tasks table (criteria B)

1. The Active Tasks table in `skills/references/status-template.md` is replaced with columns: Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total.
2. Each count cell shows `—` when the count is zero (not `0`).
3. The old `Steps pending execution` and `Steps with ticket` columns are removed.
4. Below each task row, two indented lists are rendered (each omitted when empty):
   - **Needs review** — step folder names from `steps_needs_review` (status `executed` or `review-open`)
   - **Needs work** — step folder names from `steps_needs_work` (status `skeleton`, `ticketed`, or `planned`)

## Status template — Archive section (criterion C.3)

5. The Archive section renders `archive.recent` as a bulleted list showing `author/task_folder` for each entry; the section is omitted when `archive.recent` is empty.
6. The `Last archived` table row is removed (replaced by the `recent` list).

## hb-status.md skill — JSON schema (criterion D.1)

7. The JSON schema in `skills/hb-status.md` step 2 is updated to match the new SDK output:
   - Remove `steps_pending_execution` and `steps_with_ticket` from `active_tasks[]`.
   - Add `steps_skeleton`, `steps_ticketed`, `steps_planned`, `steps_executed`, `steps_review_open`, `steps_reviewed` (int) to `active_tasks[]`.
   - Add `steps_needs_review` and `steps_needs_work` (array of str) to `active_tasks[]`.
   - Each step object gains `"status": str`.
   - `archive` changes from `{ count, last_archived }` to `{ count, recent: [...] }`.
8. The step 4 render instructions reference the new column names instead of the old ones.

## hb-status.md skill — Next Action decision tree (criterion D.2)

9. The `## Next Action` decision tree in `skills/references/status-template.md` is updated to use the new field names:
   - Replace any reference to `steps_pending_execution` with `steps_needs_work`.
   - Replace any reference to `steps_with_ticket` with the appropriate new field.
   - Ensure the logic remains correct under the new schema.

---

# Out of scope

- SDK changes (step 0)
- Changes to any skill other than `hb-status.md`
- Changes to the Next Action decision tree logic beyond field name updates
- Changing how review files are structured or authored
