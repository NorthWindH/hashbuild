> **Subflow — Push ticket(s) action.** Invoked only via
> `ticket-loop-subflow.md`'s Action Registry (§B). Sends one, several named, or
> all in-context tickets to Jira, one at a time, reusing the pre-restructuring
> push procedure unchanged in substance. For a bulk push, offers to
> auto-skip unchanged/Done tickets first (§A.1), then moves through the rest
> automatically, presenting each ticket before pushing it (§C) — no
> per-ticket "continue?" prompt. Never adds, removes, or reactivates a
> `$TICKET_CONTEXT` entry — a pushed ticket stays in context.

**Caller contract.** Before invoking this subflow, the caller must have resolved:

- `$TICKET_CONTEXT` — mutable list of ticket entries (in/out); mutated only via
  an additive, optional `pushResult` field
- (implicit) the user's triggering utterance — already visible in the same
  conversation this subflow executes in; not a formal parameter.

#### A. Resolve target set

1. `$TICKET_CONTEXT` empty → tell the user "No tickets in context to push." →
   return outcome `"Push: no tickets in context."` (no calls, no mutation).
2. Utterance requests the whole context ("push all," "push everything," or an
   equivalent) → `$TARGETS` = every entry in `$TICKET_CONTEXT`, in order.
   Continue to §A.1.
3. Utterance names one or more tickets (by id/summary):
   1. Split the utterance into its distinct named references (one or several
      — e.g. "PROJ-123 and PROJ-124" is two).
   2. For each named reference, semantic-match against every entry's
      `id_or_summary` — same posture as `clear-ticket-subflow.md` §A step 4 /
      `breakdown-ticket-subflow.md` §A / `load-ticket-subflow.md` §A ("never
      guess"):
      - Zero matches → ask the user to clarify that one reference; treat the
        clarifying reply as the name and re-match it.
      - Multiple matches → present a numbered list of the matching entries'
        `id_or_summary`s, scoped to that one reference; the user picks one —
        never auto-select.
      - One match → include it in the resolving set.
   3. `$TARGETS` = the deduplicated union of every entry resolved across all
      named references. Continue to §A.1.
4. Utterance is a bare push request ("push this," "push it," "push this
   ticket," with no name and no "all"):
   1. Exactly one entry in `$TICKET_CONTEXT` → `$TARGETS` = `[that entry]`.
   2. Else exactly one entry has `active: true` → `$TARGETS` = `[that
      entry]`.
   3. Else → ask the user "Which ticket(s) would you like to push?" and
      re-run this §A against the reply.
   Continue to §A.1 once `$TARGETS` is set.

#### A.1 Skip offer (bulk only)

Runs once `$TARGETS` is set, before any push begins. Skipped entirely when
`|$TARGETS|` = 1 — a single explicitly-requested target is never auto-skipped.

1. Identify skip candidates within `$TARGETS`. Set `$CANDIDATES` = every
   `$TARGETS` entry matching either:
   - **Unchanged** — `$TARGET.syncedContent` is set and equals
     `$TARGET.content` (no edits since the ticket was last loaded from or
     pushed to Jira).
   - **Done** — `$TARGET.jiraStatusCategory` = `"done"` (only ever set on
     Jira-sourced entries — see `load-ticket-subflow.md` §E and §B step 3
     below; file/web-sourced or not-yet-pushed entries never match this
     criterion).
2. `$CANDIDATES` empty → continue to §C unchanged, no offer made.
3. `$CANDIDATES` non-empty → present them (label + reason: unchanged / done)
   and ask: "Skip these N automatically?"
   - **Yes** → remove `$CANDIDATES` from `$TARGETS` (in place); they are not
     pushed this run, gain no `pushResult`, and stay in `$TICKET_CONTEXT`
     exactly as they were.
   - **No** → leave `$TARGETS` as resolved; every entry, candidates included,
     proceeds through §C.
4. Continue to §C with the (possibly reduced) `$TARGETS`.

#### B. Per-ticket push procedure

Invoked once per `$TARGET` by §C. Returns `{ status: "pushed" | "copy-paste",
issueKey?, browseUrl?, ideaLinked? }`. Never touches `$TICKET_CONTEXT`
membership or `active`.

1. **Detect Jira MCP & collect NL description:**
   - Look for a connected MCP tool capable of **creating a Jira issue**.
     Discover it by capability — check available tools for one that creates
     Jira issues. On Claude Code with the Atlassian Rovo MCP connected, that
     tool is `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`; the exact name
     may differ on other platforms.
   - If **no such tool is found**: set `$JIRA` = `unavailable` and skip to
     step 5, additionally telling the user that no Jira-capable MCP was
     detected and they can connect one (e.g. the Atlassian Rovo MCP on
     Claude Code) and re-run if they want to push. This is the graceful
     path — absence of the MCP must never raise an error.
   - If a tool is found: ask the user to describe the Jira target in natural
     language for **this** ticket, naming it by `$TARGET.id_or_summary` so a
     multi-target run stays distinguishable, and tell them the resolved
     details will be shown for confirmation before anything is created or
     updated. Examples: "create a Task in the MOBILE project for the auth
     refactor", "update MOBILE-412", "update the login epic in BACKEND".
     - "no" → set `$JIRA` = `declined`, go to step 5.
     - Otherwise: store the description as `$NL_DESC` and continue to step 2.
2. **NL resolution & confirmation loop.** Loop until the user accepts the
   resolved field set or aborts.

   **A. Parse `$NL_DESC`:**
   - Determine intent path: **create** (keywords: create, new, add, file a
     …) or **update** (update, edit, change, find, fix …).
   - Extract partial fields:
     - Issue key pattern `[A-Z]+-[0-9]+` → explicit `issueIdOrKey`
       candidate.
     - Project name or key fragment → `projectKey` candidate.
     - Issue type name (Story, Task, Bug, Epic …) → `issueTypeName`
       candidate.
     - Summary / title text → `summary` candidate.
     - Site name or URL → `cloudId` candidate.

   **B. Resolve `cloudId`:**
   - Call the MCP's list-accessible-sites tool. (Atlassian Rovo example:
     `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources`.)
   - Exactly one site → use it. Multiple → prompt user to choose.

   **C. Resolve remaining fields by path:**

   *Create path:*
   - **`projectKey`:** If a project candidate was extracted, filter
     `getVisibleJiraProjects` by name match. (Atlassian Rovo example:
     `mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects`.) Unambiguous →
     use it. Multiple matches → present numbered list, user picks. No match
     or not mentioned → prompt the user to choose from the full project
     list.
   - **`issueTypeName`:** If a type candidate was extracted, match against
     `getJiraProjectIssueTypesMetadata` for the resolved project. (Atlassian
     Rovo example: `mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata`.)
     Unambiguous → use it. Multiple or unclear → present list. Not mentioned
     → propose "Task" and confirm.
   - **`summary`:** If clearly stated in `$NL_DESC` → extract and propose
     for confirmation. Otherwise → propose a concise title and confirm.
     Never silently guessed (unresolved → prompt explicitly).

   *Update path:*
   - **Explicit key** (`[A-Z]+-[0-9]+` found in NL): call the MCP's
     get-issue tool to retrieve the issue and confirm its title and status.
     (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__getJiraIssue`.)
     Resolved: `issueIdOrKey` = extracted key. Also capture the retrieved
     issue's type name (`fields.issuetype.name`) as `issueTypeName`.
   - **No explicit key**: derive a JQL query from the NL description (e.g.
     `project = "MOBILE" AND text ~ "auth refactor" ORDER BY updated DESC`).
     Call the MCP's JQL search tool. (Atlassian Rovo example:
     `mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql`.) 1 match →
     present key + title for confirmation. Multiple matches → numbered
     list, user picks — **never auto-select**. 0 matches → tell the user,
     prompt for a key or a more specific description. Also capture the
     confirmed match's issue type name as `issueTypeName`.

   Failure / degradation: if any query tool errors → surface the error
   verbatim and prompt the user to supply that field directly. Never
   dead-end.

   **D. Present resolved field set:**
   - Create: `Resolved: CREATE in <projectKey> as <issueTypeName> —
     '<summary>'`
   - Update: `Resolved: UPDATE <issueKey> — '<issue title>'`

   Ask: "Does this look right?"

   **E. User response:**
   - **Accept** → set `$JIRA_FIELDS` = resolved set, set `$JIRA` = `"create"`
     or `"update"`, break loop.
   - **Refine description** → update `$NL_DESC`, return to A.
   - **Supply exact values** → accept the values the user provides as
     `$JIRA_FIELDS`, present for final confirmation, on accept break loop.
   - **Abort** → set `$JIRA` = `"declined"`, skip to step 5.
3. **Push to Jira.** Only when `$JIRA` ∈ {`create`, `update`}. Uses
   `$JIRA_FIELDS` set by step 2 — no field resolution in this step.
   - **If `$JIRA_FIELDS.path` = `create`:**
     - Call the MCP's create-issue tool with `cloudId`, `projectKey`,
       `issueTypeName`, `summary`, `description` = `$TARGET.content`
       (in place of `$WRITTEN_TICKET`), and `contentFormat: "markdown"`.
       (Atlassian Rovo example: `mcp__claude_ai_Atlassian_Rovo__createJiraIssue`.)
   - **If `$JIRA_FIELDS.path` = `update`:**
     - Call the MCP's edit-issue tool with `cloudId`, `issueIdOrKey`,
       `fields: { description: $TARGET.content }`, and `contentFormat:
       "markdown"`. (Atlassian Rovo example:
       `mcp__claude_ai_Atlassian_Rovo__editJiraIssue`.)
   - **On success:** set `$JIRA` = `pushed` and report the resulting issue
     **key and browse URL** to the user. Also store the issue key as
     `$JIRA_FIELDS.issueKey` — for the create path this is the key
     `createJiraIssue` returned; for the update path this is simply
     `$JIRA_FIELDS.issueIdOrKey` (no new call, just an alias so step 4 has
     one uniform field to read regardless of path). Additionally set
     `$TARGET.syncedContent = $TARGET.content` and
     `$TARGET.jiraStatusCategory` = the pushed issue's returned
     `fields.status.statusCategory.key` — both additive, optional fields
     (per `ticket-loop-subflow.md` §A's extensibility note) that let a later
     bulk push in the same session recognize this ticket as unchanged/done
     via §A.1, without re-querying Jira.
   - **On failure** (auth, permission, invalid field, etc.): surface the
     error verbatim, then **fall through to step 5** so the user still gets
     the copy-paste ticket — this procedure never dead-ends.
4. **Offer Jira Idea link (Epic only).**
   - **Guard**: only run when `$JIRA` = `pushed` **and**
     `$JIRA_FIELDS.issueTypeName` exactly equals `"Epic"`. Otherwise: no
     prompt, no step — proceed directly to step 6.
   - **Offer**: ask the user: "This is a Jira Epic. Would you like to link
     it to an existing Jira Idea?"
     - **No** → skip linking entirely; proceed to step 6 — the
       already-pushed ticket is unaffected.
     - **Yes** → prompt: "Provide the Idea's issue key (e.g. `PROJ-123`) or
       its bare number (e.g. `123`)." Capture as `$IDEA_REF`.
   - **Resolve `$IDEA_REF` to a full Jira issue key**:
     - Matches `[A-Z]+-[0-9]+` → use directly as the Idea key.
     - Matches `^[0-9]+$` (bare number only) → ask the user which project
       the Idea belongs to (e.g. "Which project is Idea #`<n>` in?"); never
       silently guessed — the Idea can live in a different project than the
       Epic. Combine as `<PROJECT>-<n>`.
     - Matches neither → tell the user the format wasn't recognized;
       re-prompt for a valid key or bare number, or let the user abort
       (treated as declining — same as "No" above).
   - **Call `createIssueLink`** with: `cloudId` = `$JIRA_FIELDS.cloudId`,
     `type` = `"Polaris work item link"`, `inwardIssue` =
     `$JIRA_FIELDS.issueKey` (the Epic), `outwardIssue` = the resolved Idea
     key. This direction is verified correct — never reversed.
   - **On success**: confirm to the user that the Epic is now linked to the
     Idea, naming both keys, and set `$IDEA_LINKED` = the Idea key.
   - **Failure / degradation contract**: if `createIssueLink` errors
     (invalid Idea reference, permission, API error) → surface the error
     verbatim; explicitly state that the already-created/updated ticket/
     issue is unaffected — no retry, no rollback. Proceed to step 5.
5. **Emit ticket fallback.** Reached when `$JIRA` ∈ {`unavailable`,
   `declined`} or after a step 3 failure. **Skipped** when `$JIRA` =
   `pushed`.
   - Print `$TARGET.content` in full inside a fenced block so the user can
     copy-paste it, naming the ticket by `$TARGET.id_or_summary`.
   - When `$JIRA` = `unavailable`, additionally state that no Jira MCP was
     available, so this ticket is emitted for copy-paste.
   - No `.hb/` write — this action never touches `.hb/`.
6. **Compose result.**
   - `$JIRA` = `pushed` → `{status: "pushed", issueKey: $JIRA_FIELDS.issueKey,
     browseUrl, ideaLinked: $IDEA_LINKED?}`.
   - Otherwise → `{status: "copy-paste"}`.
   - Attach the composed object as `$TARGET.pushResult` (additive, optional
     — `ticket-loop-subflow.md` §A's extensibility note covers this).
   - Return to §C.

#### C. Multi-target loop

1. `|$TARGETS|` > 1 → announce the set (every target's `id_or_summary`)
   before starting. Else skip the announcement.
2. For each `$TARGET`, in order, never concurrent:
   1. `|$TARGETS|` > 1 and this is not the first target processed →
      present the upcoming ticket by its `id_or_summary` (e.g. "Next:
      <id_or_summary>") before running §B on it.
   2. Run §B; append `{label: $TARGET.id_or_summary, result}` to
      `$PUSH_RESULTS`.
   3. Move automatically to the next target — no confirmation prompt. A
      per-ticket decline inside §B (e.g. declining to describe a Jira
      target, or aborting the field-confirmation loop) only affects that
      one ticket, falling through to its own copy-paste fallback; it never
      halts the loop.
3. Continue to §D once every target has been processed.

#### D. Compose return outcome

1. Per entry in `$PUSH_RESULTS`:
   - `status: "pushed"` → `"<label>: pushed as <issueKey> (<browseUrl>)"`,
     plus `", linked to Idea <ideaLinked>"` when set.
   - `status: "copy-paste"` → `"<label>: emitted for copy-paste (no Jira
     push)"`.
2. Present the per-target breakdown to the user.
3. Return `"Push: N of M ticket(s) processed (<breakdown>)."` (N =
   `|$PUSH_RESULTS|`, M = `|$TARGETS|`) for `ticket-loop-subflow.md` §E to
   log.

**Failure/degradation contract:** §A's empty-context and default-ambiguous
cases return without invoking §B — no calls, no mutation. §A.1's skip offer
only ever removes entries from `$TARGETS` for this run — a skipped entry is
untouched in `$TICKET_CONTEXT` and gains no `pushResult`. Every §B branch
mirrors the recovered pre-restructuring flow's contract exactly: no MCP,
decline, query error, push error, and idea-link error all fall through
without dead-ending, and §C always proceeds to the next target regardless of
how the current one resolved. A target only gains `pushResult` once its own
§B run fully completes — no partial or malformed `pushResult` is ever
attached.
