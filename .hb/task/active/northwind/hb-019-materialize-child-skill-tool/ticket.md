# Background

`references/breakdown-subflow.md`'s caller contract for `$MATERIALIZE_CHILD` documents the value as something like "invoke `hb-task-step-add --ticket <path> [--flavor <slug>]`" (see `hb-task-plan.md`'s resolution of `$MATERIALIZE_CHILD`). That phrasing is ambiguous: it doesn't say whether "invoke" means calling `hb-task-step-add` via the `Skill` tool (which runs that skill's own facts-read/commit/state-record steps) or calling the underlying `hb-sdk task step add` command directly (which skips them). Today this ambiguity is only resolved by a standing entry in `.hb/facts.md`, which future readers have to already know to look up.

# Acceptance Criteria

1. `breakdown-subflow.md`'s `$MATERIALIZE_CHILD` caller-contract entry explicitly states that when a resolved value invokes another skill (e.g. `hb-task-step-add`), it means invoking it via the `Skill` tool — not calling the underlying `hb-sdk` command directly — so this is unambiguous from the doc itself.
2. Every current caller that resolves `$MATERIALIZE_CHILD` to "invoke `hb-task-step-add` ..." (currently `hb-task-plan.md`) is checked and, if needed, updated so its own wording is consistent with the clarified contract in criterion 1.
3. The now-redundant fact in `.hb/facts.md` ("breakdown-subflow.md's `$MATERIALIZE_CHILD` ... means invoke the skill via the Skill tool, not call `hb-sdk task step add` directly") is removed once the doc itself makes this unambiguous.
4. All other places across skills, flows, and subflows (not just `$MATERIALIZE_CHILD` callers) where one skill invokes another skill are identified, and each is confirmed — or updated — to invoke via the `Skill` tool rather than calling the target skill's underlying `hb-sdk` command(s) directly.

# Out of scope

- Changing `$MATERIALIZE_CHILD`'s behavior for `hb-ticket-discuss`'s in-conversation ticket list path (`breakdown-ticket-subflow.md`), which doesn't invoke another skill and isn't affected by this ambiguity.
