> **Subflow — Clear ticket(s) action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Removes a subset (or all)
> of the tickets currently held in `$TICKET_CONTEXT` — in-memory context
> mutation only, no file I/O, no persistence implication.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- (implicit) the user's triggering utterance — already visible in the same
  conversation this subflow executes in; not a formal parameter.

#### A. Resolve target set

1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to clear."
   → return outcome `"Clear: no tickets in context."` (no mutation).
2. Utterance requests the whole context ("clear all," "clear everything," or
   an equivalent) → `$TARGETS` = every entry in `$TICKET_CONTEXT`. Continue
   to §B.
3. Utterance refers only to "the active ticket" (no other ticket named) →
   the entry with `active: true`. None active → tell the user "No active
   ticket to clear." → return outcome `"Clear: no active ticket."` (no
   mutation). Otherwise `$TARGETS` = `[that entry]`. Continue to §B.
4. Utterance names one or more tickets (by id/summary):
   1. Split the utterance into its distinct named references (one or
      several — e.g. "PROJ-123 and PROJ-124" is two).
   2. For each named reference, semantic-match against every entry's
      `id_or_summary` — same posture as `breakdown-ticket-subflow.md` §A /
      `load-ticket-subflow.md` §A ("never guess"):
      - Zero matches → ask the user to clarify that one reference; treat
        the clarifying reply as the name and re-match it.
      - Multiple matches → present a numbered list of the matching
        entries' `id_or_summary`s, scoped to that one reference; the user
        picks one — never auto-select.
      - One match → include it in the resolving set.
   3. `$TARGETS` = the deduplicated union of every entry resolved across
      all named references. Continue to §B.
5. Utterance requests none of the above (no "all," no named reference, no
   "active ticket" phrasing) → ask the user "Which ticket(s) would you like
   to clear?" and re-run this §A against the reply.

#### B. Confirm

1. `|$TARGETS|` > 1 (true for any multi-entry "all" or multi-name request) →
   present the list of `$TARGETS`' `id_or_summary`s and ask the user to
   confirm removal. Decline → return outcome `"Clear: declined, nothing
   removed."` (no mutation).
2. `|$TARGETS|` == 1 → skip confirmation; proceed directly to §C.

#### C. Apply

1. Remove every entry in `$TARGETS` from `$TICKET_CONTEXT`, matched by
   entry identity (the exact entries resolved in §A, not a fresh
   `id_or_summary` re-match).
2. Do not set `active: true` on any remaining entry, even if the removed
   set included the previously-active one — no auto-promotion. If entries
   remain and none is active, `ticket-loop-subflow.md` §C's existing
   presentation already shows "No active ticket" — no change needed there.
3. Return outcome:
   - Whole-context ("all") request → `"Cleared all N ticket(s) from
     context."`
   - Otherwise → `"Cleared N ticket(s): <label1>, <label2>, ...."`
   (N = `|$TARGETS|`; labels = each target's `id_or_summary`, in the order
   resolved.)

**Failure/degradation contract**: §A's empty-context, no-active-ticket, and
unresolved-reference cases, and §B's decline, all return without mutating
`$TICKET_CONTEXT`. No partial removal ever occurs — §C only runs once
`$TARGETS` is fully resolved and (when required) confirmed.
