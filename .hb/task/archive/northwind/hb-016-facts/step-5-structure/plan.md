# Step 5 Plan — Document `facts.md` in `structure.md`

hb-016 added `.hb/facts.md`, a project-level facts store written via
`hb-sdk facts write` (`skills/scripts/hb_sdk/facts.py:10-16`, `read_facts`/
`write_facts` operate on `path_hb_facts()` — a single top-level file directly
under `.hb/`, resolved in `skills/scripts/hb_sdk/common.py:87`). `structure.md`
(`skills/references/structure.md`) documents the `.hb/` layout but was written
before hb-016 and never mentions `facts.md` at all — neither in the prose
bullet list (lines 1–24) nor in any of the three "Structure Examples" trees
(lines 27–132). This step is a **documentation-only** change: add `facts.md`
to the prose and to the example trees so the reference doc matches what the
SDK actually creates. No code changes, no new behavior.

Source ticket: `./ticket.md`. Builds on the **shipped** work from hb-016
step-0 (`facts.py`, `common.py` — the facts store itself) and does not depend
on step-1/step-2 (planning/execution wiring), which are separate consumers of
the same file. This plan targets `structure.md` as it exists now (no
`facts.md` mention anywhere in the file).

---

## 0. Current-state facts (verified during planning)

- `skills/references/structure.md:3-4` states "all files in `.hb` at
  top-level in project directory" then immediately drops to `task/` as the
  only top-level item documented — `facts.md` is a sibling of `task/` at that
  same top level, confirmed by `path_hb_facts()` in
  `skills/scripts/hb_sdk/common.py:87` returning a path directly under the
  `.hb/` root, not nested under `task/`.
- Existing convention for "created by" notes: `structure.md:20-23` documents
  each step-level file with a one-line "created by <skill>" note, e.g.
  `` `plan.md`: created by /hb-task-step-plan ``. `facts.md` should follow the
  same phrasing style: created/maintained by `hb-sdk facts write` (not a
  slash-skill directly — multiple skills invoke that SDK command, per
  `skills/scripts/hb_sdk/facts.py:40-42`).
- Three "Structure Examples" trees exist (`structure.md:27-59`, `61-81`,
  `83-132`), each rooted at `.hb/` with only a `task/` child. All three need a
  `facts.md` leaf added as a sibling of `task/` to stay consistent with the
  updated prose.
- No other file in `skills/references/` or `skills/*.md` currently documents
  `.hb/facts.md`'s location — `skills/references/facts-template.md` covers
  authoring guidance/content, not folder placement.

### 0.1 Impact (before → after)

| Aspect | Before | After |
|---|---|---|
| Prose top-level file list | Only `task/` described | `task/` and `facts.md` both described, each with a one-line purpose |
| "created by" convention | Applied to `ticket.md`/`plan.md`/`execution-*.md`/`review.md` only | Also applied to `facts.md` → `hb-sdk facts write` |
| Example trees (×3) | `.hb/` → `task/` only | `.hb/` → `task/` and `facts.md` (sibling, shown once per tree at the `.hb/` root) |

This is purely additive — no existing line in `structure.md` is removed or
reworded beyond inserting new bullets/tree entries.

### 0.2 Non-regression proof / risk

Purely additive documentation change: no existing bullet, table row, or tree
line is altered or deleted, only new lines inserted. No code, no `hb-sdk`
behavior, no other skill file is touched. Risk is limited to prose
accuracy/formatting, which is caught by visual review in §6.

---

## 1. Design overview

Single linear change, no alternatives to weigh:

1. In the top-level prose block (`structure.md:3-4`), add a bullet for
   `facts.md` alongside the existing `task/` bullet, per AC 1.
2. Immediately after (or as part of that same bullet), note the creator per
   AC 2, mirroring the `` `plan.md`: created by /hb-task-step-plan `` style
   already used for step files.
3. In each of the three example trees, add a `facts.md` line as a sibling of
   `task/` directly under the `.hb/` root, per AC 3.

**Alternatives considered and rejected:**
- Documenting `facts.md` only in the prose and skipping the tree diagrams —
  rejected: AC 3 explicitly requires the trees stay consistent with the
  prose, and leaving them out would make the doc self-contradictory (prose
  says facts.md exists at top level, trees show it doesn't).
- Adding a new "Top-level files" subsection instead of extending the existing
  bullet list — rejected: over-structuring a two-item list; the existing flat
  bullet format already accommodates one more line without restructuring.

---

## 2. `structure.md` — specification

No code; this is prose/markdown. Content additions:

- **Prose bullet (new)** — inserted after the `- all files in `.hb` at
  top-level...` line and before/alongside the `task/` bullet:
  ```
  - `facts.md`: persistent, project-level facts store; created/maintained
    via `hb-sdk facts write`
  ```
- **Tree diagrams (3×, edit)** — in each of the three fenced code blocks
  (`structure.md:27-59`, `61-81`, `83-132`), add a `facts.md` line as a
  sibling of `task/` at the `.hb/` root, e.g.:
  ```
  .hb/
  ├── facts.md
  └── task/
      └── ...
  ```
  Use `├──` for `facts.md` and change `task/`'s connector to `└──` (or keep
  whichever ordering renders as a valid tree — `facts.md` then `task/` is
  alphabetical and matches the prose order).
- **Failure/degradation contract** — N/A, this is documentation with no
  runtime behavior.

---

## 3. Integration / wiring

Self-contained: only `skills/references/structure.md` changes. No other
skill file, script, or config references this file's exact content in a way
that would break (the other skills that mention `structure.md` in their
"Reference Files" tables just point to it by path, per
`skills/hb-status.md`'s reference table).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/structure.md` | **edit** — add `facts.md` bullet to top-level prose list; add `facts.md` line to all 3 example trees. Task/step name-format sections (lines 134-192) stay untouched. |

No dependency-manifest or lockfile effects — markdown-only change.

---

## 5. Tests

N/A — documentation-only change with no executable behavior to test. No
existing test file covers `structure.md`'s prose content (confirmed: no
`test_structure*` file under `tests/`).

---

## 6. Verification (after implementation)

1. `git diff skills/references/structure.md` shows only additive lines (no
   existing line removed/reworded).
2. Visually confirm the prose bullet for `facts.md` appears at the same
   nesting level as the `task/` bullet (both top-level children of `.hb/`).
3. Visually confirm all three tree diagrams now show `facts.md` as a sibling
   of `task/`, with consistent tree-drawing characters (no broken `├──`/`└──`
   pairs).
4. Per-AC checks:
   - AC 1: prose lists `facts.md` as a top-level file with a one-line
     purpose — confirm by reading the new bullet.
   - AC 2: prose notes `facts.md` is created/maintained via
     `hb-sdk facts write` — confirm the phrase appears verbatim.
   - AC 3: all 3 trees include a `facts.md` entry — confirm by grep:
     `grep -c facts.md skills/references/structure.md` returns `4` (1 prose
     mention + 3 tree entries).
5. Scope check: `git status --short` shows only
   `skills/references/structure.md` modified.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (prose bullet) | New bullet alongside `task/`, one-line purpose |
| 2 | §2 (prose bullet) | Same bullet states creator: `hb-sdk facts write` |
| 3 | §2 (tree diagrams) | All 3 example trees updated identically |

---

## 8. Out of scope (per ticket)

- No changes to `facts.py`, `common.py`, or any `hb-sdk` behavior.
- No changes to `facts-template.md` (authoring guidance is already covered
  there; this step only documents *location*, not *content*).
- No changes to the Task/Step Name Format sections of `structure.md`.
- No changes to other skills' "Reference Files" tables that point at
  `structure.md`.
