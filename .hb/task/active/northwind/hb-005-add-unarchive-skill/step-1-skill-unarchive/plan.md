# Step 1 Plan — Add hb-task-unarchive Skill File

Step-0 shipped `hb-sdk task unarchive <name>`, which moves a task from `task/archive/<author>/` to `task/active/<author>/`. Before this step, no skill file exposes that command to users — running `/hb-task-unarchive` would fail with "skill not found." This step creates `skills/hb-task-unarchive.md` as the single missing piece of the archive/unarchive round-trip. The change is purely additive: one new markdown file, no edits to any existing skill, script, or test. The externally observable effect once this lands is that `/hb-task-unarchive <author/task-id>` resolves and executes.

Source ticket: `./ticket.md`. Builds on the **shipped** SDK subcommand from step-0 (`skills/scripts/hb-sdk`, `cmd_task_unarchive`). This plan targets the code as it exists now.

---

## 0. Current-state facts (verified during planning)

- `skills/hb-task-archive.md` exists at `skills/hb-task-archive.md` — confirmed by directory listing. It is the structural model for the new file.
- `skills/hb-task-unarchive.md` does **not** exist — confirmed by directory listing. The gap is exactly one file.
- `hb-sdk task unarchive <name>` is fully implemented (step-0 execution). CLI signature: `hb-sdk task unarchive <name>` where `<name>` is `author/task-id` (flavor optional). On success: prints `report_paths` to stdout and exits 0. On error: prints message to stderr and exits non-zero.
- `skills/hb-task-archive.md` uses `allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)` — confirmed by reading the file.
- The commit for this step is a **non-step commit** (the skill being created is a task-level skill, not a step skill) per `committing.md` rules.

### 0.1 Impact (before → after)

| State | Before | After |
|---|---|---|
| `/hb-task-unarchive` | Skill not found | Executes `hb-sdk task unarchive`, commits, prompts user |
| Files changed | — | `skills/hb-task-unarchive.md` added |
| Existing skills | Untouched | Untouched |

### 0.2 Non-regression proof / risk

Change is purely additive — one new file, no edits. No existing skill, script, or test is touched. Risk: none.

---

## 1. Design overview

Mirror `skills/hb-task-archive.md` exactly, substituting `unarchive` for `archive` throughout. The four-step flow is identical in structure:

1. Help check → delegates to `skill-help.md`
2. SDK call → `hb-sdk task unarchive <name>`
3. Commit → non-step commit per `committing.md`
4. Prompt user → confirms restoration, suggests next actions

**Alternatives considered and rejected:**
- Combining archive/unarchive into one skill file: breaks the one-skill-one-action convention established by existing skills; rejected.
- Adding unarchive as a flag to `hb-task-archive`: wrong abstraction layer; rejects clean naming; rejected.

---

## 2. Skill file specification

**File:** `skills/hb-task-unarchive.md` — **new**

### Frontmatter

```yaml
---
name: hb-task-unarchive
description: >
  /hb-task-unarchive [--help] <author/task-id>

  Unarchive a task by moving its folder from `task/archive` to `task/active`.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *)
---
```

### Body structure (four steps, mirroring `hb-task-archive.md`)

**Step 1 — Help check**
If the first argument is `help`, `--help`, or `-h`: follow `${CLAUDE_SKILL_DIR}/references/skill-help.md`. Stop.

**Step 2 — Unarchive task**
```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task unarchive <name>
```
- `<name>` is the task name exactly as received; flavor is optional (`author/abc-123` or `author/abc-123-flavor`)
- the SDK locates the task folder under `task/archive/` and moves it to `task/active/`
- errors if the task is not found, already active, or destination already exists
- capture stdout (paths) for use in the next step
- if an error occurs, present stderr verbatim and stop

**Step 3 — Commit**
Follow `${CLAUDE_SKILL_DIR}/references/committing.md` (non-step commit — no `--step` arg).

**Step 4 — Prompt user**
> Task restored. `/clear` this conversation, then run `/hb-status` to see active tasks or `/hb-task-step-add` to continue working on it.

### Output section

Report the restored task path. If any command fails, surface the error verbatim to the caller.

### Failure contract

Any SDK error (task not found, already active, destination exists) causes the skill to print stderr verbatim and stop — identical to `hb-task-archive.md`.

---

## 3. Integration / wiring

No wiring changes. The skill file is discovered by the harness via filename convention; no registration step is required. No existing callers, scripts, or manifests are touched.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-unarchive.md` | **new** — skill file mirroring `hb-task-archive.md`; no other file touches |

Lockfile / manifests: unchanged — no new dependency.

---

## 5. Tests

Skill files are markdown instruction documents consumed by the AI harness; there is no automated test suite for skill file content. Verification is by inspection (frontmatter fields) and smoke test (end-to-end invocation).

**Non-regression:** The 91 existing `hb-sdk` tests pass unchanged — no SDK code is modified in this step.

---

## 6. Verification (after implementation)

1. **File exists:**
   ```bash
   ls skills/hb-task-unarchive.md
   ```
   Expected: file listed with no error.

2. **Frontmatter fields (AC 2 & 3):**
   ```bash
   head -10 skills/hb-task-unarchive.md
   ```
   Confirm:
   - `name: hb-task-unarchive`
   - `description` contains `/hb-task-unarchive [--help] <author/task-id>`
   - `allowed-tools` contains both `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` and `Bash(git *)`

3. **Four-step body (AC 4):**
   Read `skills/hb-task-unarchive.md` and confirm Steps 1–4 are present with the correct SDK call, commit instruction, and prompt text.

4. **Smoke test — end-to-end round-trip (AC 4 step 2):**
   ```bash
   # archive hb-003 (it's currently in archive, so unarchive first to set up)
   skills/scripts/hb-sdk task unarchive northwind/hb-003
   # then re-archive it
   skills/scripts/hb-sdk task archive northwind/hb-003
   # confirm hb-003 is in archive
   ls .hb/task/archive/northwind/
   ```
   Then invoke `/hb-task-unarchive northwind/hb-003` via the skill harness and confirm:
   - exit 0
   - `hb-003` appears in `.hb/task/active/northwind/`
   - commit created with correct message

5. **Scope check:** only `skills/hb-task-unarchive.md` is new or changed.
   ```bash
   git status --short
   ```

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `skills/hb-task-unarchive.md` exists alongside `hb-task-archive.md` | §4 file-by-file; §6 step 1 | Single new file |
| 2 — frontmatter `description` = `/hb-task-unarchive [--help] <author/task-id>` | §2 frontmatter spec; §6 step 2 | Exact string confirmed in verification |
| 3 — `allowed-tools` mirrors `hb-task-archive` | §2 frontmatter spec; §6 step 2 | Both Bash allowances present |
| 4a — Help check delegates to `skill-help.md` | §2 Step 1 | Identical to archive skill |
| 4b — Unarchive step calls `hb-sdk task unarchive`; surfaces stderr on error | §2 Step 2; §6 step 4 | SDK call specified; failure contract stated |
| 4c — Commit follows `committing.md` (non-step) | §2 Step 3; §3 | No `--step` arg |
| 4d — Prompt user confirms restoration; suggests `/hb-status` or `/hb-task-step-add` | §2 Step 4 | Exact prompt text in §2 |
| 5 — Output reports restored task path; errors surfaced verbatim | §2 Output section; §2 failure contract | Mirrors archive skill |

---

## 8. Out of scope (per ticket)

- Changes to `hb-sdk` or any other existing skill files.
- Unarchiving individual steps within a task.
- Interactive confirmation prompts.
