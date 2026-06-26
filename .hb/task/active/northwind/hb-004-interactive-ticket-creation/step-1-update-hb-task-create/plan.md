# Step 1 Plan — Wire Interactive Ticket Subflow into `hb-task-create`

Today `hb-task-create` runs in exactly two modes: explicit-ticket (when `--ticket <path>` is supplied) and skeleton-only (when it isn't). When neither flag is given the skill silently creates an empty skeleton and then tells the user to write a `ticket.md` themselves — there is no interactive elicitation. This step inserts a three-tier flag-precedence block between the help check and the SDK call, adds `--no-interactive` as a documented escape hatch (skeleton-only on demand), and updates the commit and prompt steps so they reflect the new interactive mode. The change is behavior-altering for the no-flag case, additive for `--no-interactive`, and behavior-preserving for `--ticket` and `--help`. Single externally observable effect: `/hb-task-create northwind/hb-099` with no flags now prompts for ticket content rather than creating an empty skeleton.

Source ticket: `./ticket.md`. Builds on the **shipped** step-0 work (`skills/references/interactive-ticket-subflow.md`) and the row added to `skills/references/references-toc.md`. This plan targets `skills/hb-task-create.md` as it stands now (confirmed at planning time).

---

## 0. Current-state facts (verified during planning)

Inspected `skills/hb-task-create.md` lines 1–61. Confirmed live, not assumed.

- **Frontmatter** (lines 1–10): `argument-hint` and `description` list `[--help] [--ticket <path>] [--ticket-overwrite]`. No `--no-interactive` anywhere in the file. `allowed-tools` is `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)`.
- **Inputs table** (lines 18–24): four rows — `name`, `--ticket <path>`, `--ticket-overwrite`, `help`. No `--no-interactive` row.
- **Step 1** (lines 32–33): help check only. Unchanged.
- **Step 2** (lines 35–46): unconditional `hb-sdk task create [--ticket ...] <name>` call. No flag-precedence guard. This is the only place where the SDK is called.
- **Step 3** (lines 48–50): commits task skeleton; no mention of an interactively generated ticket.
- **Step 4** (lines 52–56): final prompt is identical regardless of whether a ticket was provided. Always includes the "if not, write a `ticket.md` first" clause. Never cites `hb-task-step-plan`.
- **`interactive-ticket-subflow.md`** (shipped by step-0): caller contract requires `$TARGET_PATH` (absolute path to the folder where `ticket.md` will be written), `$TICKET_SUPPLIED`, `$NO_INTERACTIVE`. Writes `ticket.md` to `$TARGET_PATH/ticket.md`; no other side effects.
- **`hb-sdk task path <name>`**: confirmed available but not needed in interactive mode — ticket is written to `/tmp` and passed to the SDK, so the task folder path never needs to be resolved separately.

### 0.1 Impact (before → after)

| Invocation | Before | After |
|---|---|---|
| No flags | Creates empty skeleton; tells user to write ticket manually | Prompts for ticket content; writes `ticket.md`; creates skeleton seeded with that ticket |
| `--no-interactive` | Flag unrecognized; treated as unknown arg | Creates skeleton only; no ticket; no prompt |
| `--ticket <path>` | Passes ticket to SDK | Unchanged |
| `--help` | Prints help | Unchanged |

Change type: **behavior-altering** for no-flag case; **additive** for `--no-interactive`; **behavior-preserving** for `--ticket` and `--help`.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Guard preserving it |
|---|---|---|
| `--ticket <path>` supplied | SDK seeded from file | Tier-1 in flag-precedence block skips subflow entirely |
| `--ticket-overwrite` supplied | Forwarded to SDK | Flag-precedence block only gates on `--ticket` / `--no-interactive`; `--ticket-overwrite` forwarding logic is untouched |
| `--help` path | Exits at Step 1 before SDK | Step 1 unchanged; flag-precedence block is Step 2 (runs after help check) |

---

## 1. Design overview

Three-tier flag-precedence block, evaluated as the new **Step 2**:

| Tier | Trigger | Result | New? |
|---|---|---|---|
| 1 (highest) | `--ticket <path>` supplied | Proceed to SDK as today | No |
| 2 | `--no-interactive` (no `--ticket`) | Proceed to SDK skeleton-only | Yes (flag is new) |
| 3 (default) | Neither flag | Invoke subflow → write `ticket.md` → proceed to SDK with `--ticket` | Yes |

```
precedence:  --ticket  ≥  --no-interactive  ≥  interactive (default)
(tie-break: --ticket always wins; not combinable with --no-interactive)
```

The block is inserted as **Step 2**; existing steps are renumbered Step 2 → 3, Step 3 → 4, Step 4 → 5. No logic in the renamed steps is removed — only the commit step (§4) and prompt step (§5) gain interactive-mode branches.

**Interactive mode sequence (tier 3) in detail:**
1. Set `$TARGET_PATH = /tmp`. Follow `interactive-ticket-subflow.md` with `$TARGET_PATH`, `$TICKET_SUPPLIED=false`, `$NO_INTERACTIVE=false`. Subflow writes `/tmp/hb-ticket.md`.
2. Set `$WRITTEN_TICKET = /tmp/hb-ticket.md`.
3. Proceed to Step 3 (SDK call) with `--ticket $WRITTEN_TICKET`. The SDK creates the task folder and skeleton, seeding `ticket.md` from the temp file.

**Alternatives considered and rejected:**

- Write ticket directly to the task folder (resolved via `hb-sdk task path`) — rejected: requires pre-creating the task folder with `mkdir -p` before the SDK runs; writing to `/tmp` first and passing via `--ticket` is cleaner and lets the SDK own folder creation.
- Inline the subflow logic directly instead of referencing the subflow — rejected: step 2's scope is `hb-task-step-add.md`; the subflow was designed as shared to avoid duplication.
- Make interactive the opt-in path via an `--interactive` flag — rejected: ticket specifies default is interactive; skeleton-only needs an explicit opt-out (`--no-interactive`).

---

## 2. `hb-task-create.md` — specification

### 2.1 Frontmatter changes

| Field | Current value | New value |
|---|---|---|
| `argument-hint` | `"[--help] [--ticket <path>] [--ticket-overwrite] <author/task-id>"` | `"[--help] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>"` |
| `description` (usage line) | `/hb-task-create [--help] [--ticket <path>] [--ticket-overwrite] <author/task-id>` | `/hb-task-create [--help] [--ticket <path>] [--ticket-overwrite] [--no-interactive] <author/task-id>` |
| `allowed-tools` | `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)` | `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Write(/tmp/*) Write(/private/tmp/*) Read(/tmp/*) Read(/private/tmp/*) Edit(/tmp/*) Edit(/private/tmp/*)` |

The `description` prose line ("Idempotent. Ensure a task skeleton exists…") is unchanged — it remains accurate.

### 2.2 Inputs table — new row

Insert after the `--ticket-overwrite` row:

| Parameter | Required | Description |
|---|---|---|
| `--no-interactive` | no | Skip interactive ticket creation. Creates a skeleton only, with no ticket. |

### 2.3 New Step 2 — Flag precedence / interactive ticket

Insert between existing Step 1 (help check) and existing Step 2 (SDK call, which becomes Step 3):

```markdown
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

      The subflow writes `ticket.md` to `/tmp/hb-ticket.md`.
   c. Set `$WRITTEN_TICKET` = `/tmp/hb-ticket.md`.
   d. Proceed to Step 3 with `--ticket $WRITTEN_TICKET`.
```

### 2.4 Updated Step 3 — Create task skeleton (renumbered from Step 2)

Content is identical to today's Step 2 except one bullet:

- Replace: "include `--ticket <ticket_path>` only when a ticket file was provided"
- With: "include `--ticket <ticket_path>` when `$TICKET_SUPPLIED` is `true` (use user-supplied path) or when interactive mode ran (use `$WRITTEN_TICKET`); omit in skeleton-only mode"

All other bullets are unchanged.

### 2.5 Updated Step 4 — Commit (renumbered from Step 3)

Add one bullet after the existing instruction:

> - when interactive mode ran (Step 2, case 3): also stage `$WRITTEN_TICKET` (the generated `ticket.md`)

The existing instruction ("create a non-step commit … pass `--tag task-create`") is otherwise unchanged.

### 2.6 Updated Step 5 — Prompt user (renumbered from Step 4)

Replace the single static prompt with two conditional variants:

**When interactive mode ran (Step 2, case 3) — ticket was just written:**
> Task and ticket created. `/clear` this conversation, then run `/hb-task-plan <name>` to analyze acceptance criteria and create step tickets. When steps are ready, run `/hb-task-step-plan <name/step-n>` for each step.

**All other modes (skeleton-only or `--ticket` supplied) — keep current text verbatim:**
> Task created. `/clear` this conversation, then: if you have a task `ticket.md`, run `/hb-task-plan <name>` to analyze acceptance criteria and create steps to cover them. If not, write a `ticket.md` first (Background, Acceptance Criteria, Out of scope), then run `/hb-task-plan`. To add the first step manually instead, run `/hb-task-step-add <name>`.

---

## 3. Integration / wiring

- Single file changed: `skills/hb-task-create.md`.
- The subflow is invoked by reference (Claude reads and follows it); no import mechanism or shell call needed.
- Interactive mode writes a temp ticket to `/tmp/hb-ticket.md` using the `Write` tool. On macOS `/tmp` is a symlink to `/private/tmp`; the `allowed-tools` frontmatter includes both `/tmp/*` and `/private/tmp/*` patterns to cover the symlink regardless of whether the harness resolves it before matching.
- Public signature of the skill (user-facing flags and step output) is extended, not broken. Existing callers passing `--ticket` or `--help` see identical behavior.
- `references-toc.md` already contains the `interactive-ticket-subflow.md` row (added in step-0). The `! cat references-toc.md` expansion in `hb-task-create.md` will automatically include it — no change needed there.
- No new runtime dependencies; no lockfile effects.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-create.md` | **edit** — frontmatter (3 fields), Inputs table (1 new row), new Step 2 inserted, Steps 2–4 renumbered to 3–5, Step 3 bullet updated, Step 4 bullet added, Step 5 prompt made conditional |

Lockfile: unchanged — no new dependency.

---

## 5. Tests

No automated test suite applies to skill markdown files (same conclusion as step-0). Verification is manual (see §6).

Non-regression for the `--ticket` and `--help` paths is guaranteed structurally: the flag-precedence block is tier-1/tier-2 (first-match exits), so those paths never reach the subflow or the `mkdir` call.

---

## 6. Verification (after implementation)

1. **Scope check** — confirm only `skills/hb-task-create.md` changed:
   ```bash
   git diff --name-only HEAD
   ```
   Expected: `skills/hb-task-create.md` only.

2. **AC 1 — `--no-interactive` in frontmatter**
   ```bash
   grep "no-interactive" skills/hb-task-create.md
   ```
   Expected: hits in `argument-hint`, `description` usage line, and `## Inputs` table (≥ 3 lines).

3. **AC 2 — flag-precedence block exists before SDK call**
   - Open `skills/hb-task-create.md` and confirm:
     - Step 2 is the flag-precedence block.
     - Step 3 is the SDK call (`hb-sdk task create`).
     - Step 2 appears above Step 3 with no SDK call between them.

4. **AC 2.1 — `--ticket` path proceeds as today**
   Run `/hb-task-create northwind/hb-verify-1 --ticket .hb/task/active/northwind/hb-004-interactive-ticket-creation/step-1-update-hb-task-create/ticket.md` and confirm:
   - No interactive prompt is shown.
   - Task skeleton and ticket appear in `task/active/northwind/`.
   - Commit is created.

5. **AC 2.2 — `--no-interactive` creates skeleton only**
   Run `/hb-task-create northwind/hb-verify-2 --no-interactive` and confirm:
   - No interactive prompt is shown.
   - Task skeleton is created with no `ticket.md`.
   - Commit is created.

6. **AC 2.3 — interactive mode prompts, writes ticket, proceeds to SDK**
   Run `/hb-task-create northwind/hb-verify-3` (no flags) and confirm:
   - Interactive prompt appears.
   - After supplying content, a `ticket.md` is written to the new task folder.
   - SDK creates the rest of the skeleton.
   - Commit stages both skeleton files and `ticket.md`.

7. **AC 3 — commit includes ticket.md when interactive mode ran**
   After step 6: `git show --name-only HEAD` — confirm `ticket.md` appears in the committed file list.

8. **AC 4 — prompt omits "write ticket first" when interactive mode ran**
   In step 6's output: confirm the final prompt does NOT contain "write a `ticket.md` first".

9. **AC 5 — `hb-task-step-plan` cited in interactive-mode prompt**
   In step 6's output: confirm the final prompt contains `/hb-task-step-plan`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `--no-interactive` in `argument-hint`, `description`, `## Inputs` | §2.1 (frontmatter), §2.2 (Inputs table) | Three locations; verified in §6 step 2 |
| 2 — flag-precedence block after help check, before SDK call | §2.3 (new Step 2) | Structural position verified in §6 step 3 |
| 2.1 — `--ticket` proceeds as today | §2.3 tier 1 | Verified in §6 step 4 |
| 2.2 — `--no-interactive` proceeds skeleton-only | §2.3 tier 2 | Verified in §6 step 5 |
| 2.3 — neither flag: subflow → write ticket → SDK with `--ticket` | §2.3 tier 3 | Verified in §6 step 6 |
| 3 — commit includes ticket.md when interactive | §2.5 (Step 4 update) | Verified in §6 step 7 |
| 4 — final prompt omits "write ticket first" when interactive | §2.6 interactive variant | Verified in §6 step 8 |
| 5 — `hb-task-step-plan` cited when ticket exists | §2.6 interactive variant | Cited in the interactive-mode prompt; verified in §6 step 9 |

---

## 8. Out of scope (per ticket)

- Changes to `hb-task-step-add.md` — deferred to step 2.
- Any other hb-* skills.
- Validating ticket quality (content checking, schema enforcement).
- SDK changes.
