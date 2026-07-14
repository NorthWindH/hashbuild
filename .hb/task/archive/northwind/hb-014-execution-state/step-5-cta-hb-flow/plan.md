# Step 5 Plan — Route all skill "Prompt user" CTAs through /hb-flow

This step rewrites the terminal "Prompt user" message in ten `hb-*` skill files so
each points the user at `/clear` + `/hb-flow` instead of hard-coding the specific
next `hb-*` command. Today, e.g. `hb-task-step-plan.md:83` tells the user to run
`/hb-task-step-execute <step_ref>` directly — a routing decision `/hb-flow`
(`skills/hb-flow.md`) now owns via its Action Registry and `hb-sdk state
next-action`. Ten call sites currently duplicate that routing logic in prose, and
can drift out of sync with it. Documentation-only change: no skill's control flow,
SDK behavior, or `hb-flow.md` itself changes — behavior change only, no new public
API, no non-`skills/*.md` file changes. The single externally observable effect:
after this step, every one of the ten "Prompt user" messages tells the user to
`/clear` then `/hb-flow`, and none of them names a different `hb-*` skill as the
primary next action.

Source ticket: `./ticket.md`. This is a standalone step (no prior step in this task
touches these files); it targets `skills/*.md` as they exist **now** — the
canonical source per the facts store (`skills/hb-*.md` is canonical; `~/.claude/skills/hb-*/`
is just the installed copy, so only `skills/*.md` needs editing here).

> **Design decision — how much of each message to replace.** AC2 requires
> "outcome-specific context" to survive (e.g. `hb-task-step-add.md`'s "Step added
> with ticket" vs. "Step added" split) while AC1/AC4 require the *hard-coded
> next-command portion* to become `/clear` + `/hb-flow` uniformly. Resolution:
> treat each message as (branch-specific lead sentence) + (routing tail). Only the
> routing tail — any clause that names a specific next `hb-*` skill/command as the
> thing to run next — is replaced with a single canonical tail: "`/clear` this
> conversation, then run `/hb-flow` to see what to do next." (matching the
> phrasing already shipped in step-4's `HB_FLOW_HOOK_COMMAND` `systemMessage`, so
> the hook nudge and the skill CTAs read consistently). Branch-specific lead
> sentences, non-CTA asides (e.g. `hb-init.md`'s `/hb-status` tip,
> `hb-task-step-review-address.md`'s "review is iterative, re-run this same
> command" note), and non-command instructions (e.g. "edit `ticket.md` first")
> are left untouched. See §2 for the exact per-file text and §7 for the AC
> mapping.

---

## 0. Current-state facts (verified during planning)

- Confirmed via `grep -n "^### .*Prompt user"` across the ten files (plus a manual
  check for `hb-task-step-review-init.md`, whose CTA lives under `### 5. Notify
  user`, not a `### Prompt user` heading — the ticket's line-number references
  have drifted from later edits, but all ten sites were located and read in full):

  | File | Heading (current) | CTA variant(s) |
  |---|---|---|
  | `skills/hb-task-plan.md` | `### 10. Prompt user` | single |
  | `skills/hb-init.md` | `### 4. Prompt user to create their first task` | single (+ unrelated `/hb-status` aside, untouched) |
  | `skills/hb-task-archive.md` | `### 4. Prompt user` | single |
  | `skills/hb-task-unarchive.md` | `### 4. Prompt user` | single |
  | `skills/hb-task-step-review-init.md` | `### 5. Notify user` | single (CTA is the 3rd of 3 paragraphs in the blockquote; first two are non-CTA instructions, untouched) |
  | `skills/hb-task-step-review-address.md` | `### 10. Prompt user` | single (leading "review is iterative" sentence is a non-CTA aside, untouched) |
  | `skills/hb-task-step-add.md` | `### 5. Prompt user` | two branches: "ticket was just written" vs. "all other modes" |
  | `skills/hb-task-step-execute.md` | `### 9. Prompt user` | single (message lists 3 alternative next commands; none is outcome-specific, all collapse to `/hb-flow`) |
  | `skills/hb-task-step-plan.md` | `### 8. Prompt user` | single |
  | `skills/hb-task-create.md` | `### 5. Prompt user` | two branches: "ticket was just written" vs. "all other modes" |

- `skills/hb-flow.md` itself contains no "Prompt user"-style hard-coded next-command
  CTA of this kind (confirmed by inspection — it *is* the routing target); AC3
  requires it stay unchanged and no edit to it is planned.
- No test in `tests/` asserts against the literal prose of any of these ten CTA
  messages (confirmed via `grep -rln` for their exact command substrings across
  `tests/`) — the only hits were unrelated matches inside
  `tests/skills/scripts/hb_sdk/test_hb_sdk_{state,next_action,summarize}.py`,
  which test `hb-sdk`'s own `next-action` output strings, a separate system. This
  step is prose-only with no automated-test blast radius.
- `~/.claude/skills/hb-*/` is the *installed* copy of `skills/*.md` (per facts
  store); this step edits only the canonical `skills/*.md` source, not the
  installed copy — consistent with how prior steps in this repo have operated.

### 0.1 Impact (before → after)

| File | Before (routing tail) | After (routing tail) |
|---|---|---|
| All ten (see §2 for full per-branch text) | Names a specific `hb-*` skill/command as the next step | `/clear` this conversation, then run `/hb-flow` to see what to do next. |

Purely textual/prose change to Markdown skill instruction files. No code,
schema, or CLI behavior changes. Every other sentence in each message (branch
lead-ins, non-CTA asides, non-command instructions) is preserved verbatim.

### 0.2 Non-regression proof

Purely additive/substitutive prose edit confined to `skills/*.md` "Prompt user"
(or equivalent) sections. No script, SDK command, test, or `hb-flow.md` routing
logic is touched, so there is no executable behavior to regress. The only risk is
losing outcome-specific context called out in AC2 (e.g. the `hb-task-step-add.md`
/ `hb-task-create.md` branch distinctions, or `hb-task-step-review-address.md`'s
"review is iterative" note) — §2 spells out the exact preserved text per file to
guard against that, and §6 step 4 diffs each file to confirm only the routing
tail changed.

---

## 1. Design overview

Single linear change, no ordered alternatives: for each of the ten files, locate
the existing "Prompt user"/"Notify user" blockquote, and replace only the clause(s)
that name a specific next `hb-*` skill/command with the canonical tail:

> `/clear` this conversation, then run `/hb-flow` to see what to do next.

Two files (`hb-task-step-add.md`, `hb-task-create.md`) have two branches each
(interactive-ticket-written vs. other modes); apply the substitution
independently to each branch's routing tail, preserving each branch's distinct
lead sentence ("Step added with ticket." vs. "Step added.", etc.) per AC2.

**Alternatives considered and rejected:**
- *Point each message at the specific `hb-flow` Action Registry entry that applies
  next* (e.g. "run `/hb-flow` to plan the next step") — rejected: re-derives
  `hb-flow`'s own routing logic in prose again, exactly the duplication this step
  removes; `hb-flow` already reports the right next action once invoked.
  Also, `hb-flow` is used to invoke actions besides simply the currently
  recommended one — a message that could pigeonhole the user towards a specific
  action isn't accurate.
- *Drop the `/clear` instruction and just say "run `/hb-flow`"* — rejected: every
  existing CTA pairs the command with `/clear` first (context hygiene between
  skill invocations, matches the step-4 hook nudge pattern); dropping it would be
  an unrelated behavior regression, not a pure text substitution.
- *Edit `hb-flow.md` to special-case messaging when invoked right after another
  skill* — rejected: out of scope per AC3 and the ticket's explicit "Out of scope"
  section; `hb-flow.md`'s Action Registry already covers every transition being
  removed from the other ten skills.

---

## 2. Per-file CTA text — before/after

For each file, only the shown blockquote text changes; all surrounding structure
(headings, step numbering, later "Record execution state" sections) is untouched.

### `skills/hb-task-plan.md` — `### 10. Prompt user`

Before:
```
> Steps ready. `/clear` this conversation, then run `/hb-task-step-plan <name>/0` to create the implementation plan for the first step.
```
After:
```
> Steps ready. `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-init.md` — `### 4. Prompt user to create their first task`

Before (first paragraph only — the `/hb-status` paragraph and the ticket-file
explanation that follow are untouched):
```
> Hashbuild is ready. To start your first task, `/clear` this conversation to free context, then run `/hb-task-create` with the task name and an optional ticket file.
```
After:
```
> Hashbuild is ready. To start your first task, `/clear` this conversation to free context, then run `/hb-flow` to get started.
```

### `skills/hb-task-archive.md` — `### 4. Prompt user`

Before:
```
> Task archived. `/clear` this conversation, then run `/hb-status` to see remaining active tasks and decide what to work on next, or `/hb-task-create` to start a new task.
```
After:
```
> Task archived. `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-task-unarchive.md` — `### 4. Prompt user`

Before:
```
> Task restored. `/clear` this conversation, then run `/hb-status` to see active tasks or `/hb-task-step-add` to continue working on it.
```
After:
```
> Task restored. `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-task-step-review-init.md` — `### 5. Notify user`

Before (3rd paragraph of the blockquote only — the first two, about `review.md`
structure and `TODO REVIEW` comment scanning, are untouched):
```
> When done, `/clear` this conversation, then run `/hb-task-step-review-address <step_ref>` to work through the review items.
```
After:
```
> When done, `/clear` this conversation, then run `/hb-flow` to work through the review items.
```

### `skills/hb-task-step-review-address.md` — `### 10. Prompt user`

Before:
```
> Review is iterative — you can add more concerns to `review.md` or add `TODO REVIEW` comments (committed or uncommitted) and re-run `/hb-task-step-review-address <step_ref>` at any time. When the step is fully reviewed, `/clear` this conversation, then: to continue with more steps, run `/hb-task-step-add <name>` then `/hb-task-step-plan`. When all steps are done, run `/hb-task-archive <name>` to close the task.
```
After (leading "review is iterative" sentence preserved verbatim — it describes
re-running *this same* skill, not a next-step routing decision; only the trailing
next-step clause is replaced):
```
> Review is iterative — you can add more concerns to `review.md` or add `TODO REVIEW` comments (committed or uncommitted) and re-run `/hb-task-step-review-address <step_ref>` at any time. When the step is fully reviewed, `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-task-step-add.md` — `### 5. Prompt user`

Before:
```
**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Step added with ticket. `/clear` this conversation, then run `/hb-task-step-plan <step_ref>` to create the implementation plan.

**All other modes (skeleton-only or `--ticket` supplied):**

> Step added. `/clear` this conversation, then: if the step ticket is ready, run `/hb-task-step-plan <step_ref>` to create the implementation plan. If the ticket still needs its acceptance criteria filled in, edit `ticket.md` in the step folder first.
```
After (both lead sentences — "Step added with ticket." vs. "Step added." —
preserved per AC2; the "edit `ticket.md` first" branch is not a next-skill
pointer, so it is preserved too):
```
**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Step added with ticket. `/clear` this conversation, then run `/hb-flow` to see what to do next.

**All other modes (skeleton-only or `--ticket` supplied):**

> Step added. `/clear` this conversation, then: if the step ticket is ready, run `/hb-flow` to see what to do next. If the ticket still needs its acceptance criteria filled in, edit `ticket.md` in the step folder first.
```

### `skills/hb-task-step-execute.md` — `### 9. Prompt user`

Before:
```
> Step executed. `/clear` this conversation, then: to start a code review, either run `/hb-task-step-review-address <step_ref>` directly (if you added `TODO REVIEW` comments, committed or uncommitted), or run `/hb-task-step-review-init <step_ref>` to create `review.md` and fill in concerns manually. To move to the next step, run `/hb-task-step-add <name>` then `/hb-task-step-plan`. When all steps are done, run `/hb-task-archive <name>` to close the task.
```
After (no outcome-specific branch exists here — the three listed alternatives are
all just different next-step options, not distinguished by what execution
produced — so the whole tail collapses):
```
> Step executed. `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-task-step-plan.md` — `### 8. Prompt user`

Before:
```
> Plan ready. `/clear` this conversation, then run `/hb-task-step-execute <step_ref>` to carry out the plan.
```
After:
```
> Plan ready. `/clear` this conversation, then run `/hb-flow` to see what to do next.
```

### `skills/hb-task-create.md` — `### 5. Prompt user`

Before:
```
**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Task and ticket created. `/clear` this conversation, then run `/hb-task-plan <name>` to analyze acceptance criteria and create step tickets. When steps are ready, run `/hb-task-step-plan <name/step-n>` for each step.

**All other modes (skeleton-only or `--ticket` supplied):**

> Task created. `/clear` this conversation, then: if you have a task `ticket.md`, run `/hb-task-plan <name>` to analyze acceptance criteria and create steps to cover them. If not, write a `ticket.md` first (Background, Acceptance Criteria, Out of scope), then run `/hb-task-plan`. To add the first step manually instead, run `/hb-task-step-add <name>`.
```
After (both lead sentences — "Task and ticket created." vs. "Task created." —
preserved per AC2; the "write a `ticket.md` first" instruction is preserved as
it's not a next-skill pointer; the "add the first step manually instead" clause
is dropped as it's a redundant alternate routing path `/hb-flow`'s Action
Registry already covers):
```
**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Task and ticket created. `/clear` this conversation, then run `/hb-flow` to see what to do next.

**All other modes (skeleton-only or `--ticket` supplied):**

> Task created. `/clear` this conversation, then: if you have a task `ticket.md`, run `/hb-flow` to see what to do next. If not, write a `ticket.md` first (Background, Acceptance Criteria, Out of scope), then run `/hb-flow`.
```

---

## 3. Integration / wiring

No wiring changes. Nothing calls into or depends on the exact prose of these
messages programmatically (confirmed in §0) — they are surfaced to the user
verbatim by whichever agent is executing the skill's Markdown instructions, so no
build step, script, config, or entry point changes.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-plan.md` | **edit** — `### 10. Prompt user` blockquote tail only |
| `skills/hb-init.md` | **edit** — `### 4. Prompt user to create their first task`, first paragraph only; `/hb-status` paragraph and ticket-file explanation untouched |
| `skills/hb-task-archive.md` | **edit** — `### 4. Prompt user` blockquote tail only |
| `skills/hb-task-unarchive.md` | **edit** — `### 4. Prompt user` blockquote tail only |
| `skills/hb-task-step-review-init.md` | **edit** — `### 5. Notify user`, 3rd blockquote paragraph only; first two paragraphs untouched |
| `skills/hb-task-step-review-address.md` | **edit** — `### 10. Prompt user` blockquote, trailing clause only; leading "review is iterative" sentence untouched |
| `skills/hb-task-step-add.md` | **edit** — `### 5. Prompt user`, both branch blockquotes' tails; lead sentences and "edit `ticket.md`" instruction untouched |
| `skills/hb-task-step-execute.md` | **edit** — `### 9. Prompt user` blockquote, full replacement (no outcome-specific text to preserve) |
| `skills/hb-task-step-plan.md` | **edit** — `### 8. Prompt user` blockquote tail only |
| `skills/hb-task-create.md` | **edit** — `### 5. Prompt user`, both branch blockquotes' tails; lead sentences and "write a `ticket.md` first" instruction untouched |

No dependency-manifest, lockfile, or non-`skills/*.md` file changes.
`skills/hb-flow.md` is explicitly **not** in this table (AC3).

---

## 5. Tests

N/A — confirmed in §0 that no test in `tests/` asserts against the literal prose
of any of these ten messages; this is a documentation/prompt-text-only change with
no executable surface to unit-test. Verification is by direct inspection (§6).

---

## 6. Verification (after implementation)

1. **Scope check — only the ten intended files changed, plus `.hb/` bookkeeping:**
   ```bash
   git status --short
   ```
   Expect exactly the ten `skills/*.md` files listed in §4 as modified (`M`),
   plus this step's own `execution-*.md`/state files under `.hb/` once execution
   records them. `skills/hb-flow.md` must **not** appear.

2. **No hard-coded next-skill command remains in any of the ten CTA sites:**
   ```bash
   grep -n "run \`/hb-task-" skills/hb-task-plan.md skills/hb-init.md \
     skills/hb-task-archive.md skills/hb-task-unarchive.md \
     skills/hb-task-step-review-init.md skills/hb-task-step-review-address.md \
     skills/hb-task-step-add.md skills/hb-task-step-execute.md \
     skills/hb-task-step-plan.md skills/hb-task-create.md
   ```
   Expect zero matches inside each file's CTA blockquote (the "Prompt user"/"Notify
   user" section) — any surviving match must be outside that section (there are
   none expected; grep across the whole file is a deliberately strict check).

3. **`/hb-flow` now appears in the CTA of all ten files:**
   ```bash
   grep -c "run \`/hb-flow\`" skills/hb-task-plan.md skills/hb-init.md \
     skills/hb-task-archive.md skills/hb-task-unarchive.md \
     skills/hb-task-step-review-init.md skills/hb-task-step-review-address.md \
     skills/hb-task-step-add.md skills/hb-task-step-execute.md \
     skills/hb-task-step-plan.md skills/hb-task-create.md
   ```
   Expect `1` for every file except `hb-task-step-add.md` and `hb-task-create.md`,
   which expect `2` (one per branch).

4. **Per-file diff review** — for each of the ten files, `git diff -- <file>` and
   confirm the diff touches only the lines shown in §2's "Before"/"After" blocks
   (per AC2: lead sentences, non-CTA asides, and non-command instructions must be
   byte-identical before/after).

5. **`hb-flow.md` untouched (AC3):**
   ```bash
   git diff --stat -- skills/hb-flow.md
   ```
   Expect no output.

6. **Lint/format gates** (per facts store convention):
   ```bash
   uv run ruff check
   uv run ruff format --check
   ```
   Expect clean — these files are Markdown so this is a no-op sanity check that
   the edit didn't accidentally touch tracked Python.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (all ten files), §6 step 3 | Every listed CTA rewritten to `/clear` + `/hb-flow` |
| 2 | §2 (`hb-task-step-add.md`, `hb-task-create.md` branch splits; `hb-task-step-review-address.md`'s "review is iterative" note), §6 step 4 | Outcome-specific lead sentences and asides preserved verbatim |
| 3 | §1, §4 (explicit exclusion), §6 step 5 | `hb-flow.md` not edited |
| 4 | §2, §6 steps 2–3 | No remaining hard-coded `hb-*` command as primary CTA in any of the ten files |

---

## 8. Out of scope (per ticket)

- Changing `hb-flow.md`'s own resolution/routing logic (Action Registry, `hb-sdk
  state next-action` output format) — untouched, per AC3.
- Any change to skills outside the ten "Prompt user" call-to-action sites listed
  in the ticket's Background (e.g. `hb-init.md`'s `/hb-status` aside,
  `hb-task-step-review-init.md`'s first two blockquote paragraphs, and
  `hb-task-step-add.md`/`hb-task-create.md`'s non-CTA instructional clauses are
  all left as-is).
- Editing the installed copy at `~/.claude/skills/hb-*/` — this step edits only
  the canonical `skills/*.md` source (per facts store).
- Updating `HB_FLOW_HOOK_COMMAND` or any other step-4 artifact — already shipped
  and unrelated to these ten skill-file CTAs.
