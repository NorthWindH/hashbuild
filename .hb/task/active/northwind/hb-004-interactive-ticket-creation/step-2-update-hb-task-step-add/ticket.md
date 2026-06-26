# Background

Mirror of step 1 for `hb-task-step-add`. With the subflow available and `hb-task-create` already updated, this step applies the same integration to `hb-task-step-add`, making interactive ticket creation consistent across both creation points.

---

# Acceptance Criteria

1. The `--no-interactive` flag is documented in the skill's frontmatter `argument-hint`, `description`, and `## Inputs` table.
2. After the help check and before the SDK call, the skill evaluates flag precedence:
    1. If `--ticket <path>` was supplied: proceed as today (no interactive prompt, ticket file passed to SDK).
    2. If `--no-interactive` was supplied (and no `--ticket`): proceed as today without a ticket (current behavior).
    3. If neither flag was supplied: follow `interactive-ticket-subflow.md` to prompt the user, transform content, and write `ticket.md` to the step folder path resolved by the SDK. Then proceed to the SDK call (with `--ticket <written_path>` so the SDK does not overwrite it) and commit.
3. The commit step includes the generated `ticket.md` when interactive mode ran.
4. The final prompt message (Step 4) reflects that a ticket has already been written when interactive mode ran, directing the user straight to `/hb-task-step-plan` rather than asking them to fill in the ticket first.

---

# Out of scope

- Changes to `hb-task-create.md` (step 1).
- Other hb-* skills.
- Validating ticket quality.
