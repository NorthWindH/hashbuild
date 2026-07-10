# Background

Covers the execution half of AC2, plus AC4 and AC5, of the parent ticket
(`northwind/hb-016`). Step-0 built the `hb-sdk facts read`/`write` CLI surface;
step-1 wired reads into planning. This step wires the facts store into
`hb-task-step-execute`: read before executing, then re-read and update
afterward, so the store stays current for the next planning/execution cycle.

---

# Acceptance Criteria

1. `hb-task-step-execute.md`'s Steps include a step that runs `hb-sdk facts
   read` before executing the plan, and the execution step is instructed to
   take the returned facts into account.
2. After execution and before the commit step, `hb-task-step-execute.md`
   includes a step that:
    1. re-reads the current facts store (`hb-sdk facts read`);
    2. removes or corrects any facts discovered to be stale or incorrect
       during this execution, via `hb-sdk facts write`;
    3. adds new facts discovered during execution only when they are likely
       to matter for future planning/execution, weighed against the size
       guidance from step-0 (target <= 100 lines, hard max 1000 lines, <= 120
       chars/line).
3. Any facts-store changes made during this step are included in the step's
   commit, per `committing.md`.
4. End-to-end (parent ticket AC5): recording the fact "skills live in the
   project under `./skills`" via `hb-sdk facts write`, a later
   `/hb-task-step-plan` or `/hb-task-step-execute` invocation reads it back
   (per step-1/this step), and a subsequent execution that finds it stale
   removes or updates it — demonstrated manually as part of this step's
   verification.

---

# Out of scope

- Planning-time reads — already covered by step-1.
- Automatic/programmatic detection of which facts are stale — the agent
  applies judgement, per the parent ticket's Out of scope.
