# Background

The "read facts store → compose updated content → gate on diff → write facts store"
sequence is currently duplicated, with slightly drifting wording, across four
hb-task-* lifecycle skills: `hb-task-step-plan.md`, `hb-task-plan.md`,
`hb-task-step-execute.md`, and `hb-task-step-review-address.md`. Separately,
hb-016/step-6's STEP-6-REVIEW-3 reassessed `.hb/facts.md` by hand against three
criteria — drop what's inferable from disk elsewhere, keep each fact under ~120
characters total, and keep only facts that correct a planning error and help future
planning — and used that process to trim `.hb/facts.md` from five facts down to
three. That discipline was applied once, manually, during review; it should instead
be baked into how facts get written every time, not left to periodic review cleanup.

---

# Acceptance Criteria

1. A new shared subflow reference file (e.g. `references/facts-write-subflow.md`) is
   created that encapsulates the "read facts store → compose updated content → gate
   on diff → write facts store" steps, generalized from the sub-steps currently
   duplicated in `hb-task-step-plan.md`, `hb-task-plan.md`, `hb-task-step-execute.md`,
   and `hb-task-step-review-address.md`.
2. The subflow's composition guidance bakes in the reassessment criteria applied in
   hb-016/step-6 STEP-6-REVIEW-3: prefer dropping facts derivable from current on-disk
   state, keep each fact short (target <= 120 characters total), and keep only facts
   that correct a planning error / inform future planning — applied on every write,
   not only during periodic review cleanup.
3. `hb-task-step-plan.md`, `hb-task-plan.md`, `hb-task-step-execute.md`, and
   `hb-task-step-review-address.md` are updated to inject/call the new shared subflow
   instead of their own inline "read facts / compose / write facts" steps, following
   the same injection convention already used for other shared subflows (e.g.
   `review-init-subflow.md`).
4. No behavior regression: each of the four skills still reads facts before use and
   writes facts only when composed content differs from current content.
5. The current (post STEP-6-REVIEW-3) content of `.hb/facts.md` remains valid under
   the new subflow's guidance — i.e. the subflow's criteria don't immediately flag the
   existing three facts as violations.
