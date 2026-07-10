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
- `skills/hb-*.md` in this repo is the canonical source for skill definitions.
  `~/.claude/skills/hb-*/` is a separate installed/deployed copy, not the source to
  edit. This has caused repeated confusion across sessions (see hb-005/step-1 and
  hb-008/step-1 review notes, and the ad4cd403 session referenced in hb-016/step-6
  STEP-6-REVIEW-2) — check this before assuming where a skill lives.
- hb-015/step-1 deleted (not preserved dormant) the pre-existing Jira push/NL-resolution
  /Idea-link logic from `skills/hb-ticket-discuss.md` while rewriting it into the loop
  skeleton — a deviation from that step's plan, which had wanted it left in place. The
  exact original wording is fully recoverable via `git show 7bd2c42:skills/hb-ticket-
  discuss.md` (last commit before the rewrite), not present in the live file. hb-015/
  step-5 (Push action) will need to re-author it from that git history; hb-015/step-2
  (Load action) reused only its Jira *update-path* resolution algorithm (explicit key →
  getJiraIssue; else JQL search → searchJiraIssuesUsingJql; ambiguous → numbered list,
  never auto-select) in adapted, read-only form — never its create path.