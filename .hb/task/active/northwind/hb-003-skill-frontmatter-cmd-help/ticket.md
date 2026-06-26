# Background

When a user browses skills in the Claude Code harness, the first thing they see is the `description` field from each skill's YAML frontmatter. Currently every description opens with prose — a summary of what the skill does — but contains no usage line. The user cannot tell what arguments a skill expects without reading the full skill body.

The fix is mechanical: prepend a one-line usage synopsis to the `description` of each skill file so it is the first text visible in the harness skill browser.

Skills and their current argument surfaces (derived from each file's `## Inputs` table):

| Skill | Usage synopsis |
|---|---|
| `hb-init` | `/hb-init [--help]` |
| `hb-status` | `/hb-status [--help]` |
| `hb-task-archive` | `/hb-task-archive <author/task-id> [--help]` |
| `hb-task-create` | `/hb-task-create <author/task-id> [--ticket <path>] [--ticket-overwrite] [--help]` |
| `hb-task-plan` | `/hb-task-plan <author/task-id> [--help]` |
| `hb-task-step-add` | `/hb-task-step-add <author/task-id> [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] [--help]` |
| `hb-task-step-execute` | `/hb-task-step-execute <author/task-id/step-n> [--help]` |
| `hb-task-step-plan` | `/hb-task-step-plan <author/task-id/step-n> [--help]` |
| `hb-task-step-review-address` | `/hb-task-step-review-address <author/task-id/step-n> [--no-todo-scan] [--commits N] [--help]` |
| `hb-task-step-review-init` | `/hb-task-step-review-init <author/task-id/step-n> [--help]` |

---

# Acceptance Criteria

1. Every `skills/*.md` file has a usage synopsis as the first line of its `description` field.
    1. The synopsis follows the form `/hb-<name> [<required-args>] [<optional-args>]`, using `<angle-brackets>` for placeholders and `[square brackets]` for optional items.
    2. The synopsis is separated from the existing prose description by a newline so both are visible in the harness.
    3. The synopsis matches the arg surface documented in that skill's `## Inputs` table — no args added or omitted.
2. The existing prose description is preserved verbatim after the synopsis; only the prepended line is new content.
3. All 10 skill files are updated: `hb-init.md`, `hb-status.md`, `hb-task-archive.md`, `hb-task-create.md`, `hb-task-plan.md`, `hb-task-step-add.md`, `hb-task-step-execute.md`, `hb-task-step-plan.md`, `hb-task-step-review-address.md`, `hb-task-step-review-init.md`.
4. No other content in any skill file is changed — steps, reference tables, allowed-tools, and `name` field are untouched.

---

# Out of scope

- Changes to skill logic, step instructions, or reference files.
- Adding synopsis lines anywhere other than the frontmatter `description` field.
- Creating new skills or modifying the `hb-sdk` scripts.
