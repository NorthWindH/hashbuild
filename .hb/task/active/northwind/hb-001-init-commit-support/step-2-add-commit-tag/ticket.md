# Background

When reading `git log` on a task branch, commit subjects like `hb-001/step-2: add routes` give no indication of which lifecycle phase produced them — planning, execution, review, etc. This makes it hard to orient quickly in history.

Fix: add an optional `--tag <tag>` flag to `task` and `task-step` modes in `commit write-message-file`. When set, the tag is injected into the subject as `(tag)` immediately after the prefix separator:

- `task` without tag: `hb-001: short desc`
- `task` with `--tag step-add`: `hb-001: (step-add) short desc`
- `task-step` without tag: `hb-001/step-2: short desc`
- `task-step` with `--tag step-plan`: `hb-001/step-2: (step-plan) short desc`

Skills are then updated to pass the appropriate tag when they call `commit write-message-file`.

---

# Acceptance Criteria

## A. SDK — `commit write-message-file` flag

1. `task` mode accepts an optional `--tag <tag>` argument.
    1. With `--tag <t>`: subject is `<task_id>: (<t>) <short>`
    2. Without `--tag`: subject is `<task_id>: <short>` (no change to existing behavior)
2. `task-step` mode accepts an optional `--tag <tag>` argument.
    1. With `--tag <t>`: subject is `<task_id>/step-<n>: (<t>) <short>`
    2. Without `--tag`: subject is `<task_id>/step-<n>: <short>` (no change to existing behavior)
3. `plain` mode is unaffected — it does not accept `--tag` and passing it is an error.
4. `--tag` is valid alongside `--long`; `--long` body is unaffected.

## B. `committing.md` updated

5. The mode table in `committing.md` reflects the optional `--tag` flag for `task` and `task-step` rows.
6. The examples section includes at least one example showing `--tag` usage for each of `task` and `task-step`.

## C. Skills pass correct tags

Each skill below passes the specified `--tag` value when calling `commit write-message-file`. Skills that call it multiple times (e.g. intermediate commits) pass the same tag each time.

| Skill file | Tag value |
|---|---|
| `skills/hb-task-archive.md` | `task-archive` |
| `skills/hb-task-unarchive.md` | `task-unarchive` |
| `skills/hb-task-create.md` | `task-create` |
| `skills/hb-task-step-add.md` | `step-add` |
| `skills/hb-task-step-plan.md` | `step-plan` |
| `skills/hb-task-step-execute.md` | `step-execute` |
| `skills/hb-task-step-review-init.md` | `step-review` |
| `skills/hb-task-step-review-address.md` | `step-review` |

7. Skills not in the table (`hb-init`, `hb-status`, `hb-task-plan`) are not modified.

## D. Tests

8. `tests/skills/scripts/test_hb-sdk.py` is updated to cover:
    1. `task` mode with `--tag`: subject contains `(tag)` in the correct position
    2. `task` mode without `--tag`: subject is unchanged from current behavior
    3. `task-step` mode with `--tag`: subject contains `(tag)` in the correct position
    4. `task-step` mode without `--tag`: subject is unchanged from current behavior
    5. `plain` mode rejects `--tag`
9. All existing tests pass without modification.

---

# Out of scope

- Validating or restricting the set of allowed tag values (any non-empty string is accepted).
- Adding `--tag` support to `plain` mode.
- Changing the `--long` body format.
- Updating any execution or review artifacts to surface the tag.
