> **Subflow — breakdown.** Shared by `hb-task-plan` and (in a later step)
> `hb-ticket-discuss`'s Breakdown ticket action. Drafts child ticket files at
> temp paths for review; it does not decide where or how a confirmed child
> becomes durable — that is the calling skill's responsibility.

**Caller contract.** Before injecting this subflow, the calling skill must have resolved:

- `$PARENT_LABEL` — a short identifying label for the parent, used only in user-facing messages (e.g. the task name, or a ticket id/summary)
- `$PARENT_CRITERIA` — the parent's Acceptance Criteria section (numbered list), already extracted from its `ticket.md`
- `$CHILDREN` — a list of existing children, each with a label and its Acceptance Criteria section (or "no ticket" if it has none); may be empty
- `$MATERIALIZE_CHILD` — how the calling skill turns one confirmed child ticket (a drafted file at a temp path) into something durable (e.g. "invoke `hb-task-step-add --ticket <path> [--flavor <slug>]`" or "add it to the in-conversation ticket list as the active ticket"); the subflow calls back into this once per confirmed child and performs no persistence itself

#### A. Gap analysis

- extract each top-level condition from `$PARENT_CRITERIA`
- for each condition, check whether any `$CHILDREN` entry addresses it (fully or partially) via its Acceptance Criteria text
- if `$CHILDREN` is empty, every condition is a gap
- produce a gap report: list each uncovered condition, and note which children, if any, partially address it

#### B. No-gaps exit

- if Section A's gap report has zero entries: notify the user that all of `$PARENT_LABEL`'s acceptance criteria appear covered by existing children, and **stop** — return control to the caller; propose nothing

#### C. Propose-confirm loop

- present the Section A gap report together with a proposed high-level breakdown of the gaps into candidate children (grouped small-to-medium, sized against sibling children when available)
- ask the user to **confirm**, **request changes**, or **decline**
- on request-changes: revise the proposed breakdown and re-present
- on decline: **stop** — return control to the caller noting the decline (the caller decides the follow-up, e.g. asking "how would you like to proceed?")
- on confirm: proceed to Section D with the confirmed candidate list

#### D. Per-child create-confirm loop

For each confirmed candidate, in order:

1. **Draft**: write a temporary ticket file using [${CLAUDE_SKILL_DIR}/references/ticket-template.md](ticket-template.md) as the structural template:
   - **Background**: state which parent criteria this candidate closes and why
   - **Acceptance Criteria**: concrete, checkable conditions that close the identified gap(s)
   - **Out of scope**: anything left to sibling candidates
   - keep the draft small to medium (target less than 300 estimated lines of changes)
2. **Present**: show the draft to the user
3. **Resolve**: loop **confirm / request changes / skip** until resolved
   - on request-changes: revise the draft and re-present
   - on skip: record this candidate as skipped; move to the next candidate
   - on confirm: continue to step 4
4. **Materialize**: invoke `$MATERIALIZE_CHILD` with the temp path and collect its result (created path or error)

Repeat until no candidates remain.

**Failure/degradation contract:** empty `$CHILDREN` → Section A treats every parent condition as a gap (no error). User declines in Section C → clean stop, no drafts written, no materialization calls made. User skips a child in Section D → that child is neither drafted-and-abandoned in a durable location nor materialized; move on. Endless revision requests in either loop are supported (no iteration cap).

**Return value:** the list of materialized children (temp-draft path × which gap(s) it closes × the `$MATERIALIZE_CHILD` result), plus any skipped entries — for the caller's own reporting step.
