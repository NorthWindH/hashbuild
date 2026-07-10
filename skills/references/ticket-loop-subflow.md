> **Subflow — ticket loop iteration.** Owns per-iteration state presentation,
> natural-language action dispatch, and the return-to-top control flow for
> `hb-ticket-discuss`. Later steps extend this skill's action set only via
> §B (the Action Registry) — Sections A, C, D, E do not change when a new
> action is added.

**Caller contract.** Before injecting this subflow, the calling skill must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (§A); caller initializes to `[]`
- `$TICKET_SEQ` — mutable integer counter; caller initializes to `0`
- `$ACTION_LOG` — mutable list of strings; caller initializes to `[]`

#### A. Ticket entry model

Each entry in `$TICKET_CONTEXT` is `{ id_or_summary, content, active }`:

- `content` — the full verbatim text of the ticket, read back from its scratch
  file immediately after it's written. This keeps `$TICKET_CONTEXT`
  self-contained; the `/tmp` scratch file is a mechanical artifact of reusing
  `interactive-ticket-subflow.md`'s write step, not the source of truth.
- `id_or_summary` — a short human-identifying label for the entry.
- `active` — boolean; at most one entry has `active: true` at any time.

**Extensibility note**: this triple is the contract every action reuses
unmodified. Later steps may attach *additional* optional fields to an entry
for their own bookkeeping — that is additive, not a redefinition, and doesn't
require revisiting this subflow.

#### B. Action Registry

The single edit point later steps use to add new actions (one new row plus
one new sibling subflow file, following the same shape as the two rows
below):

| Action | Selectable via (examples) | Dispatch subflow |
|---|---|---|
| Describe ticket | "describe a ticket", "create a new one", "let's write a ticket for X" | `describe-ticket-subflow.md` |
| Exit | "exit", "I'm done", "end the session" | `exit-ticket-loop-subflow.md` |

#### C. Present state

At the start of every iteration, present:

1. The active ticket's `id_or_summary`, or "No active ticket" if none is
   marked active (including when `$TICKET_CONTEXT` is empty — "No tickets in
   context yet").
2. The count of tickets currently in `$TICKET_CONTEXT`.
3. A numbered list of every entry's `id_or_summary`.
4. The available actions from §B (name + one-line description), then ask:
   "What would you like to do?"

#### D. Dispatch

Match the user's freeform reply against §B's action names and example
phrasings using semantic match, not exact keyword match. On an ambiguous or
unmatched reply: ask a clarifying question and re-prompt, without re-running
all of §C. On a confident match: invoke the matched action's dispatch
subflow, passing `$TICKET_CONTEXT` and `$TICKET_SEQ` by reference (the
callee mutates them in place).

#### E. Log + loop continue

When the dispatched action subflow returns (every action except Exit returns
control here), append one line to `$ACTION_LOG` describing what happened
(e.g. `"Described ticket: <label>"`), then return to §C. Exit does not return
here — it ends the loop itself (see `exit-ticket-loop-subflow.md`), and
control passes back up through this subflow's own return to the calling
skill.

**Failure/degradation contract:** an empty `$TICKET_CONTEXT` at the first
iteration is valid (§C shows "No tickets in context yet"). Unrecognized
action replies re-prompt — never error. There is no iteration cap.
