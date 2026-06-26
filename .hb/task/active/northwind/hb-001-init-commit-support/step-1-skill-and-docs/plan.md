# Step 1 Plan — Wire hb-init to `plain` mode and document all three modes in committing.md

Step-0 shipped the `plain` / `task` / `task-step` subparser redesign for `hb-sdk commit write-message-file`, but left two documentation artifacts pointing at the old flat-flag form: `skills/references/committing.md` still shows `--task <task> --step <step>` as the single invocation shape, and `skills/hb-init.md` step 3 defers wholesale to that stale reference for commit message generation. The motivating failure: a Claude agent following `hb-init` today would attempt `commit write-message-file --task <task> ...` but `hb-init` has no task, making the `--task` required arg unsatisfiable — the command exits 2. This step is documentation-only (no SDK changes); it corrects both artifacts so `hb-init` calls `plain` mode directly and `committing.md` documents all three modes with per-mode required/forbidden flags, subject formats, and usage examples.

Source ticket: `./ticket.md`. Builds on the **shipped** SDK work from step-0 (`skills/scripts/hb-sdk` — lines 769–831, confirmed live). The plan targets the files as they exist now in `master` (commit `3c5961e`).

---

## 0. Current-state facts (verified during planning)

- **`skills/hb-init.md` step 3** (`hb-init.md:34`): `"create a non-step commit by following ${CLAUDE_SKILL_DIR}/references/committing.md and including any new or changed files related to this task"`. No explicit `commit write-message-file` call; delegates entirely to `committing.md`. Confirmed live.

- **`skills/references/committing.md` §2 "Generate commit message"** (`committing.md:69–86`): single invocation form `hb-sdk commit write-message-file --task <task> --step <step> --short <desc> --long <desc>`. Lists `--task` as required, `--step` as optional. No `plain`, `task`, or `task-step` modes mentioned. Confirmed live.

- **`skills/scripts/hb-sdk` lines 804–828** (step-0 output): `wmf_subs` subparser with three parsers:
  - `plain` — `--short` required, `--long` optional; rejects `--task`/`--step` (argparse enforces)
  - `task` — `--task` + `--short` required, `--long` optional; rejects `--step`
  - `task-step` — `--task` + `--step` + `--short` required, `--long` optional
  Confirmed via step-0 execution and blast-radius grep.

- **Blast-radius**: only `hb-init.md` (indirectly, through `committing.md`) and `committing.md` itself contain the old invocation shape. All test and skill files were migrated in step-0. No skill other than `hb-init` needs updating.

### 0.1 Impact (before → after)

| File | Before | After |
|---|---|---|
| `skills/hb-init.md` step 3 | Delegates to `committing.md` for message generation (broken — no task available for `--task`) | Explicitly calls `plain --short "initialize hashbuild"`; still delegates staging/commit mechanics to `committing.md` §1 and §3 |
| `skills/references/committing.md` §2 | Single flat-flag form with `--task` required | Three documented modes with per-mode required/forbidden flags, subject format, and usage example |

Both changes are additive documentation edits. No SDK behavior changes.

### 0.2 Non-regression proof / risk

Purely additive — no behavior-altering code changed. Other hb-* skills that follow `committing.md` for the `task` or `task-step` case are unaffected: those modes retain identical flag shapes and subject formats. The only structural change to `committing.md` is the "Generate commit message" section; staging and commit mechanics (§1, §3) are untouched.

---

## 1. Design overview

Two independent edits; no ordering dependency between them.

**`hb-init.md` change:** Replace the vague "follow `committing.md`" delegation in step 3 with a three-part explicit commit block:
1. Stage: follow `committing.md` §1 (IDENTIFY → CHECK → COMMITREQUIRED → ADD)
2. Generate message: call `hb-sdk commit write-message-file plain --short "initialize hashbuild"` → capture path
3. Commit: `git commit -F <path>`

The staging and commit-mechanics steps still reference `committing.md`; only message generation is made explicit. This satisfies AC 1 (explicit `plain` call) and AC 1a (no manually written message strings) without duplicating the staging rules.

**`committing.md` change:** Replace the single invocation block in §2 "Generate commit message" with a three-mode table plus per-mode detail blocks (when to use, required flags, forbidden flags, subject format, usage example). The `--long` flag applies to all modes and can be noted once.

**Alternatives considered and rejected:**
- Make `committing.md` a decision tree that selects mode based on context: overly complex for what is a simple three-case enumeration; skill authors should choose the mode, not derive it dynamically.
- Keep `hb-init.md` delegating entirely to `committing.md` and have `committing.md` auto-select `plain` when no task is present: `committing.md` is a reference document, not executable logic — skill code is where mode selection belongs.

---

## 2. File changes — specification

### 2.1 `skills/hb-init.md` — step 3 rewrite

**Current (lines 33–35):**
```markdown
### 3. Commit

- create a non-step commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](${CLAUDE_SKILL_DIR}/references/committing.md) and including any new or changed files related to this task
```

**Replacement:**
```markdown
### 3. Commit

1. Stage relevant files by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) §1 (IDENTIFY → CHECK → COMMITREQUIRED → ADD), including any new or changed files related to the init.

2. Generate commit message:
   ```bash
   ${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file plain --short "initialize hashbuild"
   ```
   Capture the printed path as `$MSG_FILE`.

3. Commit: `git commit -F $MSG_FILE`
```

**Contract:**
- Subject line produced: `hb: initialize hashbuild`
- No `--task` or `--step` flags used anywhere in this step
- No manually written commit message strings anywhere in the skill

### 2.2 `skills/references/committing.md` — §2 rewrite

**Current §2 "Generate commit message" (lines 69–86):**
```markdown
### 2. Generate commit message

Invoke `${CLAUDE_SKILL_DIR}/scripts/hb-sdk` as follows to generate a commit message:

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file --task <task> --step <step> --short <short_description> --long <long_description>
```

- args:
  - required:
    - `--task <task>`: ...
    - `--short <short_desccription>`: ...
  - optional:
    - `--step <step>`: ...
    - `--long <long_description>`: ...
- returns path to file that contains commit message on stdout
- returns error messages on stderr
- if any error occurs, present verbatim to the user or fix automatically if possible
```

**Replacement:** A three-mode reference block. Each mode entry covers: when to use, required flags, forbidden flags, resulting subject line format, and a usage example.

```markdown
### 2. Generate commit message

Invoke `${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file <MODE>` to generate a commit message.
Choose the mode that matches the current context:

| Mode | When to use | Required flags | Forbidden flags | Subject format |
|---|---|---|---|---|
| `plain` | Framework bootstrap commits with no task (e.g. `hb-init`) | `--short` | `--task`, `--step` | `hb: <short>` |
| `task` | Task-level commits (skill operates on a task, not a step) | `--task`, `--short` | `--step` | `<task_id>: <short>` |
| `task-step` | Step-level commits (skill operates on a specific step) | `--task`, `--step`, `--short` | — | `<task_id>/step-<n>: <short>` |

All modes accept an optional `--long <desc>` for a longer explanation of why the change was made (only include when the why is non-obvious). Wrap `--short` and `--long` values in `""` to avoid shell issues.

Returns the path to the commit message file on stdout. Returns error messages on stderr. If any error occurs, surface verbatim to the user or fix automatically if possible.

**Examples:**

```bash
# plain — hb-init bootstrap commit
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file plain \
  --short "initialize hashbuild"
# → subject: hb: initialize hashbuild

# task — operating on a task (no step)
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task \
  --task northwind/hb-001-init-commit-support \
  --short "add step-1 ticket"
# → subject: hb-001: add step-1 ticket

# task-step — operating on a specific step
${CLAUDE_SKILL_DIR}/scripts/hb-sdk commit write-message-file task-step \
  --task northwind/hb-001-init-commit-support \
  --step 1 \
  --short "wire hb-init to plain mode"
# → subject: hb-001/step-1: wire hb-init to plain mode
```
```

---

## 3. Integration / wiring

No executable code changes. Both edits are documentation/skill markdown files.

- `hb-init.md` step 3 replaces a vague delegation with an explicit three-part block; steps 1, 2, and 4 are untouched.
- `committing.md` §1 (staging) and §3 (commit command) are untouched; only §2 "Generate commit message" changes.
- All other hb-* skills that reference `committing.md` for `task` or `task-step` commits are unaffected: the new `committing.md` still documents those modes with the same flag shapes.
- No tests need updating (no SDK changes; the new skill text is not unit-tested separately).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-init.md` | **edit** — step 3 rewritten to explicit three-part commit block; steps 1, 2, 4 untouched |
| `skills/references/committing.md` | **edit** — §2 "Generate commit message" rewritten with three-mode table and per-mode examples; §1 and §3 untouched |

No dependency manifests. No lockfile changes. No new files.

---

## 5. Tests

No new tests. This step makes no SDK changes — the SDK behavior was locked by step-0's 12 added tests (see `tests/skills/scripts/test_hb-sdk.py`). The skill markdown files are not unit-tested. The verification steps below substitute for automated tests.

**Non-regression:** `make test` must pass unchanged after this step — no SDK code touched.

---

## 6. Verification (after implementation)

1. **Full test suite clean:**
   ```bash
   make test
   ```
   Expect: 100 passed, 0 failed.

2. **AC 1 — `plain` mode produces correct subject:**
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file plain --short "initialize hashbuild")
   cat "$FILE"
   ```
   Expect: `hb: initialize hashbuild` (and a blank line if no `--long`).

3. **AC 1a — no manually written commit message strings in `hb-init.md`:**
   ```bash
   grep -n "hb: \|commit message" skills/hb-init.md
   ```
   Expect: zero matches for any hard-coded message strings (the SDK call line will show, but no quoted subject literals).

4. **AC 2 — all three modes documented in `committing.md`:**
   ```bash
   grep -n "plain\|task-step" skills/references/committing.md
   ```
   Expect: both `plain` and `task-step` appear; confirm table row and example block for each.

5. **AC 2 per-mode detail check — manual review of `committing.md`:**
   Confirm each mode entry states: when to use, required flags, forbidden flags, subject format, usage example.

6. **Scope check:**
   ```bash
   git diff --name-only
   ```
   Expect: only `skills/hb-init.md` and `skills/references/committing.md` (plus the step plan.md commit itself).

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `hb-init` calls `plain --short "initialize hashbuild"` | §2.1 (`hb-init.md` step 3 rewrite) | Verified by §6 steps 2–3 |
| 1a — no manually written commit message strings | §2.1 | Confirmed by grep in §6 step 3 |
| 1b — subject line is `hb: initialize hashbuild` | §2.1 + SDK `cmd_commit_wmf_plain` (step-0) | Verified by §6 step 2 |
| 2 — `committing.md` documents all three modes | §2.2 (`committing.md` §2 rewrite) | Verified by §6 steps 4–5 |
| 2a — `plain` entry (when/required/forbidden/subject) | §2.2 mode table + examples | |
| 2b — `task` entry (when/required/forbidden/subject) | §2.2 mode table + examples | |
| 2c — `task-step` entry (when/required/forbidden/subject) | §2.2 mode table + examples | |
| 2d — each mode has a usage example | §2.2 examples block | |

---

## 8. Out of scope (per ticket)

- Changes to `hb-sdk` itself (completed in step-0; 100 tests locked)
- Changes to any hb-* skill other than `hb-init`
- Changes to the task or step name format
- Updating test files (no SDK changes in this step)
