# Step 3 Plan — `hb-flow` router/presenter skill

Today, after any `hb-*` skill finishes, the only way to find out what to do next is to run `/hb-status` (read-only, always shows the *recommended* action) or to already know the exact next command yourself — there is no conversational entry point that reports where a task/step left off and lets the user say, in plain language, what they actually want to do next (including something other than the recommended action, e.g. "archive this task instead" while the recommendation is "execute step 2"), then actually carry it out. This step adds that entry point: `./skills/hb-flow.md`, a new skill meant to be run as the *first* command in a fresh session (a just-started session, or immediately after `/clear`). It reports state (reusing `hb-sdk`, never re-deriving it), maps a natural-language reply to a specific `hb-*` invocation, confirms that invocation with the user, and — once confirmed — invokes that skill directly in the same session via the harness's native skill-invocation tool. Scope boundary: **one new file only** — `skills/hb-flow.md` is additive; every skill it dispatches to (including `hb-task-archive`) is invoked exactly as it exists today, unmodified. The single externally observable effect once this lands: running `/hb-flow` reports where things left off, asks what to do (with examples), confirms the resolved command, and then runs it for you — for any valid action, not just the recommended one.

Source ticket: `./ticket.md` (revised twice — see the two corrections below). Builds on the **shipped** work from step-1 (`hb-sdk state record`) and step-2 (`hb-sdk state next-action`, `skills/scripts/hb_sdk/next_action.py`). This plan targets the code as it exists **now** (verified 2026-07-14).

> **Design decision — `hb-flow` invokes the resolved skill via the harness's native `Skill` tool, not by re-reading/re-executing its steps.** Two earlier drafts of this plan considered (1) only printing the resolved invocation for the user to run themselves, and (2) `Read`-ing the target skill's `.md` file and manually re-executing its `## Steps` inline. Both are superseded: the calling harness itself exposes a tool for exactly this ("Execute a skill within the main conversation," taking a skill name and an argument string) — the same mechanism this very conversation was started with. Using it directly means `hb-flow` never re-derives or duplicates a target skill's logic (trivially satisfies AC 7.1's "rather than duplicating them inline"), and the target skill's own commit / prompt-user / state-record steps execute exactly as they do when a user runs it directly, because they *are* that same execution — not a hand-rolled re-enactment of it.
>
> **Consequence — `hb-flow`'s `allowed-tools` no longer needs the multi-skill union.** The rejected "manually read and follow" design would have required `hb-flow.md`'s own `allowed-tools` to cover the superset of every dispatch target's tools (worked out to `Bash(*) Read Write Edit` in the prior revision of this plan), because the harness gates tool calls by whichever skill is *currently active in-context*. Invoking via the `Skill` tool avoids this: `hb-flow` only ever calls the `Skill` tool itself plus its own read-only `hb-sdk` lookups; whatever tools the invoked skill needs are its own concern, governed by its own frontmatter, exactly as when it's run directly. `hb-flow.md`'s required `allowed-tools` shrinks to `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Read Skill` (§2). This is the first `hb-*` skill file to reference the `Skill` tool in `allowed-tools` — flagged in §6 as something to concretely verify at execution time, since there's no existing precedent in this codebase for its exact permission syntax.
>
> **Dropped — no archive-time confirmation for unexecuted/unreviewed steps.** An earlier revision of this plan added a new step to `hb-task-archive.md` checking for unexecuted/unreviewed steps before archiving. This is dropped per explicit product decision: archiving is trivially reversible via `/hb-task-unarchive`, so the extra guard isn't worth the complexity. `hb-task-archive` is therefore back to being invoked completely as-is — this step touches exactly one file.

---

## 0. Current-state facts (verified during planning)

- `skills/hb-flow.md` does not exist yet — confirmed via `find skills -maxdepth 1 -type f`; this step creates it fresh.
- `skills/scripts/hb_sdk/state.py:61-69` (`cmd_state_next_action`) — `hb-sdk state next-action --format md|json` prints, per active task, a stage/message/invocation/choices tuple. Live-verified output (2026-07-14, this repo): md is one bullet per active task (nested sub-bullets for the `review_or_next`/`steps_complete` stages); json is a list of `{task, stage, message, invocation, choices}` objects, `invocation` is `null` exactly when `choices` is non-null.
- `skills/scripts/hb_sdk/state.py:43-58` (`cmd_state_show`) — `hb-sdk state show --format md` prints the last-recorded action (`Skill`/`Outcome`/`Timestamp`/`Task`/`Step`, each `—` if absent) or `No recorded state.` if `.hb/state.json` doesn't exist yet.
- `skills/scripts/hb_sdk/summarize.py:216-290` (`build_data`) — `hb-sdk summarize --format json` gives, per active task, `steps` (each with `name`/`has_ticket`/`has_plan`/`has_execution`/`has_review`/`status`), `steps_needs_work`, `steps_needs_review`, and `next_pending_step`. This is what `hb-flow` uses to resolve a step target that is *not* the currently-recommended one (e.g. "re-plan step 2").
- `skills/scripts/hb_sdk/task.py:120-140` (`cmd_task_archive`) — archiving performs no check for unexecuted/unreviewed steps. Confirmed still true; **not addressed by this step** — see the Design decision callout ("Dropped") and ticket Out-of-scope.
- The `Skill` tool ("Execute a skill within the main conversation," parameters `skill` = exact skill name with no leading slash, `args` = optional argument string) is a harness-level tool available to the calling agent — the same class of tool that loaded this very `hb-task-step-plan` invocation. No existing `hb-*` skill file references it in `allowed-tools` today (grepped `skills/*.md` for `Skill(` / `SlashCommand` — no hits); `hb-flow` is the first.
- The `!`cat <path>`` directive used throughout this codebase for Reference Files and shared subflows (e.g. `hb-task-step-review-init.md:35`, `hb-ticket-discuss.md:52`) is resolved once, at skill-load/parse time — irrelevant to this design now that dispatch goes through the runtime `Skill` tool rather than a file read, but still governs `hb-flow`'s own (static) Reference Files section.
- `skills/references/facts-write-subflow.md:1-5` scopes itself explicitly to `hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address`. `hb-flow` is not extended to inject this subflow — it makes no `ticket.md`/`plan.md`/execution/review writes of its own. When it invokes one of those four skills via the `Skill` tool, that invocation runs the target skill's own facts-store steps as part of its normal execution, unchanged.
- `next_action.py:42-57` (the `review_or_next` stage) always offers `/hb-task-step-review-address`, never `/hb-task-step-review-init`, because review-address self-creates `review.md` when missing. `hb-flow`'s mapping table mirrors this: "review" defaults to review-address; review-init is offered only when the user explicitly wants to just seed `review.md` without addressing it yet.
- `skills/references/structure.md:170-186` — step refs accepted by `hb-sdk task step number|path <ref>` are `step-<n>`, bare integer `<n>`, or the full `step-<n>-<flavor>` name; `hb-flow` reuses these SDK lookups to validate any explicitly-named step rather than parsing folder names itself.
- No skill anywhere in `skills/*.md` uses an `AskUserQuestion`-style structured-choice tool; every prompt/confirmation in this framework is plain conversational text, kept harness-agnostic (`references/README.md:7-12` lists OpenCode as supported-but-experimental). `hb-flow`'s report/prompt/confirm/decline-and-reprompt loop follows the same convention — plain text, no structured-choice tool.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| Discovering + acting on the next step | `/hb-status` (read-only); user manually runs the next command | `/hb-flow` reports state, asks what to do (with examples), confirms, then invokes the confirmed `hb-*` skill directly via the `Skill` tool, in the same session |

Purely additive: one new file, zero existing files touched (the archive-confirmation idea from a prior revision is dropped — see Design decision callout).

### 0.2 Non-regression proof / risk

Purely additive — one new file (`skills/hb-flow.md`), zero existing files touched. Risk is confined to the new file: (a) its mapping table could drift from real target-skill argument shapes — mitigated by grounding every invocation shape directly in the target skill's own `argument-hint`; (b) the `Skill` tool's exact `allowed-tools` permission syntax is unverified in this codebase (§0) — flagged as a concrete execution-time check (§6).

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
   │     │    state the resolved invocation ("/hb-<skill> <args>")│
   │     │    and ask the user to confirm                        │
   │     │          │                                            │
   │     │     ┌────┴─────┐                                      │
   │     │  declines    confirms                                 │
   │     │     │          │                                      │
   │     │     │          ▼                                      │
   │     │     │    call Skill(skill=<target-skill-name>,        │
   │     │     │    args=<resolved args string>) — its own       │
   │     │     │    commit / prompt-user / state-record run as   │
   │     │     │    part of that invocation                      │
   │     │     │          │                                      │
   │     │     │          ▼                                      │
   │     │     │         done                                    │
   ▼     ▼     ▼                                                 │
ask a clarifying / "what would you like instead" question ───────┘
```

No iteration cap — every unmatched, ambiguous, or declined reply re-prompts, never guesses and never invokes unconfirmed (ticket AC 5, AC 7.2).

**Alternatives considered and rejected:**

- **Only print the resolved invocation, let the user run it themselves.** Rejected — superseded by ticket AC 7's explicit confirm-then-invoke requirement.
- **`Read` the target skill's `.md` file and manually re-execute its `## Steps` inline.** Rejected — the native `Skill` tool already does this correctly (loads and runs the target skill's own instructions, including its own tool permissions) without hand-rolled duplication risk or the large `allowed-tools` union the manual approach required. See Design decision callout.
- **Re-implement each target skill's logic from scratch inside `hb-flow.md`.** Rejected — directly violates AC 7.1 ("rather than duplicating them inline") and would create eight parallel copies of logic to keep in sync.
- **Add an unexecuted/unreviewed-steps confirmation before archiving** (either inside `hb-flow` or inside `hb-task-archive`). Rejected per explicit product decision — archiving is trivially reversible via `/hb-task-unarchive`; not worth the added complexity in either location. See Design decision callout ("Dropped").

---

## 2. `hb-flow` skill — specification

**File:** `skills/hb-flow.md` (new — the only file this step changes).

**Frontmatter:**

```yaml
---
name: hb-flow
argument-hint: "[--help] [<natural language request>]"
description: >
  /hb-flow [--help] [<natural language request>]

  Report where the active task/step left off and the recommended next action, then
  interpret a natural-language reply, confirm the resolved hb-* skill invocation with
  the user, and invoke it directly — including calls-to-action other than the
  currently recommended one.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Read Skill
---
```

- no `arguments:` field — mirrors `hb-status.md`/`hb-ticket-discuss.md` (no formally-named single positional token; the optional trailing text is freeform).
- `allowed-tools` covers: read-only `hb-sdk` lookups, `Read` (for the `!`cat`` Reference Files include), and `Skill` (to invoke the confirmed target — §0/Design decision). No `Bash(git *)`, `Write`, or `Edit` — `hb-flow` itself makes no commits and writes no files; whatever the invoked skill needs is scoped by its own frontmatter, not `hb-flow`'s.

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

   | Action | Target skill name (for `Skill(skill=...)`) | Args shape | Example phrasings |
   |---|---|---|---|
   | Plan task into steps | `hb-task-plan` | `<task_ref>` | "plan this task", "break it into steps" |
   | Add a step | `hb-task-step-add` | `<task_ref>` | "add a step", "add another step" |
   | Plan a step | `hb-task-step-plan` | `<task_ref>/<step_n>` | "plan the next step", "let's plan it", "go back and re-plan step 2" |
   | Execute a step | `hb-task-step-execute` | `<task_ref>/<step_n>` | "execute this step", "run the plan" |
   | Start/continue review | `hb-task-step-review-address` (default) or `hb-task-step-review-init` (only if the user explicitly wants to just seed `review.md`) | `<task_ref>/<step_n>` | "let's review", "review this step", "just create review.md" |
   | Move to the next step | whatever `state next-action`'s `review_or_next`/`steps_complete` choices resolve to | as printed in `$NEXT_ACTIONS`'s choices | "move on", "next step" |
   | Archive task | `hb-task-archive` | `<task_ref>` | "archive this task", "close it out" |
   | Unarchive task | `hb-task-unarchive` | `<task_ref>` | "unarchive it", "restore this task" |

   On no confident match: ask a clarifying question, re-prompt (AC 5) — do not guess.

6. **Resolve target task/step** — this is what makes AC 4 work ("any valid current state, not only the currently-recommended action"):
   - If the reply names a task/step ref explicitly, validate it via `hb-sdk task path <ref>` / `hb-sdk task step number <task_ref>/<n>` rather than assuming it exists; surface the SDK's error verbatim and re-prompt if it doesn't.
   - Otherwise derive it from data already gathered (`hb-sdk summarize --format json` if not already fetched this turn):
     - task-level actions: if exactly one active task, use it; if more than one and none named, ask which (AC 6 — never silently pick one).
     - "plan a step": first step with `has_ticket=true, has_plan=false`; if the first pending step has no ticket, say so instead of resolving to it.
     - "execute a step": first step with `has_plan=true, has_execution=false`.
     - "review": first entry in `steps_needs_review`.
   - If still ambiguous, ask a clarifying question (AC 5) instead of guessing.

7. **Confirm** — state the exact resolved invocation (`/hb-<skill> <args>`, matching the target skill's real `argument-hint` shape) and ask the user to confirm it (AC 7).
   - **Declines / asks for something different:** ask what to change, return to Step 5 with the new information (AC 7.2). Do not invoke anything.
   - **Confirms:** proceed to Step 8.

8. **Invoke** — call the `Skill` tool: `skill = <target-skill-name>` (from §2's Action Registry, e.g. `hb-task-step-plan`), `args = <resolved args string>` (e.g. `northwind/hb-014-execution-state/step-3-hb-flow-skill`) — the same string a user would type after the slash command. This runs the target skill within the current session per the `Skill` tool's own contract. `hb-flow` performs no separate commit or state-record of its own — the invoked skill's own steps (commit, prompt-user, state-record) run as part of its own execution (AC 7.1).

**Failure/degradation contract:**

- `.hb/` not initialized / no active tasks → report and stop.
- Ambiguous or unmatched reply, at any stage (intent, target, confirmation) → clarifying question, re-prompt; never error, never guess, never invoke unconfirmed (AC 5, AC 7.2).
- Named task/step ref that doesn't exist → surface the `hb-sdk` error verbatim, re-prompt.
- `hb-flow` itself makes no commit and no `hb-sdk state record` call — the invoked skill's own steps are authoritative for that.

---

## 3. Integration / wiring

- `skills/hb-flow.md` is new; it *reads* existing `hb-sdk` subcommands (`state show`, `state next-action`, `summarize`, `task path`, `task step number`) and, after confirmation, *invokes* one of the 8 existing skill files via the harness's `Skill` tool. No target skill file is modified; each remains independently invocable exactly as today.
- No build/entry-point/dependency-manifest wiring — skills are picked up by the installer's existing symlink mechanism purely by filename under `skills/`.
- `references/references-toc.md` is **not** edited — `hb-flow.md` introduces no new shared reference/subflow file.
- `references/README.md` (skills table, lifecycle diagram) is **not** updated — out of scope (§8), mirrors the ticket's own exclusion of the analogous `hb-init` prompt update.
- `skills/hb-task-archive.md` is **not** edited — the archive-confirmation idea from a prior revision of this plan is dropped (Design decision callout, "Dropped").

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-flow.md` | **new** — router/presenter/invoker skill per §2. |

No dependency-manifest or lockfile effects — one new markdown file, no Python code touched.

---

## 5. Tests

N/A — this step adds no Python/executable code (`skills/hb-flow.md` is a markdown skill prompt, consumed by the AI harness, not by `pytest`). `tests/skills/scripts/hb_sdk/` (covering `hb-sdk` itself) is unaffected. Correctness is exercised via the manual scenario walkthroughs in §6.

---

## 6. Verification (after implementation)

1. **Static checks stay green** (no Python changed):
   ```bash
   uv run ruff check
   uv run ruff format --check
   ```
2. **Re-confirm the `hb-sdk` calls `hb-flow.md` depends on**, against this repo's live `.hb/` state:
   ```bash
   ./skills/scripts/hb-sdk state show --format md
   ./skills/scripts/hb-sdk state next-action --format md
   ./skills/scripts/hb-sdk summarize --format json
   ```
3. **`Skill`-tool permission check (new, unverified mechanism — §0/Design decision):** after installing `hb-flow.md`, drive it through one full confirm → invoke cycle (e.g. resolve to `/hb-status`-adjacent low-risk action, or any real pending action in this repo) and confirm the `Skill` tool call is either auto-permitted by `allowed-tools: ... Skill` or prompts the user exactly once for approval — not silently blocked or silently no-op'd. If the harness rejects the bare `Skill` entry in `allowed-tools`, this is the one thing in this plan most likely to need a follow-up correction.
4. **Frontmatter conformance**: `skills/hb-flow.md`'s `allowed-tools` literally equals `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Read Skill`; no `Bash(git *)`/`Write`/`Edit` present (confirms `hb-flow` makes no changes of its own).
5. **Per-AC scenario walkthrough** (hand-traced against this repo's current multi-task `.hb/` state — no automated skill-markdown harness exists):
   - No arguments, one active task at each lifecycle stage → confirm §2 Step 3's report matches `state next-action`'s per-stage message (AC 2).
   - Multiple active tasks (this repo currently has ≥7) → confirm §2 Step 3 reports every one (AC 6).
   - A reply naming an action other than the recommended one, with an explicit non-default step number (e.g. "re-plan step 0" while the recommendation is to plan step 1) → confirm §2 Steps 5-6 resolve to `skill=hb-task-step-plan, args=<ref>/0` (AC 4).
   - Confirm step: after a resolved invocation is stated, a decline ("no, do X instead") routes back to Step 5 without invoking anything; a confirmation proceeds to Step 8 and the `Skill` tool is called with the exact resolved `skill`/`args` (AC 7).
   - "archive this task" on a task with unexecuted/unreviewed steps → confirm §2 Steps 5-8 resolve straight to `Skill(skill=hb-task-archive, args=<task_ref>)` with **no** extra confirmation beyond §2 Step 7's generic one (AC 4 — no archive-specific guard exists per the Dropped decision).
   - A vague reply ("do the thing") → clarifying question, no invocation guessed (AC 5).
   - A reply naming no task while ≥2 active tasks exist → clarifying question naming the candidates (AC 5, AC 6).
6. **Invariant check**: every `(skill, args)` pair `hb-flow.md` can produce is validated against the target skill's own `argument-hint` (cross-read each of the 8 target skill files).
7. **Scope check**: `git status --short` shows only `skills/hb-flow.md` as new; no other tracked file modified (in particular, `skills/hb-task-archive.md` untouched).

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (frontmatter, Help check, Reference Files) | Mirrors existing skill structure. |
| 2.1 | §2 Step 2 | `state next-action` + `state show`; no inline traversal/status logic. |
| 2.2 | §2 Steps 2-3 | Reports last-recorded action + recommendation. |
| 2.3 | §2 Step 4 | Prompts with example phrasings from the Action Registry. |
| 3 | §2 Step 5 (Action Registry table) | Covers all 7 named call-to-actions plus "move to next step". |
| 4 | §2 Steps 6, 8 | Non-default targets resolved via `hb-sdk` lookups, then invoked via `Skill` exactly like the recommended path — no special-casing. |
| 5 | §2 Steps 5-7 (no-match / still-ambiguous / decline) | Always re-prompts, never guesses, never invokes unconfirmed. |
| 6 | §2 Step 3 | `state next-action --format md` already iterates every active task. |
| 7.1 | §2 Step 8 | Invokes the target skill via the native `Skill` tool — no inline duplication, no re-derivation of its steps. |
| 7.2 | §2 Step 7 (declines branch) | Asks what to change, returns to Step 5; nothing invoked until confirmed. |

---

## 8. Out of scope (per ticket)

- Any change to the behavior of the skills `hb-flow` dispatches to (`hb-task-plan`, `hb-task-step-plan`, `hb-task-step-execute`, `hb-task-step-review-init`, `hb-task-step-review-address`, `hb-task-archive`, `hb-task-unarchive`) — all invoked exactly as they exist today.
- A confirmation/guard for archiving a task with unexecuted or unreviewed steps — considered in an earlier revision of this plan and dropped; archiving is trivially reversible via `/hb-task-unarchive`.
- Further `hb-sdk` changes — `hb-flow` only consumes the existing `state`/`summarize`/`task` surface.
- Updating `hb-init`'s "what to do next" prompt to mention `hb-flow`.
- Updating `references/README.md` to document `hb-flow`.
