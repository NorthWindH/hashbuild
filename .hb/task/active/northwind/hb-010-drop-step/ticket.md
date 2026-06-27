# Background

There is currently no way to remove a step once it has been added to a task. A `hb-task-step-drop` skill backed by an `hb-sdk` command is needed to delete a step folder cleanly.

---

# Acceptance Criteria

1. `hb-sdk` exposes a `step drop <author/task-id/step-n>` subcommand that deletes the target step folder.
2. A `hb-task-step-drop` skill is created that accepts a fully-qualified step name and calls the SDK command.
3. Running the skill on a valid step removes the step folder from the filesystem.
4. The skill commits the deletion following the standard committing rules.
