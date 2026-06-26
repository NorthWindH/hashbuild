# Step 2 Plan — Add Interactive Ticket Creation to hb-task-step-add

`hb-task-step-add` currently has no interactive ticket creation: when called without `--ticket`, it creates only a skeleton step folder and asks the user to fill in `ticket.md` manually. Step 1 added this capability to `hb-task-create` via a shared `interactive-ticket-subflow.md`. This step applies the same integration to `hb-task-step-add`, making interactive mode consistent across both creation points. Scope: one file edited (`skills/hb-task-step-add.md`); no SDK, no other skill, no other file changes. Observable effect: calling `/hb-task-step-add author/task-id` without flags now prompts the user for ticket content before creating the step folder.

Source ticket: `./ticket.md`. Builds on the shipped step-1 work in `skills/hb-task-create.md` and the shared `skills/references/interactive-ticket-subflow.md`. This plan targets the code as it exists now.

---

## 0. Current-state facts (verified during planning)

Inspected `skills/hb-task-step-add.md` directly. Facts confirmed live, not assumed.

**Frontmatter (lines 1–10):**
```
argument-hint: "[--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
```
- `--no-interactive` is absent from `argument-hint`, `description`, and `allowed-tools`.
- No tmp Write/Read/Edit permissions — required for interactive mode.

**Inputs table (lines 18–29):** no `--no-interactive` row.

**Steps (lines 31–62):**
- Step 1: Help check
- Step 2: Add step (SDK call `hb-sdk task step add`)
- Step 3: Commit
- Step 4: Prompt user

No flag-precedence section exists. Current step 2 calls the SDK unconditionally.

**Reference model — `skills/hb-task-create.md` (step-1 output, confirmed current):**
- Frontmatter includes `--no-interactive` in argument-hint, description, and allowed-tools (with `//tmp/*` and `//private/tmp/*` patterns).
- Step 2 is "Flag precedence / interactive ticket": sets `$TICKET_SUPPLIED` / `$NO_INTERACTIVE`, evaluates three ordered cases, writes to `/tmp/ticket.md` in interactive mode, passes `--ticket $WRITTEN_TICKET` to SDK.
- Commit step stages `$WRITTEN_TICKET` when interactive mode ran.
- Prompt step has two variants.

**`skills/references/references-toc.md` line 14:** already lists `interactive-ticket-subflow.md` as shared by `hb-task-create` and `hb-task-step-add`. No TOC change needed.

**SDK behavior (from step-1 evidence):** `hb-sdk task step add --ticket <path>` copies `<path>` into the new step folder as `ticket.md`. No SDK changes needed.

### 0.1 Impact (before → after)

| Invocation | Before | After |
|---|---|---|
| `hb-task-step-add author/hb-004` (no flags) | SDK called immediately; skeleton only; user edits ticket.md manually | Interactive prompt fires; ticket.md written to /tmp; SDK called with `--ticket`; step folder seeded with ticket |
| `hb-task-step-add --ticket /path/to/ticket.md author/hb-004` | SDK called with ticket path | Unchanged |
| `hb-task-step-add --no-interactive author/hb-004` | Flag unrecognized (not yet present) | Skeleton-only; SDK called without ticket |

Change is additive: existing `--ticket` path is behavior-preserving. The `--no-interactive` path is new but identical to the current no-flag path.

### 0.2 Non-regression proof / risk

| At-risk case | Current behavior | Guard |
|---|---|---|
| `--ticket <path>` supplied | SDK called with ticket path, no interactive | `$TICKET_SUPPLIED` check is first-priority in precedence table |
| `--flavor <slug>` supplied (no ticket) | SDK called with `--flavor`; skeleton | Interactive mode still fires; `--flavor` still forwarded to SDK |
| `--ticket-overwrite` supplied | Forwarded to SDK | Forwarded unchanged in all three branches |

Change cannot alter the `--ticket` path: the guard checks `$TICKET_SUPPLIED` before any interactive logic.

---

## 1. Design overview

Mirror the three-tier flag precedence from `hb-task-create` step 2, inserting it as new step 2 in `hb-task-step-add`, and renumbering the remaining steps.

| Tier | Trigger | Behavior | New? |
|---|---|---|---|
| 1 | `--ticket <path>` supplied | Pass ticket to SDK; skip interactive | No (existing) |
| 2 | `--no-interactive` supplied (no `--ticket`) | Skeleton-only; skip interactive | Yes |
| 3 | Neither flag | Interactive mode: follow subflow → write /tmp/ticket.md → SDK with `--ticket` | Yes |

```
precedence:  --ticket  ≥  --no-interactive  ≥  interactive   (tie-break: first match wins)
```

`$TARGET_PATH` for interactive mode is `/tmp` — the step folder does not yet exist when the subflow runs, so we cannot write directly to it. The SDK copies the ticket from `/tmp/ticket.md` into the created step folder.

**Alternatives considered and rejected:**
- Resolve the next-step folder path first and write directly to it: requires SDK dry-run support that isn't documented; writing to a non-existent folder would require `mkdir`, adding blast radius.
- Write to `/tmp/<unique-name>.md` to avoid collision with parallel invocations: out of scope; `hb-task-create` uses a fixed `/tmp/ticket.md` path; this step mirrors that pattern.

---

## 2. hb-task-step-add.md — specification

Single file edited. All changes are additive or insertions; no existing behavior is removed.

### 2.1 Frontmatter additions

| Field | Current | After |
|---|---|---|
| `argument-hint` | `[--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>` | `[--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>` |
| `description` (usage line) | `/hb-task-step-add [--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>` | `/hb-task-step-add [--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>` |
| `allowed-tools` | `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)` | `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*) Edit(//tmp/*) Edit(//private/tmp/*)` |

### 2.2 Inputs table — new row

Insert after the `--ticket-overwrite` row:

| Parameter | Required | Description |
|---|---|---|
| `--no-interactive` | no | Skip interactive ticket creation. Creates a skeleton only, with no ticket. |

### 2.3 New step 2 — Flag precedence / interactive ticket

Insert as step 2 between the current step 1 (help check) and step 2 (SDK call), which becomes step 3 after insertion.

```
### 2. Flag precedence / interactive ticket

Set:

- `$TICKET_SUPPLIED` = `true` if `--ticket <path>` was provided; otherwise `false`
- `$NO_INTERACTIVE` = `true` if `--no-interactive` was provided; otherwise `false`

Evaluate in order (first match wins):

1. **`$TICKET_SUPPLIED` is `true`** — proceed to Step 3; pass `--ticket <ticket_path>` to the SDK as today.
2. **`$NO_INTERACTIVE` is `true`** — skeleton-only mode; proceed to Step 3 without a ticket.
3. **Neither flag** — interactive mode:
   a. Set `$TARGET_PATH` = `/tmp`.
   b. Follow [${CLAUDE_SKILL_DIR}/references/interactive-ticket-subflow.md](references/interactive-ticket-subflow.md) with:
   - `$TARGET_PATH` = `/tmp`
   - `$TICKET_SUPPLIED` = `false`
   - `$NO_INTERACTIVE` = `false`

   The subflow writes `ticket.md` to `/tmp/ticket.md`.
   c. Set `$WRITTEN_TICKET` = `/tmp/ticket.md`.
   d. Proceed to Step 3 with `--ticket $WRITTEN_TICKET`.
```

### 2.4 Renumbering

Current steps 2, 3, 4 become steps 3, 4, 5. No content changes to step 3 (SDK call) beyond the step number heading.

### 2.5 Updated step 4 — Commit

Add one bullet at the end of the existing commit step:

```
- when interactive mode ran (Step 2, case 3): also stage `$WRITTEN_TICKET` (the generated `ticket.md`)
```

### 2.6 Updated step 5 — Prompt user

Replace the single prompt message with two variants:

```
**When interactive mode ran (Step 2, case 3) — ticket was just written:**

> Step added with ticket. `/clear` this conversation, then run `/hb-task-step-plan <step_ref>` to create the implementation plan.

**All other modes (skeleton-only or `--ticket` supplied):**

> Step added. `/clear` this conversation, then: if the step ticket is ready, run `/hb-task-step-plan <step_ref>` to create the implementation plan. If the ticket still needs its acceptance criteria filled in, edit `ticket.md` in the step folder first.
```

---

## 3. Integration / wiring

- Single file changed: `skills/hb-task-step-add.md`.
- The `interactive-ticket-subflow.md` reference is already in `references-toc.md` (line 14) — no change needed.
- No SDK changes — `hb-sdk task step add --ticket <path>` already handles seeding from a ticket file.
- No changes to any other skill, script, or config file.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-step-add.md` | **edit** — frontmatter (argument-hint, description, allowed-tools), Inputs table (add `--no-interactive` row), insert new step 2, renumber steps 2→3/3→4/4→5, update commit and prompt steps; existing SDK call logic unchanged |

No dependency manifests or lockfiles are involved.

---

## 5. Tests

No automated test suite for skill markdown files. Verification is manual (see §6). Non-regression for existing `--ticket` behavior is structural: the `$TICKET_SUPPLIED` guard fires first, before any interactive logic.

---

## 6. Verification (after implementation)

1. **Read `skills/hb-task-step-add.md`** and confirm each AC directly:

   a. **AC 1 — Frontmatter docs:** `--no-interactive` appears in `argument-hint`, in the `description` usage line, and in the `## Inputs` table.

   b. **AC 2 — Flag precedence section:** new step 2 is present immediately before the SDK call step (now step 3). Confirm three ordered cases: `$TICKET_SUPPLIED` → `$NO_INTERACTIVE` → interactive.

   c. **AC 3 — Commit includes ticket.md:** step 4 (commit) has the conditional bullet staging `$WRITTEN_TICKET`.

   d. **AC 4 — Prompt message:** step 5 has the two-variant message; interactive variant directs straight to `/hb-task-step-plan`.

2. **Scope check:** only `skills/hb-task-step-add.md` changed. Confirm with `git diff --name-only`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 + §2.2 + §6.1a | `--no-interactive` in argument-hint, description, Inputs table |
| 2 | §1 + §2.3 + §6.1b | New step 2: three-tier flag precedence; interactive writes to /tmp, passes to SDK |
| 3 | §2.5 + §6.1c | Commit step stages `$WRITTEN_TICKET` when interactive mode ran |
| 4 | §2.6 + §6.1d | Prompt has two variants; interactive directs to `/hb-task-step-plan` |

---

## 8. Out of scope (per ticket)

- Changes to `hb-task-create.md` (completed in step 1).
- Other hb-* skills.
- Validating ticket quality.
- Handling parallel invocations writing to `/tmp/ticket.md` simultaneously.
