# Background

With `interactive-ticket-subflow.md` in place, `hb-task-create` needs to invoke it when no `--ticket` is provided. This step wires the subflow in, adds `--no-interactive` as a documented flag, and updates the commit and final-prompt steps to account for the ticket already being written before the commit.

---

# Acceptance Criteria

1. The `--no-interactive` flag is documented in the skill's frontmatter `argument-hint`, `description`, and `## Inputs` table.
2. After the help check and before the SDK call, the skill evaluates flag precedence:
    1. If `--ticket <path>` was supplied: proceed as today (no interactive prompt, ticket file passed to SDK).
    2. If `--no-interactive` was supplied (and no `--ticket`): proceed as today without a ticket (current behavior).
    3. If neither flag was supplied: follow `interactive-ticket-subflow.md` to prompt the user, transform content, and write `ticket.md` to the task folder path resolved by the SDK. Then proceed to the SDK call (with `--ticket <written_path>` so the SDK does not overwrite it) and commit.
3. The commit step includes the generated `ticket.md` when interactive mode ran.
4. The final prompt message (Step 4) reflects that a ticket has already been written when interactive mode ran, omitting the "write a ticket.md first" guidance in that case.
5. `hb-task-step-plan` is still cited as the next step after a task with a ticket is created.

---

# Out of scope

- Changes to `hb-task-step-add.md` (step 2).
- Other hb-* skills.
- Validating ticket quality.
