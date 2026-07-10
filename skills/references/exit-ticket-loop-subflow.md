> **Subflow — Exit action.** Invoked only via `ticket-loop-subflow.md`'s
> Action Registry (§B). Ends the loop; never discards a ticket.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — list of ticket entries (read-only here)
- `$ACTION_LOG` — list of strings describing actions taken this session (read-only here)

#### Behavior

1. Compose a summary: the count and `id_or_summary` of every entry still in `$TICKET_CONTEXT`, and the full `$ACTION_LOG`.
2. Present the summary to the user.
3. Tell the user to `/clear` the conversation when ready.
4. Signal loop termination: this subflow, and `ticket-loop-subflow.md` above it, return to the calling skill, which then ends. No further iterations run.

**Failure/degradation contract:** N/A — no external calls, no failure mode. An empty `$TICKET_CONTEXT` / `$ACTION_LOG` summarizes as "0 tickets left in context" / "no actions taken."
