# Facts Store

- The read-before/write-after facts pattern (hb-sdk facts read then facts write, gated
  on composed content differing) is implemented in all four hb-task-* lifecycle
  skills: hb-task-step-execute, hb-task-step-review-address, hb-task-step-plan,
  hb-task-plan. hb-ticket-discuss and hb-task-step-add do not yet participate.
- The write-after judgement clause in hb-task-step-plan.md (step 6) and hb-task-plan.md
  (step 8) now explicitly includes user corrections/interruptions during the session as
  a fact source, not just what ended up written into plan.md/a step ticket. The older
  write-after steps in hb-task-step-execute.md (step 7) and
  hb-task-step-review-address.md (step 9f) still only say "based on what this execution
  revealed" and were not updated to call this out explicitly — same latent gap, left
  as-is since out of scope for hb-016/step-6.