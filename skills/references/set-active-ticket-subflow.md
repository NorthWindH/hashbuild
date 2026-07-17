> **Subflow — Set active ticket action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Marks one existing entry in
> `$TICKET_CONTEXT` as active — in-memory flag mutation only, no file I/O, no
> content change.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out); mutated only via
  `active` flags, never `content` or `id_or_summary`.
- (implicit) the user's triggering utterance — already visible in the same
  conversation this subflow executes in; not a formal parameter.
- (implicit) the order of the most-recently-presented `ticket-loop-subflow.md`
  §C numbered list.

#### A. Resolve target

1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to set
   active." → return outcome `"Set active: no tickets in context."` (no
   mutation).
2. Utterance holds a bare positional reference to the last-presented §C list,
   such as "ticket 2" or "the second one":
   - In range (`1..=|$TICKET_CONTEXT|`) → `$TARGET` = the entry at that
     position in §C's current order. Continue to §B.
   - Out of range → tell the user, re-ask which ticket, re-run this §A
     against the reply.
3. Utterance names a ticket by `id_or_summary`, no positional reference —
   semantic-match against every entry's `id_or_summary`, same posture as
   `clear-ticket-subflow.md` §A step 4 ("never guess"):
   - Zero matches → ask the user to clarify; treat the clarifying reply as
     the name and re-match it.
   - Multiple matches → present a numbered list of the matching entries'
     `id_or_summary`s; the user picks one — never auto-select.
   - One match → `$TARGET` = that entry. Continue to §B.
4. Neither a positional nor a named reference → ask "Which ticket would you
   like to set active?" and re-run this §A against the reply.

#### B. Apply

1. Set `$TARGET.active = true`.
2. Unset `active` on every other entry, so at most one entry stays active.
3. Never modify `$TARGET.content` or any other field.
4. Return outcome `"Set active: <id_or_summary> is now the active ticket."`
   naming `$TARGET.id_or_summary`.

**Failure/degradation contract:** every early-return path in §A (empty
context, out-of-range, zero-match, no-reference) leaves `$TICKET_CONTEXT`
unmutated. A successful §B pass sets exactly one entry active and unsets
every other, with no partial state.
