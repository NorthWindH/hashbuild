# Background

When `hb-task-create` or `hb-task-step-add` are called without a `--ticket` argument,
the task/step skeleton is created but no `ticket.md` is written. The user must then
manually write one before they can plan or execute. Interactively prompting for the
essential ticket fields at creation time removes that gap and keeps the workflow unblocked.

---

# Acceptance Criteria

1. `hb-task-create <name>` (no `--ticket`) enters interactive mode and receives ticket
   content in any form from the user, then transforms it into a conforming `ticket.md`
   (Background, Acceptance Criteria, Out of scope sections) and writes it to the task
   folder before committing.
   1. If the received content is already structured as Background + Acceptance Criteria +
      optional Out of scope: transcribe verbatim if it is a perfect or near-perfect match
      to the standard form, or massage it minimally to conform if minor adjustments are
      needed.
   2. The commit includes the generated `ticket.md`.
2. `hb-task-step-add <name>` (no `--ticket`) applies the same interactive flow —
   receives content in any form, transforms it, and writes `ticket.md` to the step
   folder before committing.
3. Passing `--no-interactive` to either skill skips the prompt and creates the skeleton
   without a ticket (current behavior).
4. Passing `--ticket <path>` continues to work as before; `--no-interactive` is a no-op
   in that case (ticket file takes precedence).
5. The help output for both skills documents the new flag.

---

# Out of scope

- Modifying any other hb-\* skills.
- Validating the quality or completeness of user-provided content.
- Adding `--no-interactive` to skills other than `hb-task-create` and `hb-task-step-add`.
