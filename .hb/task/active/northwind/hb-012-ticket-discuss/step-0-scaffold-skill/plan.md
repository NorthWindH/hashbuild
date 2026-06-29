# Step 0 Plan — Scaffold `hb-ticket-discuss` skill (generation only)

Today there is no way to produce a hashbuild-shaped `ticket.md` without also
materializing a task or step folder: the only two entry points to the interactive
ticket flow are `hb-task-create` and `hb-task-step-add`, and both end by calling
`hb-sdk task ...`, which writes into `.hb/task/active/...`. The motivating case is a
user who wants to draft a ticket to paste into Jira (or hand off elsewhere) **without**
creating any hashbuild bookkeeping — that path does not exist. This step scaffolds a
new sibling skill, `hb-ticket-discuss`, that runs the same interactive flow against a
scratch path and emits the result to stdout. Scope boundary: **generation only** — no
Jira/Atlassian integration (deferred to step 1), no changes to the shared subflow or
its existing callers. Once this lands, `/hb-ticket-discuss` produces a standalone
`ticket.md` at a scratch path and prints it for copy-paste, touching nothing under `.hb/`.

Source ticket: `./ticket.md`. This is the first step of `hb-012-ticket-discuss`; it
builds on the **shipped** shared subflow at `skills/references/interactive-ticket-subflow.md`
(reused today by `hb-task-create` and `hb-task-step-add`). This plan targets the skills
tree as it exists **now**.

> **Design decision — reuse the subflow standalone, drop the SDK/commit machinery.**
> The two sibling skills wrap the interactive subflow in (a) flag-precedence logic for
> `--ticket` / `--no-interactive`, (b) an `hb-sdk task ...` call that creates a folder and
> reports a *permanent* `ticket.md` path, and (c) a git commit that stages that permanent
> path. This skill must produce a **standalone** ticket (AC 5, 6), so it keeps only the
> subflow and deliberately omits (a), (b), and (c): it drives the subflow directly with
> `$TARGET_PATH` = a scratch path, makes **no** `hb-sdk task` calls, and does **not** commit
> (there is no repo artifact to commit — the ticket lives only at the scratch path). The
> single guard that makes this correct: the subflow "contains no side effects (no commit,
> no SDK calls, no user notification beyond the prompt itself)"
> (`interactive-ticket-subflow.md:1-2`), so invoking it in isolation is safe and complete.
> See §1 (design) and §7 (AC traceability).

---

## 0. Current-state facts (verified during planning)

All facts below were confirmed by reading the live files, not assumed.

- **The interactive flow is already a standalone, side-effect-free subflow.**
  `skills/references/interactive-ticket-subflow.md` declares its caller contract
  (`$TARGET_PATH`, `$TICKET_SUPPLIED`, `$NO_INTERACTIVE` — lines 5-9), guards on the two
  flags (Section A, lines 11-15), prompts (Section B), transforms via
  `ticket-template.md` (Section C), and writes to `$TARGET_PATH/ticket.md` (Section D,
  lines 52-73). It performs **no** SDK call or commit (stated at lines 1-2). → This is the
  chokepoint this step reuses; blast radius of reusing it = zero (read-only reference).

- **Both existing callers drive the subflow with `$TARGET_PATH = /tmp`.**
  `hb-task-create.md:48-56` and `hb-task-step-add.md:48-57` both set `$TARGET_PATH = /tmp`,
  inject the subflow with `$TICKET_SUPPLIED=false` / `$NO_INTERACTIVE=false`, then set
  `$WRITTEN_TICKET = /tmp/ticket.md`. → This skill mirrors that exact invocation but stops
  *before* the SDK/commit steps the siblings perform next.

- **Sibling frontmatter shape is uniform.** `hb-task-create.md:1-10` and
  `hb-task-step-add.md:1-10` each have: `name`, `argument-hint`, `arguments`,
  a folded `description:` whose first line is the `/<skill> [--help] ...` usage string, and
  an `allowed-tools:` line of the form
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)`.
  → This step's frontmatter copies that shape and **trims** the two tool grants it does not
  use (`hb-sdk` and `git`), keeping the `/tmp` + `/private/tmp` Write/Read/Edit grants the
  subflow needs.

- **Sibling body shape is uniform.** Both have, in order: an H1 + one-line summary, a
  `## Inputs` table, a `## Reference Files` section that is a single `` !`cat
  ${CLAUDE_SKILL_DIR}/references/references-toc.md` `` injection, and numbered `## Steps`
  whose **Step 1 is always the help check** delegating to `references/skill-help.md`
  (`hb-task-create.md:32-34`, `hb-task-step-add.md:33-35`). → This step copies that body
  skeleton.

- **The help handler stops the skill.** `references/skill-help.md:41` ("After printing,
  stop — do not execute the skill's normal steps") guarantees AC 8 once Step 1 delegates
  to it.

### 0.1 Impact (before → after)

| Surface | Before | After |
|---|---|---|
| `skills/hb-ticket-discuss.md` | does not exist | new skill file present |
| Standalone ticket generation | impossible without creating a task/step folder | `/hb-ticket-discuss` produces a ticket at a scratch path + stdout, no `.hb/` writes |
| `interactive-ticket-subflow.md` and its two existing callers | as-is | **unchanged** |

This step is **purely additive**: one new file, no edits to existing files.

### 0.2 Non-regression proof / risk

Purely additive — a single new skill file. No existing file is edited, so no existing
behavior (the two sibling skills, the shared subflow, the SDK, or any commit path) can
regress. The only "risk" is authoring correctness of the new file, verified manually in §6.

---

## 1. Design overview

Single linear skill, modeled on the siblings but with the SDK/commit tail removed:

| # | Step | Source it mirrors / reuses | New? |
|---|---|---|---|
| 1 | Help check → `references/skill-help.md`, stop | identical to sibling Step 1 | reuse |
| 2 | Set `$TARGET_PATH` = scratch (`/tmp`); inject `interactive-ticket-subflow.md` with `$TICKET_SUPPLIED=false`, `$NO_INTERACTIVE=false` | sibling Step 2 case 3 (a–c), **minus** SDK/`$WRITTEN_TICKET` handoff | reuse |
| 3 | Emit the generated `/tmp/ticket.md` content to stdout (copy-paste output) | new — no sibling does this | **new** |
| 4 | Prompt user (standalone ticket ready; note Jira push is step 1) | analogous to sibling Step 5 prompt | new wording |

```
control flow:  help? ──yes──▶ print help, STOP
                 │no
                 ▼
            $TARGET_PATH=/tmp ──▶ interactive-ticket-subflow (prompt→transform→write /tmp/ticket.md)
                 ▼
            read /tmp/ticket.md ──▶ print to stdout ──▶ prompt next-step (Jira = step 1)
```

No `hb-sdk task` call anywhere; no commit; no task/step folder created.

**Alternatives considered and rejected:**
- *Add a `--standalone` flag to `hb-task-create` instead of a new skill* — rejected: the
  ticket scopes a distinct user-facing skill (`hb-ticket-discuss`), and overloading
  `hb-task-create` would entangle standalone generation with folder creation and break the
  "no `.hb/` writes" invariant the rest of `hb-012` depends on.
- *Duplicate the prompt/transform/write logic inline* — rejected: AC 5 explicitly requires
  *referencing* the shared subflow, not duplicating it.
- *Keep the `--ticket` / `--no-interactive` flag-precedence block from the siblings* —
  rejected: those flags exist to feed an SDK that this skill doesn't call; for a
  generation-only interactive skill they add surface with no behavior. Kept minimal
  (`--help` only) for this step.

---

## 2. `skills/hb-ticket-discuss.md` — specification

A single new skill file. Exact shape:

**Frontmatter** (mirrors `hb-task-create.md:1-10`, trimmed grants):

```yaml
---
name: hb-ticket-discuss
argument-hint: "[--help]"
description: >
  /hb-ticket-discuss [--help]

  Run hashbuild's interactive ticket-creation flow to produce a standalone ticket
  (not attached to any task or step) and print it for copy-paste. Makes no .hb/ writes.
allowed-tools: Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)
---
```

- **`name`** — `hb-ticket-discuss` (matches the file basename, like every sibling).
- **`argument-hint`** — `"[--help]"`; this step exposes no positional/other flags.
- **`description`** — folded scalar whose **first line is the usage string** beginning
  `/hb-ticket-discuss [--help]` (satisfies AC 2; same pattern as `hb-task-create.md:5-8`).
- **`allowed-tools`** — copies the siblings' `Write`/`Read`/`Edit` grants for `//tmp/*` and
  `//private/tmp/*` (the subflow's write target + reading the result back for stdout) and
  **omits** `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` and `Bash(git *)` because this skill
  makes no SDK call and no commit (enforces AC 6 at the permission layer).

**Body** (mirrors sibling structure exactly):

- `# hb-ticket-discuss` + one-line summary sentence.
- `## Inputs` table — single row: `help`, `--help`, `-h` → "Print help and exit."
- `## Reference Files` — the single injection `` !`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md` ``
  (identical to `hb-task-create.md:28`).
- `## Steps` with the four numbered steps from §1:

  **### 1. Help check** — verbatim sibling pattern:
  "If the first argument is `help`, `--help`, or `-h`: follow
  `[${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md)`. Stop."

  **### 2. Generate standalone ticket** —
  - Set `$TARGET_PATH` = `/tmp` (scratch; the generated ticket is standalone — it lives only
    here and is never moved into `.hb/`).
  - Follow `[${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](references/interactive-ticket-subflow.md)`
    with `$TARGET_PATH` = `/tmp`, `$TICKET_SUPPLIED` = `false`, `$NO_INTERACTIVE` = `false`.
  - The subflow writes `ticket.md` to `/tmp/ticket.md`; set `$WRITTEN_TICKET` = `/tmp/ticket.md`.

  **### 3. Emit ticket** —
  - Read `$WRITTEN_TICKET` and print its full content to stdout inside a fenced block so the
    user can copy-paste it. State that this is the standalone ticket (no `.hb/` folder was
    created) and the fallback output path step 1 will keep when no Jira MCP is available.

  **### 4. Prompt user** —
  - Tell the user the standalone ticket is ready above; note that pushing it to Jira will be
    added by step 1 of this task. (No `/clear` + next-`hb-*`-skill handoff, since nothing was
    written to `.hb/`.)

- `## Output` section — one line: "Print the generated ticket content and the scratch path.
  If any step fails, surface the error verbatim to the caller."

**Failure / degradation contract:** the subflow owns prompt/transform/write failures. If the
user provides no usable input, the subflow's transform rules still produce the three-section
skeleton; the skill prints whatever the subflow wrote.

---

## 3. Integration / wiring

- **No call sites edited.** This is a new, self-contained skill file. The shared subflow is
  *referenced* (a markdown link, exactly as the siblings reference it), not modified.
- **No SDK / no git wiring.** Unlike the siblings, this skill calls neither
  `hb-sdk task ...` nor `git ...`; correspondingly its `allowed-tools` omits both grants.
- **No registration step.** Per the ticket's out-of-scope, the skill is *only* the file;
  nothing registers it beyond its existence in `skills/`.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-ticket-discuss.md` | **new** — the scaffold skill (frontmatter + Inputs + Reference Files + 4 Steps + Output) per §2 |

No other files change. `interactive-ticket-subflow.md`, `hb-task-create.md`,
`hb-task-step-add.md`, `references-toc.md`, `skill-help.md`, and everything under
`scripts/` and `.hb/` remain **untouched**. No dependency manifest or lockfile exists/changes.

---

## 5. Verification artifacts (no automated test framework)

Skills are markdown procedures; there is no unit-test harness in this repo. Verification is
the manual / shell-checkable sequence in §6. The "test cases" are:

- **Help path** — `/hb-ticket-discuss --help` prints help and stops, generating nothing (AC 4, 8).
- **Happy path** — `/hb-ticket-discuss` (no args) runs the subflow, writes `/tmp/ticket.md`,
  and prints it (AC 1–3, 5, 7).
- **Standalone invariant** — after a happy-path run, `.hb/` has no new task/step folder and
  no new `ticket.md` (AC 6).
- **Structure conformance** — the new file's frontmatter and body match the sibling shape
  (AC 2, 3), checkable by diffing section headings against a sibling.

---

## 6. Verification (after implementation)

1. **File exists and parses as a skill.** `test -f skills/hb-ticket-discuss.md` and confirm the
   YAML frontmatter has `name: hb-ticket-discuss`, an `argument-hint`, a `description` whose
   first content line begins `/hb-ticket-discuss [--help]`, and an `allowed-tools` line
   (AC 1, 2).
2. **Structure conformance.** `grep -nE '^## (Inputs|Reference Files|Steps)' skills/hb-ticket-discuss.md`
   shows all three; `grep -n '### 1. Help check' skills/hb-ticket-discuss.md` confirms Step 1 is
   the help check; the Reference Files section contains the
   `` !`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md` `` injection (AC 3, 4).
3. **Reuse, not duplication.** `grep -n 'interactive-ticket-subflow.md' skills/hb-ticket-discuss.md`
   shows the skill *references* the subflow; confirm the prompt/transform/write text is **not**
   pasted inline (AC 5).
4. **No SDK / no folder creation, statically.** `grep -nE 'hb-sdk task|git ' skills/hb-ticket-discuss.md`
   returns nothing (AC 6).
5. **Capture a pre-run baseline.** Snapshot `.hb/task/active/` (e.g. `ls -R .hb/task/active > /tmp/hb-before.txt`).
6. **Exercise the help path.** Run `/hb-ticket-discuss --help`: it prints the generated help and
   stops; no `/tmp/ticket.md` is written by this invocation (AC 8).
7. **Exercise the happy path.** Run `/hb-ticket-discuss`, answer the subflow prompt; confirm
   `/tmp/ticket.md` is written with the three-section structure and that its content is echoed
   to stdout in a copy-paste block (AC 5, 7).
8. **Standalone invariant.** `ls -R .hb/task/active > /tmp/hb-after.txt && diff /tmp/hb-before.txt /tmp/hb-after.txt`
   shows **no** new task/step folder or `ticket.md` under `.hb/` (AC 6).
9. **Scope check.** `git status --short` shows only `skills/hb-ticket-discuss.md` added (plus this
   step's own plan/execution artifacts); no edits to the subflow or sibling skills.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — file at `skills/hb-ticket-discuss.md` | §2, §4 | new file; verified §6.1 |
| 2 — frontmatter (name, argument-hint, description-with-usage, allowed-tools scoped) | §2 frontmatter | `allowed-tools` trims `hb-sdk`/`git`; verified §6.1 |
| 3 — body: Inputs / Reference Files / numbered Steps | §2 body | verified §6.2 |
| 4 — Step 1 help check → `skill-help.md`, stop | §1 row 1, §2 Step 1 | verified §6.2, §6.6 |
| 5 — reuses (references, not duplicates) the subflow, scratch `$TARGET_PATH`, standalone | §1, §2 Step 2 | verified §6.3, §6.7 |
| 6 — no `hb-sdk task` calls, no task/step folder | Design decision, §3, allowed-tools | verified §6.4, §6.8 |
| 7 — emit ticket content to stdout | §2 Step 3 | verified §6.7 |
| 8 — `--help` prints help and stops without generating | §1 row 1, §2 Step 1 (via `skill-help.md:41`) | verified §6.6 |

---

## 8. Out of scope (per ticket)

- **Jira / Atlassian MCP integration** — deferred to step 1. This skill's stdout emission is
  the fallback step 1 will keep when no Jira MCP is available.
- **Changes to `interactive-ticket-subflow.md`, `hb-task-create`, or `hb-task-step-add`** —
  none required; the subflow is reused as-is.
- **Registering the skill** anywhere beyond creating the skill file itself.
