# Background

With the `hb-sdk task unarchive` subcommand in place (step-0), this step adds the `hb-task-unarchive` skill file that wraps it — mirroring the structure of `hb-task-archive.md`.

---

# Acceptance Criteria

1. `skills/hb-task-unarchive.md` exists alongside `skills/hb-task-archive.md`.
2. Frontmatter `description` field contains the synopsis: `/hb-task-unarchive [--help] <author/task-id>`.
3. `allowed-tools` mirrors `hb-task-archive`: `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` and `Bash(git *)`.
4. Skill body follows the same four-step flow as `hb-task-archive`:
    1. **Help check** — delegates to `skill-help.md`.
    2. **Unarchive task** — calls `hb-sdk task unarchive <name>`; surfaces stderr verbatim on error and stops.
    3. **Commit** — follows `committing.md` (non-step commit, so no step number in message).
    4. **Prompt user** — tells the user the task is restored and suggests `/hb-status` or `/hb-task-step-add`.
5. Output section reports the restored task path; errors surfaced verbatim.

---

# Out of scope

- Changes to `hb-sdk` or any other existing skill files.
- Unarchiving individual steps within a task.
- Interactive confirmation prompts.
