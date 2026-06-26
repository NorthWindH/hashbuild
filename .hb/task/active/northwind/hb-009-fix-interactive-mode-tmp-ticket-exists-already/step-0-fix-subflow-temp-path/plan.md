# Step 0 Plan — Fix Subflow Temp Path Collision

`interactive-ticket-subflow.md` Section D writes `ticket.md` to `$TARGET_PATH/ticket.md` without first checking whether that file already exists. Both callers (`hb-task-create` and `hb-task-step-add`) pass `$TARGET_PATH = /tmp`, making the effective write destination a fixed path: `/tmp/ticket.md`. If a prior run left that file behind — whether from a partial invocation, a crash, or a rapid successive call — the next run silently overwrites it without any indication that stale content was present. The fix is a single-line addition to Section D of the shared subflow: **delete `$TARGET_PATH/ticket.md` if it exists before writing the new one** (Option A). The change is purely internal to the subflow; both callers and the SDK invocation that consumes `$WRITTEN_TICKET` are unaffected.

Source ticket: `./ticket.md`. This is step 0, so there is no prior shipped work to build on.

> **Design decision — Option A (delete-before-write) vs. Option B (unique temp path).** The ticket offers both options. Option B (unique path) would require callers to read back the chosen path from the subflow output, since they currently hardcode `$WRITTEN_TICKET = /tmp/ticket.md` after the subflow runs. That is a behavioral change in both callers, not "cosmetic." Option A requires only a single new instruction in Section D of the shared subflow; callers are untouched. Option A is chosen. See §2 and §7 for AC mapping.

---

## 0. Current-state facts (verified during planning)

Confirmed by direct inspection of the files listed below.

- **`interactive-ticket-subflow.md` Section D** (`skills/references/interactive-ticket-subflow.md:52–71`): The write step reads "Write the derived content to `$TARGET_PATH/ticket.md`" with no prior deletion or uniqueness step. There is no guard against a pre-existing file.

- **`hb-task-create.md` interactive branch** (`skills/hb-task-create.md:48–55`): Sets `$TARGET_PATH = /tmp`, calls the subflow, then hardcodes `$WRITTEN_TICKET = /tmp/ticket.md`.

- **`hb-task-step-add.md` interactive branch** (`skills/hb-task-step-add.md:49–56`): Identical pattern — `$TARGET_PATH = /tmp`, same hardcoded `$WRITTEN_TICKET`.

- **Blast radius of the subflow change**: both callers invoke the subflow by injecting it via `!`; neither has any post-write logic that depends on a pre-existing file at the path. Deleting the file before writing cannot break either caller.

- **No other callers**: confirmed by inspection — only `hb-task-create.md` and `hb-task-step-add.md` reference `interactive-ticket-subflow.md`.

### 0.1 Impact (before → after)

| Scenario | Before | After |
|---|---|---|
| Normal invocation, no stale file | Subflow writes `/tmp/ticket.md` | Same — deletion of non-existent file is a no-op |
| Second invocation with stale `/tmp/ticket.md` | Stale file silently overwritten; user may not notice | Stale file explicitly deleted first; new content written cleanly |
| Concurrent invocations (race) | Last writer wins; first caller may receive stale content | Each invocation deletes before writing; still last-writer-wins, but stale-file-from-a-prior-session risk is eliminated |

### 0.2 Non-regression proof / risk

The change is additive to Section D only. All other sections (A guard, B prompt, C transform) are untouched.

| At-risk case | Current behavior | Why it can't change |
|---|---|---|
| `$TICKET_SUPPLIED = true` guard | Subflow skips entirely | Guard (Section A) fires before Section D; deletion step in D is never reached |
| `$NO_INTERACTIVE = true` guard | Subflow skips entirely | Same — Section A guard fires first |
| Content of the written ticket | Derived from `$USER_INPUT` via Section C rules | The deletion step removes the old file only; the written content comes from Section C, which is unchanged |
| Caller `$WRITTEN_TICKET` path | `/tmp/ticket.md` | Option A does not change the output path — callers can keep `$WRITTEN_TICKET = /tmp/ticket.md` unchanged |

---

## 1. Design overview

The fix is a single new instruction inserted at the start of Section D of `interactive-ticket-subflow.md`:

> Before writing, delete `$TARGET_PATH/ticket.md` if it already exists.

Control flow after the fix:

```
Section D (Write step):
  1. If $TARGET_PATH/ticket.md exists → delete it   ← NEW
  2. Write derived content to $TARGET_PATH/ticket.md ← unchanged
```

No new variables, no new sections, no change to the caller contract.

**Alternatives considered and rejected:**

| Alternative | Reason rejected |
|---|---|
| Option B: unique temp path in subflow | Requires callers to read back the dynamic path; changes caller behavior — violates AC 2 |
| Option B: unique path set by callers | Requires behavioral edits to both callers — same violation |
| No change to subflow; add deletion in callers | Duplicates the fix in two places; defeats the purpose of a shared subflow |

---

## 2. Core change — Section D of `interactive-ticket-subflow.md`

**Current text** (line 53):
```
Write the derived content to `$TARGET_PATH/ticket.md` using this structure:
```

**New text**:
```
Before writing, if `$TARGET_PATH/ticket.md` already exists, delete it.

Write the derived content to `$TARGET_PATH/ticket.md` using this structure:
```

- **Instruction type**: new imperative step (delete-before-write).
- **Contract**: the agent executing the subflow must delete the file (using `rm -f "$TARGET_PATH/ticket.md"` or equivalent) before the Write tool call. Deletion of a non-existent file is a no-op.
- **Failure contract**: if deletion fails (e.g., permission denied), the agent should surface the error and abort — do not proceed to write, as the stale content would remain inconsistent.
- **No change** to Sections A, B, or C; no change to the written content structure.

---

## 3. Integration / wiring

- **`hb-task-create.md`** and **`hb-task-step-add.md`**: no behavioral changes. The comment "The subflow writes `ticket.md` to `/tmp/ticket.md`." (line 54 / line 55 respectively) remains accurate — the output path is unchanged. No edits to these files are required.
- The subflow is injected at runtime via `!`; callers do not cache or snapshot its content. The fix takes effect immediately upon the next invocation with no wiring change.
- No build steps, dependency manifests, or SDK changes involved.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/interactive-ticket-subflow.md` | **edit** — insert one "delete-before-write" instruction at the start of Section D (line 53); all other sections unchanged |
| `skills/hb-task-create.md` | **unchanged** |
| `skills/hb-task-step-add.md` | **unchanged** |

Lockfile: N/A — no dependencies.

---

## 5. Tests

These are Markdown skill-definition files executed by an AI agent, not compiled code. There is no automated test suite. Verification is observational (§6). The relevant test scenarios are:

| Scenario | What to assert |
|---|---|
| **Happy path — no stale file** | Subflow runs; `/tmp/ticket.md` is written with the expected content |
| **Motivating case — stale file present** | Pre-create `/tmp/ticket.md` with sentinel content; run the subflow; assert the new content appears, not the sentinel |
| **Guard bypass — `$TICKET_SUPPLIED = true`** | Section A skips the subflow; `/tmp/ticket.md` is not touched (deletion step not reached) |
| **Guard bypass — `$NO_INTERACTIVE = true`** | Same as above |
| **Non-regression — caller output path** | `$WRITTEN_TICKET` is still `/tmp/ticket.md` after the subflow; SDK call succeeds |

These map to verification steps in §6.

---

## 6. Verification (after implementation)

1. **Diff the change**: confirm `git diff` shows only the addition of the delete instruction in Section D of `interactive-ticket-subflow.md`; no other files modified.

2. **Stale-file test** (motivating case):
   ```bash
   echo "STALE" > /tmp/ticket.md
   # Now invoke hb-task-create in interactive mode (provide any task name, give input at the prompt)
   cat /tmp/ticket.md
   # Assert: content is the newly derived ticket, not "STALE"
   ```

3. **No-stale-file test** (happy path):
   ```bash
   rm -f /tmp/ticket.md
   # Invoke hb-task-create in interactive mode
   cat /tmp/ticket.md
   # Assert: well-formed ticket.md written successfully
   ```

4. **Guard bypass — AC 2** (non-regression):
   ```bash
   # Invoke hb-task-create with --no-interactive
   # Assert: /tmp/ticket.md is NOT written or deleted; skeleton created without ticket
   ```

5. **Scope check**: `git diff --name-only` shows exactly one file: `skills/references/interactive-ticket-subflow.md`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — subflow no longer uses a hardcoded `/tmp/ticket.md` without protection (Option A: delete before write) | §2 edit to Section D | Option A chosen; see §1 design rationale |
| 2 — fix applies automatically to both callers; no separate changes required | §3 integration | Callers pass `$TARGET_PATH = /tmp`; subflow handles deletion; callers untouched |
| 3 — all other interactive subflow behavior unchanged | §2 (Sections A–C untouched), §0.2 non-regression table | Content, guards, prompt, transform all unchanged |

---

## 8. Out of scope (per ticket)

- Changes to `hb-task-create.md` or `hb-task-step-add.md` beyond any cosmetic updates (none needed).
- Changes to the SDK or any SDK-adjacent scripts.
- Resolving true concurrent-invocation races (two processes writing simultaneously) — Option A reduces the stale-session risk but does not add locking.
- Any other behavior of the interactive subflow (prompt wording, transform rules, ticket structure).
