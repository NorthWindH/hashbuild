> **Subflow — Other action.** Invoked only via `ticket-loop-subflow.md`'s
> Action Registry (§B), as the fallback for a confident zero-match against
> every other registered action. Attempts the user's request as asked,
> including tool calls — the harness's `allowed-tools` and any live
> permission prompt decide feasibility, not this subflow.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out); mutated only
  when §B edits an existing entry's `content` or `id_or_summary`, on explicit
  request. Unmutated when the request needs no ticket-data change (e.g. a
  lookup).
- (implicit) the triggering utterance — already visible in the same
  conversation this subflow executes in, matching none of the six other
  registered actions.
- (implicit) whatever tools the harness's `allowed-tools` and live permission
  prompts make available. This subflow neither expands nor restricts that
  set.

#### A. Establish request

1. Treat the triggering utterance itself as the candidate request,
   `$OTHER_REQUEST`.
2. It already names a specific operation on `$TICKET_CONTEXT` data, such as
   reformatting content → skip to §B.
3. It's too vague, such as "something else" → ask "What would you like to
   do?" and capture the reply as `$OTHER_REQUEST`.
4. Repeat step 3 until specific, or the user aborts → return outcome `"Other:
   no action taken."` (no mutation).

#### B. Perform

1. If `$OTHER_REQUEST` names a target entry, resolve it the same way as
   `set-active-ticket-subflow.md` §A step 3 — never guess on ambiguous or
   zero matches.
2. Attempt `$OTHER_REQUEST` as asked, tool calls included. This subflow makes
   no in-scope/out-of-scope judgment of its own — whether a given tool call
   proceeds is decided entirely by the harness's `allowed-tools` and any live
   permission prompt.
3. Attempt succeeds → mutate only what the request specifies (or nothing, for
   a pure lookup). Continue to §C.
4. Attempt is blocked by the harness, or otherwise fails → no mutation.
   Continue to §C with that outcome to report.

#### C. Compose outcome

- Succeeded in §B.3 → outcome naming what changed (or what was found, for a
  lookup).
- Blocked/failed in §B.4 → outcome naming what happened, briefly.
- Aborted in §A.4 → `"Other: no action taken."`
- Return to `ticket-loop-subflow.md` §E.

**Failure/degradation contract:** every path — abort, blocked, failed,
handled — returns a composed outcome string. A blocked tool call is always
reported, never silently dropped or retried around.
