# Background

`hb-sdk state next-action` sometimes embeds a "run `/clear` first" instruction directly into a next-action's description or command string (e.g. `Move to the next step (run \`/clear\` first): ...` or `Run \`/clear\`, then \`/hb-task-plan ...\``). This makes sense when the SDK output is consumed in isolation, but `hb-flow` presents these same next actions under its own contract, which already assumes the user invoked `/hb-flow` in a fresh session (after `/clear` or a new session) — or, if not, that they know what they're doing. Surfacing a redundant "run `/clear` first" instruction inside `hb-flow`'s own report is confusing and contradicts that assumption.

---

# Acceptance Criteria

1. When `hb-flow` reports next actions to the user (its Step 3, sourced from `hb-sdk state next-action`), any "run `/clear` first" instruction embedded in an action's description or command string is stripped/dropped before display.
    1. Covers the parenthetical form, e.g. `(run \`/clear\` first)`.
    2. Covers the prefix form, e.g. `Run \`/clear\`, then \`/hb-task-plan ...\``, which should be reduced to just the underlying action (e.g. `\`/hb-task-plan ...\` to plan ... into steps`).
2. The resolved invocation `hb-flow` ultimately confirms and invokes (Steps 6-8) is unaffected by this change — it only concerns the human-readable report in Step 3, not the underlying action resolution or the `Skill` tool call.
3. `hb-sdk state next-action`'s own raw output (for callers other than `hb-flow`) is unchanged — the tag is dropped only in `hb-flow`'s presentation layer, not in the SDK itself.

---

# Out of scope

- Changing whether `hb-flow` itself calls `/clear` before or after invoking a target skill — no such behavior exists today and none is being added.
- Any other formatting changes to `hb-sdk state next-action`'s output beyond dropping the `/clear` instruction.
