# Step 0 Plan — Subflow Extraction for review-init

This step fixes two linked bugs in `hb-task-step-review-address` by extracting the `review.md` file-creation logic from `review-init` into a shared reference file. **The motivating case:** when `review-address` creates `review.md` by calling `review-init` as a sub-skill, the agent receives a "fill in review items and re-run" notification and stops prematurely (Bug 1), and a spurious intermediate commit shifts `HEAD` so the `TODO REVIEW` scan targets the wrong commit (Bug 2). Both bugs share a root cause: `review-init` contains side effects (notification, commit) that are inappropriate in a subflow context. The fix is additive — a new `review-init-subflow.md` reference file contains the file-creation core, leaving standalone `review-init` behaviour identical to today. The general class is "shared skill logic called in two contexts with incompatible side-effect requirements"; no other skills are affected. Externally observable result: `review-address` silently creates `review.md` when missing, then immediately proceeds to the TODO REVIEW scan without user interruption.

Source ticket: `./ticket.md`. This is step 0 (no prior shipped steps).

> **Design decision — shared subflow via `!` injection vs. extracted helper skill.** The `!`cat ...`` injection mechanism is already used in both skills for Reference Files. Extracting a helper skill would add a new invocation boundary with its own entry/exit semantics — exactly the problem being solved. Using `!` injection keeps the shared logic as inlined prose with no call boundary. The guard: the injected subflow is a passive document (no side effects of its own); all side effects (notification, commit) remain in the calling skill's explicit steps. See §1 and §7 for coverage.

---

## 0. Current-state facts (verified during planning)

**`skills/hb-task-step-review-init.md`** (133 lines, confirmed):
- Steps 1–6: help check → resolve step folder + number → check for existing → create file → notify user → commit
- Steps 2–4 (lines 29–109): file-creation core — hb-sdk path/number calls, existence check with stop logic, and the full `review.md` template literal including README-1 and README-2 blocks
- Step 5 (lines 111–119): user notification; last two lines reference "README-1 defined in step 4" and "README-2 defined in step 4"
- Step 6 (lines 122–124): step commit via `committing.md`

**`skills/hb-task-step-review-address.md`** (181 lines, confirmed):
- Step 2 (lines 38–48): resolves `$STEP_PATH` and `$N` via hb-sdk
- Step 3 (lines 52–55): conditional — reads existing `review.md` or invokes `review-init` skill; the single chokepoint is line 55: `if it does not exist: invoke the hb-task-step-review-init skill for <step_ref>`
- Steps 4–9: unaffected by this change

**`skills/references/review-init-subflow.md`**: does not exist (confirmed — `ls skills/references/` lists no subflow file).

Blast radius: one conditional branch in one step of `review-address`. Steps 4–9 of `review-address` are untouched. No callers of `review-init` change.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `review-address` — `review.md` missing | Calls `review-init` skill → notify + commit + agent stops | Inlines subflow → create file, continue immediately, no notify, no commit |
| Bug 1 — context loss | Agent receives notify message and stops prematurely | Eliminated: no notify step in subflow or step 3 |
| Bug 2 — wrong HEAD for TODO scan | `review-init` commit shifts HEAD before step 4 scan | Eliminated: no intermediate commit in subflow path |
| `review-init` standalone | Unchanged | Unchanged (subflow injected, same sequence: resolve → check → create → notify → commit) |
| `review-address` — `review.md` exists | Read and continue | Identical |

### 0.2 Non-regression proof

| At-risk case | Current behaviour | Guard |
|---|---|---|
| `review-init` standalone — creates `review.md` | Correct today | Steps 5–6 (notify + commit) remain explicit in `review-init`; subflow does NOT contain them |
| `review-init` standalone — already exists | "nothing to do" + stop | Subflow step B "check for existing" preserves this stop path; standalone still reaches it |
| `review-address` — `review.md` exists | Read and continue (step 3 `if` branch) | Outer `if` in step 3 is unchanged; subflow only reached in the `else` branch |
| `review-address` — subflow step B triggers in `else` branch | N/A (review.md confirmed absent by outer `if`) | Outer condition guarantees absence; step B is a harmless redundant guard |

---

## 1. Design overview

Three targeted changes:

1. **New** `skills/references/review-init-subflow.md` — passive shared document; contains the file-creation core (resolve folder/number, check for existing, write file); no side effects.
2. **Edit** `skills/hb-task-step-review-init.md` — collapse steps 2–4 to a single heading with `!` injection; update step 5's back-reference from "step 4" to "subflow step C above".
3. **Edit** `skills/hb-task-step-review-address.md` — replace step 3's `else` branch (invoke skill) with `!` injection; retitle step 3.

The `!`cat ${CLAUDE_SKILL_DIR}/references/...`` pattern is already used in both skills' Reference Files sections — no new mechanism.

**Control flow in `review-address` after this change:**

```
step 2: resolve $STEP_PATH, $N via hb-sdk
step 3: if review.md exists → read it, continue
        else → [subflow A: re-resolve $STEP_PATH/$N (idempotent)]
               [subflow B: check for existing (guard, never fires here)]
               [subflow C: write review.md from template]
               → read newly written review.md, continue
step 4: TODO REVIEW scan
        HEAD = user's work commit (no intermediate commit was made) ← Bug 2 fixed
```

**Alternatives considered and rejected:**

- *Separate helper skill for subflow*: introduces a new invocation boundary with its own entry/exit semantics — the root cause of the bug.
- *Duplicate creation logic in `review-address` step 3*: any future template change must be made in two places.
- *Pass a flag to `review-init` suppressing notification/commit*: complicates `review-init`'s interface; adds branching inside a standalone skill.

---

## 2. Core component — specification

### 2.1 `skills/references/review-init-subflow.md` (new)

A passive shared document injected via `!` by both skills. No notify step, no commit step.

Uses lettered sub-headings (A, B, C) to avoid numbering collision with the parent skill's numbered steps.

**Exact content to write:**

````markdown
> **Subflow — review.md file creation.** Shared by `hb-task-step-review-init` and
> `hb-task-step-review-address`. Contains no side effects (no user notification, no commit).

#### A. Resolve step folder

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step path <step_ref>
```

- captures the absolute path as `$STEP_PATH`
- if an error occurs, surface it verbatim and stop

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step number <step_ref>
```

- captures the numeric step number as `$N`
- if an error occurs, surface it verbatim and stop

#### B. Check for existing review.md

If `$STEP_PATH/review.md` already exists:

- read it and verify the required structure is present:
  - a `## Status` section containing a table with at least one row
  - a `## Notes` section containing at least one `### STEP-N-REVIEW-` heading
  - IDs in the status table match IDs in the notes section
- if structure is intact: report "review.md already exists — nothing to do" and stop
- if structure has drifted in a meaningful way (missing sections, empty table, mismatched IDs): notify the user of what is missing or inconsistent, then stop without modifying the file

#### C. Create review.md

Write `$STEP_PATH/review.md` with the following content (substituting `N` with the actual step number):

```markdown
# Step N Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-N-REVIEW-1 |            |

---

## Notes

###

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
```
````

**Failure contract:** If `hb-sdk` returns an error, surface verbatim and stop. If the Write fails, surface the error and stop.

### 2.2 `skills/hb-task-step-review-init.md` — step changes (refactor, behaviour preserved)

Replace the body of steps 2, 3, and 4 (lines 29–109) with a single consolidated heading plus `!` injection:

```markdown
### 2–4. Resolve step folder, check for existing review.md, and create review.md

!`cat ${CLAUDE_SKILL_DIR}/references/review-init-subflow.md`
```

Update step 5's two back-reference lines (currently "README-1 defined in step 4" / "README-2 defined in step 4") to:

```markdown
- README-1 defined in subflow step C above
- README-2 defined in subflow step C above
```

Steps 5 and 6 are otherwise unchanged.

| Original section | Status |
|---|---|
| `### 2. Resolve step folder` (lines 29–43) | Removed; content moved to subflow step A |
| `### 3. Check for existing review.md` (lines 45–58) | Removed; content moved to subflow step B |
| `### 4. Create review.md` (lines 60–109) | Removed; content moved to subflow step C |
| `### 5. Notify user` (lines 111–119) | Kept; back-reference to "step 4" updated to "subflow step C above" |
| `### 6. Commit` (lines 122–124) | Unchanged |

### 2.3 `skills/hb-task-step-review-address.md` — step 3 change (behaviour-altering)

Replace step 3 in full (lines 52–55). Current text:

```markdown
### 3. Read review.md

- if `$STEP_PATH/review.md` exists: read it and continue
- if it does not exist: invoke the `hb-task-step-review-init` skill for `<step_ref>`, then read the newly created `$STEP_PATH/review.md` and continue
```

Replacement:

```markdown
### 3. Create or read review.md

If `$STEP_PATH/review.md` already exists: read it and continue.

If it does not exist, create it now by following the subflow below, then read the newly created `$STEP_PATH/review.md` and continue. The subflow contains no user notification and creates no commit:

!`cat ${CLAUDE_SKILL_DIR}/references/review-init-subflow.md`
```

---

## 3. Integration / wiring

- Both skills reference `${CLAUDE_SKILL_DIR}/references/review-init-subflow.md` — the same `${CLAUDE_SKILL_DIR}` they already use for `hb-sdk`, `committing.md`, and `review-template.md`.
- No public skill interfaces change. No changes to `hb-sdk`, commit tooling, or any other skill.
- `skills/references/references-toc.md` should be extended with a row for the new subflow file so it appears in the Reference Files lookup table.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/review-init-subflow.md` | **new** — file-creation subflow (steps A, B, C); no side effects |
| `skills/hb-task-step-review-init.md` | **edit** — collapse steps 2–4 to `!` injection; update step 5 back-reference |
| `skills/hb-task-step-review-address.md` | **edit** — replace step 3 `else` branch with `!` injection; retitle step 3 |
| `skills/references/references-toc.md` | **edit** — add row for `review-init-subflow.md` |

No dependency manifests or lockfiles involved.

---

## 5. Tests

N/A — these are markdown skill instruction files consumed by the Claude agent at runtime, not executable code with a test suite. Correctness is verified through the manual trace in §6.

---

## 6. Verification (after implementation)

1. **Scope check** — only the four files in §4 changed: `git diff --name-only HEAD` should list exactly those four paths.

2. **Subflow structural integrity** — read `skills/references/review-init-subflow.md`: confirm exactly three sections (A, B, C); confirm no `### 5` or `### 6` step; confirm no "Tell the user" or notify block; confirm no `committing.md` reference.

3. **review-init trace** — read `skills/hb-task-step-review-init.md` and trace: step 1 (help check) → `### 2–4` heading with `!` injection → step 5 (notify, back-reference says "subflow step C above") → step 6 (commit). Confirm steps 5–6 are present and unchanged in substance.

4. **review-init idempotency preserved** — trace subflow step B: "if `$STEP_PATH/review.md` already exists … stop" — this path is still reachable from standalone `review-init`; confirm it fires before step C and before steps 5–6.

5. **review-address Bug 1 fix** — read `skills/hb-task-step-review-address.md` step 3: confirm no "invoke the `hb-task-step-review-init` skill" text; confirm no notify/tell-user instruction within step 3; confirm `!` injection of subflow is present in the `else` branch.

6. **review-address Bug 2 fix** — read step 3: confirm no `committing.md` reference within step 3; confirm the instruction to "read the newly created `$STEP_PATH/review.md` and continue" follows the subflow injection.

7. **references-toc.md** — confirm the new row for `review-init-subflow.md` is present.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Verified by |
|---|---|---|
| 1 — `review-init-subflow.md` exists with resolve + check + create logic | §2.1 (new file content) | §6.2 |
| 2 — `review-init` uses `!` injection; retains notify (step 5) and commit (step 6) | §2.2 (edit spec) | §6.3 |
| 3 — `review-address` step 3 uses `!` injection instead of invoking skill | §2.3 (edit spec) | §6.5 |
| 4 — `review-address` proceeds to step 4 after creating file; no notification shown | §2.3 (no notify in subflow; no notify in step 3) | §6.5 |
| 5a — `review-init` standalone: create, notify, commit | §2.2 (steps 5–6 kept) | §6.3 |
| 5b — `review-init` standalone: idempotent on existing `review.md` | §2.1 subflow step B (stop if exists) | §6.4 |

---

## 8. Out of scope (per ticket)

- Changes to the TODO REVIEW scan logic (step 4 of `review-address`).
- The `--commits N` default value.
- Any `review-address` steps beyond step 3.
- Changes to `hb-sdk` scripts or commit tooling.
