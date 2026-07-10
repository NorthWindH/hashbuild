> **Subflow — Load ticket action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Loads an *existing* ticket
> from a file, a connected Jira MCP, or a fetchable URL and adds it to the
> loop's in-conversation context as the active entry. Never creates or
> updates anything outside `$TICKET_CONTEXT`.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out)
- `$TICKET_SEQ` — mutable integer counter (in/out)
- (implicit) the user's triggering utterance — already visible in the same
  conversation this subflow executes in; not a formal parameter.

#### A. Classify source

Pattern-match the user's triggering utterance into `$SOURCE ∈ {file, jira, web}`:

- A file path or glob (e.g. `/tmp/draft.md`, `drafts/*.md`) → `file`.
- An explicit Jira issue key (`[A-Z]+-[0-9]+`) or "Jira"/issue-description
  phrasing (e.g. "load the login epic from MOBILE") → `jira`.
- A `https?://` URL → `web`.

**Never guess.** If no pattern matches, or if the utterance matches two
patterns at once (e.g. a URL that also looks like a file path), ask the user
which source they mean and wait for their answer before continuing.

#### B. File source

1. Resolve the named path or glob. Zero matches → tell the user, return to
   the loop menu (no entry added, `$TICKET_SEQ` unchanged). Multiple matches
   → present a numbered list of matches; the user picks one — never
   auto-select. One match → use it.
2. Read the resolved file. Read failure → surface the error verbatim, return
   to the loop menu (no entry added).
3. Set `$RAW_CONTENT` = the file's full text. Continue to §E.

#### C. Jira source

Mirrors the update-path resolution algorithm from the pre-existing Jira push
flow — read-only, no create branch:

1. Capability check: confirm a connected MCP tool that can read a Jira issue
   by key or by JQL search is available (e.g. `getJiraIssue` /
   `searchJiraIssuesUsingJql`, with `getAccessibleAtlassianResources` for
   site/`cloudId` resolution). None available → tell the user, suggest
   connecting one, return to the loop menu (no entry added).
2. Explicit key present in the utterance → call the get-issue tool directly
   with that key.
3. No explicit key → derive a JQL query from the description, then call the
   JQL search tool.
   - 0 matches → tell the user, ask for a key or a more specific description;
     if still unresolved, return to the loop menu (no entry added).
   - 1 match → use it.
   - Multiple matches → present a numbered list of key + title; the user
     picks one — never auto-select.
4. Any tool error → surface the error verbatim, return to the loop menu (no
   entry added).
5. Set `$RAW_CONTENT` = the resolved issue's `description` field (fallback:
   summary/title if the description is empty). Capture `$ISSUE_KEY` and
   `$ISSUE_TITLE`. Continue to §E.

#### D. Web source

1. Capability check: confirm a URL-fetching tool (`WebFetch`) is available in
   this session. Not available → tell the user, return to the loop menu (no
   entry added).
2. Fetch the named URL. Failure (network, HTTP, or unparseable response) →
   surface the error verbatim, return to the loop menu (no entry added).
3. Set `$RAW_CONTENT` = the fetched page's extracted main text. Continue to
   §E.

#### E. Finalize

Shared by all three sources:

1. Transform `$RAW_CONTENT` by applying `interactive-ticket-subflow.md` §C's
   Rule 1 (near-perfect match → transcribe) and Rule 2 (freeform → derive) as
   written there.
2. Increment `$TICKET_SEQ`. Set `$TARGET_PATH` =
   `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` — a fresh, non-colliding
   scratch folder for this call.
3. Write step: before writing, if `$TARGET_PATH/ticket.md` already exists,
   delete it. Write the transformed content to `$TARGET_PATH/ticket.md` using
   `interactive-ticket-subflow.md` §D's file structure.
4. Read back `$TARGET_PATH/ticket.md`'s full text as `$content`.
5. Derive `$id_or_summary`:
   - Jira source → `"$ISSUE_KEY: $ISSUE_TITLE"`.
   - File/web source → the ticket's Background section, its first clause or
     sentence, truncated to roughly 8 words.
6. Unset `active` on every existing `$TICKET_CONTEXT` entry, then append
   `{ id_or_summary: $id_or_summary, content: $content, active: true,
   source: { type: $SOURCE, ref: <path | issue key | url> } }`. `source` is
   an additive, optional field per `ticket-loop-subflow.md` §A's
   extensibility note — Describe and Exit ignore it safely.
7. Return to the caller with outcome string `"Loaded ticket: $id_or_summary
   (from $SOURCE)"`.

**Failure/degradation contract:** every §B/§C/§D failure branch returns to
the loop menu without mutating `$TICKET_CONTEXT` or `$TICKET_SEQ` and without
raising an error — the returned outcome string instead describes the failure
(e.g. `"Load ticket failed: <reason>"`) so `ticket-loop-subflow.md` §E still
logs the attempt. No partial or malformed entry is ever appended.
