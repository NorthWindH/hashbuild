# Background

`hb-sdk` has a `task archive` subcommand but no inverse. This step adds the symmetric `task unarchive` subcommand that moves a task folder from `task/archive/` back to `task/active/`, following the same conventions as `task archive`.

---

# Acceptance Criteria

1. `hb-sdk task unarchive <name>` locates the task folder under `task/archive/` using `_find_matching_task_folders` (author + task-id match, flavor optional) and moves it to `task/active/<author>/`.
    1. Creates `task/active/<author>/` if it does not already exist.
    2. Prints source and destination paths via `report_paths` on success.
2. If the archive author directory is empty after the move, it is removed (mirrors archive cleanup of empty active author directory).
3. Errors are printed verbatim to stderr in each of these cases:
    1. Task not found in archive (or anywhere).
    2. Task exists but is already in `task/active/` (not archived).
    3. Destination path already exists.
4. Running `hb-sdk task archive <name>` followed by `hb-sdk task unarchive <name>` on the same task leaves the task folder in `task/active/` with identical contents (round-trip invariant).
5. Exits 0 on success; non-zero on any error.

---

# Out of scope

- The `hb-task-unarchive` skill file (covered in step-1).
- Unarchiving individual steps within a task.
- Bulk unarchive of multiple tasks in one invocation.
