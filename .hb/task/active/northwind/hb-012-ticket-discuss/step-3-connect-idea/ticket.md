# Background

- `hb-ticket-discuss` creates or updates a standalone ticket and can push it to a connected Jira. When the ticket being created/updated is an **Epic**, we additionally need the ability to link it to an existing Jira **Idea**, since Epics are expected to trace back to their originating Idea.
- Linking uses Jira's `createIssueLink` with type `"Polaris work item link"`. **Direction matters**: the Epic must be passed as `inwardIssue` and the Idea as `outwardIssue`. A prior session verified this directly:

  | inwardIssue | outwardIssue | type | result |
  |---|---|---|---|
  | CSS-2649 (Epic) | EO-32 (Idea) | Polaris work item link | correct |
  | EO-31 (Idea) | CSS-2664 (Epic) | Polaris work item link | wrong (reversed) |

---

# Acceptance Criteria

1. When the ticket being created or updated via `hb-ticket-discuss` is an Epic, the user is offered the ability to link it to a Jira Idea.
    1. Whether this is implemented as an additional step appended after ticket create/update, or as an optional idea-id field collected during the information-collection stage, is a design decision for `plan.md` — either satisfies this criterion.
2. Idea linking is optional: skipping it still allows ticket creation/update to complete successfully.
3. A supplied idea reference resolves to a Jira issue key (accepting either a full key or a bare number, consistent with existing NL target resolution) before the link is attempted.
4. The link is created via `createIssueLink` with type `"Polaris work item link"`, the Epic as `inwardIssue` and the Idea as `outwardIssue` — matching the verified-correct direction above; the reversed pairing must never occur.
5. If the ticket being created/updated is not an Epic, no idea-linking prompt/step occurs.
6. If linking fails (invalid idea reference, API error), the failure is surfaced to the user and the already-created/updated ticket is not discarded or rolled back.

---

# Out of scope

- Creating a new Jira Idea when none exists — this step only links to an existing Idea.
- Linking issue types other than Epic to an Idea.
- Unlinking or editing an existing Epic↔Idea link.
