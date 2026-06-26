# Step 0 Plan — Add `task unarchive` subcommand to hb-sdk

`hb-sdk task archive` has no inverse. Currently, restoring a task from `task/archive/` back to `task/active/` requires manual shell commands. This step adds the symmetric `task unarchive <name>` subcommand to `hb-sdk`. The change is purely additive — one new `cmd_task_unarchive` function and one new parser registration in `_def_cli_task`; no existing commands, callers, or tests are touched. Once this lands, `hb-sdk task unarchive <name>` moves the task folder and prints affected paths, completing the archive/unarchive round-trip.

Source ticket: `./ticket.md`. No prior steps — this is step 0.

---

## 0. Current-state facts (verified during planning)

- **`task archive` implementation**: `cmd_task_archive` at `skills/scripts/hb-sdk:334-374`. It: (1) calls `_find_matching_task_folders`, (2) asserts source is under `task/active/` via `relative_to`, (3) `mkdir`s the archive author dir, (4) checks dest doesn't exist, (5) renames, (6) removes empty active author dir, (7) calls `report_paths`. Confirmed live.
- **`_find_matching_task_folders`** at `hb-sdk:126-141`: searches both `active/` and `archive/` subtrees; returns `(task_path, TaskName)` pairs sorted by path. This is the right lookup function for `unarchive` — it will find tasks in `archive/` without modification.
- **`report_paths`** at `hb-sdk:89-92`: prints `=== affected paths: ===` then one absolute path per line. Used by archive; must be used the same way here.
- **`_def_cli_task`** at `hb-sdk:261-328`: registers subparsers for `archive`, `path`, `create`, `step`. The new `unarchive` parser is wired in here, following the same pattern as the `archive` parser (`p_ta` at line 266).
- **Test file**: `tests/skills/scripts/test_hb-sdk.py`. Archive tests are at lines 192-257. New tests mirror that group exactly (same `run()` / `archive_path()` / `task_path()` helpers). 81 tests pass currently via `make test`.

### 0.1 Impact (before → after)

| Scenario | Before | After |
|---|---|---|
| `hb-sdk task unarchive hasan/abc-1` | `error: argument <action>: invalid choice: 'unarchive'` | moves task from `archive/hasan/abc-1` → `active/hasan/abc-1`; exits 0 |
| task not in archive | N/A | exits non-zero; "task not found" to stderr |
| task already active | N/A | exits non-zero; "task is not archived" to stderr |
| dest already exists | N/A | exits non-zero; "destination already exists" to stderr |
| archive author dir empty after move | N/A | empty `archive/<author>/` dir is removed |

Change is purely additive — no existing subcommand behavior changes.

### 0.2 Non-regression proof

The change adds one new function and one new `add_parser` call. No existing function bodies are modified. All 81 existing tests remain unaffected.

---

## 1. Design overview

`cmd_task_unarchive` is the exact structural mirror of `cmd_task_archive`:

1. Parse and look up the task via `_find_matching_task_folders`.
2. Assert the found path is under `task/archive/` (not `task/active/`).
3. Ensure `task/active/<author>/` exists (create if absent).
4. Assert destination doesn't already exist.
5. `rename` source → dest.
6. Remove archive author dir if empty.
7. `report_paths`.

**Alternatives considered and rejected:**
- Reusing `cmd_task_archive` via a direction flag — adds complexity and an extra parameter for no gain; two symmetric functions with clear names are simpler.
- Looking only in `archive/` (not calling `_find_matching_task_folders`) — `_find_matching_task_folders` handles author+task_id matching and flavor-optional resolution; reimplementing that logic is redundant.

---

## 2. `cmd_task_unarchive` — specification

**Signature** (new):
```python
def cmd_task_unarchive(args: argparse.Namespace) -> None:
```

**Algorithm:**
```python
tn = _parse_task_name(args.name)

matching_tasks = _find_matching_task_folders(tn)
if len(matching_tasks) == 0:
    _die(f"error: task not found: {args.name}")
if len(matching_tasks) > 1:
    _die("error: found multiple existing tasks with same author/task_id:\n" + ...)

task_path, _ = matching_tasks[0]

archive_base = _path_hb_asserted() / "task" / TASK_FOLDER_ARCHIVE
try:
    task_path.relative_to(archive_base)
except ValueError:
    _die(f"error: task is not archived: {task_path.absolute()}")

active_author_dir = _path_hb_asserted() / "task" / TASK_FOLDER_ACTIVE / tn.author
active_author_dir.mkdir(parents=True, exist_ok=True)

dest = active_author_dir / task_path.name
if dest.exists():
    _die(f"error: destination already exists: {dest.absolute()}")

paths = [task_path]
archive_author_dir = archive_base / tn.author
task_path.rename(dest)
paths.append(dest)

if archive_author_dir.exists() and not any(archive_author_dir.iterdir()):
    archive_author_dir.rmdir()
    paths.append(archive_author_dir)

report_paths(paths)
```

**Error messages** (verbatim to stderr, non-zero exit):
- Task not found anywhere: `"error: task not found: {args.name}"`
- Task is in `active/`, not archived: `"error: task is not archived: {task_path.absolute()}"`
- Destination already exists: `"error: destination already exists: {dest.absolute()}"`
- Multiple matches: `"error: found multiple existing tasks with same author/task_id:\n..."` (mirrors archive)

---

## 3. Integration / wiring

One addition to `_def_cli_task` (`hb-sdk:266`), immediately after the `archive` parser block:

```python
p_tu = task_subs.add_parser("unarchive", help="Unarchive a task (move from archive to active)")
p_tu.add_argument("name", help="Fully-qualified task name (author/task-id[-extra])")
p_tu.set_defaults(func=cmd_task_unarchive)
```

No other call sites, signatures, or wiring change. The function `cmd_task_unarchive` is self-contained; it calls only existing helpers (`_parse_task_name`, `_find_matching_task_folders`, `_path_hb_asserted`, `_die`, `report_paths`).

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — add `cmd_task_unarchive` function (after `cmd_task_archive`); add `unarchive` subparser in `_def_cli_task`; all other functions untouched |
| `tests/skills/scripts/test_hb-sdk.py` | **edit** — add `task_unarchive` helper and `# ── task unarchive` test group (mirrors archive group) |

No new dependencies. Lockfile unchanged.

---

## 5. Tests

Mirror the `# ── task archive ──` group in `test_hb-sdk.py` (lines 192–257). Fixture strategy: `tmp_path` (pytest built-in), hermetic temp dirs. Same `run()` / `task_path()` / `archive_path()` helpers used throughout.

**New helper:**
```python
def task_unarchive(cwd: Path, name: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["task", "unarchive", name], cwd, ok=kwargs.get("ok", True))
```

**Test cases:**

| Test | Asserts |
|---|---|
| `test_task_unarchive_moves_to_active` | archive then unarchive → task back in `active/`, not in `archive/` |
| `test_task_unarchive_with_extra` | round-trip with flavor suffix (e.g. `abc-1-add-login`) |
| `test_task_unarchive_preserves_contents` | `ticket.md` and `.hb-task.json` intact after round-trip |
| `test_task_unarchive_creates_active_author_dir` | `active/<author>/` created if absent |
| `test_task_unarchive_task_not_found` | `ok=False`; `"task not found"` in stderr |
| `test_task_unarchive_already_active` | unarchiving a task that's in `active/` → `ok=False`; `"task is not archived"` in stderr |
| `test_task_unarchive_reports_dest_path` | absolute dest path appears in stdout |
| `test_task_unarchive_name_by_task_id_only` | `abc-1-some-flavor` unarchived when addressed as `abc-1` |
| `test_task_unarchive_removes_empty_archive_author_dir` | after last task for an author is unarchived, `archive/<author>/` dir is removed |
| `test_task_unarchive_round_trip` | `archive` → `unarchive` leaves folder in `active/` with identical contents (AC 4) |

**Non-regression:** existing 81 tests unchanged; `make test` must still pass.

---

## 6. Verification (after implementation)

1. `make test` — all 81 existing tests + new unarchive tests pass.
2. Smoke test — archive/unarchive round-trip in a real `.hb/` repo:
   ```bash
   cd /home/hkamal/repos/hashbuild
   python skills/scripts/hb-sdk task archive northwind/hb-003
   python skills/scripts/hb-sdk task unarchive northwind/hb-003
   ls .hb/task/active/northwind/
   ```
   Expected: `hb-003-...` folder present; `archive/northwind/` absent or empty.
3. Per-AC checks:
   - **AC 1**: `unarchive <name>` moves folder from `archive/` to `active/<author>/`; `report_paths` output contains both src and dest.
   - **AC 1.1**: `active/<author>/` created if absent (test `test_task_unarchive_creates_active_author_dir`).
   - **AC 1.2**: `report_paths` called on success (test `test_task_unarchive_reports_dest_path`).
   - **AC 2**: after last task for an author is unarchived, `archive/<author>/` removed (test `test_task_unarchive_removes_empty_archive_author_dir`).
   - **AC 3.1**: task not found → non-zero exit, `"task not found"` on stderr.
   - **AC 3.2**: task already in `active/` → non-zero exit, `"task is not archived"` on stderr.
   - **AC 3.3**: destination already exists → non-zero exit, `"destination already exists"` on stderr.
   - **AC 4**: round-trip test confirms folder contents identical (test `test_task_unarchive_round_trip`).
   - **AC 5**: `ok=True` in happy-path helpers asserts `returncode == 0`; `ok=False` in error helpers asserts non-zero.
4. Scope check: only `skills/scripts/hb-sdk` and `tests/skills/scripts/test_hb-sdk.py` changed.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `unarchive` locates task in `archive/` and moves to `active/<author>/` | §2 algorithm; `test_task_unarchive_moves_to_active` | uses `_find_matching_task_folders` |
| 1.1 — creates `active/<author>/` if absent | §2 (`mkdir(parents=True, exist_ok=True)`); `test_task_unarchive_creates_active_author_dir` | |
| 1.2 — `report_paths` on success | §2; `test_task_unarchive_reports_dest_path` | mirrors archive |
| 2 — removes empty archive author dir | §2; `test_task_unarchive_removes_empty_archive_author_dir` | mirrors archive cleanup of empty active author dir |
| 3.1 — task not found error | §2 `_die`; `test_task_unarchive_task_not_found` | |
| 3.2 — task already active error | §2 `relative_to` check; `test_task_unarchive_already_active` | |
| 3.3 — destination exists error | §2 `dest.exists()` check; `test_task_unarchive_dest_exists` | |
| 4 — round-trip invariant | `test_task_unarchive_round_trip` | archive then unarchive → identical contents |
| 5 — exits 0 on success, non-zero on error | `run(ok=True/False)` harness in every test | |

---

## 8. Out of scope (per ticket)

- The `hb-task-unarchive` skill file (step-1).
- Unarchiving individual steps within a task.
- Bulk unarchive of multiple tasks in one invocation.
