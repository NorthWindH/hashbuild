# Background

With ideas storable and listable (steps 0–1), this step adds `hb-idea-promote` — the skill that graduates an idea into a full task ticket or step ticket. Promotion seeds the existing interactive ticket creation flow with the idea's content so the user can expand on it, then removes the idea once the ticket is written.

---

# Acceptance Criteria

1. `hb-idea-promote <author>/<index> <target>` is a new skill file at `skills/hb-idea-promote.md`.
2. Accepts two required positional arguments: `<author>/<index>` (the idea to promote) and `<target>` (the destination).
3. Fetches the idea's current content via `hb-sdk idea show <author>/<index>`; exits non-zero with a clear error if the idea does not exist.
4. When `<target>` is `<author>/<task_id>` (no step component):
    1. Seeds the `hb-task-create` interactive ticket creation flow with the idea's content pre-populated as the starting prompt.
    2. The user may expand or revise the content before the ticket is written.
    3. On successful ticket write, calls `hb-sdk idea remove <author>/<index>` to remove the source idea.
5. When `<target>` is `<author>/<task_id>/step-N`:
    1. Seeds the `hb-task-step-add` interactive ticket creation flow with the idea's content pre-populated.
    2. The user may expand or revise the content before the ticket is written.
    3. On successful ticket write, calls `hb-sdk idea remove <author>/<index>`.
6. If the user cancels or the downstream skill fails, the idea is NOT removed.
7. The skill includes a `--help` / `-h` flag that prints usage and exits.

---

# Out of scope

- `hb-idea-edit` — deferred to step-3.
- `README.md` and `structure.md` updates — deferred to step-4.
- Bulk promotion — excluded per task ticket.
