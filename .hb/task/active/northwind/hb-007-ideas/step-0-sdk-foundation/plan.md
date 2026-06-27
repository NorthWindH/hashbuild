# Step 0 Plan — idea subcommands: data layer and SDK CLI

`hb-sdk` has no `idea` subcommands or storage support today. Any skill that
stores, retrieves, or modifies idea entries must call SDK subcommands that do
not exist — meaning all idea skills (planned for steps 1–3) are blocked on this
step. The gap is entirely in `hb_sdk/`: the four commands (`idea add`, `idea
remove`, `idea show`, `idea set-content`) plus the `.hb/idea/<author>/ideas.json`
file format must be created. This step is additive only — no existing subcommand
or behavior changes. The single externally observable effect once this lands: a
caller can round-trip an idea through `add → show → set-content → remove` and
see the expected JSON at each stage.

Source ticket: `./ticket.md`. No prior steps — this is step 0, starting from
the current SDK state (confirmed below).

> **Design decision — `next_index` counter in the ideas file vs. derived from
> existing entries.** AC 2 requires that `index` is monotonically increasing and
> *never reused*. Deriving the next index as `max(existing) + 1` is wrong after
> all entries are removed (empty list → no max) and after deletion of the highest
> entry (would reuse). The chosen resolution: store `next_index` as a top-level
> field in `ideas.json` alongside the `ideas` array. On `add`, use `next_index`
> then increment it; on `remove`, leave `next_index` unchanged. The guard is that
> `next_index` is the only mutable counter touched by `add` — no other command
> reads or writes it. See §2 (data model) and AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `skills/scripts/hb_sdk/__main__.py:11–19`: registers exactly four subcommands
  (`init`, `task`, `summarize`, `commit`) via `def_cli_*` functions. No `idea`
  subcommand exists. Confirmed live.
- `skills/scripts/hb_sdk/` contains: `__init__.py`, `__main__.py`, `commit.py`,
  `common.py`, `init_cmd.py`, `summarize.py`, `task.py`. No `idea.py`.
- `common.py:50–68` provides `path_hb()`, `path_hb_asserted()`, `die()`,
  `progress()` — the utilities all subcommands use. Confirmed live.
- No `.hb/idea/` directory exists in the project or any test fixture. There is no
  pre-existing storage format to migrate.
- Tests live in `tests/skills/scripts/hb_sdk/`; they invoke `hb-sdk` via
  `subprocess.run` from a shared `helpers.py` pattern (`run()`, `init()`,
  `tmp_path` fixture, pytest). Confirmed live at
  `tests/skills/scripts/hb_sdk/helpers.py`.

### 0.1 Impact (before → after)

| Behavior | Before | After |
|---|---|---|
| `hb-sdk idea ...` | error: unrecognized command | executes correctly |
| `.hb/idea/<author>/ideas.json` | does not exist | created on first `add` |
| Idea round-trip | impossible | `add → show → set-content → remove` works |
| Existing subcommands | n/a | unchanged (additive only) |

### 0.2 Non-regression proof / risk

This step is purely additive — it adds a new module and wires it into
`__main__.py` without touching any existing module other than adding two lines to
`__main__.py`. The only risk is an import error breaking the existing subcommands
at startup. Guard: the new import is isolated; existing `def_cli_*` calls are
unchanged and the parser dispatch table is append-only.

| Case | Current behavior | Why it can't change |
|---|---|---|
| `hb-sdk init` | creates `.hb/` | `init_cmd.py` untouched |
| `hb-sdk task ...` | all task ops | `task.py` untouched |
| `hb-sdk summarize` | summary output | `summarize.py` untouched |
| `hb-sdk commit ...` | commit messages | `commit.py` untouched |

---

## 1. Design overview

A single new module `idea.py` implements all four idea subcommands. It follows
the exact pattern of `task.py`: one `cmd_idea_*` function per subcommand, one
`def_cli_idea(subs)` registration function, imported and called in `__main__.py`.

Storage is one JSON file per author at `.hb/idea/<author>/ideas.json`. The file
has two top-level fields:

```
{"next_index": <int>, "ideas": [<idea_object>, ...]}
```

The `ideas` array holds only the live (non-removed) entries. `next_index` starts
at 0 and increments on every successful `add`; it is never decremented or reset.
There is no separate metadata file — the counter lives inside the same file as
the ideas to keep the storage atomic.

`idea show` (no extra arg) collects ideas from all authors by globbing
`.hb/idea/*/ideas.json`. This is the only cross-author operation; all others are
scoped to a single author.

**Alternatives considered and rejected:**

- *Derive next_index from `max(existing indices) + 1`*: fails on empty list and
  allows reuse after high-index deletion. Rejected — violates AC 2.
- *Separate `.hb-idea-meta.json` next to `ideas.json`*: two-file write is not
  atomic; adds complexity with no benefit. Rejected.
- *Per-project global ideas store (not per-author)*: contradicts AC 1
  (`<author>/ideas.json`). Rejected.
- *NDJSON (one JSON object per line)*: not idiomatic for random access and
  requires custom parsing. Rejected — standard JSON array is simpler and all
  ideas per author are small enough to load entirely.

---

## 2. idea.py — specification

### 2.1 Data model

```python
# On-disk representation inside ideas.json
IdeaFile = {
    "next_index": int,          # monotonically increasing counter; never decremented
    "ideas": list[IdeaEntry],   # only live entries; removed entries are absent
}

IdeaEntry = {
    "index": int,       # permanent ID assigned at add time
    "content": str,     # the idea text; mutable via set-content
    # additional metadata fields are allowed (not required by this step)
}
```

### 2.2 Path helpers (new, in idea.py)

```python
def path_idea_dir(author: str) -> Path:
    # Returns .hb/idea/<author>/  (not asserted to exist)

def path_idea_file(author: str) -> Path:
    # Returns .hb/idea/<author>/ideas.json  (not asserted to exist)
```

Both call `path_hb_asserted()` to guard against uninitialised `.hb/`.

### 2.3 Storage helpers (new, internal)

```python
def _load_idea_file(author: str) -> dict:
    # Reads and parses ideas.json; returns {"next_index": 0, "ideas": []} if file absent.
    # Calls path_hb_asserted() (raises die() if .hb/ absent).

def _save_idea_file(author: str, data: dict) -> None:
    # Creates .hb/idea/<author>/ if absent, then writes ideas.json atomically.
    # Indent: 2 spaces, trailing newline.
```

**Failure contract for `_load_idea_file`**: file absent → return empty
`{"next_index": 0, "ideas": []}` (not an error). `.hb/` absent → `die()`.
Malformed JSON → propagate `json.JSONDecodeError` (crash loudly — indicates
filesystem corruption, not a user error).

### 2.4 ID parsing (new, internal)

```python
def _parse_idea_ref(ref: str) -> tuple[str, int]:
    # Accepts "<author>/<index>" — splits on last "/", parses index as int.
    # Calls die() on malformed input.
```

### 2.5 Subcommand functions (new)

| Function | Signature | Contract | Status |
|---|---|---|---|
| `cmd_idea_add` | `(args: Namespace) -> None` | reads `.ideas.json`, appends new entry with `next_index`, increments counter, saves, prints `<author>/<index>` to stdout | new |
| `cmd_idea_remove` | `(args: Namespace) -> None` | loads file, finds entry by index, removes it, saves; `die()` if not found | new |
| `cmd_idea_show` | `(args: Namespace) -> None` | three modes depending on `args.target` (see §2.6); prints JSON to stdout | new |
| `cmd_idea_set_content` | `(args: Namespace) -> None` | loads file, finds entry, replaces `content`, saves; `die()` if not found | new |

### 2.6 `idea show` dispatch logic

```
args.target is None       → glob .hb/idea/*/ideas.json, collect all "ideas" arrays, print combined list
args.target == "<author>" → load single author file, print "ideas" array
args.target == "<author>/<index>" → load single author file, find by index, print single object; die() if absent
```

Disambiguation: `args.target` contains a `/` → parsed as `<author>/<index>`;
no `/` → treated as `<author>`. Author names cannot contain `/` (same constraint
as task author field in `common.py`).

### 2.7 CLI registration (new)

```python
def def_cli_idea(subs) -> None:
    p_idea = subs.add_parser("idea", help="Idea operations")
    idea_subs = p_idea.add_subparsers(dest="idea_command", metavar="<action>")
    idea_subs.required = True

    # add: hb-sdk idea add <author> <content>
    p_add = idea_subs.add_parser("add", ...)
    p_add.add_argument("author")
    p_add.add_argument("content")
    p_add.set_defaults(func=cmd_idea_add)

    # remove: hb-sdk idea remove <author>/<index>
    p_rm = idea_subs.add_parser("remove", ...)
    p_rm.add_argument("idea_ref", metavar="<author>/<index>")
    p_rm.set_defaults(func=cmd_idea_remove)

    # show: hb-sdk idea show [<author>[/<index>]]
    p_show = idea_subs.add_parser("show", ...)
    p_show.add_argument("target", nargs="?", default=None,
                        metavar="[<author>[/<index>]]")
    p_show.set_defaults(func=cmd_idea_show)

    # set-content: hb-sdk idea set-content <author>/<index> <new_content>
    p_sc = idea_subs.add_parser("set-content", ...)
    p_sc.add_argument("idea_ref", metavar="<author>/<index>")
    p_sc.add_argument("new_content")
    p_sc.set_defaults(func=cmd_idea_set_content)
```

---

## 3. Integration / wiring

`__main__.py` requires two additive changes:

```python
# line after existing imports (currently line 7)
from .idea import def_cli_idea

# line after def_cli_commit(subs) call (currently line 19)
def_cli_idea(subs)
```

All other existing imports and `def_cli_*` calls are untouched. Public
signatures of `main()` and all existing subcommands are preserved. No build
wiring, entry points, or dependency manifests change — `idea.py` uses only
stdlib (`json`, `pathlib`, `argparse`) and `common.py`, which is already a
dependency of every other module.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/idea.py` | **new** — all `idea` subcommand logic; `def_cli_idea` registration |
| `skills/scripts/hb_sdk/__main__.py` | **edit** — add `from .idea import def_cli_idea` import and `def_cli_idea(subs)` call; all existing lines untouched |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_idea.py` | **new** — full test suite for all four idea subcommands (mirrors `test_hb_sdk_task.py` style) |
| `tests/skills/scripts/hb_sdk/helpers.py` | **edit** — add `idea_add`, `idea_remove`, `idea_show`, `idea_set_content` helper functions |

`pyproject.toml`, lockfiles, and all other files: **unchanged** — no new
dependencies; stdlib only.

---

## 5. Tests

Mirror `test_hb_sdk_task.py` style: `tmp_path` fixture, subprocess invocation
via `helpers.py`. Fixture strategy: temp dir with `init()` called to create
`.hb/`; no pre-created fixtures needed (all state is built up by the test).

New helpers in `helpers.py`:

```python
def idea_add(cwd, author, content, *, ok=True) -> CompletedProcess
def idea_remove(cwd, idea_ref, *, ok=True) -> CompletedProcess
def idea_show(cwd, target=None, *, ok=True) -> CompletedProcess
def idea_set_content(cwd, idea_ref, new_content, *, ok=True) -> CompletedProcess
```

### Test cases — `idea add`

| Test | Asserts |
|---|---|
| `test_idea_add_basic` | returns `<author>/0` on stdout; `ideas.json` created with one entry `index=0`; `next_index=1` |
| `test_idea_add_sequential_indices` | three adds produce indices 0, 1, 2 in order; `next_index=3` |
| `test_idea_add_creates_parent_dir` | `.hb/idea/<author>/` dir is created if absent |
| `test_idea_add_no_hb` | without `init()`, exits non-zero with `.hb/` error message |

### Test cases — `idea remove`

| Test | Asserts |
|---|---|
| `test_idea_remove_basic` | entry removed from `ideas` array; file still exists; `next_index` unchanged |
| `test_idea_remove_not_found` | exits non-zero with clear error; `ideas` array unchanged |
| `test_idea_remove_index_not_reused` | add two ideas, remove index 0, add again → new idea gets index 2 (not 0) |
| `test_idea_remove_no_hb` | without `init()`, exits non-zero |

### Test cases — `idea show`

| Test | Asserts |
|---|---|
| `test_idea_show_all_no_ideas` | no `ideas.json` files → prints `[]` |
| `test_idea_show_all_multiple_authors` | two authors, add one idea each → all-show returns array with both |
| `test_idea_show_author` | returns only that author's ideas as JSON array |
| `test_idea_show_author_empty` | author has no ideas (file absent) → prints `[]` |
| `test_idea_show_single` | prints single idea object matching `index` and `content` |
| `test_idea_show_single_not_found` | exits non-zero with clear error |
| `test_idea_show_no_hb` | without `init()`, exits non-zero |

### Test cases — `idea set-content`

| Test | Asserts |
|---|---|
| `test_idea_set_content_basic` | `content` field updated; `index` unchanged; other fields preserved |
| `test_idea_set_content_not_found` | exits non-zero with clear error |
| `test_idea_set_content_no_hb` | without `init()`, exits non-zero |

### Non-regression

Existing test files `test_hb_sdk_task.py`, `test_hb_sdk_init.py`,
`test_hb_sdk_summarize.py`, `test_hb_sdk_commit.py` must all pass unchanged.
The change to `__main__.py` is append-only — no existing parser branch is
touched — so no regression is possible from the wiring change.

---

## 6. Verification (after implementation)

1. **Full test suite green:**
   ```bash
   cd /home/hkamal/repos/hashbuild
   python -m pytest tests/ -v
   ```
   All existing tests must pass; new `test_hb_sdk_idea.py` tests must all pass.

2. **Manual smoke — add and show:**
   ```bash
   cd /tmp && mkdir hb_smoke && cd hb_smoke
   python /home/hkamal/repos/hashbuild/skills/scripts/hb-sdk init
   python /home/hkamal/repos/hashbuild/skills/scripts/hb-sdk idea add alice "first idea"
   # expected stdout: alice/0
   python /home/hkamal/repos/hashbuild/skills/scripts/hb-sdk idea add alice "second idea"
   # expected stdout: alice/1
   python /home/hkamal/repos/hashbuild/skills/scripts/hb-sdk idea show alice
   # expected: JSON array with index 0 and 1
   ```

3. **Per-AC checks:**

   | AC | Check |
   |---|---|
   | 1 (storage location) | `cat .hb/idea/alice/ideas.json` exists after first `add` |
   | 2 (index fields) | JSON output contains `"index"` (int) and `"content"` (str) fields |
   | 3 (add stdout) | `idea add alice "x"` prints exactly `alice/0` |
   | 4 (remove error) | `idea remove alice/99` exits non-zero with error on stderr |
   | 5a (show all) | `idea show` with two authors prints combined array |
   | 5b (show author) | `idea show alice` prints only alice's ideas |
   | 5c (show single) | `idea show alice/0` prints single object; `alice/99` exits non-zero |
   | 6 (set-content) | set-content changes content; `show alice/0` reflects new text |
   | 7 (no .hb/) | all four subcommands exit non-zero with `.hb/` message in uninitialized dir |
   | 8 (non-regression) | existing subcommand smoke: `hb-sdk task create alice/hb-1` still works |

4. **Scope check:** only the four files listed in §4 should appear in `git diff
   --name-only`. No other file should change.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — storage at `.hb/idea/<author>/ideas.json`; created on first write | §2.3 `_save_idea_file`; §2.5 `cmd_idea_add` | Verified in §6 AC-1 check |
| 2 — `index` (int, monotonic, never reused) + `content` (str) fields | §2.1 data model; §2.3 `_load_idea_file` / `_save_idea_file`; §2.5 `cmd_idea_add` | Design decision justification in preamble; test `test_idea_remove_index_not_reused` |
| 3 — `idea add <author> <content>` prints `<author>/<index>` | §2.5 `cmd_idea_add`; §2.7 CLI | Test `test_idea_add_basic`; §6 AC-3 |
| 4 — `idea remove` exits non-zero on missing ID | §2.5 `cmd_idea_remove`; `die()` path | Test `test_idea_remove_not_found`; §6 AC-4 |
| 5 — `idea show` three forms | §2.5 `cmd_idea_show`; §2.6 dispatch | Tests `test_idea_show_*`; §6 AC-5a/5b/5c |
| 6 — `idea set-content` replaces content; non-zero on missing | §2.5 `cmd_idea_set_content` | Tests `test_idea_set_content_*`; §6 AC-6 |
| 7 — all subcommands exit non-zero when `.hb/` absent | `path_hb_asserted()` called first in all `cmd_idea_*` functions | Tests `test_idea_*_no_hb`; §6 AC-7 |
| 8 — existing subcommands unchanged | §3 (wiring is append-only); §0.2 non-regression proof | Existing test suites; §6 AC-8 |

---

## 8. Out of scope (per ticket)

- Skill files (`hb-idea-add`, `hb-idea-remove`, `hb-idea-show`, `hb-idea-set-content`) — deferred to steps 1–3.
- `idea-list-template.md` reference file — deferred to step 1.
- Bulk operations — excluded per task ticket.
- Additional metadata fields beyond `index` and `content` — allowed by AC 2 but not required; not specified or implemented in this step.
