# Background

The previous step added `hb-sdk state record`/`hb-sdk state show`, giving hashbuild a place to persist a last-executed-action record — but no skill actually calls it yet. Task ticket AC 1 requires the record to be written "after each relevant `hb-*` skill completes." The relevant skills are the ones that change task/step state: `hb-task-create`, `hb-task-step-add`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`, `hb-task-archive`, `hb-task-unarchive`. (`hb-init` runs before any task exists; `hb-status` is read-only; `hb-ticket-discuss` explicitly makes no `.hb/` writes — none of these three carry task/step execution state, so they are excluded.)

The prior step's design had the invoking skill pass a `--timestamp` obtained via a shell `date` call. That would require granting a new `Bash(date *)` permission on every one of the 8 skills' front-matter and adds a step an LLM-driven flow can get wrong (wrong format, forgotten capture, etc.) for no real benefit. Revised approach: `hb-sdk` determines the timestamp itself at record time; skills no longer pass one.

---

# Goal

Every skill in the list above records a last-executed-action entry (skill name, task/step ref, outcome) via `hb-sdk state record` as its final step, on both success and failure paths where the skill has a defined failure outcome.

---

# Acceptance Criteria

1. Each of the 8 skills listed in Background gains a final "Record execution state" step in its `.md` file that invokes `hb-sdk state record --skill <this-skill-name> --outcome <success|failure> [--task <ref>] [--step <ref>]` after its existing terminal steps (e.g. after commit, after report).
    1. For step-scoped skills (`hb-task-step-add`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`), the record includes both the task ref and the step ref.
    2. For task-scoped skills (`hb-task-create`, `hb-task-archive`, `hb-task-unarchive`), the record includes the task ref only.
2. `hb-sdk state record` determines the timestamp itself (current local time at call time, timezone-aware — not UTC) rather than accepting one from the caller. No skill's `.md` file passes a timestamp, obtains one via a shell `date` call, or requires any new shell-command permission to support this step.
3. If a skill's flow already has an early-exit/error path (e.g. "surface the error verbatim and stop"), that path is documented to also record an outcome of `failure` before stopping, where practical — skills whose error paths stop before any task/step is resolved (e.g. an invalid task name) are exempt and documented as such.
4. `hb-sdk state show` after running any one of the 8 skills reflects that skill's name, ref, outcome, and a timestamp.
5. No behavior of the 8 skills changes other than the added recording step — existing acceptance criteria/behavior for each skill (commits, file writes, prompts) are unaffected.

---

# Out of scope

- Changes to `hb-sdk state`'s `--skill`/`--outcome`/`--task`/`--step` handling, or to `hb-sdk state show` — already delivered in the prior step. (Only the timestamp source moves from caller-supplied to self-generated; see AC 2.)
- Deriving or displaying a recommended next-action from the recorded state — deferred to the next step.
- `hb-init`, `hb-status`, `hb-ticket-discuss` — excluded per Background.
