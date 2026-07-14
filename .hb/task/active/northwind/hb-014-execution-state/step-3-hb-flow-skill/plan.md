# Step 3 Plan — `hb-flow` router/presenter skill

Today, after any `hb-*` skill finishes, the only way to find out what to do next is to run `/hb-status` (read-only, always shows the *recommended* action) or to already know the exact next command yourself — there is no conversational entry point that reports where a task/step left off and lets the user say, in plain language, what they actually want to do next (including something other than the recommended action, e.g. "archive this task instead" while the recommendation is "execute step 2"), then actually carry it out. This step adds that entry point: `./skills/hb-flow.md`, a new skill meant to be run as the *first* command in a fresh session (a just-started session, or immediately after `/clear`). It reports state (reusing `hb-sdk`, never re-deriving it), maps a natural-language reply to a specific `hb-*` invocation, confirms that invocation with the user, and — once confirmed — carries it out directly in the same session by following the target skill's own steps. It also closes a real gap surfaced while researching this step: `hb-task-archive` archives a task with zero regard for unexecuted/unreviewed steps, so this step adds that confirmation directly to `hb-task-archive` itself (not to `hb-flow`), so the protection applies whether a user runs `/hb-task-archive` directly or reaches it via `/hb-flow`. Scope boundary: `hb-flow` is new and additive; `hb-task-archive` gets exactly one new step (the confirmation) and is otherwise unchanged. The single externally observable effect once this lands: running `/hb-flow` reports where things left off, asks what to do (with examples), confirms the resolved command, and then runs it for you — for any valid action, not just the recommended one.

Source ticket: `./ticket.md` (revised — see the two corrections below). Builds on the **shipped** work from step-1 (`hb-sdk state record`) and step-2 (`hb-sdk state next-action`, `skills/scripts/hb_sdk/next_action.py`). This plan targets the code as it exists **now** (verified 2026-07-14).

> **Design decision — `hb-flow` confirms, then invokes, by following the target skill's own steps in place.** An earlier draft of this plan had `hb-flow` only *print* the resolved invocation, reasoning that every other skill's "Prompt user" step tells the user to `/clear` then run the next command themselves, and that auto-chaining would break that context-freshness discipline. That reasoning no longer holds: `hb-flow` is explicitly defined (ticket Background) as the *first* thing run in an already-fresh session, and it resolves to at most one downstream action per invocation — so having it carry out that one action in place is exactly as context-fresh as the user running it directly, while also matching the ticket's now-explicit AC 7 ("confirms... on confirmation carries it out directly... by following the target skill's own steps"). The mechanism (§2) is: after confirmation, Read the target skill's `.md` file at runtime with the `Read` tool (not a static `!`cat``, since the target is chosen dynamically from the user's reply, and `!`cat`` is resolved once at parse time — see §1) and execute its `## Steps` section (skipping its own Help check) with the already-resolved task/step ref, letting that skill's own Commit / Prompt user / Record execution state steps run exactly as written. This is what makes AC 7.1 ("delegates... rather than duplicating them inline") literal rather than aspirational.
>
> **Consequence — `hb-flow`'s `allowed-tools` must be the union of every skill it might invoke.** Because the harness gates tool calls by the *currently active* skill's frontmatter (there is no per-target-skill re-scoping when `hb-flow` inlines another skill's steps), `hb-flow.md`'s own `allowed-tools` has to cover the superset of all 8 dispatch targets' tools, not just `hb-sdk`/`Read`. Derived in §2 Step "Frontmatter": `Bash(*) Read Write Edit` (two of the eight targets — `hb-task-step-execute.md`, `hb-task-step-review-address.md` — already carry unrestricted `Bash(*)`, which subsumes every narrower `Bash(hb-sdk *)`/`Bash(git *)`/`Bash(find *)` entry across the other six). This is a real, intentional blast-radius increase versus the read-only design originally planned, and is called out here so it isn't missed in review.

---

## 0. Current-state facts (verified during planning)

- `skills/hb-flow.md` does not exist yet — confirmed via `find skills -maxdepth 1 -type f`; this step creates it fresh.
- `skills/scripts/hb_sdk/state.py:61-69` (`cmd_state_next_action`) — `hb-sdk state next-action --format md|json` prints, per active task, a stage/message/invocation/choices tuple. Live-verified output (2026-07-14, this repo): md is one bullet per active task (nested sub-bullets for the `review_or_next`/`steps_complete` stages); json is a list of `{task, stage, message, invocation, choices}` objects, `invocation` is `null` exactly when `choices` is non-null.
- `skills/scripts/hb_sdk/state.py:43-58` (`cmd_state_show`) — `hb-sdk state show --format md` prints the last-recorded action (`Skill`/`Outcome`/`Timestamp`/`Task`/`Step`, each `—` if absent) or `No recorded state.` if `.hb/state.json` doesn't exist yet.
- `skills/scripts/hb_sdk/summarize.py:216-290` (`build_data`) — `hb-sdk summarize --format json` gives, per active task, `steps` (each with `name`/`has_ticket`/`has_plan`/`has_execution`/`has_review`/`status`), `steps_needs_work` (status in `skeleton`/`ticketed`/`planned`), `steps_needs_review` (status in `executed`/`review-open`), and `next_pending_step`. Both `hb-flow` (to resolve non-default targets) and `hb-task-archive`'s new confirmation step (AC 8) read this same field pair — no new `hb-sdk` output is needed for either.
- `skills/scripts/hb_sdk/task.py:120-140` (`cmd_task_archive`) — archiving performs **no check at all** for unexecuted/unreviewed steps today; it only checks the task exists and is currently active (also confirmed absent from `skills/hb-task-archive.md`'s current steps). This is the gap AC 8 closes, directly in `hb-task-archive.md`, using data already exposed by `summarize` — no `hb-sdk` code changes needed.
- Frontmatter `allowed-tools` across the 8 dispatch targets (grep-verified 2026-07-14, `skills/hb-task-*.md`):

  | Skill | `allowed-tools` |
  |---|---|
  | `hb-task-plan.md` | `Bash(hb-sdk *) Bash(git *) Bash(find *) Read Write` |
  | `hb-task-step-add.md` | `Bash(hb-sdk *) Bash(git *) Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)` |
  | `hb-task-step-plan.md` | `Bash(hb-sdk *) Bash(git *) Read Write` |
  | `hb-task-step-execute.md` | `Bash(hb-sdk *) Bash(git *) Read Write Edit Bash(*)` |
  | `hb-task-step-review-init.md` | `Bash(hb-sdk *) Bash(git *) Read Write` |
  | `hb-task-step-review-address.md` | `Bash(hb-sdk *) Bash(git *) Read Write Edit Bash(*)` |
  | `hb-task-archive.md` | `Bash(hb-sdk *) Bash(git *)` (unchanged by AC 8 — the new step only calls `hb-sdk summarize`) |
  | `hb-task-unarchive.md` | `Bash(hb-sdk *) Bash(git *)` |

  Union (plain `Bash(*)`/`Read`/`Write`/`Edit` subsume every scoped/tmp-scoped entry above): `Bash(*) Read Write Edit`. This is `hb-flow.md`'s required `allowed-tools`.
- The `!`cat <path>`` directive used throughout this codebase for Reference Files and shared subflows (e.g. `hb-task-step-review-init.md:35`, `hb-ticket-discuss.md:52`) is resolved once, at skill-load/parse time — it cannot conditionally include one of 8 different files chosen by a natural-language reply that hasn't been received yet. `hb-flow`'s target-skill inclusion must therefore be a normal runtime `Read` tool call (already covered by the `allowed-tools` union above), issued after the target is resolved — a deliberate, documented deviation from the static-include convention, not an oversight.
- `skills/references/facts-write-subflow.md:1-5` scopes itself explicitly to `hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address`. `hb-flow` is not extended to inject this subflow for its *own* reporting/resolving work — but when it inlines one of those four skills' steps after confirmation (AC 7.1), that skill's own facts-store steps run as part of following its steps verbatim, unchanged.
- `next_action.py:42-57` (the `review_or_next` stage) always offers `/hb-task-step-review-address`, never `/hb-task-step-review-init`, because review-address self-creates `review.md` when missing. `hb-flow`'s mapping table mirrors this: "review" defaults to review-address; review-init is offered only when the user explicitly wants to just seed `review.md` without addressing it yet.
- `skills/references/structure.md:170-186` — step refs accepted by `hb-sdk task step number|path <ref>` are `step-<n>`, bare integer `<n>`, or the full `step-<n>-<flavor>` name; `hb-flow` reuses these SDK lookups to validate any explicitly-named step rather than parsing folder names itself.
- No skill anywhere in `skills/*.md` uses an `AskUserQuestion`-style structured-choice tool; every prompt/confirmation in this framework is plain conversational text, kept harness-agnostic (`references/README.md:7-12` lists OpenCode as supported-but-experimental). `hb-flow`'s report/prompt/confirm/decline-and-reprompt loop follows the same convention — plain text, no structured-choice tool.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| Discovering + acting on the next step | `/hb-status` (read-only); user manually runs the next command | `/hb-flow` reports state, asks what to do (with examples), confirms, then runs the confirmed `hb-*` skill directly in the same session |
| Archiving a task with unfinished steps | `/hb-task-archive` archives unconditionally, no matter how many steps are unexecuted/unreviewed | `/hb-task-archive` lists the at-risk steps and asks for confirmation first (whether invoked directly or via `/hb-flow`) |

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| `/hb-task-archive <ref>` on a task with **no** unexecuted/unreviewed steps | Archives immediately | AC 8's new step is additive — a guard that's a no-op when both `steps_needs_work` and `steps_needs_review` are empty; the archive path itself (`task archive` SDK call, commit, prompt, state record) is untouched |
| Any other `hb-*` skill run directly (not via `/hb-flow`) | Runs its own steps as written | None of the 7 other dispatch targets are edited by this step; only `hb-task-archive.md` gains one new step, everything after it unchanged |

The one behavior-touching change (`hb-task-archive` gaining a confirmation) is additive-only (new prompt on a subset of invocations); the archive mechanics themselves are unchanged. `hb-flow` itself is a wholly new file — nothing existing to regress.

---

## 1. Design overview

```
invoke /hb-flow [freeform request]      (assumed: fresh/just-cleared session)
        │
        ▼
gather state:
  hb-sdk state show --format md
  hb-sdk state next-action --format md
        │
        ▼
report: "left off at ...", "recommended next: ..." (one block per active task if >1)
        │
        ▼
◄───────────────────────────────────────────────────────────────┐
have a freeform request already (initial arg)? if not, ask       │
"what would you like to do?" with example phrasings from §2's    │
Action Registry, and await the reply                             │
        │                                                        │
        ▼                                                        │
match reply against the Action Registry (§2)                     │
        │                                                        │
   ┌────┴─────┐                                                  │
no match/    confident match                                     │
ambiguous     │                                                  │
   │          ▼                                                  │
   │    resolve target task/step (explicit ref → validate via    │
   │    hb-sdk; else derive from state/summarize data, §2)       │
   │          │                                                  │
   │     ┌────┴─────┐                                            │
   │  still       resolved                                       │
   │  ambiguous     │                                            │
   │     │          ▼                                            │
   │     │    state the resolved invocation, ask user to confirm │
   │     │          │                                            │
   │     │     ┌────┴─────┐                                      │
   │     │  declines    confirms                                 │
   │     │     │          │                                      │
   │     │     │          ▼                                      │
   │     │     │    Read the target skill's .md file at runtime, │
   │     │     │    follow its ## Steps (skip its own Help       │
   │     │     │    check) with the resolved ref — including     │
   │     │     │    ITS OWN commit / prompt-user / state-record  │
   │     │     │          │                                      │
   │     │     │          ▼                                      │
   │     │     │         done                                    │
   ▼     ▼     ▼                                                 │
ask a clarifying / "what would you like instead" question ───────┘
```

No iteration cap — every unmatched, ambiguous, or declined reply re-prompts, never guesses and never runs an unconfirmed invocation (ticket AC 5, AC 7.2).

**Alternatives considered and rejected:**

- **Only print the resolved invocation, let the user run it themselves.** This was the original plan for this step. Rejected on revision — the ticket now explicitly requires confirm-then-invoke (AC 7), and the original rationale (protecting `/clear`-between-steps discipline) doesn't apply once `hb-flow` is itself defined as the fresh-session entry point that resolves to at most one action per invocation. See the Design decision callout above.
- **Re-implement each target skill's logic inline inside `hb-flow.md` instead of reading and following the target file.** Rejected — directly violates AC 7.1 ("rather than duplicating them inline") and would create eight parallel copies of logic to keep in sync; reading the real file at runtime means `hb-flow` can never drift from the skill it's dispatching to.
- **Statically `!`cat`` all 8 possible target skill files into every `hb-flow` invocation, then branch on which one applies.** Rejected — bloats every invocation's context with 7 unused skill files' full content regardless of what the user asks for; a runtime `Read` of only the one resolved file is both cheaper and simpler. (`!`cat`` is also unable to conditionally select a file chosen after parse time — see §0.)
- **Add the unexecuted-step confirmation inside `hb-flow` instead of `hb-task-archive`.** Rejected per explicit correction to this plan — `hb-task-archive` run directly (not via `hb-flow`) would keep the gap; putting the check in `hb-task-archive` protects both entry points and needs zero `hb-sdk` changes.

---

## 2. `hb-flow` skill — specification

**File:** `skills/hb-flow.md` (new).

**Frontmatter:**

```yaml
---
name: hb-flow
argument-hint: "[--help] [<natural language request>]"
description: >
  /hb-flow [--help] [<natural language request>]

  Report where the active task/step left off and the recommended next action, then
  interpret a natural-language reply, confirm the resolved hb-* skill invocation with
  the user, and carry it out directly — including calls-to-action other than the
  currently recommended one.
allowed-tools: Bash(*) Read Write Edit
---
```

- no `arguments:` field — mirrors `hb-status.md`/`hb-ticket-discuss.md` (no formally-named single positional token; the optional trailing text is freeform).
- `allowed-tools` is the union derived in §0 — required because `hb-flow` inlines whichever target skill's steps it ends up confirming (see Design decision callout).

**Steps:**

1. **Help check** — identical to every other skill.

2. **Gather state** — run, in order:
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/hb-sdk state show --format md
   ${CLAUDE_SKILL_DIR}/scripts/hb-sdk state next-action --format md
   ```
   Capture as `$LAST_ACTION` / `$NEXT_ACTIONS`. If `.hb/` is not initialized (`next-action` reports `not_initialized`), report that and stop. If there are no active tasks (`no_active_tasks`), report that and stop.

3. **Report** — plain language: where things left off (`$LAST_ACTION`, or "no prior recorded action"), and the recommended next action(s) (`$NEXT_ACTIONS` — already one block per active task, satisfying AC 6 by construction).

4. **Prompt for intent** — if the initial invocation already carried a freeform request, use it; otherwise ask "What would you like to do?" and list 3-4 example phrasings drawn from the Action Registry below (AC 2.3). Await the reply.

5. **Resolve intent** — match the reply against the **Action Registry** using semantic match (not exact keywords), same dispatch discipline as `ticket-loop-subflow.md` §D:

   | Action | Target skill(s) | Invocation shape | Example phrasings |
   |---|---|---|---|
   | Plan task into steps | `hb-task-plan` | `/hb-task-plan <task_ref>` | "plan this task", "break it into steps" |
   | Add a step | `hb-task-step-add` | `/hb-task-step-add <task_ref>` | "add a step", "add another step" |
   | Plan a step | `hb-task-step-plan` | `/hb-task-step-plan <task_ref>/<step_n>` | "plan the next step", "let's plan it", "go back and re-plan step 2" |
   | Execute a step | `hb-task-step-execute` | `/hb-task-step-execute <task_ref>/<step_n>` | "execute this step", "run the plan" |
   | Start/continue review | `hb-task-step-review-address` (default) or `hb-task-step-review-init` (only if the user explicitly wants to just seed `review.md`) | `/hb-task-step-review-address <task_ref>/<step_n>` or `/hb-task-step-review-init <task_ref>/<step_n>` | "let's review", "review this step", "just create review.md" |
   | Move to the next step | whatever `state next-action`'s `review_or_next`/`steps_complete` choices resolve to | as printed in `$NEXT_ACTIONS`'s choices | "move on", "next step" |
   | Archive task | `hb-task-archive` | `/hb-task-archive <task_ref>` | "archive this task", "close it out" |
   | Unarchive task | `hb-task-unarchive` | `/hb-task-unarchive <task_ref>` | "unarchive it", "restore this task" |

   On no confident match: ask a clarifying question, re-prompt (AC 5) — do not guess.

6. **Resolve target task/step** — this is what makes AC 4 work ("any valid current state, not only the currently-recommended action"):
   - If the reply names a task/step ref explicitly, validate it via `hb-sdk task path <ref>` / `hb-sdk task step number <task_ref>/<n>` rather than assuming it exists; surface the SDK's error verbatim and re-prompt if it doesn't.
   - Otherwise derive it from data already gathered (`hb-sdk summarize --format json` if not already fetched this turn):
     - task-level actions: if exactly one active task, use it; if more than one and none named, ask which (AC 6 — never silently pick one).
     - "plan a step": first step with `has_ticket=true, has_plan=false`; if the first pending step has no ticket, say so instead of resolving to it.
     - "execute a step": first step with `has_plan=true, has_execution=false`.
     - "review": first entry in `steps_needs_review`.
   - If still ambiguous, ask a clarifying question (AC 5) instead of guessing.

7. **Confirm** — state the exact resolved invocation (`/hb-<skill> <args>`) and ask the user to confirm it (AC 7).
   - **Declines / asks for something different:** ask what to change, return to Step 5 with the new information (AC 7.2). Do not invoke anything.
   - **Confirms:** proceed to Step 8.

8. **Invoke** — `Read` `${CLAUDE_SKILL_DIR}/<target-skill-name>.md` and execute its `## Steps` section in place, in this same session, starting from its first substantive step (skip its own Help check — not applicable) with the resolved task/step ref substituted for the ref that skill would otherwise have parsed from its own arguments. Let that skill's own Commit, Prompt user, and Record execution state steps run exactly as written (AC 7.1) — `hb-flow` performs no separate commit or state-record of its own.

**Failure/degradation contract:**

- `.hb/` not initialized / no active tasks → report and stop.
- Ambiguous or unmatched reply, at any stage (intent, target, confirmation) → clarifying question, re-prompt; never error, never guess, never invoke unconfirmed (AC 5, AC 7.2).
- Named task/step ref that doesn't exist → surface the `hb-sdk` error verbatim, re-prompt.
- `hb-flow` itself makes no commit and no `hb-sdk state record` call before Step 8; once Step 8 runs, the invoked skill's own steps (including its commit/state-record) are authoritative.

---

## 2b. `hb-task-archive` — new confirmation step (AC 8)

**File:** `skills/hb-task-archive.md` (edit — insert one new step; renumber the rest).

Insert after the existing "1. Help check" and before "2. Archive task" (current numbering from `hb-task-archive.md:29-44`):

**New step "2. Check for unexecuted/unreviewed steps":**

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize --format json
```

- locate the entry in `active_tasks` matching `<name>` (same author/task-id match the SDK itself uses; the task must be active — the existing archive step already errors if it isn't)
- if that task's `steps_needs_work` and `steps_needs_review` are both empty: proceed directly to the (renumbered) Archive step, no prompt
- otherwise: list the step names from both lists and ask:
  > Archiving `<name>` will skip N step(s) not yet fully executed/reviewed: `<step names>`. Archive anyway?
  - if the user declines: stop, do not archive
  - if the user confirms: proceed to the (renumbered) Archive step

Renumber existing steps 2-5 (`Archive task`, `Commit`, `Prompt user`, `Record execution state`) to 3-6. No other content in those steps changes. `allowed-tools` is unchanged (`Bash(hb-sdk *) Bash(git *)` — the new step only calls `hb-sdk summarize`, already covered).

---

## 3. Integration / wiring

- `skills/hb-flow.md` is new; it *reads* existing `hb-sdk` subcommands (`state show`, `state next-action`, `summarize`, `task path`, `task step number`) and, after confirmation, *reads* one of the 8 existing skill files with the ordinary `Read` tool at runtime (§0/§1 — not the static `!`cat`` mechanism). No target skill file is modified to support this; they remain independently invocable exactly as today.
- `skills/hb-task-archive.md` is edited to insert one new step (§2b) between its existing Help check and Archive steps; every other step (Archive task, Commit, Prompt user, Record execution state) is renumbered but otherwise byte-identical. Its `allowed-tools` frontmatter is unchanged.
- No build/entry-point/dependency-manifest wiring — skills are picked up by the installer's existing symlink mechanism purely by filename under `skills/`.
- `references/references-toc.md` is **not** edited — `hb-flow.md` introduces no new shared reference/subflow file (its Action Registry lives inline; its dynamic target-skill read is a runtime `Read` call, not a registered reference file).
- `references/README.md` (skills table, lifecycle diagram) is **not** updated — out of scope (§8), mirrors the ticket's own exclusion of the analogous `hb-init` prompt update.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-flow.md` | **new** — router/presenter/invoker skill per §2. |
| `skills/hb-task-archive.md` | **edit** — insert the unexecuted/unreviewed-steps confirmation step per §2b; renumber steps 2-5 → 3-6; no other content changes. |

No dependency-manifest or lockfile effects — markdown-only changes, no Python code touched.

---

## 5. Tests

N/A — neither change touches Python/executable code (`skills/hb-flow.md` is new markdown; `skills/hb-task-archive.md`'s edit is a new markdown step calling an existing, already-tested `hb-sdk` command). `tests/skills/scripts/hb_sdk/` (covering `hb-sdk` itself) is unaffected. Correctness is exercised via the manual scenario walkthroughs in §6.

---

## 6. Verification (after implementation)

1. **Static checks stay green** (no Python changed):
   ```bash
   uv run ruff check
   uv run ruff format --check
   ```
2. **Re-confirm the `hb-sdk` calls both files depend on**, against this repo's live `.hb/` state:
   ```bash
   ./skills/scripts/hb-sdk state show --format md
   ./skills/scripts/hb-sdk state next-action --format md
   ./skills/scripts/hb-sdk summarize --format json
   ```
3. **Frontmatter conformance**: `skills/hb-flow.md`'s `allowed-tools` literally equals `Bash(*) Read Write Edit` (§0's derived union); re-grep the 8 target skills' `allowed-tools` and confirm none has since gained a tool outside that union (would mean the union in this plan is stale).
4. **Per-AC scenario walkthrough** (hand-traced against this repo's current multi-task `.hb/` state — no automated skill-markdown harness exists):
   - No arguments, one active task at each lifecycle stage → confirm §2 Step 3's report matches `state next-action`'s per-stage message (AC 2).
   - Multiple active tasks (this repo currently has ≥7) → confirm §2 Step 3 reports every one (AC 6).
   - A reply naming an action other than the recommended one, with an explicit non-default step number (e.g. "re-plan step 0" while the recommendation is to plan step 1) → confirm §2 Steps 5-6 resolve to `/hb-task-step-plan <ref>/0` (AC 4).
   - Confirm step: after a resolved invocation is stated, a decline ("no, do X instead") routes back to Step 5 without invoking anything; a confirmation proceeds to Step 8 (AC 7).
   - `/hb-task-archive` run **directly** (not via `hb-flow`) against a task with a non-empty `steps_needs_work`/`steps_needs_review` (e.g. any task in this repo currently mid-steps) → confirm the new §2b step prompts before archiving (AC 8) — this must hold independent of `hb-flow`.
   - A vague reply ("do the thing") → clarifying question, no invocation guessed (AC 5).
   - A reply naming no task while ≥2 active tasks exist → clarifying question naming the candidates (AC 5, AC 6).
5. **Invariant check**: every invocation string `hb-flow.md` can produce is validated against the target skill's own `argument-hint`; §2b's renumbering in `hb-task-archive.md` leaves no gap or duplicate step number and no step's own content (beyond the number) changed.
6. **Scope check**: `git status --short` shows only `skills/hb-flow.md` (new) and `skills/hb-task-archive.md` (modified) — no other tracked file changed.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (frontmatter, Help check, Reference Files) | Mirrors existing skill structure. |
| 2.1 | §2 Step 2 | `state next-action` + `state show`; no inline traversal/status logic. |
| 2.2 | §2 Steps 2-3 | Reports last-recorded action + recommendation. |
| 2.3 | §2 Step 4 | Prompts with example phrasings from the Action Registry. |
| 3 | §2 Step 5 (Action Registry table) | Covers all 7 named call-to-actions plus "move to next step". |
| 4 | §2 Steps 6, 8; §2b | Non-default targets resolved via `hb-sdk` lookups; archive confirmation lives in `hb-task-archive`, not duplicated in `hb-flow`. |
| 5 | §2 Steps 5-7 (no-match / still-ambiguous / decline) | Always re-prompts, never guesses, never invokes unconfirmed. |
| 6 | §2 Step 3 | `state next-action --format md` already iterates every active task. |
| 7.1 | §2 Step 8 | Reads and follows the target skill's own `## Steps` at runtime — no inline duplication. |
| 7.2 | §2 Step 7 (declines branch) | Asks what to change, returns to Step 5; nothing invoked until confirmed. |
| 8 | §2b | New confirmation step in `hb-task-archive.md`, using existing `summarize` data; no `hb-sdk` change. |

---

## 8. Out of scope (per ticket)

- Any change to the behavior of the skills `hb-flow` dispatches to, other than `hb-task-archive`'s new confirmation step (AC 8) — `hb-task-plan`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`, `hb-task-unarchive` are invoked as-is; `hb-task-archive`'s existing archive/move mechanics are otherwise unchanged.
- Further `hb-sdk` changes — AC 8 is implemented purely as a new `hb-task-archive.md` step consuming existing `hb-sdk summarize` output; `hb-flow` itself only consumes the existing `state`/`summarize`/`task` surface.
- Updating `hb-init`'s "what to do next" prompt to mention `hb-flow`.
- Updating `references/README.md` to document `hb-flow` or the new archive-confirmation behavior.
