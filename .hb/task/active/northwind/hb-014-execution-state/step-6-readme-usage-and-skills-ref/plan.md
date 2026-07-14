# Step 6 Plan — README usage guidance + skills reference sync

This step updates `README.md` only: it adds primary usage guidance recommending
`/hb-init` then `/hb-flow` as the standard entry point, and brings the Skills
table in sync with the skills actually present in `skills/*.md`. No code,
scripts, or other skill files change.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-flow` skill
(`skills/hb-flow.md`, installed at `~/.claude/skills/hb-flow/`) from earlier
steps of this task, which is the orchestrator this step tells users to reach
for. This plan targets `README.md` as it exists now (280 lines, read in full
during planning).

> **Design decision — keep the manual step-by-step walkthrough, add `hb-flow`
> as the recommended front door.** The existing "Getting started" section
> (README.md:84–203) walks through each `hb-*` skill manually and never
> mentions `hb-flow`, even though `hb-flow` (shipped in earlier steps of this
> task) is meant to be the standard way users navigate the lifecycle day to
> day. Rather than rewriting Getting started around `hb-flow` and losing the
> documentation of what each primitive skill does, this plan keeps the manual
> walkthrough intact (it's the reference for what's happening under the hood)
> and adds `hb-flow` guidance in two places: the Skills table (§2) and a new
> lead-in at the top of Getting started (§3) that tells the user to run
> `/hb-init` then `/hb-flow` and let it drive the rest, with the numbered
> steps kept as the "what's actually happening" reference. This satisfies AC1
> without discarding documentation value. See §7 for AC traceability.

---

## 0. Current-state facts (verified during planning)

- `README.md` (280 lines) has a `## Skills` table at lines 66–81 listing 11
  skills, and a `## Getting started` section at lines 84–203 with a numbered
  1–6 walkthrough plus an "Unarchive a task" and "Check status at any time"
  subsection. Neither mentions `/hb-flow` anywhere in the file (confirmed:
  `grep -n hb-flow README.md` — no match).
- `skills/*.md` on disk (13 files, the canonical source per the facts store)
  vs. the README Skills table (11 rows) — diffing the two:

  | Skill file | In README table? |
  |---|---|
  | `hb-flow.md` | **missing** |
  | `hb-init.md` | present |
  | `hb-status.md` | present |
  | `hb-task-archive.md` | present |
  | `hb-task-create.md` | present |
  | `hb-task-plan.md` | present |
  | `hb-task-step-add.md` | present |
  | `hb-task-step-execute.md` | present |
  | `hb-task-step-plan.md` | present |
  | `hb-task-step-review-address.md` | present |
  | `hb-task-step-review-init.md` | present |
  | `hb-task-unarchive.md` | present |
  | `hb-ticket-discuss.md` | **missing** |

  Two skills are missing from the table: `hb-flow` and `hb-ticket-discuss`.
- Each skill file's frontmatter `description:` field gives the one-line
  summary to source the new table rows from (verified via
  `head -20 skills/hb-flow.md` and `skills/hb-ticket-discuss.md`):
  - `hb-flow`: "Report where the active task/step left off and the
    recommended next action, then interpret a natural-language reply,
    confirm the resolved hb-* skill invocation with the user, and invoke it
    directly — including calls-to-action other than the currently
    recommended one."
  - `hb-ticket-discuss`: "Run a persistent, multi-turn loop for drafting
    standalone tickets (not attached to any task or step). Holds any number
    of tickets in in-conversation context and, each iteration, presents a
    menu of next actions (e.g. describe, load, exit) selectable via natural
    language. Makes no .hb/ writes."
- `hb-flow`'s own argument-hint is `[--help] [<natural language request>]`
  (`skills/hb-flow.md:2`) — its invocation form in the README must match.
- `hb-ticket-discuss` is standalone (no task/step ref, not part of the
  create→plan→step lifecycle) — it belongs in the Skills table but not in the
  numbered Getting started lifecycle walkthrough, which is scoped to the
  task/step flow.

### 0.1 Impact (before → after)

| Item | Before | After |
|---|---|---|
| Skills table row count | 11 | 13 |
| `hb-flow` documented | not mentioned anywhere | own table row + named as standard entry point in Getting started intro |
| `hb-ticket-discuss` documented | not mentioned anywhere | own table row |
| Getting started intro | starts directly at "1. Initialize your project" | new short lead-in before step 1 recommending `/hb-init` → `/hb-flow` |

Purely additive: existing rows, existing numbered steps, and all other
sections (Installation, Lifecycle diagram, File structure) are untouched.

### 0.2 Non-regression proof

Additive-only change to a Markdown file — no code, no scripts, no tests to
regress. The only risk is documentation drift (adding an inaccurate skill
description or breaking Markdown table formatting), guarded by copying
descriptions verbatim from each skill's own frontmatter (§0) and by the
verification table render check in §6.

---

## 1. Design overview

Two independent additive edits to `README.md`, both documentation-only:

1. **Skills table** (§2): add two rows, sourced from each skill's frontmatter
   `description:` (first sentence, trimmed to match the table's existing
   one-line style).
2. **Getting started lead-in** (§2): insert a short paragraph + code block
   before the existing "### 1. Initialize your project" subsection,
   recommending `/hb-init` then `/hb-flow` as the standard entry point, and
   explicitly framing the numbered steps that follow as what `/hb-flow` walks
   the user through under the hood.

**Alternatives considered and rejected:**
- *Rewrite Getting started entirely around `/hb-flow`, removing the manual
  numbered steps* — rejected: loses the per-skill documentation value (what
  each command does, its exact args) that the numbered walkthrough currently
  provides, and the ticket only asks to *add* the `hb-init` → `hb-flow`
  recommendation, not restructure existing content.
- *Add `hb-flow` only to the Skills table, skip the Getting started lead-in*
  — rejected: fails AC1, which explicitly requires "primary usage guidance"
  recommending the `hb-init` → `hb-flow` sequence, not just a table entry.

---

## 2. File-by-file changes

| File | Change |
|---|---|
| `README.md` | **edit** — (a) add `hb-flow` and `hb-ticket-discuss` rows to the `## Skills` table (lines 66–81); (b) insert a short lead-in paragraph + fenced command block immediately before `### 1. Initialize your project` (line 86) recommending `/hb-init` then `/hb-flow`. Everything else in the file — Installation, Lifecycle diagram, File structure, the existing numbered steps 1–6 — stays untouched. |

No other files change (no `skills/*.md`, no scripts, no `.hb/` files besides
this step's own `plan.md` and, conditionally, `.hb/facts.md`).

### 2.1 Skills table — new rows

Insert alphabetically is not the existing convention (table is lifecycle-
ordered); place `hb-flow` first (it's the entry point) and `hb-ticket-discuss`
last (it's the standalone, out-of-lifecycle skill):

```markdown
| `/hb-flow`                     | Report state and recommended next action, then route to the right skill from a natural-language reply |
```
at the top of the table (immediately after the header/separator, before
`/hb-init`), and:

```markdown
| `/hb-ticket-discuss`           | Draft standalone tickets in a multi-turn loop (not attached to a task/step) |
```
at the bottom of the table (after `/hb-task-unarchive`).

### 2.2 Getting started lead-in

Insert immediately before `### 1. Initialize your project` (currently
README.md:86):

```markdown
The fastest way to work with hashbuild day to day: run `/hb-init` once, then
run `/hb-flow` whenever you're not sure what to do next — it reports where
things left off and routes you to the right skill from a plain-language
reply. The steps below spell out what `/hb-flow` is doing under the hood, and
remain the reference for each skill's exact arguments.
```

The existing "### 1. Initialize your project" heading and all subsequent
numbered steps are unchanged.

---

## 3. Tests

Documentation-only change — no test suite applies. Verification is manual
inspection (§6): the file renders as valid Markdown, the new table rows match
each skill's real frontmatter description, and no existing content was
altered.

---

## 4. Verification (after implementation)

1. `grep -n "hb-flow\|hb-ticket-discuss" README.md` — confirms both skills
   now appear (table row) and `hb-flow` also appears in the new Getting
   started lead-in.
2. Render the Skills table (e.g. `sed -n '66,83p' README.md`) and visually
   confirm 13 data rows, valid pipe-table syntax, and that `hb-flow`'s row
   sits first and `hb-ticket-discuss`'s row sits last.
3. `git diff README.md` — confirm only the two additive hunks from §2 appear;
   no other line in the file changed.
4. **AC1 check**: confirm the new lead-in paragraph (§2.2) explicitly names
   `/hb-init` first and `/hb-flow` second, and frames `/hb-flow` as the
   standard/day-to-day entry point.
5. **AC2 check**: confirm every file in `skills/*.md` has a corresponding row
   in the Skills table (`ls skills/*.md` vs. table row count — 13 vs. 13).

---

## 5. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.2 | New lead-in before "### 1. Initialize your project" names `/hb-init` then `/hb-flow` as the standard entry point |
| 2 | §2.1 | Adds the two missing rows (`hb-flow`, `hb-ticket-discuss`) so the table matches `skills/*.md` |

---

## 6. Out of scope (per ticket)

- Rewriting or removing the existing numbered Getting started walkthrough
  (steps 1–6, Unarchive, Check status) — kept as-is per the design decision
  in the header.
- Any change to `skills/*.md`, install scripts, or `.hb/` behavior.
- Adding `hb-ticket-discuss` to the numbered lifecycle walkthrough or Lifecycle
  diagram — it's a standalone skill outside that flow (§0).
