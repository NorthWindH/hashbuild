# Background

There is currently no way to restore an archived task back to active. `hb-task-archive` moves a task from `task/active/` to `task/archive/` with a wrapped `hb-sdk task archive` call, but no inverse exists — neither in the SDK nor as a skill.

This task adds the symmetric counterpart: a `task unarchive` subcommand to `hb-sdk` and a `hb-task-unarchive` skill that wraps it, following the same structure and error-handling conventions as `hb-task-archive`.

---

# Acceptance Criteria

## A. SDK command: `hb-sdk task unarchive <name>`

1. Locates the task folder under `task/archive/` using `_find_matching_task_folders` (author + task-id match, flavor optional).
2. Moves the task folder to `task/active/<author>/` — creating the author directory if it does not exist.
3. Prints the source and destination paths via `report_paths`.
4. If the archive author directory is empty after the move, removes it (mirrors archive cleanup of empty active author dir).
5. Errors verbatim on stderr in each of these cases:
    1. Task not found in either location.
    2. Task exists but is already in `task/active/` (not archived).
    3. Destination path already exists.

## B. Skill: `skills/hb-task-unarchive.md`

1. Frontmatter synopsis in `description`: `/hb-task-unarchive [--help] <author/task-id>`.
2. `allowed-tools` mirrors `hb-task-archive`: `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` and `Bash(git *)`.
3. Steps follow the same four-step flow as `hb-task-archive`:
    1. Help check — delegates to `skill-help.md`.
    2. Unarchive task — calls `hb-sdk task unarchive <name>`, surfaces stderr verbatim on error.
    3. Commit — follows `committing.md` (non-step commit).
    4. Prompt user — tells the user the task is restored and suggests `/hb-status` or `/hb-task-step-add`.
4. Output section reports the restored task path; errors surfaced verbatim.

## C. Integration

1. The new skill file appears under `skills/` alongside `hb-task-archive.md`.
2. Running `hb-sdk task unarchive <name>` on a valid archived task moves it to active and exits 0.
3. Running `hb-sdk task archive` followed by `hb-sdk task unarchive` on the same task name leaves the task folder in `task/active/` in its original state.

---

# Out of scope

- Changes to any existing skill files.
- Unarchiving steps within a task (only whole-task unarchive is in scope).
- Interactive confirmation prompts before unarchiving.
- Bulk unarchive of multiple tasks in one invocation.
