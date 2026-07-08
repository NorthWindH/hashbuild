# Background

The previous two steps gave `hb-sdk` a persisted last-executed-action record and a shared next-action derivation module (`hb_sdk/next_action.py`, exposed via `hb-sdk state next-action`). Task ticket AC 4 requires a new skill that surfaces this to the user conversationally and lets them navigate by intent, not just by running the exact recommended command. No such skill exists today — `hb-status` reports state but is read-only and does not drive the user through a decision.

---

# Goal

Add `./skills/hb-flow.md`: on invocation it reports where the active task/step left off and the recommended next action (per AC 3's rules, via `hb-sdk state next-action`), then interprets the user's natural-language response and dispatches to the matching `hb-*` skill/call-to-action — including calls-to-action that are *not* the currently recommended one.

---

# Acceptance Criteria

1. `./skills/hb-flow.md` is added following the structure/conventions of existing skill files (frontmatter with `name`, `argument-hint`, `description`, `allowed-tools`; a Help check step; Reference Files section).
2. On invocation with no arguments, the skill:
    1. Calls `hb-sdk state next-action --format json` (or `md`) to obtain the current stage, message, and any choices — it does not re-implement task/step traversal, ticket/plan/execution/review file-presence checks, or status logic inline (satisfies AC 4.3 by construction).
    2. Reports to the user, in plain language, where the active task/step left off (the last-executed action, if a record exists) and what the recommended next call-to-action is.
3. The skill accepts natural-language input describing what the user wants to do next (e.g. "move on to the next step", "archive this task", "let's review", "update the plan", "go back and re-plan step 2") and maps it to the corresponding `hb-*` skill invocation, per a documented mapping table in the skill file covering at least: plan task (`hb-task-plan`), add step (`hb-task-step-add`), plan step (`hb-task-step-plan`), execute step (`hb-task-step-execute`), start/continue review (`hb-task-step-review-init`/`hb-task-step-review-address`), archive task (`hb-task-archive`), unarchive task (`hb-task-unarchive`).
4. The mapping in AC 3 works from **any** valid current state, not only the state's currently-recommended action — e.g. if the recommended action is "execute step 2" but the user says "archive this task instead," the skill still resolves and offers/invokes the archive call-to-action (with a sanity check/confirmation if archiving would skip unexecuted steps, consistent with how `hb-task-archive` itself behaves).
5. When the user's input is ambiguous or does not match any known call-to-action, the skill asks a clarifying question rather than guessing or failing silently.
6. When multiple active tasks exist, the skill reports next-action for each (or asks the user which task, if that's clearer) rather than silently picking one — consistent with how `hb-sdk summarize` already lists all active tasks.
7. The skill delegates the actual work (creating steps, planning, executing, reviewing, archiving) to the existing corresponding `hb-*` skill rather than duplicating that skill's steps inline — `hb-flow` is a router/presenter, not a reimplementation.

---

# Out of scope

- Any change to the behavior of the skills `hb-flow` dispatches to (`hb-task-plan`, `hb-task-step-plan`, etc.) — they are invoked as-is.
- Further `hb-sdk` changes — `hb-flow` only consumes the `hb-sdk state`/`summarize` surface delivered in the prior two steps.
- Updating `hb-init`'s "what to do next" prompt to mention `hb-flow` (nice-to-have, not required by any AC) — may be addressed later if desired.
