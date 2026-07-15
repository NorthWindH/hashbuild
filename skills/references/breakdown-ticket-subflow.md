> **Subflow — Breakdown ticket action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Decomposes a ticket already
> held in `$TICKET_CONTEXT` into child tickets, reusing `breakdown-subflow.md`'s
> gap-analysis/propose-confirm/per-child create-confirm logic. Never edits
> `breakdown-subflow.md` itself.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- (implicit) the user's triggering utterance — already visible in the same
  conversation this subflow executes in; not a formal parameter.

#### A. Resolve target ticket

1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to break
   down." → return outcome `"Breakdown: no tickets in context."` (no subflow
   invocation, no mutation).
2. Utterance names a ticket → semantic-match against every entry's
   `id_or_summary`. Zero matches → ask which ticket to target; treat the
   clarifying reply as the name and re-match. Multiple matches → numbered
   list of `id_or_summary`s, user picks (never auto-select). One match → use
   it.
3. Utterance names no ticket → use the entry with `active: true`. If none is
   active → ask the user which ticket to target.
4. Set `$PARENT_LABEL` = target's `id_or_summary`. Extract `$PARENT_CRITERIA`
   = target's `content`'s `# Acceptance Criteria` section.

#### B. Supply + invoke

1. `$CHILDREN` = every `$TICKET_CONTEXT` entry (excluding the target itself)
   whose optional `parent` field equals `$PARENT_LABEL`, each mapped to
   `{label: entry.id_or_summary, criteria: entry.content's Acceptance
   Criteria section}`. May be empty.
2. `$MATERIALIZE_CHILD` = "follow §C below, once per confirmed child."
3. Follow [${CLAUDE_SKILL_DIR}/references/breakdown-subflow.md](breakdown-subflow.md)
   with `$PARENT_LABEL`, `$PARENT_CRITERIA`, `$CHILDREN`, `$MATERIALIZE_CHILD`
   as resolved above. Capture its return value (materialized list + skipped
   list, or an early-stop signal from its own §B/§C) for §D.

#### C. Materialize callback

Invoked by `breakdown-subflow.md` §D step 4, once per confirmed child, given
the temp path of that child's drafted+confirmed `ticket.md`:

1. Read `$TEMP_PATH/ticket.md`'s full text as `$content`.
2. Derive `$id_or_summary` from its Background section's first clause,
   truncated to roughly 8 words.
3. Unset `active` on every existing `$TICKET_CONTEXT` entry.
4. Append `{ id_or_summary: $id_or_summary, content: $content, active: true,
   parent: $PARENT_LABEL }`. `parent` is an additive, optional field per
   `ticket-loop-subflow.md` §A's extensibility note — Load/Describe/Exit
   ignore it safely.
5. Return `$id_or_summary` to `breakdown-subflow.md` §D step 4 as this
   materialize call's result.

#### D. Compose return outcome

Once `breakdown-subflow.md` itself returns control (no-gaps exit, decline, or
per-child loop exhausted):

- No-gaps exit → `"Breakdown '$PARENT_LABEL': no gaps found, nothing
  created."`
- Declined at propose-confirm → `"Breakdown '$PARENT_LABEL': declined,
  nothing created."`
- Otherwise → `"Breakdown '$PARENT_LABEL': created N child ticket(s):
  <label1>, <label2>, ...; M skipped."`, with N/labels/M read off
  `breakdown-subflow.md`'s own return value from §B step 3.

**Failure/degradation contract:** §A's empty-context and ambiguous-target
cases return without invoking `breakdown-subflow.md` at all (no mutation).
Every other failure/degradation mode is `breakdown-subflow.md`'s own
(no-gaps, decline, skip) — this subflow does not add a new one. No partial or
malformed entry is ever appended: §C only appends after a child is fully
confirmed by `breakdown-subflow.md`'s own resolve loop.
