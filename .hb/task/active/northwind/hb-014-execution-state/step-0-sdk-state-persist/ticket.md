# Background

The task ticket (AC 1, 2) requires hashbuild to persist a record of the last executed action (which skill ran, against which task/step, and its outcome) so it survives across conversations. Today `.hb/` has no `state.json` or any mechanism for recording execution state — `hb_sdk/summarize.py` only re-derives status by inspecting files on disk each time.

This step builds the foundational `hb-sdk` persistence primitive that later steps (wiring skills to call it, and deriving next-action from it) will depend on. It does not wire any existing skill to call the new mechanism yet, and does not implement next-action derivation logic — those are separate steps.

---

# Goal

Add a `hb-sdk state` command group that can record and read a last-executed-action entry at `.hb/state.json`, and ensure that file is never tracked by git.

---

# Acceptance Criteria

## A. State persistence

1. A new `hb_sdk/state.py` module exposes:
    1. A function to write a last-executed-action record to `.hb/state.json`, capturing at minimum: the skill name, the task/step reference it ran against (if any), the outcome (e.g. `success`/`failure`), and a caller-supplied timestamp string (the module does not generate timestamps itself — it accepts one as an argument, since `hb-sdk` must stay deterministic/testable).
    2. A function to read the current record back from `.hb/state.json`, returning `None`/absent-equivalent when the file does not exist.
2. `hb-sdk state record --skill <name> --outcome <outcome> --timestamp <ts> [--task <ref>] [--step <ref>]` writes the record (overwriting any prior record — only the latest action is retained).
3. `hb-sdk state show [--format json|md]` prints the current record (or a clear "no recorded state" message/empty JSON when absent).
4. Writing `.hb/state.json` uses the same `exists_or_do`/`progress`/path-helper conventions as other `hb_sdk/common.py`-based commands where applicable (e.g. a `path_hb_state()` helper in `common.py`).

## B. Git exclusion

5. `hb-sdk init` idempotently ensures `.hb/state.json` is listed in the project's `.gitignore` (creating `.gitignore` if absent, appending the entry only if not already present).
6. Running `hb-sdk init` twice in a row does not duplicate the `.gitignore` entry.
7. No existing `hb-*` skill or `hb-sdk commit` staging path stages or commits `.hb/state.json` (verify `hb_sdk/commit.py`'s staging logic does not pick it up, e.g. by relying on the `.gitignore` entry).

## C. Tests / verification

8. Manual verification: after `hb-sdk init` in a fresh temp dir, `.gitignore` contains a `.hb/state.json` (or equivalent `.hb/*.json`-scoped, but not overly broad) entry; `hb-sdk state record ...` followed by `hb-sdk state show` round-trips the same values.

---

# Out of scope

- Wiring any existing `hb-*` skill (`hb-task-create`, `hb-task-step-plan`, etc.) to actually call `hb-sdk state record` after completing — deferred to the next step.
- Deriving a recommended next-action from the recorded state — deferred to a later step (`hb-sdk` next-action logic step).
- The new `hb-flow` skill that surfaces this state to the user — deferred to a later step.
