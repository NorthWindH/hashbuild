# Background

The previous step added `hb-sdk state record`/`hb-sdk state show`, giving hashbuild a place to persist a last-executed-action record — but no skill actually calls it yet. Task ticket AC 1 requires the record to be written "after each relevant `hb-*` skill completes." The relevant skills are the ones that change task/step state: `hb-task-create`, `hb-task-step-add`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`, `hb-task-archive`, `hb-task-unarchive`. (`hb-init` runs before any task exists; `hb-status` is read-only; `hb-ticket-discuss` explicitly makes no `.hb/` writes — none of these three carry task/step execution state, so they are excluded.)

---

# Goal

Every skill in the list above records a last-executed-action entry (skill name, task/step ref, outcome) via `hb-sdk state record` as its final step, on both success and failure paths where the skill has a defined failure outcome.

---

# Acceptance Criteria

1. Each of the 8 skills listed in Background gains a final "Record execution state" step in its `.md` file that invokes `hb-sdk state record --skill <this-skill-name> --outcome <success|failure> [--task <ref>] [--step <ref>] --timestamp <ts>` after its existing terminal steps (e.g. after commit, after report).
    1. For step-scoped skills (`hb-task-step-add`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`), the record includes both the task ref and the step ref.
    2. For task-scoped skills (`hb-task-create`, `hb-task-archive`, `hb-task-unarchive`), the record includes the task ref only.
2. The timestamp is obtained by the skill's invoking agent (e.g. via a shell `date` call documented in the skill step) and passed through to `hb-sdk state record`, consistent with `hb-sdk` remaining deterministic (per the prior step's design).
3. If a skill's flow already has an early-exit/error path (e.g. "surface the error verbatim and stop"), that path is documented to also record an outcome of `failure` before stopping, where practical — skills whose error paths stop before any task/step is resolved (e.g. an invalid task name) are exempt and documented as such.
4. `hb-sdk state show` after running any one of the 8 skills reflects that skill's name, ref, and outcome.
5. No behavior of the 8 skills changes other than the added recording step — existing acceptance criteria/behavior for each skill (commits, file writes, prompts) are unaffected.

---

# Out of scope

- Changes to `hb-sdk state` itself (module, CLI) — already delivered in the prior step.
- Deriving or displaying a recommended next-action from the recorded state — deferred to the next step.
- `hb-init`, `hb-status`, `hb-ticket-discuss` — excluded per Background.
