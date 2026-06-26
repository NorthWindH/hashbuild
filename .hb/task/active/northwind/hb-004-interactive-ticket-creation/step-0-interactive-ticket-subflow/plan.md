# Step 0 Plan — Create interactive-ticket-subflow.md

This step adds `skills/references/interactive-ticket-subflow.md`, a shared reference file that documents the interactive ticket-creation subflow. Currently, neither `hb-task-create` nor `hb-task-step-add` provides interactive prompting — when called without `--ticket`, they silently write a blank skeleton. Extracting the prompt/transform/write logic into a dedicated reference file (the same pattern as `review-init-subflow.md`) gives steps 1 and 2 a single authoritative source to inject via `!` rather than duplicating the wording in each skill. This step is purely additive: two files change, no callers are modified.

Source ticket: `./ticket.md`. No prior steps — this is step 0, starting from the current repo state.

---

## 0. Current-state facts (verified during planning)

- `skills/references/interactive-ticket-subflow.md` **does not exist**. Confirmed: `ls skills/references/` lists 12 entries, none named `interactive-ticket-subflow.md`.
- `skills/references/references-toc.md` has 14 rows (11 reference-file rows + 1 blank trailing + 1 `hb-task-unarchive.md` row pointing outside the references folder). Confirmed at `skills/references/references-toc.md:1-14`.
- Analog pattern: `skills/references/review-init-subflow.md` — blockquote header, lettered sections (A/B/C), no SDK calls, no commits, no user notifications except those described within. Confirmed at `skills/references/review-init-subflow.md:1-81`.
- Neither `hb-task-create.md` nor `hb-task-step-add.md` currently contains interactive logic or a `--no-interactive` flag. Confirmed via grep — both files only reference `--ticket` and `--ticket-overwrite`. Integration into those skills is out of scope for this step.
- The subflow will rely on two caller-supplied variables: `$TARGET_PATH` (the folder where `ticket.md` will be written) and `$TICKET_SUPPLIED` / `$NO_INTERACTIVE` (guard-clause signals). These are documented as a caller contract within the file; actually adding them to callers is steps 1 and 2.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| `skills/references/interactive-ticket-subflow.md` | absent | new file, full subflow |
| `skills/references/references-toc.md` | 14 rows (11 refs + extras) | 15 rows (12 refs) — one new entry |
| `hb-task-create.md` | unchanged | unchanged (out of scope) |
| `hb-task-step-add.md` | unchanged | unchanged (out of scope) |

Change type: **additive only**. No existing file content is altered except appending one row to `references-toc.md`.

### 0.2 Non-regression proof / risk

Purely additive. The only existing-file edit is a single appended row in `references-toc.md` — the table is a static lookup reference, not parsed by any script. No behavioral risk.

---

## 1. Design overview

Model `interactive-ticket-subflow.md` directly on `review-init-subflow.md`:

| Element | `review-init-subflow.md` | `interactive-ticket-subflow.md` |
|---|---|---|
| Header | Blockquote with shared-by list and no-side-effects statement | Same pattern |
| Sections | A. Resolve step folder / B. Check existing / C. Create | A. Guard clause / B. Prompt / C. Transform / D. Write |
| Caller contract | `$STEP_PATH`, `$N` (set by caller before injection) | `$TARGET_PATH`, `$TICKET_SUPPLIED`, `$NO_INTERACTIVE` |
| Side effects | None | None (no commit, no SDK call, no notification beyond the prompt) |

The subflow has four ordered sections:

```
A. Guard clause   → exit early (skip) if --ticket or --no-interactive supplied
B. Prompt step    → ask user for content in any form
C. Transform step → derive three-section ticket.md structure from user input
D. Write step     → write $TARGET_PATH/ticket.md
```

**Alternatives considered and rejected:**

- *Embed the logic directly in each skill file*: rejected — duplicates wording and transform rules; any future change requires edits in two places.
- *Use a bash script instead of a reference file*: rejected — the "transformation" step is an LLM reasoning task, not a deterministic shell operation. Reference files (injected as prose instructions) are the established pattern for agent-executed subflows.

---

## 2. `interactive-ticket-subflow.md` — specification

### 2.1 Header block

```markdown
> **Subflow — interactive ticket creation.** Shared by `hb-task-create` and
> `hb-task-step-add`. Contains no side effects (no commit, no SDK calls, no user
> notification beyond the prompt itself).
```

Caller contract (stated inline below the header):

> **Caller contract.** Before injecting this subflow, the calling skill must have resolved:
> - `$TARGET_PATH` — absolute path to the folder where `ticket.md` will be written
> - `$TICKET_SUPPLIED` — set to `true` if `--ticket <path>` was passed; otherwise unset or `false`
> - `$NO_INTERACTIVE` — set to `true` if `--no-interactive` was passed; otherwise unset or `false`

### 2.2 Section A — Guard clause

- If `$TICKET_SUPPLIED` is `true`: skip this entire subflow (a ticket file was supplied; it takes precedence). Do nothing.
- If `$NO_INTERACTIVE` is `true`: skip this entire subflow (skeleton-only mode requested). Do nothing.
- Otherwise: continue to Section B.

### 2.3 Section B — Prompt step

Instruct the agent to ask the user:

> "Please describe what this ticket should cover. You can share content in any form: freeform prose, a bullet list, a structured draft, or a fully-formed Background / Acceptance Criteria / Out of scope."

Capture the user's response as `$USER_INPUT`. Do not restate or summarize the input yet; proceed to Section C.

### 2.4 Section C — Transform step

Apply these rules to convert `$USER_INPUT` into the standard three-section `ticket.md` structure.

**Rule 1 — Near-perfect match (transcribe):**

If `$USER_INPUT` already contains recognizable Background and Acceptance Criteria sections (exact or near-exact heading names, in any order):
- Transcribe verbatim.
- Apply only minimal conforming adjustments: normalize heading levels to `#`, capitalize section names (`Background`, `Acceptance Criteria`, `Out of scope`), and normalize list markers to `- ` or `1. ` as appropriate.
- Do not paraphrase or restructure.

**Rule 2 — Freeform (derive):**

If `$USER_INPUT` is prose, bullets, or a partial draft that does not match Rule 1:

| Section | Derived from |
|---|---|
| `# Background` | The "why": motivation, context, and the problem being solved. Narrative prose, 1–3 sentences. |
| `# Acceptance Criteria` | Discrete checkable conditions. Numbered list. Extract explicit requirements; infer additional criteria only when clearly implied by the user's intent. |
| `# Out of scope` | Explicit exclusions stated by the user. **Omit this section entirely if the user stated no exclusions.** |

**Ambiguity rule:** When content could belong in either Background or Acceptance Criteria, prefer Background for narrative/context statements and Acceptance Criteria for conditions that can be verified true or false.

### 2.5 Section D — Write step

Write the derived content to `$TARGET_PATH/ticket.md` using this structure:

```
# Background

<background text>

---

# Acceptance Criteria

<numbered list>

---

# Out of scope         ← omit this section and the preceding --- if none

<bullet list>
```

---

## 3. Integration / wiring

This step creates a new standalone file. No existing skill files are modified; `references-toc.md` gains one appended row. Callers (`hb-task-create.md`, `hb-task-step-add.md`) are not touched in this step.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/interactive-ticket-subflow.md` | **new** — full subflow document per §2 specification |
| `skills/references/references-toc.md` | **edit** — append one row for `interactive-ticket-subflow.md` |
| All other files | **unchanged** |

No dependency manifests or lockfiles are affected.

---

## 5. Tests

N/A — the hashbuild skills framework uses no automated test suite for reference files. Verification is manual, per §6.

---

## 6. Verification (after implementation)

1. Confirm `skills/references/interactive-ticket-subflow.md` exists.
2. Confirm the file opens with a blockquote header that names `hb-task-create` and `hb-task-step-add` as consumers and states "no side effects."
3. Confirm Section A is present and covers both guard conditions: `$TICKET_SUPPLIED` and `$NO_INTERACTIVE`.
4. Confirm Section B is present and instructs asking the user for content in any form (freeform prose, bullet list, structured draft, fully-formed three-section).
5. Confirm Section C is present with Rule 1 (near-perfect → transcribe) and Rule 2 (freeform → derive), and that "Out of scope" is marked as omit-if-absent.
6. Confirm Section D is present and targets `$TARGET_PATH/ticket.md` with the standard three-section structure.
7. Confirm `skills/references/references-toc.md` has a new row for `interactive-ticket-subflow.md` with a description consistent with the `review-init-subflow.md` row style.
8. Confirm no other files were modified: `git diff --name-only` lists only the two files above.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1. File `skills/references/interactive-ticket-subflow.md` exists | §4 (new file) | Verified in §6 step 1 |
| 1.1 Header block identifying as shared subflow with no side effects | §2.1 | Verified in §6 step 2 |
| 1.2 Guard clause: skip if `--ticket` or `--no-interactive` supplied | §2.2 (Section A) | Verified in §6 step 3 |
| 1.3 Prompt step: ask for content in any form | §2.3 (Section B) | Verified in §6 step 4 |
| 1.4 Transform step: near-perfect transcribe + freeform derive rules | §2.4 (Section C) | Verified in §6 step 5 |
| 1.5 Write step: write to `$TARGET_PATH/ticket.md` | §2.5 (Section D) | Verified in §6 step 6 |
| 2. `references-toc.md` gains a row consistent with `review-init-subflow.md` row style | §4 (edit) | Verified in §6 step 7 |

---

## 8. Out of scope (per ticket)

- Updating `hb-task-create.md` to invoke the subflow (step 1).
- Updating `hb-task-step-add.md` to invoke the subflow (step 2).
- Adding a `--no-interactive` flag to any skill.
- Any SDK changes.
- Validation of ticket quality or completeness.
