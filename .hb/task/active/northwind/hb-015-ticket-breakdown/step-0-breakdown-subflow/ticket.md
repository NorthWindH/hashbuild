# Background

`hb-task-plan` already contains gap-analysis and step-creation logic (Steps 6–8 of its skill file) for breaking a task's acceptance criteria down into child steps. The task ticket (AC 6) requires `hb-ticket-discuss` to gain an equivalent "Breakdown ticket" action that decomposes any ticket into child tickets. Rather than duplicating the gap-analysis / propose-confirm / per-child create-confirm logic in both skills, AC 11 requires it to live in one shared subflow file that both skills inject.

This step extracts that logic now, before either skill needs to change its call site further, and re-points `hb-task-plan` at it with no behavior change — proving the extraction is faithful before `hb-ticket-discuss`'s breakdown action (a later step) becomes the second consumer.

---

# Acceptance Criteria

1. A new reference subflow file (e.g. `references/breakdown-subflow.md`, following the existing pattern of `references/interactive-ticket-subflow.md` and `references/review-init-subflow.md`) exists and is generalized over a **parent** (with acceptance criteria) and a set of **existing children** (each with acceptance criteria, may be empty), producing:
    1. A gap report: parent-level criteria not addressed by any existing child, noting which children partially address each.
    2. A "no gaps" exit path: if none found, report that and stop without proposing anything.
    3. A propose-confirm loop: given the gaps, propose a high-level breakdown into candidate children, present it, and loop accepting user confirmation or requested changes until confirmed.
    4. A per-child create-confirm loop: once the breakdown is confirmed, draft each child's ticket one at a time (using `references/ticket-template.md`), present it, and loop accepting confirmation or requested changes until confirmed, before moving to the next.
2. The subflow's caller contract (what the calling skill must resolve before injecting it — e.g. how to fetch parent/children criteria, how to materialize a confirmed child) is stated explicitly at the top of the file, matching the documentation style of the existing subflow files.
3. The subflow is side-effect-free with respect to persistence: it does not itself decide *where* a child ticket is written or *how* it becomes durable (task step, in-memory context entry, etc.) — that remains the calling skill's responsibility, passed back through the caller contract.
4. `hb-task-plan`'s Steps 6–8 (gap analysis, propose, per-step creation) are replaced with an injection of this subflow, with `hb-task-plan` supplying: task ticket as parent, existing step tickets as children, and — on each confirmed child — a call to `hb-task-step-add --ticket <path>` as the materialization step.
5. `hb-task-plan`'s user-facing behavior is unchanged: given the same task/step ticket inputs, it still reports the same gaps, asks the same confirmation questions, and creates equivalent steps via `hb-task-step-add`.
6. `references/references-toc.md` is updated to list the new subflow file alongside the existing ones.

---

# Out of scope

- Any change to `hb-ticket-discuss` — it does not yet consume this subflow (that's a later step in this task).
- Any change to `hb-task-plan`'s task→step scoping, step-numbering, or step-creation mechanics beyond routing through the shared subflow.
- New MCP/source integrations.
