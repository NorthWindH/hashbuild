# Background

The `description` field in each skill's YAML frontmatter is the first text visible when a user browses skills in the Claude Code harness. Currently every description opens with prose but has no usage line, so the user cannot tell what arguments a skill accepts without reading the full skill body.

Prepend a one-line usage synopsis to the `description` field of all 10 `skills/*.md` files. The synopses are already defined in the task-level `ticket.md` Background table and must match each file's `## Inputs` table exactly.

---

# Acceptance Criteria

1. Every `skills/*.md` file has a usage synopsis as the first line of its `description` field.
    1. The synopsis follows the form `/hb-<name> [--help] [<other-optional-flags>] <positional-args>` — `--help` first, then other optional flags, then required positional args last.
    2. A blank line separates the synopsis from the existing prose description.
    3. The synopsis matches the arg surface in that skill's `## Inputs` table exactly — no args added or omitted.
2. The existing prose description is preserved verbatim after the synopsis.
3. All 10 files are updated: `hb-init.md`, `hb-status.md`, `hb-task-archive.md`, `hb-task-create.md`, `hb-task-plan.md`, `hb-task-step-add.md`, `hb-task-step-execute.md`, `hb-task-step-plan.md`, `hb-task-step-review-address.md`, `hb-task-step-review-init.md`.
4. No other content in any skill file is changed — `name`, `allowed-tools`, step instructions, and reference tables are untouched.

---

# Out of scope

- Changes to skill logic, step instructions, or reference files.
- Adding synopsis lines anywhere other than the frontmatter `description` field.
- Creating new skills or modifying `hb-sdk` scripts.
