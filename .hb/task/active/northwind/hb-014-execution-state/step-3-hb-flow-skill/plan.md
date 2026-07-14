# Step 3 Plan — `hb-flow` router/presenter skill

Today, after any `hb-*` skill finishes, the only way to find out what to do next is to run `/hb-status` (read-only, always shows the *recommended* action) or to already know the exact next command yourself — there is no conversational entry point that reports where a task/step left off and lets the user say, in plain language, what they actually want to do next (including something other than the recommended action, e.g. "archive this task instead" while the recommendation is "execute step 2"). This step adds that entry point: `./skills/hb-flow.md`, a new skill that reports state (reusing `hb-sdk`, never re-deriving it) and maps freeform natural-language replies to the exact `hb-*` invocation to run. Scope boundary: **additive only** — no existing skill, `hb-sdk` command, or file changes; `hb-flow` consumes the `hb-sdk state`/`summarize` surface delivered in step-1/step-2 as-is. The single externally observable effect once this lands: running `/hb-flow` reports where things left off and, after a natural-language reply, tells the user the exact next `/hb-*` command to run for whatever they asked for — even actions the tool didn't recommend.

Source ticket: `./ticket.md`. Builds on the **shipped** work from step-1 (`hb-sdk state record`, wired into every terminal `hb-*` skill) and step-2 (`hb-sdk state next-action`, `skills/scripts/hb_sdk/next_action.py`). This plan targets the code as it exists **now** (verified 2026-07-14).

> **Design decision — `hb-flow` offers the resolved invocation, it does not auto-run it.** Every existing `hb-*` skill ends its "Prompt user" step by telling the user to `/clear` the conversation and then run the next command *themselves* (e.g. `hb-status.md`'s own next-action passthrough, `hb-task-archive.md:53-57`, `hb-task-plan.md:93-97`) — no skill in this codebase invokes another skill inline. The framework's own stated goal (`references/README.md:18`: "Human in the loop at every step... Every step produces an artifact you can read and approve before moving on") and its explicit `/clear`-between-steps discipline (`references/README.md:135`) both depend on this. Ticket AC 3/AC 4 ask `hb-flow` to "map" natural language to "the corresponding invocation" and "resolve and offer/invoke" it — resolving to a printed invocation string satisfies this without breaking context-freshness. See §2 Step 6 and the AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `skills/hb-flow.md` does not exist yet — confirmed via `find skills -maxdepth 1 -type f` (§ Reads above); this step creates it fresh.
- `skills/scripts/hb_sdk/state.py:61-69` (`cmd_state_next_action`) — `hb-sdk state next-action --format md|json` prints, per active task, a stage/message/invocation/choices tuple. Live-verified output (2026-07-14, this repo):
  - md: one bullet per active task, e.g. `` - Run `/clear`, then `/hb-task-step-plan northwind/hb-014-execution-state/step-3-hb-flow-skill` to plan the next step. ``, and for the `review_or_next` stage a bullet with nested sub-bullets, one per reviewable step plus a final "Move to the next step"/next-task-stage choice.
  - json: a list of `{task, stage, message, invocation, choices}` objects; `invocation` is `null` exactly when `choices` is non-null (i.e. the stage offers more than one option — `review_or_next` and `steps_complete`).
- `skills/scripts/hb_sdk/state.py:43-58` (`cmd_state_show`) — `hb-sdk state show --format md` prints the last-recorded action (`Skill`, `Outcome`, `Timestamp`, `Task`, `Step`, each `—` if absent) or `No recorded state.` if `.hb/state.json` doesn't exist yet. Live-verified: currently shows `Skill: hb-task-step-review-address`, `Task: northwind/hb-014-execution-state`, `Step: 2`.
- `skills/scripts/hb_sdk/summarize.py:216-290` (`build_data`) — `hb-sdk summarize --format json` gives, per active task, `steps` (each with `name`/`has_ticket`/`has_plan`/`has_execution`/`has_review`/`status`), `steps_needs_work` (status in `skeleton`/`ticketed`/`planned`), `steps_needs_review` (status in `executed`/`review-open`), and `next_pending_step`. This is the only data `hb-flow` needs to locate a step target that is *not* the currently-recommended one (e.g. "re-plan step 2").
- `skills/scripts/hb_sdk/task.py:120-140` (`cmd_task_archive`) — archiving performs **no check at all** for unexecuted/unreviewed steps; it only checks the task exists and is currently active. Ticket AC 4 asks for a confirmation "consistent with how `hb-task-archive` itself behaves," but there is nothing to be consistent with — `hb-task-archive` has no such guard today (also confirmed absent from `skills/hb-task-archive.md`). `hb-flow` must therefore implement this sanity check itself, from `summarize`'s `steps_needs_work`/`steps_needs_review` lists, before offering the archive invocation — delegating to `hb-task-archive` would silently skip the check ticket AC 4 requires.
- `skills/references/facts-write-subflow.md:1-5` scopes itself explicitly to `hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address` — the planning/execution skills. `hb-flow` is a router/presenter (ticket AC 7), not one of these, and makes no `ticket.md`/`plan.md`/execution/review writes of its own, so it has nothing that would justify writing new facts. It is **not** extended to inject this subflow.
- `next_action.py:42-57` (the `review_or_next` stage) always offers `/hb-task-step-review-address`, never `/hb-task-step-review-init`, because review-address self-creates `review.md` when missing (`hb-task-step-review-address.md:57-61`, its own step 3). `hb-flow`'s mapping table mirrors this: the "review" action's primary/default invocation is review-address; review-init is only offered when the user explicitly asks to just create/seed `review.md` without addressing it yet (README's documented "Option B", `references/README.md:159-171`).
- `skills/references/structure.md:170-186` — step refs accepted by `hb-sdk task step number|path <ref>` are `step-<n>`, bare integer `<n>`, or the full `step-<n>-<flavor>` name; `hb-flow` reuses these SDK lookups rather than parsing step folder names itself.
- No skill anywhere in `skills/*.md` uses an `AskUserQuestion`-style structured-choice tool or a `SlashCommand`-style skill-invocation tool in its `allowed-tools`; every clarifying question and every "run this next" prompt is plain conversational text, kept harness-agnostic (README.md:7-12 lists OpenCode as a supported-but-experimental harness). `hb-flow` follows the same convention.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| Discovering next action | `/hb-status` (read-only report only) | `/hb-status` unchanged; `/hb-flow` additionally reports state and accepts a natural-language reply, resolving it to an exact `hb-*` invocation |
| Acting on something other than the recommendation | User must already know the exact skill/args | `/hb-flow` resolves it from a documented mapping table + `hb-sdk` lookups, asking a clarifying question when ambiguous |

Purely additive: no existing behavior changes, no existing file's output changes.

### 0.2 Non-regression proof / risk

Purely additive — one new file (`skills/hb-flow.md`), zero existing files touched. The only risk is internal to the new file: its mapping table or step logic could drift from the real `hb-sdk`/skill argument shapes it documents. Mitigated by grounding every invocation shape in this plan directly in the target skill's own `argument-hint`/frontmatter (read live in §0 research, cited per-row in §2's mapping table) rather than re-deriving them from memory.

---

## 1. Design overview

Control flow, single linear pass with one re-prompt loop:

```
invoke /hb-flow [freeform request]
        │
        ▼
gather state:
  hb-sdk state show --format md         (last-executed action, if any)
  hb-sdk state next-action --format md  (recommended action, per active task)
  hb-sdk summarize --format json        (full step-status detail, for non-default targets)
        │
        ▼
report: "left off at ...", "recommended next: ..." (one block per active task if >1)
        │
        ▼
◄──────────────────────────────────────────────────────────────┐
have a freeform request? (from the initial invocation arg,     │
or await the user's reply if not)                              │
        │                                                       │
        ▼                                                       │
match against the Action Registry (§2 mapping table)            │
        │                                                       │
   ┌────┴─────┐                                                 │
   │           │                                                │
no match /   confident match                                    │
ambiguous     │                                                 │
   │           ▼                                                │
   │     resolve target task/step:                              │
   │       - explicit ref in the reply → validate via hb-sdk     │
   │       - else → derive from state/summarize data (§2)       │
   │       - if still ambiguous (e.g. >1 active task, no        │
   │         ref named) → ask which one                         │
   │           │                                                │
   │      ┌────┴─────┐                                          │
   │      │           │                                         │
   │  still        resolved                                     │
   │  ambiguous       │                                         │
   │      │           ▼                                         │
   │      │     archive target? → run sanity check (§2 Step 5)  │
   │      │           │                                         │
   │      │           ▼                                         │
   │      │     present resolved invocation, tell user to        │
   │      │     /clear then run it                               │
   │      │           │                                         │
   ▼      ▼           ▼                                         │
ask a clarifying question, await reply ─────────────────────────┘
```

No iteration cap (mirrors `ticket-loop-subflow.md`'s failure/degradation contract) — every unmatched or ambiguous reply re-prompts, never guesses (ticket AC 5), and the skill's own steps end once a resolved invocation has been presented (it does not loop back to re-report full state each time, only re-asks narrowly on ambiguity).

**Alternatives considered and rejected:**

- **Auto-invoke the resolved `hb-*` skill inline instead of printing it.** Rejected — no precedent in this codebase (every skill ends by telling the user to `/clear` then run the next command themselves), and it would silently break the `/clear`-between-steps context-freshness discipline that's a stated framework goal (`references/README.md:18,135`). See the Design decision callout above.
- **Delegate the archive-with-unexecuted-steps confirmation to `hb-task-archive` itself.** Rejected — `hb-task-archive`/`cmd_task_archive` (`task.py:120-140`) performs no such check today, and adding one there is an `hb-sdk`/existing-skill change explicitly out of scope for this step (task ticket's own out-of-scope list only permits consuming the existing `hb-sdk state`/`summarize` surface). `hb-flow` performs the check itself from data it already has.
- **A new `hb-sdk` subcommand that does the natural-language interpretation in Python.** Rejected — NL interpretation is model-layer work; the existing precedent (`ticket-loop-subflow.md` §D "Dispatch") already keeps semantic matching in the skill's own instructions, not in deterministic SDK code, and the ticket's out-of-scope list excludes further `hb-sdk` changes.

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
  interpret a natural-language reply and resolve it to the matching hb-* skill
  invocation — including calls-to-action other than the currently recommended one.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Read
---
```

- no `arguments:` field — mirrors `hb-status.md`/`hb-ticket-discuss.md`, which also take no formally-named single positional token; the optional trailing text is freeform, not a structured arg.
- `allowed-tools` matches `hb-status.md` exactly: read-only `hb-sdk` calls plus `Read` (for the `!`cat`` reference-file includes). No `Bash(git *)`, no `Write`/`Edit` — `hb-flow` makes no commits and writes no files (§0 facts-write-subflow scoping; no artifact of its own).

**Steps:**

1. **Help check** — identical to every other skill: if first argument is `help`/`--help`/`-h`, follow `references/skill-help.md`, stop.

2. **Gather state** — run, in this order:
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/hb-sdk state show --format md
   ${CLAUDE_SKILL_DIR}/scripts/hb-sdk state next-action --format md
   ```
   Capture stdout as `$LAST_ACTION` and `$NEXT_ACTIONS` respectively. If `state show` reports "No recorded state.", note that plainly rather than fabricating a last action. If `.hb/` is not initialized (`state next-action` reports the `not_initialized` stage), skip straight to reporting that and stop — there is nothing to route.

3. **Report** — print, in plain language:
   - Where things left off: derived from `$LAST_ACTION` (skill/task/step/outcome, or "no prior recorded action").
   - The recommended next action(s): render `$NEXT_ACTIONS` (one block per active task — this already satisfies ticket AC 6's "report next-action for each" without extra code, since `hb-sdk state next-action` already iterates every active task).

4. **Resolve intent** — take the freeform request, either from the initial invocation argument (if the user passed one directly, e.g. `/hb-flow archive this task instead`) or by asking "What would you like to do?" and awaiting the reply if none was passed. Match it against the **Action Registry** below using semantic match (not exact keywords), same dispatch discipline as `ticket-loop-subflow.md` §D:

   | Action | Target skill(s) | Invocation shape | Example phrasings |
   |---|---|---|---|
   | Plan task into steps | `hb-task-plan` | `/hb-task-plan <task_ref>` | "plan this task", "break it into steps" |
   | Add a step | `hb-task-step-add` | `/hb-task-step-add <task_ref>` | "add a step", "add another step" |
   | Plan a step | `hb-task-step-plan` | `/hb-task-step-plan <task_ref>/<step_n>` | "plan the next step", "let's plan it", "go back and re-plan step 2" |
   | Execute a step | `hb-task-step-execute` | `/hb-task-step-execute <task_ref>/<step_n>` | "execute this step", "run the plan" |
   | Start/continue review | `hb-task-step-review-address` (default) or `hb-task-step-review-init` (only if the user explicitly wants to just seed `review.md` without addressing yet) | `/hb-task-step-review-address <task_ref>/<step_n>` or `/hb-task-step-review-init <task_ref>/<step_n>` | "let's review", "review this step", "just create review.md" |
   | Move to the next step | (whatever `state next-action`'s `review_or_next`/`steps_complete` choices resolve to) | as printed in `$NEXT_ACTIONS`'s choices | "move on", "next step" |
   | Archive task | `hb-task-archive` | `/hb-task-archive <task_ref>` | "archive this task", "close it out" |
   | Unarchive task | `hb-task-unarchive` | `/hb-task-unarchive <task_ref>` | "unarchive it", "restore this task" |

   - On no confident match: ask a clarifying question, re-prompt (ticket AC 5) — do not guess.

5. **Resolve target task/step** — this is what makes AC 4 work ("any valid current state, not only the currently-recommended action"):
   - If the reply names a task/step ref explicitly (e.g. "step 2", "hb-014"), validate it exists via `hb-sdk task path <ref>` / `hb-sdk task step number <task_ref>/<n>` (reuses SDK per AC 4.3's "does not re-implement task/step traversal" — same principle applied here since this step is the direct extension point of that logic) rather than assuming it. Surface the SDK's error verbatim and re-prompt if it doesn't exist.
   - Otherwise, derive the target from data already gathered:
     - task-level actions (plan task, add step, archive, unarchive): if exactly one active task, use it; if more than one and none named, ask which (ticket AC 6 — never silently pick one; the last-recorded-state task from `$LAST_ACTION` may be offered as a suggested default in the question, not auto-selected).
     - "plan a step": the first step in `summarize`'s `steps` list with `has_ticket=true, has_plan=false`. If the first pending step has no ticket yet, say so (nothing to plan) rather than resolving to it anyway.
     - "execute a step": the first step with `has_plan=true, has_execution=false` (`next_pending_step` when it also has a plan).
     - "review": the first entry in `steps_needs_review`.
   - If, after this, no task/step target is unambiguous, ask a clarifying question (ticket AC 5) instead of guessing.

6. **Sanity-check archive** — only when the resolved action is Archive: read `steps_needs_work`/`steps_needs_review` for the target task from `hb-sdk summarize --format json`. If either is non-empty, ask for explicit confirmation naming which steps would be skipped, before presenting the archive invocation (§0's finding that `hb-task-archive` itself has no such guard — this check exists only in `hb-flow`).

7. **Present resolved invocation** — print the exact `/hb-<skill> <args>` string resolved in steps 4-6, and tell the user to `/clear` this conversation then run it (matching the exact phrasing convention every other skill's own "Prompt user" step already uses, e.g. `hb-task-archive.md:55-57`). Do not run it.

**Failure/degradation contract:**

- `.hb/` not initialized → report that and stop (mirrors `not_initialized` stage from `next_action.py:90-100`).
- No active tasks → report that and stop (mirrors `no_active_tasks` stage).
- Ambiguous or unmatched natural-language reply → clarifying question, re-prompt; never error, never guess (ticket AC 5).
- Named task/step ref that doesn't exist → surface the `hb-sdk` error verbatim, re-prompt.
- No commit, no `.hb/facts.md` write, no `hb-sdk state record` call — `hb-flow` performs no lifecycle action of its own; the downstream skill the user actually runs records its own state and does its own commit, exactly as it does today when run directly.

---

## 3. Integration / wiring

- No existing file is edited. `hb-flow.md` is a new, independent skill file that only *reads* via existing `hb-sdk` subcommands (`state show`, `state next-action`, `summarize`, `task path`, `task step number`) — all already shipped by step-1/step-2 and this repo's `main` history; none are modified.
- No build/entry-point/dependency-manifest wiring: skills are picked up by the installer's existing symlink mechanism (`install`) purely by filename under `skills/`; adding a new `.md` file there requires no registration step (confirmed by every prior step-add-a-skill task in this repo's history following the same one-file pattern).
- `references/references-toc.md` is **not** edited — `hb-flow.md` introduces no new shared reference/subflow file (its Action Registry lives inline, is used by no other skill, unlike `ticket-loop-subflow.md`'s registry which is a shared subflow by design).
- `references/README.md` (skills table, lifecycle diagram, "Getting started" walkthrough) is **not** updated — out of scope, see §8 (mirrors the ticket's own explicit exclusion of the analogous `hb-init` prompt update).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-flow.md` | **new** — router/presenter skill per §2. No other file changes. |

No dependency-manifest or lockfile effects — this step adds a markdown skill file only, no Python code.

---

## 5. Tests

N/A — this step adds no Python/executable code (`skills/hb-flow.md` is a markdown skill prompt, consumed by the AI harness, not by `pytest`). The existing `tests/skills/scripts/hb_sdk/` suite covers `hb-sdk` itself, which is unmodified by this step. Correctness is instead exercised by manual scenario walkthroughs in §6.

---

## 6. Verification (after implementation)

1. **Static checks stay green** (no Python changed by this step, but confirm no regression):
   ```bash
   uv run ruff check
   uv run ruff format --check
   ```
2. **Confirm the `hb-sdk` calls `hb-flow.md` depends on still behave as documented in §0**, against this repo's live `.hb/` state:
   ```bash
   ./skills/scripts/hb-sdk state show --format md
   ./skills/scripts/hb-sdk state next-action --format md
   ./skills/scripts/hb-sdk summarize --format json
   ```
   Confirm the shapes match §0's citations (per-task md bullets; JSON `invocation`/`choices` mutual-exclusivity; `steps_needs_work`/`steps_needs_review`/`next_pending_step` fields present).
3. **Frontmatter conformance** — diff `skills/hb-flow.md`'s frontmatter block against `skills/hb-status.md`'s (closest analog: read-only, no task_id arg) and confirm `name`/`description`/`allowed-tools` follow the same shape, `argument-hint` is present and correctly bracketed.
4. **Per-AC scenario walkthrough** (hand-traced against this repo's current multi-task `.hb/` state, since there is no automated skill-markdown harness):
   - No arguments, one active task at each lifecycle stage (`plan_step`, `plan_task`, `review_or_next`, `steps_complete`) → confirm §2 Step 3's report matches `state next-action`'s per-stage message (AC 2).
   - Multiple active tasks (this repo currently has ≥7) → confirm §2 Step 3 reports every one, not just the first (AC 6).
   - A reply naming an action *other than* the recommended one, with an explicit step number not currently pending (e.g. "re-plan step 0" on a task whose recommendation is to plan step 1) → confirm §2 Steps 4-5 resolve to `/hb-task-step-plan <ref>/0`, not the recommended step (AC 4).
   - A reply for "archive" on a task with unexecuted steps (e.g. `northwind/hb-002-harness-templating`, which has `total_steps: 0` today, or any task with a non-empty `steps_needs_work`) → confirm §2 Step 6 asks for confirmation before presenting the invocation (AC 4).
   - A vague reply ("do the thing") → confirm a clarifying question is asked, no invocation is guessed (AC 5).
   - A reply naming no task while ≥2 active tasks exist → confirm a clarifying question naming the candidates is asked (AC 5, AC 6).
5. **Invariant check**: every invocation string `hb-flow.md` can produce is validated against the target skill's own `argument-hint` (cross-read each of the 8 target skill files) — no row in §2's mapping table introduces a shape the target skill doesn't accept.
6. **Scope check**: `git status --short` shows only `skills/hb-flow.md` as new; no other tracked file modified.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (frontmatter, Help check step, Reference Files section via `references-toc.md` include) | Mirrors `hb-status.md` structure exactly. |
| 2.1 | §2 Step 2 | `hb-sdk state next-action --format md\|json`; no inline traversal/status logic. |
| 2.2 | §2 Steps 2-3 | Reports `state show`'s last-recorded action plus `state next-action`'s recommendation. |
| 3 | §2 Step 4 (Action Registry table) | Covers all 7 named call-to-actions plus "move to next step". |
| 4 | §2 Steps 5-6; §1 Alternatives | Resolves non-default targets via `hb-sdk` lookups; archive sanity check implemented in `hb-flow` itself (§0 finding: `hb-task-archive` has none). |
| 5 | §2 Step 4 (no-match), Step 5 (still-ambiguous) | Always re-prompts, never guesses. |
| 6 | §2 Step 3 | `state next-action --format md` already iterates every active task. |
| 7 | §2 Step 7; §1 Design decision | Presents the resolved invocation for the user to run; delegates actual execution, never reimplements target-skill steps inline. |

---

## 8. Out of scope (per ticket)

- Any change to the behavior of the skills `hb-flow` dispatches to (`hb-task-plan`, `hb-task-step-plan`, etc.) — invoked as-is, unmodified.
- Further `hb-sdk` changes — `hb-flow` only consumes the existing `state`/`summarize`/`task` surface.
- Updating `hb-init`'s "what to do next" prompt to mention `hb-flow`.
- Updating `references/README.md` (skills table, lifecycle diagram, "Getting started" walkthrough) to mention `hb-flow` — not required by any AC, same reasoning as the `hb-init` exclusion above; may be addressed later if desired.
- Auto-invoking the resolved downstream skill instead of printing it — see Design decision callout and §1 Alternatives.
- Adding an unexecuted-steps confirmation to `hb-task-archive` itself — the check is implemented only inside `hb-flow` (§0, §2 Step 6).
