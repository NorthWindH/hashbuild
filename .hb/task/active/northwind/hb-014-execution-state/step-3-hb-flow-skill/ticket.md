# Background

The previous two steps gave `hb-sdk` a persisted last-executed-action record and a shared next-action derivation module (`hb_sdk/next_action.py`, exposed via `hb-sdk state next-action`). Task ticket AC 4 requires a new skill that surfaces this to the user conversationally and lets them navigate by intent, not just by running the exact recommended command. No such skill exists today — `hb-status` reports state but is read-only and does not drive the user through a decision.

`hb-flow` is meant to be the first thing a user runs in a fresh session — either a just-started session, or immediately after `/clear`. It reports where things left off, asks in plain language what to do next, resolves that to a specific `hb-*` invocation, confirms it with the user, and — once confirmed — carries it out directly in that same session by following the target skill's own steps.

---

# Goal

Add `./skills/hb-flow.md`: on invocation it reports where the active task/step left off and the recommended next action (per AC 3's rules, via `hb-sdk state next-action`), prompts the user for what to do next with example phrasings, interprets the reply and resolves it to a specific `hb-*` invocation — including calls-to-action that are *not* the currently recommended one — confirms the resolved invocation with the user, and on confirmation carries it out directly by following the target skill's own steps in the same session.

---

# Acceptance Criteria

1. `./skills/hb-flow.md` is added following the structure/conventions of existing skill files (frontmatter with `name`, `argument-hint`, `description`, `allowed-tools`; a Help check step; Reference Files section).
2. On invocation with no arguments, the skill:
    1. Calls `hb-sdk state next-action --format json` (or `md`) to obtain the current stage, message, and any choices, and `hb-sdk state show` for the last-recorded action — it does not re-implement task/step traversal, ticket/plan/execution/review file-presence checks, or status logic inline (satisfies AC 4.3 by construction).
    2. Reports to the user, in plain language, where the active task/step left off (the last-executed action, if a record exists) and what the recommended next call-to-action is.
    3. Prompts the user, in natural language, for what they'd like to do next, giving example phrasings drawn from the mapping table in AC 3.
3. The skill accepts natural-language input describing what the user wants to do next (e.g. "move on to the next step", "archive this task", "let's review", "update the plan", "go back and re-plan step 2") and maps it to the corresponding `hb-*` skill invocation, per a documented mapping table in the skill file covering at least: plan task (`hb-task-plan`), add step (`hb-task-step-add`), plan step (`hb-task-step-plan`), execute step (`hb-task-step-execute`), start/continue review (`hb-task-step-review-init`/`hb-task-step-review-address`), archive task (`hb-task-archive`), unarchive task (`hb-task-unarchive`).
4. The mapping in AC 3 works from **any** valid current state, not only the state's currently-recommended action — e.g. if the recommended action is "execute step 2" but the user says "archive this task instead," the skill still resolves the archive call-to-action (subject to whatever confirmation `hb-task-archive` itself performs when archiving would skip unexecuted steps, per AC 8 — `hb-flow` does not duplicate that check itself).
5. When the user's input is ambiguous or does not match any known call-to-action, the skill asks a clarifying question rather than guessing or failing silently.
6. When multiple active tasks exist, the skill reports next-action for each (or asks the user which task, if that's clearer) rather than silently picking one — consistent with how `hb-sdk summarize` already lists all active tasks.
7. Before carrying out any resolved call-to-action, the skill states the exact invocation it resolved to (skill + target task/step) and asks the user to confirm it:
    1. If the user confirms, the skill carries out that invocation directly, in the same session, by following the target `hb-*` skill's own steps exactly as written — it delegates the actual work (creating steps, planning, executing, reviewing, archiving) to the existing corresponding `hb-*` skill's instructions rather than duplicating them inline (`hb-flow` is a router/presenter, not a reimplementation).
    2. If the user does not confirm (declines, or asks for something different), the skill asks what to change and re-resolves per AC 3 — it never carries out an invocation that hasn't been confirmed.
8. `./skills/hb-task-archive.md` gains a confirmation step: before archiving, it checks the target task's unexecuted/unreviewed steps (via `hb-sdk summarize --format json`) and, if any exist, lists them and asks the user to confirm before proceeding. This check lives in `hb-task-archive` itself (not `hb-flow`), so running `/hb-task-archive` directly gets the same protection as archiving via `hb-flow`.

---

# Out of scope

- Any change to the behavior of the skills `hb-flow` dispatches to, other than `hb-task-archive`'s new unexecuted-step confirmation (AC 8) — `hb-task-plan`, `hb-task-step-plan`, `hb-task-step-execute`, etc. are invoked as-is; `hb-task-archive`'s existing archive/move logic is otherwise unchanged.
- Further `hb-sdk` changes — AC 8's check is implemented as a new step in `hb-task-archive.md` using the existing `hb-sdk summarize` output; no new `hb-sdk` command is needed. `hb-flow` itself only consumes the `hb-sdk state`/`summarize` surface delivered in the prior two steps.
- Updating `hb-init`'s "what to do next" prompt to mention `hb-flow` (nice-to-have, not required by any AC) — may be addressed later if desired.
- Updating `references/README.md` to document `hb-flow` (nice-to-have, not required by any AC) — may be addressed later if desired.
