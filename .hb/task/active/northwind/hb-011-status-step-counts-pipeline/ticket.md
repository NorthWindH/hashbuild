# Background

The `hb-sdk summarize --format md` status table currently counts each step toward only the single column that matches its current status (e.g., a Reviewed step increments R only, not S/T/P/E/RO). This means the table cannot be read as a pipeline — a step that has been reviewed has also passed through every earlier stage, but those earlier columns show nothing. Changing to cumulative counting (each step increments every column it has passed through) makes the total and per-stage depth immediately visible and turns the status row into a true pipeline progress bar.

---

# Acceptance Criteria

1. `hb-sdk summarize --format md` counts each step in every column whose stage it has passed through (cumulative / pipeline counting), not only the column for its current status.
    1. A step at status S is counted in S only.
    2. A step at status T is counted in S and T.
    3. A step at status P is counted in S, T, and P.
    4. A step at status E is counted in S, T, P, and E.
    5. A step at status RO is counted in S, T, P, E, and RO.
    6. A step at status R is counted in S, T, P, E, RO, and R.
2. The column headers, row layout, and all other table content are unchanged.
3. The rendering change applies only to the markdown format output of `summarize`; no other output format or data path is affected.
4. Existing snapshot/fixture tests (if any) are updated to reflect the new cumulative counts; all other tests pass unchanged.

---

# Out of scope

- Horizontal stacked-bar visualization — deferred to a future task.
- Changes to any output format other than `--format md`.
- Changes to how step statuses are computed or stored internally.
