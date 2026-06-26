# Background

When a user browses skills in the Claude Code harness, the first thing they see is the `description` field from each skill's YAML frontmatter. Currently every description opens with prose — a summary of what the skill does — but contains no usage line. The user cannot tell what arguments a skill expects without reading the full skill body.

The fix is mechanical: prepend a one-line usage synopsis to the `description` of each skill file so it is the first text visible in the harness skill browser.

Skills and their current argument surfaces (derived from each file's `## Inputs` table):

| Skill                         | Usage synopsis                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| `hb-init`                     | `/hb-init [--help]`                                                                                    |
| `hb-status`                   | `/hb-status [--help]`                                                                                  |
| `hb-task-archive`             | `/hb-task-archive [--help] <author/task-id>`                                                           |
| `hb-task-create`              | `/hb-task-create [--help] [--ticket <path>] [--ticket-overwrite] <author/task-id>`                     |
| `hb-task-plan`                | `/hb-task-plan [--help] <author/task-id>`                                                              |
| `hb-task-step-add`            | `/hb-task-step-add [--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>` |
| `hb-task-step-execute`        | `/hb-task-step-execute [--help] <author/task-id/step-n>`                                               |
| `hb-task-step-plan`           | `/hb-task-step-plan [--help] <author/task-id/step-n>`                                                  |
| `hb-task-step-review-address` | `/hb-task-step-review-address [--help] [--no-todo-scan] [--commits N] <author/task-id/step-n>`         |
| `hb-task-step-review-init`    | `/hb-task-step-review-init [--help] <author/task-id/step-n>`                                           |

---

# Acceptance Criteria

1. Every `skills/*.md` file has a usage synopsis as the first line of its `description` field.
   1. The synopsis follows the form `/hb-<name> [--help] [<other-optional-flags>] <positional-args>`, using `<angle-brackets>` for placeholders and `[square brackets]` for optional items — `--help` appears first, then any other optional flags, then required positional args last.
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
