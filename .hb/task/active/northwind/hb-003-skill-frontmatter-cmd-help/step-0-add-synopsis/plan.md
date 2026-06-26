# Step 0 Plan — Add Synopsis to Skill Frontmatter Descriptions

Each of the 10 `skills/*.md` files exposes its argument surface only inside the skill body (`## Inputs` table), which the harness does not surface to the user browsing skills. A user sees only the `description` field from YAML frontmatter, which currently contains prose only — no usage line. This step prepends a one-line usage synopsis to every `description` field so the argument surface is visible immediately. The change is additive only: no step logic, allowed-tools, reference files, or any other field is touched in any file.

Source ticket: `./ticket.md`. No prior steps — this is step 0 and the task starts here.

---

## 0. Current-state facts (verified during planning)

All 10 `skills/*.md` files use YAML's folded scalar style (`description: >`). Confirmed live by reading the first ~10 lines of each file.

Example (confirmed at `skills/hb-init.md:3-6`):

```yaml
description: >
  Idempotent. Ensure that hashbuild directory structure exists (.hb directory).
  Should be called before any other /hb-* skills are invoked for the first time.
```

**YAML folded scalar semantics** (load-bearing for the design):
- Consecutive non-blank lines are joined with a single space → forms one paragraph.
- A blank line within the scalar body becomes a literal `\n\n` in the parsed value → paragraph break.
- So inserting a synopsis + blank line before the existing prose produces `synopsis\n\nexisting prose\n` in the parsed value — correctly separating the two.

**Blast radius:** Only the `description` field value changes. The `name`, `allowed-tools`, and all body content are untouched. No code or scripts read the `description` field (verified: `tests/skills/scripts/test_hb-sdk.py` tests `hb-sdk`, not frontmatter; no other test files found).

**Synopses** (derived from each file's `## Inputs` table, already verified in the task ticket):

| File | Synopsis |
|---|---|
| `hb-init.md` | `/hb-init [--help]` |
| `hb-status.md` | `/hb-status [--help]` |
| `hb-task-archive.md` | `/hb-task-archive [--help] <author/task-id>` |
| `hb-task-create.md` | `/hb-task-create [--help] [--ticket <path>] [--ticket-overwrite] <author/task-id>` |
| `hb-task-plan.md` | `/hb-task-plan [--help] <author/task-id>` |
| `hb-task-step-add.md` | `/hb-task-step-add [--help] [--flavor <slug>] [--ticket <path>] [--ticket-overwrite] <author/task-id>` |
| `hb-task-step-execute.md` | `/hb-task-step-execute [--help] <author/task-id/step-n>` |
| `hb-task-step-plan.md` | `/hb-task-step-plan [--help] <author/task-id/step-n>` |
| `hb-task-step-review-address.md` | `/hb-task-step-review-address [--help] [--no-todo-scan] [--commits N] <author/task-id/step-n>` |
| `hb-task-step-review-init.md` | `/hb-task-step-review-init [--help] <author/task-id/step-n>` |

### 0.1 Impact (before → after)

| File | Before (description first line) | After (description first line) |
|---|---|---|
| all 10 files | prose (e.g. `Idempotent. Ensure…`) | synopsis (e.g. `/hb-init [--help]`) |

Change type: **additive only** — a new first line + blank separator are inserted; existing prose is unchanged.

### 0.2 Non-regression proof

The change is purely additive — no existing line is removed or altered. The only file content changing is the description block (two new lines prepended inside it). Nothing else in any file changes.

---

## 1. Design overview

For each file, the description block changes from:

```yaml
description: >
  <prose>
```

to:

```yaml
description: >
  <synopsis>

  <prose>
```

The blank line between synopsis and prose creates a YAML paragraph break (`\n\n` in the parsed value), satisfying AC 1.2. The synopsis is a single literal line; the existing prose lines follow unchanged.

No alternatives needed — the change is mechanical and the YAML scalar approach is the only sensible representation given the existing `>` style.

---

## 2. Edit specification

**Unit: frontmatter `description` block in each `skills/*.md` file**

For each file, the edit replaces the `description: >` opening plus the first prose line with the synopsis line + blank line + first prose line. The exact old/new strings for each file:

| File | old_string (beginning of description block) | New first two lines inserted |
|---|---|---|
| `hb-init.md` | `description: >\n  Idempotent. Ensure` | synopsis + blank before `Idempotent. Ensure` |
| `hb-status.md` | `description: >\n  Report the current` | synopsis + blank before `Report the current` |
| `hb-task-archive.md` | `description: >\n  Archive a task` | synopsis + blank before `Archive a task` |
| `hb-task-create.md` | `description: >\n  Idempotent. Ensure a task skeleton` | synopsis + blank before `Idempotent. Ensure a task skeleton` |
| `hb-task-plan.md` | `description: >\n  Analyze a task` | synopsis + blank before `Analyze a task` |
| `hb-task-step-add.md` | `description: >\n  Idempotent. Add the next step` | synopsis + blank before `Idempotent. Add the next step` |
| `hb-task-step-execute.md` | `description: >\n  Read plan.md` | synopsis + blank before `Read plan.md` |
| `hb-task-step-plan.md` | `description: >\n  Idempotent. Create or update` | synopsis + blank before `Idempotent. Create or update` |
| `hb-task-step-review-address.md` | `description: >\n  Read review.md` | synopsis + blank before `Read review.md` |
| `hb-task-step-review-init.md` | `description: >\n  Idempotent. Create review.md` | synopsis + blank before `Idempotent. Create review.md` |

Each edit uses the Edit tool with `old_string` = current description opening and `new_string` = synopsis line + blank line + current prose (unchanged remainder). The edit is unique in each file because the first prose word differs.

**Failure contract:** N/A — this is a text substitution; there is no runtime behavior or error path.

---

## 3. Integration / wiring

No wiring changes. The `description` field is read only by the Claude Code harness UI; no internal script or test code reads it. No build steps, lockfiles, or dependency manifests are affected.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-init.md` | **edit** — prepend synopsis + blank line to `description` block; all other content untouched |
| `skills/hb-status.md` | **edit** — same pattern |
| `skills/hb-task-archive.md` | **edit** — same pattern |
| `skills/hb-task-create.md` | **edit** — same pattern |
| `skills/hb-task-plan.md` | **edit** — same pattern |
| `skills/hb-task-step-add.md` | **edit** — same pattern |
| `skills/hb-task-step-execute.md` | **edit** — same pattern |
| `skills/hb-task-step-plan.md` | **edit** — same pattern |
| `skills/hb-task-step-review-address.md` | **edit** — same pattern |
| `skills/hb-task-step-review-init.md` | **edit** — same pattern |

Lockfile: unchanged — no new dependency. No new files created.

---

## 5. Tests

No new tests are needed and no existing tests need updating. The existing test suite (`tests/skills/scripts/test_hb-sdk.py`) tests the `hb-sdk` CLI script only — it does not read or validate skill frontmatter. The change is to static YAML metadata consumed only by the harness, not by any tested code path.

**Non-regression:** Run `pytest tests/` to confirm the existing suite stays green — this is a no-op regression guard since no tested code is affected.

---

## 6. Verification (after implementation)

1. **Full test run:** `cd /home/hkamal/repos/hashbuild && python -m pytest tests/ -q` — must pass cleanly (no failures introduced).

2. **Synopsis present in all 10 files:** Confirm each description block now starts with the synopsis:
   ```bash
   grep -A1 "description: >" skills/hb-init.md
   grep -A1 "description: >" skills/hb-status.md
   grep -A1 "description: >" skills/hb-task-archive.md
   grep -A1 "description: >" skills/hb-task-create.md
   grep -A1 "description: >" skills/hb-task-plan.md
   grep -A1 "description: >" skills/hb-task-step-add.md
   grep -A1 "description: >" skills/hb-task-step-execute.md
   grep -A1 "description: >" skills/hb-task-step-plan.md
   grep -A1 "description: >" skills/hb-task-step-review-address.md
   grep -A1 "description: >" skills/hb-task-step-review-init.md
   ```
   Each should print the synopsis line (e.g. `  /hb-init [--help]`).

3. **Blank line separator present:** Confirm the blank line between synopsis and prose exists in each file:
   ```bash
   grep -A3 "description: >" skills/hb-init.md
   # expect: line 1 = synopsis, line 2 = blank, line 3 = start of prose
   ```

4. **Prose unchanged:** For one representative file, diff the prose portion against git HEAD:
   ```bash
   git diff skills/hb-init.md
   # expect: only 2 lines added (synopsis + blank); no lines removed; no other context changed
   ```

5. **Scope check:** Only the 10 `skills/*.md` files changed; `skills/references/`, `skills/scripts/`, and all other repo files are untouched:
   ```bash
   git diff --name-only
   # expect: exactly the 10 skills/*.md files
   ```

6. **AC 1.3 count check:** Confirm exactly 10 files are modified:
   ```bash
   git diff --name-only | wc -l
   # expect: 10
   ```

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — synopsis as first line of `description` | §2 (edit spec) + §6 step 2 | All 10 files edited |
| 1.1 — synopsis form: `[--help]` first, optional flags, positional last | §0 synopsis table + §2 | Synopses taken verbatim from task ticket, derived from Inputs tables |
| 1.2 — blank line separates synopsis from prose | §2 (new_string format) + §6 step 3 | YAML blank line → `\n\n` in parsed value |
| 1.3 — synopsis matches arg surface in `## Inputs` | §0 synopsis table | Verified against each file's Inputs table during planning |
| 2 — prose preserved verbatim | §2 (old prose lines unchanged) + §6 step 4 | Only prepend; no removal |
| 3 — all 10 files updated | §4 + §6 step 6 | All 10 listed; diff count check |
| 4 — no other content changed | §2 + §6 step 5 | Edit tool touches only the description opening |

---

## 8. Out of scope (per ticket)

- Changes to skill logic, step instructions, or reference files.
- Adding synopsis lines anywhere other than the frontmatter `description` field.
- Creating new skills or modifying `hb-sdk` scripts.
- Updating `tests/` — no test covers skill frontmatter.
