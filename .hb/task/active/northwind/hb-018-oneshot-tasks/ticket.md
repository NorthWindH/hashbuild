# Background

For a small task, the current create → plan-into-steps → plan-step → execute → review → archive pipeline is onerous: most small tasks end up planned into exactly one step anyway, so the task-level planning pass is pure overhead. We want a fast path — a "oneshot" task — that skips straight from ticket to a single step and guides the user through planning, execution, and review in one continuous flow, while still allowing the user to bail out at any checkpoint and fall back to the normal per-task workflow.

This requires two things: (1) a lighter-weight naming scheme so oneshot tasks don't need a hand-picked `hb-NNN` number, and (2) a guided subflow that walks create → plan → execute → review → archive as one loop with confirmation checkpoints.

**Naming/numbering.** Fully-qualified task names today are `author/hb-NNN-flavor`, numbered by convention, not by any sequence the SDK tracks. For oneshot tasks we want the SDK to own numbering via named, collision-safe sequences:

- Rejected: a random unique slug (e.g. `quick-fy6543g`) — ids become unreadable/hard to follow.
- Rejected: a timestamp (e.g. `quick-2026-07-08-12-56-23-0400`) — ids become long, and timezone choice is awkward (UTC avoids TZ bugs but makes the id hard to read at a glance).
- Rejected: a single global `.json` counter at `.hb/` root tracking `quick-0, quick-1, ...` — collides when multiple authors create oneshot tasks and commit concurrently.
- Rejected: one sequence per author with the prefix baked into the name (e.g. `quick-northwind-123`) — works but stutters the author name into the id (`northwind/quick-northwind-123`).
- **Chosen approach:** the SDK tracks named "prefix sequences," each scoped to either one author or the whole repo. Every author automatically gets a default per-author sequence (prefix `oneshot`). Users can also define additional named sequences (their own prefix, their own scope) for cases beyond the default oneshot flow.

**Naming amendment.** "Quick" was rejected as a name for this concept — it implies speed, when the point is skipping the task/step split. The concept and its CLI flag are named **oneshot** (`--oneshot`) throughout.

# Goal

Let a user create, plan, execute, and review a small task in one guided pass via `--oneshot`, with SDK-managed collision-safe sequence numbering, without adding overhead to the existing multi-step task workflow.

---

# Acceptance Criteria

## A. Prefix sequences (SDK-level numbering)

1. The SDK supports named "prefix sequences" that hand out the next integer id for a given prefix and increment atomically, safe under concurrent authors committing simultaneously.
2. Every author automatically has a default sequence with prefix `oneshot`, scoped to that author (no setup required to use `--oneshot`).
3. Users can define additional named sequences beyond the default, each with:
    1. its own prefix string
    2. a scope of either `author` (isolated to one author) or `repo` (shared across all authors)
4. Collision rules the SDK enforces when creating a new named sequence:
    1. **author-scope**: rejected if the same author already has another sequence (any scope) with the same prefix, or if a `repo`-scope sequence exists with that prefix.
    2. **repo-scope**: rejected if any other sequence, at either scope and for any author, already uses that prefix.

## B. `hb-sdk task create` — prefix-based invocation form

5. `hb-sdk task create` accepts a new invocation form in addition to the existing fully-qualified `author/hb-NNN-flavor` form:
    1. `author/prefix` — resolves `prefix` against that author's sequences (falling back to a `repo`-scope sequence of the same name if no author-scope match exists), consumes the next id from it, and increments the sequence. No number or flavor may be embedded in this form.
    2. `author` alone (no `/prefix`) — allowed **only** when `--oneshot` is also passed; resolves to that author's default `oneshot` sequence.
6. `--number <n>`: supplies the task number explicitly instead of consuming one from the resolved sequence.
    1. Errors if the positional argument already embedded a number (i.e. the fully-qualified `author/hb-NNN-flavor` form was used).
    2. If omitted, the SDK consumes the next id from the resolved prefix sequence; errors if the sequence doesn't exist.
7. `--flavor <slug>`: supplies the flavor slug explicitly.
    1. Errors if the positional argument already embedded a flavor (i.e. the fully-qualified form was used).
8. `--oneshot`: marks this as a oneshot-mode task creation.
    1. Defaults the resolved prefix to `oneshot` when no explicit prefix was given in the positional argument.
    2. Triggers the oneshot guided subflow (Section C) at the skill level, not just the SDK create call.

## C. Oneshot guided subflow

9. `--oneshot` on `hb-task-create` (and its equivalent surfaced through `hb-flow`) runs a new, dedicated subflow — documented as its own reference file, the same way `breakdown-subflow.md` and `interactive-ticket-subflow.md` are — distinct from the normal single-shot task-create flow, since it spans task creation through archival in one loop.
10. The subflow proceeds through these checkpoints, each an explicit stop-or-continue prompt to the user:
    1. Create the task as usual (interactive or non-interactive ticket creation).
    2. Present the created ticket, take any requested updates, confirm.
    3. Prompt: continue to planning, or stop here (task remains a normal task, resumable later via `/clear` + `/hb-flow`).
    4. If continuing: evaluate whether the ticket looks like it fits in one step, using existing step-sizing guidance.
        1. If it looks too big for one step: warn the user and require an explicit "continue anyway" before proceeding; otherwise direct them to stop and run normal `hb-task-plan` instead.
    5. If continuing: create exactly one step, seeding the step's ticket from the task's own ticket content.
    6. Plan that step.
    7. Present the plan, take any requested updates, loop until confirmed.
    8. Prompt: continue to execution, or stop here (resumable later via the normal `hb-task-step-execute` flow).
    9. If continuing: execute the step.
    10. After execution: gather review items (via `TODO REVIEW` comments or natural-language description), addressing each, looping until the user signals review is finished.
    11. Prompt: archive the task, or leave it as-is (still resumable via the normal per-task actions: add a step, more review, archive later, etc).
11. Stopping at any checkpoint leaves the task in a valid state consumable by the existing (non-oneshot) `hb-task-*` skills — the subflow does not leave partial/inconsistent state behind.

## D. Prefix management skills

12. New skills expose the prefix-sequence functionality from Section A, following the same thin-wrapper convention as other `hb-*` skills: each skill parses its own args and hands execution off to a corresponding `hb-sdk prefix` subcommand. Whether args are passed through verbatim or need some reshaping is left as an implementation decision.
13. `hb-prefix-create <scope> <name>`:
    1. `scope` is `author` or `repo`.
    2. When `scope` is `author`, `name` must be of the form `author/prefix` (`prefix` following the standard prefix-name rules).
    3. When `scope` is `repo`, `name` must be just `prefix` (same prefix-name rules, no author segment).
    4. `--next-value <n>`: sets the initial next value to hand out; defaults to `0` when omitted.
    5. Creation is handed off to `hb-sdk`, which enforces the collision rules from AC 4.
14. `hb-prefix-list`:
    1. Prints prefix names only by default.
    2. `--long`: also prints each prefix's attributes (e.g. next value).
    3. `--scope <author|repo>`: filters to prefixes of the given scope.
    4. `--author <name>`: filters to prefixes belonging to the given author; implies `scope=author`; errors if combined with `--scope repo`.
    5. `--prefix <name>`: filters to one exact prefix.
    6. `--format <md|json>`: selects markdown or JSON output.
15. `hb-prefix-drop <scope> <name>`: drops an existing prefix; takes the same positional args as `hb-prefix-create`.
16. `hb-prefix-update <scope> <name>`: updates an existing prefix; takes the same positional args as `hb-prefix-create`, plus `--next-value <n>` to set the next value.

---

# Out of scope

- Renaming or otherwise migrating existing `hb-NNN`-numbered tasks onto the new sequence mechanism.
- A UI/command for listing, editing, or deleting prefix sequences — only creation and consumption are covered here.
