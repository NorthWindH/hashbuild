# Background

In hb-status work summary rows, each active step item currently appends the task tag at the end, e.g. `- Needs review: step-0-interactive-ticket-subflow (hb-004)`. The tag should be repositioned to immediately follow the status label, before the step name, so task context is visible first: `- Needs review: (hb-004) step-0-interactive-ticket-subflow`.

---

# Acceptance Criteria

1. In all hb-status work summary rows, the task tag in parentheses appears before the step name, not after.
    1. Before: `- Needs review: step-0-interactive-ticket-subflow (hb-004)`
    2. After: `- Needs review: (hb-004) step-0-interactive-ticket-subflow`
2. The change applies to every status label variant (e.g. Needs review, In progress, Blocked, etc.) that includes a task tag.
3. All other hb-status output is unchanged — counts, section headings, next action, and any rows without a tag are unaffected.
