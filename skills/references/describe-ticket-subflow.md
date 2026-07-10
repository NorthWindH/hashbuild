> **Subflow — Describe ticket action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Creates a new ticket and
> adds it to the loop's in-conversation context as the active entry.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- `$TICKET_SEQ` — mutable integer counter (in/out)

#### Behavior

1. Increment `$TICKET_SEQ`. Set `$TARGET_PATH` = `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` — a fresh, non-colliding scratch folder for this call.
2. Follow [${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](interactive-ticket-subflow.md) with `$TARGET_PATH` as set above, `$TICKET_SUPPLIED` = `false`, `$NO_INTERACTIVE` = `false`. This writes `$TARGET_PATH/ticket.md`.
3. **Review loop** — repeat until the user is satisfied:
   1. Read `$TARGET_PATH/ticket.md` and display its full content as formatted markdown (not a fenced block).
   2. Ask the user: "Does this ticket look right? Reply **yes** to continue, or describe any changes."
   3. If the user replies **yes** (or an equivalent affirmation): break — proceed to step 4.
   4. Otherwise: treat the reply as corrections. Re-run only Sections C (Transform) and D (Write) of `interactive-ticket-subflow.md`, incorporating the user's feedback into the derived content. Then return to step 3.1.
4. On confirm: read back `$TARGET_PATH/ticket.md`'s full text as `$content`. Derive `$id_or_summary` from the ticket's Background section — its first clause or sentence, truncated to roughly 8 words.
5. Unset `active` on every existing entry in `$TICKET_CONTEXT`, then append `{ id_or_summary: $id_or_summary, content: $content, active: true }`.
6. Return to the caller with outcome string `"Described ticket: $id_or_summary"`.

**Failure/degradation contract:** identical to `interactive-ticket-subflow.md`'s own — its guard clause is not reachable here since this subflow always calls it with both `$TICKET_SUPPLIED` and `$NO_INTERACTIVE` set to `false`.
