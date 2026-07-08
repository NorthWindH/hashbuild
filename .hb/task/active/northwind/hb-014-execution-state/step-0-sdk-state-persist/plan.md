# Step 0 Plan — Add `hb-sdk state` persistence + `.gitignore` primitive

This step adds the foundational `hb-sdk` primitive for recording and reading a
last-executed-action record. Today `.hb/` has no persistence mechanism at all —
`hb_sdk/summarize.py` (`skills/scripts/hb_sdk/summarize.py:249-323`) only re-derives
status by walking files on disk each time it runs, so nothing survives across
conversations to answer "what did the last skill invocation do?". This step is
purely additive: a new `hb_sdk/state.py` module, two small `common.py` helpers, and
one call from `cmd_init`. No existing command's behavior, signature, or output
changes. The single externally observable effect once this lands: after any
`hb-sdk init`, `.hb/state.json` is listed in `.gitignore`, and
`hb-sdk state record ...` followed by `hb-sdk state show` round-trips a JSON record
that git never tracks.

Source ticket: `./ticket.md`. This is the first step of task `hb-014`; there is no
prior step to build on — this plan targets `hb_sdk` as it exists on `master` today
(commit `50a2148`).

> **Design decision — where does "staging" actually happen, and how do we verify
> AC8?** The ticket asks to "verify `hb_sdk/commit.py`'s staging logic does not
> pick up `.hb/state.json`". Inspection of `hb_sdk/commit.py` (read in full) shows
> it never calls `git add` — it only writes a commit-message file to a temp path.
> The actual staging happens in skill Markdown, per
> `skills/references/committing.md` §Process/1: the executing assistant runs
> `git status --short -b` to enumerate changed files, then `git add
> <file_or_directory>` only for files that step identifies as "relevant". So there
> is no staging *code* to unit-test directly. The correct, testable proxy is: once
> `.hb/state.json` is listed in `.gitignore`, `git status --short` never reports it
> (neither as `??` untracked nor as modified), so it can never appear in that
> "relevant files" enumeration in the first place, and `git add .` (or any
> file-by-file `git add`) will not pick it up either. §5 adds a test that does
> exactly this: `git init` a temp repo, run `hb-sdk init` + `hb-sdk state record`,
> then assert `git status --short` output does not mention `state.json`.

---

## 0. Current-state facts (verified during planning)

- `hb_sdk/common.py` (`skills/scripts/hb_sdk/common.py`) holds all shared path
  helpers (`path_hb()`, `path_hb_git_keep()`, `path_hb_asserted()`,
  `path_task_ticket()`, `path_step_ticket()`) and the `exists_or_do` /
  `progress` / `die` conventions. There is no gitignore-related helper yet, and
  no top-level `.gitignore` path helper.
- `hb_sdk/init_cmd.py:10-17` (`cmd_init`) currently does exactly two things via
  `exists_or_do`: create `.hb/` and touch `.hb/.gitkeep`. `exists_or_do` creates a
  path **only if absent** and dies if creation silently fails — it is designed for
  idempotent file/dir creation, not for content mutation of an existing file, so it
  does not fit the "idempotently append a line to `.gitignore`" operation this step
  needs (see §2 for why `ensure_gitignore_entry` is a standalone function instead).
- `hb_sdk/idea.py` is the closest existing precedent for a JSON-file-backed command
  group: `_load_idea_file`/`_save_idea_file` (`idea.py:19-29`) read/write JSON with
  `json.loads(p.read_text())` / `p.write_text(json.dumps(data, indent=2) + "\n")`,
  and `def_cli_idea` (`idea.py:101-122`) shows the nested-subparser pattern
  (`p_idea` → `idea_subs` with `required = True` → per-action parsers). `state`
  will mirror this shape exactly (`p_state` → `state_subs` → `record`/`show`).
- `hb_sdk/summarize.py:326-343` (`cmd_summarize`/`def_cli_summarize`) is the
  existing precedent for a `--format json|md` flag: `choices=["json", "md"]`,
  `default="json"`. `state show` reuses this exact flag shape.
- `hb_sdk/__main__.py:1-28` wires each command group with one `def_cli_*(subs)`
  call inside `main()`. Adding `state` means one new import + one new call, in the
  same alphabetized-by-topic style already used (init, task, summarize, commit,
  idea).
- Repo root `.gitignore` (`/Users/hasan.kamal-al-deen/repos/hashbuild/.gitignore`)
  currently has 5 lines (`HANDOFF.json`, `__pycache__`, `.venv`, `.pytest_cache`,
  `.planning`) and no trailing-newline issues — it ends cleanly. There is no
  existing `.hb/` entry in it today; `hb-sdk init` has never touched
  `.gitignore` before this step.
- Tests live at `tests/skills/scripts/hb_sdk/` (not `tests/skills/scripts/` —
  confirmed via `find`), run via `uv run pytest` (`Makefile:4`) from repo root.
  `helpers.py` (`tests/skills/scripts/hb_sdk/helpers.py`) is the single place that
  wraps CLI invocations as Python functions for tests (`run`, `init`,
  `task_create`, `idea_add`, etc.) — all following the same
  `run(args, cwd, ok=...) -> CompletedProcess` shape via `SDK = Path(__file__).parents[4] / "skills" / "scripts" / "hb-sdk"`.
  New tests need `state_record`/`state_show` helpers added here.
- `test_hb_sdk_init.py` (3 tests, 23 lines) is the existing precedent for `init`
  behavior tests (idempotency, `.gitkeep` creation, failure without `.hb/`) — this
  step extends it with gitignore-entry assertions rather than creating a parallel
  file, since it is testing the same command.

### 0.1 Impact (before → after)

| Aspect | Before | After |
|---|---|---|
| `.hb/state.json` | Does not exist; no code path creates or reads it | Created/overwritten by `hb-sdk state record`; read by `hb-sdk state show` |
| `.gitignore` (repo root) | No `.hb/` entries | Contains a `.hb/state.json` line, added once by `hb-sdk init` |
| `hb-sdk` CLI surface | `init`, `task`, `summarize`, `commit`, `idea` | + `state` (`record`, `show`) |
| `hb_sdk/common.py` | No gitignore helper | + `path_project_gitignore()`, `path_hb_state()`, `ensure_gitignore_entry()` |

This is purely additive: no existing function signature, CLI flag, JSON shape, or
file layout changes. `cmd_init` gains one extra `progress`-logged side effect
(the `.gitignore` append) but its existing two `exists_or_do` calls and its
`report_paths` output are unchanged.

### 0.2 Non-regression proof

Purely additive change — no table needed. `cmd_init` only gains a new statement
appended after its existing two `exists_or_do(...)` calls; those calls, their
return values, and `report_paths(paths)` are untouched, so `test_init_creates_hb_dir`
and `test_init_idempotent` continue to pass unmodified. No other command reads or
writes `.gitignore` or `.hb/state.json`, so there is no cross-command interaction
to break.

---

## 1. Design overview

Single linear addition, no ordered alternatives or precedence chain:

1. `common.py` gains three additions: `path_project_gitignore()` (path helper),
   `path_hb_state()` (path helper), and `ensure_gitignore_entry(entry: str) -> None`
   (the reusable idempotent-append primitive from AC5).
2. New `hb_sdk/state.py` owns the record/read functions and the `state`
   CLI subcommand group (`record`, `show`), mirroring `idea.py`'s shape.
3. `init_cmd.py::cmd_init` calls `ensure_gitignore_entry(".hb/state.json")` after
   its existing two `exists_or_do` calls.
4. `__main__.py` imports and registers `def_cli_state`.

**Alternatives considered and rejected:**

- *Store state under `.hb/` with its own per-file `.gitignore` (e.g.
  `.hb/.gitignore`) instead of the project-root `.gitignore`.* Rejected — AC6
  explicitly says "`hb-sdk init` calls this primitive to ensure `.hb/state.json`
  is listed in the project's `.gitignore`", i.e. the root one. A nested
  `.hb/.gitignore` would also require every consumer of `git status`/`git add`
  (i.e. the assistant following `committing.md`, which runs those commands from
  the repo root) to know about a second ignore file's semantics — extra
  indirection for no benefit.
- *Use `exists_or_do` for the `.gitignore` append.* Rejected — `exists_or_do` only
  ever creates a path once; the append must run and be checked for idempotency
  every single time `hb-sdk init` runs (AC7: "twice in a row does not duplicate"),
  including on a `.gitignore` that already exists with unrelated content. That is
  a different operation (conditional in-place mutation) than "create if absent",
  so `ensure_gitignore_entry` is its own function that does its own existence/dup
  check, called unconditionally from `cmd_init`.
- *Make `state record` merge/append multiple records (a list/log) instead of
  overwriting.* Rejected — AC2 is explicit: "overwriting any prior record — only
  the latest action is retained." A log is also explicitly deferred by the ticket
  ("Out of scope": next-action derivation, `hb-flow` surfacing — both later steps
  that may or may not need history; this step stays minimal).
- *Auto-generate the timestamp inside `state.py` (e.g. `datetime.now()`).*
  Rejected — ticket AC1.1 explicitly requires a caller-supplied timestamp so
  `hb-sdk` stays deterministic/testable, matching the project's existing
  determinism stance (no other `hb_sdk` module calls `datetime.now()` or
  similar).

---

## 2. `hb_sdk/common.py` — new helpers

**Data model:** none (no new dataclass) — `ensure_gitignore_entry` operates on
plain text lines.

**Interfaces / signatures** (all **new**):

```python
def path_project_gitignore() -> Path:
    """Repo-root .gitignore, alongside .hb/ (not inside it)."""
    return Path.cwd() / ".gitignore"


def path_hb_state() -> Path:
    return path_hb() / "state.json"


def ensure_gitignore_entry(entry: str) -> None:
    """Idempotently append `entry` as its own line to the project .gitignore.

    Creates the file if absent. No-ops if a line matching `entry` verbatim
    already exists (exact line match, not substring).
    """
```

**Algorithm / rules:**

- Read `path_project_gitignore()` if it exists; split into lines with
  `.splitlines()` (strips trailing newline artifacts so comparison is exact
  per-line, not substring).
- If `entry` already equals one of those lines exactly: no-op (`progress` a
  "already present" message for symmetry with `_progress_already_exists`, but do
  not reuse that private helper since it takes a `Path`, not a string — write a
  small inline `progress(...)` call instead).
- Otherwise: append `entry + "\n"` to the file, creating it if it doesn't exist.
  When appending to an existing file, first ensure the existing content ends with
  a newline (guard against a `.gitignore` whose last line lacks one) before
  writing the new line, so the entry never gets glued onto the previous line.
- Failure/degradation: none of the modes here can silently fail — direct
  `Path.write_text`/`read_text` calls raise on OS errors, which is the same
  fail-loud behavior as every other `hb_sdk` file-writing function (e.g.
  `idea._save_idea_file`). No new error handling is added, matching the "no
  defensive code for cases that can't happen" project convention.

**Conflict resolution:** N/A — single-writer, single-entry-per-call operation. No
concurrent access to `.gitignore` is a stated concern in the ticket.

---

## 3. `hb_sdk/state.py` — new module

**Data model:** the on-disk record at `.hb/state.json` is a flat JSON object:

```json
{
  "skill": "hb-task-step-plan",
  "outcome": "success",
  "timestamp": "2026-07-08T00:00:00Z",
  "task": "northwind/hb-014",
  "step": "0"
}
```

`task` and `step` are `null` when not supplied (they are independent optional
fields — AC2's CLI signature lists `[--task <ref>]` and `[--step <ref>]`
separately, so the record does not assume a combined "task/step ref" string, and
neither is validated against `TASK_NAME_RE` since a caller may record state for a
skill invocation that doesn't cleanly map to an existing task).

**Interfaces / signatures** (all **new**):

```python
def write_state(record: dict[str, str | None]) -> Path:
    """Overwrite .hb/state.json with `record`. Returns the path written."""

def read_state() -> dict[str, str | None] | None:
    """Return the current record, or None if .hb/state.json does not exist."""

def cmd_state_record(args: argparse.Namespace) -> None: ...
def cmd_state_show(args: argparse.Namespace) -> None: ...
def def_cli_state(subs: Any) -> None: ...
```

**Algorithm / rules:**

- `write_state`: use `path_hb_asserted()` (not bare `path_hb()`) before deriving
  `path_hb_state()` — consistent with `idea.py`'s `path_idea_dir`/`path_idea_file`,
  which both key off `path_hb_asserted()` so that recording state without having
  run `hb-init` first fails with the same clear
  `"error: .hb/ directory not found; ..."` message every other command gives,
  rather than a raw `FileNotFoundError`. `progress(f"writing state to {p.absolute()} ...")`
  then `p.write_text(json.dumps(record, indent=2) + "\n")`, mirroring
  `idea._save_idea_file`'s exact JSON-dump formatting.
- `read_state`: `path_hb_asserted()` then check `path_hb_state().exists()` → return
  `None`; else `json.loads(p.read_text())`.
- `cmd_state_record`: build the record dict from `args.skill`, `args.outcome`,
  `args.timestamp`, `args.task` (`None` if not passed — `argparse` default),
  `args.step` (`None` if not passed), call `write_state(record)`. No stdout output
  (matches `idea_remove`/`idea_set_content`, which are silent on success — only
  `idea_add` prints, because it returns a generated index the caller needs).
- `cmd_state_show`:
  - `record = read_state()`
  - if `args.format == "md"`:
    - if `record is None`: `print("No recorded state.")`
    - else: render a small fixed-order list (`Skill`, `Outcome`, `Timestamp`,
      `Task`, `Step`), using `"—"` for `None` fields (same placeholder character
      `summarize._render_md._cell` already uses for "no value", for visual
      consistency across `hb-sdk` markdown output).
  - else (`json`, the default): `print(json.dumps(record if record is not None else {}, indent=2))`
    — matches AC3's "or empty JSON when absent" wording exactly.
- **Failure/degradation contract:** `state show` never errors on a missing
  record — absence is a valid, expected state (first run before anything has
  executed), so it prints the empty/placeholder form rather than calling `die`.
  `state record` requires `--skill`, `--outcome`, `--timestamp` (argparse
  `required=True`); missing any of them is argparse's own usage error, consistent
  with how `commit write-message-file`'s required flags behave.

**Conflict resolution:** N/A — `record` always overwrites in full (AC2), no
merge logic.

**CLI wiring** (mirrors `idea.py:101-122`):

```python
def def_cli_state(subs: Any) -> None:
    p_state = subs.add_parser("state", help="State persistence operations")
    state_subs = p_state.add_subparsers(dest="state_command", metavar="<action>")
    state_subs.required = True

    p_record = state_subs.add_parser("record", help="Record last-executed-action state")
    p_record.add_argument("--skill", required=True, metavar="<name>")
    p_record.add_argument("--outcome", required=True, metavar="<outcome>")
    p_record.add_argument("--timestamp", required=True, metavar="<ts>")
    p_record.add_argument("--task", metavar="<ref>")
    p_record.add_argument("--step", metavar="<ref>")
    p_record.set_defaults(func=cmd_state_record)

    p_show = state_subs.add_parser("show", help="Show current recorded state")
    p_show.add_argument("--format", choices=["json", "md"], default="json")
    p_show.set_defaults(func=cmd_state_show)
```

---

## 4. Integration / wiring

- `init_cmd.py::cmd_init`: after the existing two `exists_or_do(...)` calls (line
  14), add one call: `ensure_gitignore_entry(".hb/state.json")`. Import
  `ensure_gitignore_entry` from `.common` alongside the existing imports.
  `cmd_init`'s signature, its `paths` list, and `report_paths(paths)` call are
  **unchanged** — the gitignore write is a side effect, not a tracked "affected
  path" (mirrors how `.gitkeep`'s creation *is* tracked because it's a fresh path
  under `.hb/`, whereas `.gitignore` is a pre-existing repo-root file being
  mutated, not created — consistent with `report_paths`'s doc comment "affected
  paths" referring to newly-created `.hb/` structure).
- `__main__.py`: add `from .state import def_cli_state` (alphabetically after
  `.init_cmd`? — existing imports are ordered `commit, idea, init_cmd, summarize,
  task`, i.e. alphabetical by module name; `state` sorts after `summarize` and
  before `task`) and add `def_cli_state(subs)` in the same relative position
  inside `main()`.
- No build, dependency, or entry-point script changes — `skills/scripts/hb-sdk`
  already dispatches through `hb_sdk.__main__.main`, so a new subcommand needs no
  changes there.

---

## 5. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/common.py` | **extend** — add `path_project_gitignore()`, `path_hb_state()`, `ensure_gitignore_entry()`; all existing functions/constants untouched |
| `skills/scripts/hb_sdk/state.py` | **new** — `write_state`, `read_state`, `cmd_state_record`, `cmd_state_show`, `def_cli_state` |
| `skills/scripts/hb_sdk/init_cmd.py` | **extend** — `cmd_init` gains one call to `ensure_gitignore_entry`; import list gains `ensure_gitignore_entry`; `def_cli_init` untouched |
| `skills/scripts/hb_sdk/__main__.py` | **extend** — add `state` import + registration; all other command registrations untouched |
| `tests/skills/scripts/hb_sdk/helpers.py` | **extend** — add `state_record(cwd, **kwargs)` and `state_show(cwd, **kwargs)` wrapper functions, matching the existing `idea_*`/`commit_*` helper shape |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_init.py` | **extend** — add gitignore-entry assertions to (or alongside) the existing init tests |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_state.py` | **new** — full test suite for `state record`/`state show`, plus the git-status non-tracking test |

No dependency manifest or lockfile changes — `pyproject.toml` dependencies stay
`[]`; the module only uses stdlib (`argparse`, `json`, `subprocess` in tests).

---

## 6. Tests

Framework/layout: `pytest`, mirroring `test_hb_sdk_idea.py`'s structure (plain
functions, `tmp_path` fixture, section-comment dividers per subcommand,
`helpers.py`-wrapped CLI calls). Fixture strategy: hermetic `tmp_path` dirs via
the CLI subprocess helper (`helpers.run`), same as every other `hb_sdk` test file
— no in-memory mocking of the CLI.

**`helpers.py` additions:**

```python
def state_record(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["state", "record"]
    if skill := kwargs.get("skill"):
        args += ["--skill", skill]
    if outcome := kwargs.get("outcome"):
        args += ["--outcome", outcome]
    if timestamp := kwargs.get("timestamp"):
        args += ["--timestamp", timestamp]
    if task := kwargs.get("task"):
        args += ["--task", task]
    if step := kwargs.get("step"):
        args += ["--step", step]
    return run(args, cwd, ok=kwargs.get("ok", True))


def state_show(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["state", "show"]
    if fmt := kwargs.get("format"):
        args += ["--format", fmt]
    return run(args, cwd, ok=kwargs.get("ok", True))
```

**`test_hb_sdk_state.py` — new, grouped by subcommand:**

- *record — happy path*
  - `test_state_record_writes_json_file`: `init`, `state_record(skill="hb-task-create", outcome="success", timestamp="2026-01-01T00:00:00Z")`; assert `.hb/state.json` exists and `json.loads(...)` matches all fields, with `task`/`step` both `None`.
  - `test_state_record_with_task_and_step`: same but with `task="northwind/hb-014"`, `step="0"`; assert both round-trip.
- *record — overwrite semantics (AC2)*
  - `test_state_record_overwrites_prior_record`: record twice with different `skill`/`outcome` values; assert the file contains only the second record (no list, no merge).
- *record — no `.hb/` (fail-loud, matches every other command)*
  - `test_state_record_no_hb`: call `state_record` without `init`; assert non-zero exit and `".hb/"` in stderr (same assertion shape as `test_idea_add_no_hb`).
- *record — missing required flags*
  - `test_state_record_requires_skill` / `_outcome` / `_timestamp`: omit each required flag one at a time; assert non-zero exit (argparse usage error).
- *show — happy path, JSON (default)*
  - `test_state_show_json_after_record`: record then show with no `--format`; assert parsed JSON equals the recorded fields.
- *show — happy path, JSON, absent (AC3)*
  - `test_state_show_json_absent`: `init` only, no record; assert `json.loads(stdout) == {}`.
- *show — markdown (AC3)*
  - `test_state_show_md_after_record`: record then `state_show(format="md")`; assert stdout contains the skill/outcome/timestamp values as text (not JSON-parsed — markdown is prose).
  - `test_state_show_md_absent`: no record; assert stdout is the "no recorded state" message (exact string match against `"No recorded state."`).
- *show — no `.hb/`*
  - `test_state_show_no_hb`: call without `init`; assert non-zero exit and `.hb/` in stderr.
- *gitignore integration (AC5, AC6, AC7) — colocated here since they're state.json-specific, though they exercise `init`*
  - `test_init_adds_state_json_to_gitignore`: `init(tmp_path)`; assert `(tmp_path / ".gitignore").read_text()` contains a `.hb/state.json` line.
  - `test_init_twice_does_not_duplicate_gitignore_entry`: `init` twice; assert the `.gitignore` text contains exactly one line equal to `.hb/state.json` (count via `.splitlines()`, not substring count, so a hypothetical `.hb/state.json.bak` entry wouldn't false-positive).
  - `test_init_preserves_existing_gitignore_content`: pre-write a `.gitignore` with an unrelated entry (e.g. `"node_modules\n"`) before calling `init`; assert both the original line and the new `.hb/state.json` line are present afterward, and the original line is untouched.
- *AC8/AC9 — git-status non-tracking end-to-end proof*
  - `test_state_json_not_reported_by_git_status`: `subprocess.run(["git", "init"], cwd=tmp_path, ...)` (also set a throwaway `user.email`/`user.name` via `git -C tmp_path config` if the sandboxed git requires it — check locally first, since CI git may already have global config), then `init(tmp_path)`, `state_record(...)`, then `subprocess.run(["git", "status", "--short"], cwd=tmp_path, capture_output=True, text=True)`; assert `"state.json"` does not appear anywhere in `result.stdout`. This is the direct, automatable proxy for AC8 discussed in the design-decision callout above.

**Non-regression:** `test_hb_sdk_init.py`'s two existing tests
(`test_init_creates_hb_dir`, `test_init_idempotent`) must keep passing unmodified
— they assert `.hb/` and `.hb/.gitkeep` exist, which `cmd_init`'s new statement
doesn't touch. `test_init_fails_without_hb` also stays unchanged (unrelated to
`state` or `.gitignore`). All existing `test_hb_sdk_idea.py`,
`test_hb_sdk_commit.py`, `test_hb_sdk_task.py`, `test_hb_sdk_summarize.py` suites
are unaffected since no shared function they call changes signature or behavior.

---

## 7. Verification (after implementation)

1. **Full test run is green:** `uv run pytest` from repo root — all existing
   suites plus the new `test_hb_sdk_state.py` pass.
2. **Manual round-trip (AC9), fresh temp dir:**
   ```bash
   cd "$(mktemp -d)"
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk init
   cat .gitignore   # expect: a line containing .hb/state.json
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk init   # run twice
   grep -c '^\.hb/state\.json$' .gitignore   # expect: 1 (not 2)
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk state record --skill hb-task-create --outcome success --timestamp 2026-01-01T00:00:00Z --task northwind/hb-014 --step 0
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk state show
   # expect: JSON with skill/outcome/timestamp/task/step matching the record call
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk state show --format md
   # expect: readable markdown, no stack trace
   ```
3. **Per-AC checks:** the traceability table in §8 maps every AC to a test in §6
   and/or a verification command here; run through it and confirm each row's
   named test actually passes.
4. **Invariant checks:** `.hb/state.json` is valid JSON at all times after a
   `record` call (`json.loads` in the tests is the authoritative check); `.gitignore`
   never loses pre-existing lines (`test_init_preserves_existing_gitignore_content`
   is authoritative).
5. **Scope check:** `git diff --stat` after implementation should show changes
   only in the 4 source files + 3 test files listed in §5 — no changes to
   `task.py`, `summarize.py`, `commit.py`, `idea.py`, or any skill Markdown
   (wiring skills to call `state record` is explicitly out of scope for this
   step).

---

## 8. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 (`hb_sdk/state.py` module: write + read functions) | §3 | `write_state`/`read_state` |
| 1.1 (write captures skill, task/step ref, outcome, caller-supplied timestamp) | §3 data model | `task`/`step` optional, `timestamp` never generated internally |
| 1.2 (read returns `None`/absent when file missing) | §3 `read_state` | `test_state_show_json_absent` exercises this via the CLI |
| 2 (`hb-sdk state record ...` overwrites) | §3 `cmd_state_record`/CLI wiring | `test_state_record_overwrites_prior_record` |
| 3 (`hb-sdk state show [--format json|md]`) | §3 `cmd_state_show` | `test_state_show_json_after_record`, `test_state_show_md_after_record`, absent-case tests |
| 4 (`exists_or_do`/`progress`/path-helper conventions where applicable; `path_hb_state()` in `common.py`) | §2, §3 | `path_hb_state()` added to `common.py`; `exists_or_do` doesn't fit overwrite semantics (see design-decision callout in §1's alternatives) — `progress()` and `path_hb_asserted()` conventions are used instead |
| 5 (`ensure_gitignore_entry` primitive in `common.py`, idempotent, used by `cmd_init` and available for future commands) | §2 | `test_init_adds_state_json_to_gitignore`, `test_init_twice_does_not_duplicate_gitignore_entry` |
| 6 (`hb-sdk init` ensures `.hb/state.json` is in `.gitignore`) | §4 | `test_init_adds_state_json_to_gitignore` |
| 7 (running `init` twice doesn't duplicate the entry) | §2, §4 | `test_init_twice_does_not_duplicate_gitignore_entry` |
| 8 (no skill or `commit` staging path stages/commits `.hb/state.json`) | §1 design-decision callout, §6 | `test_state_json_not_reported_by_git_status` — automated proxy since the real staging step is manual (`committing.md`), not code |
| 9 (manual verification: fresh-dir `init` → `.gitignore` entry; `record`→`show` round-trip) | §7 step 2 | Manual command sequence; also covered automatically by `test_state_record_writes_json_file` + `test_state_show_json_after_record` |

---

## 9. Out of scope (per ticket)

- Wiring any existing `hb-*` skill to call `hb-sdk state record` after completing
  — deferred to the next step.
- Deriving a recommended next-action from the recorded state — deferred to a
  later step.
- The `hb-flow` skill that surfaces this state to the user — deferred to a later
  step.
- A history/log of past actions (only the single latest record is retained, per
  AC2).
