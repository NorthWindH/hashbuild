# Background

Covers the planning half of AC2 of the parent ticket (`northwind/hb-016`). Once
`hb-sdk facts read`/`write` exist (step-0), the planning skills named in the
parent ticket — `hb-task-step-plan` and `hb-task-plan` (this skill) — must
actually read the facts store so recorded facts inform planning output, rather
than facts being written but never consulted.

---

# Acceptance Criteria

1. `hb-task-step-plan.md`'s Steps include a step that runs `hb-sdk facts read`
   before generating/updating `plan.md`, and the plan-generation step is
   instructed to take the returned facts into account.
2. `hb-task-plan.md`'s Steps include a step that runs `hb-sdk facts read` before
   gap analysis / breakdown, so drafted step tickets can reflect known facts.
3. In both skills, when the facts store is empty or missing (per step-0's
   `read` contract), the skill proceeds unaffected — no error, no blocking
   prompt.
4. Manual verification: with the fact "skills live in the project under
   `./skills`" recorded via `hb-sdk facts write`, running `/hb-task-step-plan`
   on a step whose ticket concerns skill files produces a plan that reflects
   that fact (e.g. references the correct `./skills` path) without needing it
   restated in the ticket.

---

# Out of scope

- Execution-time reads or post-execution updates to the facts store —
  step-2.
- Any planning-adjacent skill not named in the parent ticket (e.g.
  `hb-task-step-add`, `hb-ticket-discuss`).
