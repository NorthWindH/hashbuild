# Facts Store

- The read-before/write-after facts pattern (hb-sdk facts read then facts write, gated
  on composed content differing) is implemented in all four hb-task-* lifecycle
  skills: hb-task-step-execute, hb-task-step-review-address, hb-task-step-plan,
  hb-task-plan. hb-ticket-discuss and hb-task-step-add do not yet participate.