# Step 0 Plan — Facts Store (`hb-sdk facts read`/`write`)

This step adds a persistent facts store: a single markdown file at `.hb/facts.md`
plus an `hb-sdk facts read`/`facts write` CLI surface. Today there is no
`facts.md` at all — the only precedent for a project-level `.hb/`-adjacent file
is the JSON state file (`hb_sdk/state.py`, `.hb/.state.ignore.json`), which
behaves differently in one key way this step must NOT copy: `state.py` calls
`path_hb_asserted()` and **dies** if `.hb/` is missing, whereas AC3.2 here
requires `facts write` to create `.hb/` itself if absent. This is a
purely additive change — one new module, one new `common.py` helper, one new
reference doc — that does not touch `state.py`, `idea.py`, or any existing
subcommand. The externally observable effect: after this lands, `hb-sdk facts
write "<content>"` followed by `hb-sdk facts read` round-trips arbitrary text
through `.hb/facts.md`, working even in a project where `.hb/` does not yet
exist.

Source ticket: `./ticket.md`. This is the first step of `northwind/hb-016`; there
is no prior step to build on. This plan targets the codebase as it exists now,
at `skills/scripts/hb_sdk/`.

> **Design decision — lazy creation means `facts` must NOT use
> `path_hb_asserted()`.** Every existing subcommand that touches `.hb/`
> (`state.py:14`, `state.py:24`) calls `path_hb_asserted()` first, which calls
> `sys.exit(1)` if `.hb/` doesn't exist (`common.py:58-68`). AC3.2 explicitly
> requires `facts write` to create `.hb/` (and `facts.md`) when neither exists —
> the opposite of `path_hb_asserted()`'s contract — and AC4 rules out adding a
> separate `facts init` subcommand to pre-create it. The resolution: `facts.py`
> creates `.hb/` directly via `path_hb().mkdir(parents=True, exist_ok=True)`
> instead of asserting it, for both `read` and `write`. This is safe because
> `read`'s only job is "does `.hb/facts.md` exist" — if `.hb/` is absent, the
> file trivially doesn't exist either, so the AC2.2 empty-response behavior
> falls out with no special-casing. See §2 and the AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- No `facts.md` or `facts.py` exists anywhere in the repo today (confirmed via
  `grep -ril facts skills/` — the only hit is the word "facts" in
  `plan-template.md`'s own section heading, unrelated).
- `hb_sdk/state.py` is the closest existing precedent for a `.hb/`-scoped
  persistence subcommand:
  - `write_state()` (`state.py:12-18`) calls `path_hb_asserted()` then
    `p.write_text(json.dumps(record, indent=2) + "\n")` — **dies if `.hb/`
    missing**.
  - `read_state()` (`state.py:21-27`) calls `path_hb_asserted()` then returns
    `None` if the state file itself doesn't exist — **also dies if `.hb/`
    missing**, which `facts` must not do (see design decision above).
  - `def_cli_state()` (`state.py:59-74`) is the subparser-registration pattern
    to mirror: `subs.add_parser("state", ...)`, a required sub-subparser for
    `<action>`, one `add_parser` per action, `set_defaults(func=...)`.
  - Registered in `hb_sdk/__main__.py:8,23` as `from .state import
    def_cli_state` / `def_cli_state(subs)`.
- `hb_sdk/idea.py` is the precedent for accepting free-text content as a plain
  positional CLI argument rather than via stdin or a flag: `cmd_idea_add`
  (`idea.py:45-49`) and `cmd_idea_set_content` (`idea.py:91-98`) both take
  `args.content` / `args.new_content` as a bare positional
  (`p_add.add_argument("content")`, `idea.py:108`). `facts write` follows the
  same shape: `content` as a required positional, not `--content` or stdin.
- `common.py` holds all shared path helpers as tiny one-line functions —
  `path_hb()` (`common.py:50-51`), `path_hb_state()` (`common.py:83-84`). A
  `path_hb_facts()` following the exact same shape is the natural, minimal
  addition; `path_hb()` itself does not require `.hb/` to exist (it's just
  `Path.cwd() / ".hb"`), which is what makes the lazy-creation design work.
- Tests live in `tests/skills/scripts/hb_sdk/`, one file per subcommand module
  (`test_hb_sdk_state.py`, `test_hb_sdk_idea.py`, etc.), driven through
  `helpers.py`'s `run()` (`helpers.py:14-25`), which shells out to the real
  `hb-sdk` executable via `subprocess.run([sys.executable, str(SDK), *args],
  cwd=cwd, ...)` — no in-process mocking. `test_hb_sdk_state.py` is the closest
  structural mirror (happy path → overwrite semantics → missing-input/error
  cases), though `facts` has no "no-`.hb/`" error case since that's precisely
  what AC3.2 removes.
- Reference docs live in `skills/references/` (flat, one file per template:
  `ticket-template.md`, `plan-template.md`, `execution-template.md`,
  `review-template.md`), each indexed by one row in
  `skills/references/references-toc.md`. Precedent for adding both together in
  one step: commit `6912b92` added `breakdown-subflow.md` plus its
  `references-toc.md` row in the same commit that introduced it, without
  touching every skill file that doesn't yet consume it (wiring consumers is a
  separate, later concern — matching this ticket's own "out of scope" list for
  the skills that will read facts).

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `.hb/facts.md` does not exist, run `hb-sdk facts read` | command does not exist | prints nothing, exit 0 |
| No `.hb/` at all, run `hb-sdk facts write "..."` | command does not exist | creates `.hb/` and `.hb/facts.md` with the given content, exit 0 |
| `.hb/facts.md` exists with content A, run `hb-sdk facts write "B"` then `read` | n/a | prints exactly `B` (full overwrite, not append) |

Purely additive: no existing command, file, or test changes behavior.

### 0.2 Non-regression proof

Additive-only — new module (`facts.py`), new `common.py` function, new
`__main__.py` registration line, new reference doc, new test file. No existing
function signature or call site is edited. `state.py` and `idea.py` are read
for pattern-matching only, not modified.

---

## 1. Design overview

Single linear addition, mirroring the `state` subcommand's structure but with
two deliberate deviations driven by the ticket:

| Aspect | `state` (existing) | `facts` (this step) |
|---|---|---|
| Storage format | JSON object | raw text (markdown) |
| Missing `.hb/` | dies via `path_hb_asserted()` | creates it (write) / treats as empty (read) |
| Missing file | `read` returns `None`, caller formats | `read` prints empty string directly |
| Content input | structured `--skill`/`--outcome`/... flags | one positional `content` string (mirrors `idea`) |

Control flow:
- `facts write <content>` → ensure `.hb/` exists → overwrite `.hb/facts.md`
  with `content` verbatim (no injected header, no trailing-newline
  normalization) → exit 0.
- `facts read` → if `.hb/facts.md` exists, print its exact contents (no added
  newline); else print nothing → exit 0.

**Alternatives considered and rejected:**
- *Store facts as JSON like `state.py`* — rejected: AC1/AC3 call it a "facts
  store file" read/written as raw contents, and the parent ticket frames it as
  agent-authored markdown prose, not a structured record with fixed fields.
- *Auto-inject the size-limit guidance as a header comment on every write* —
  rejected: breaks the exact round-trip required by AC6.3 (`write` then `read`
  must return exactly what was written) and duplicates guidance that belongs in
  a reference doc the agent reads once before authoring content, not in the
  file's own bytes on every write.
- *Add a `facts init` subcommand to pre-create the file* — explicitly rejected
  by AC4.
- *Call `path_hb_asserted()` in `facts read`/`write` like `state.py` does* —
  rejected: contradicts AC3.2 (write must create `.hb/` if absent) and would
  make `read` error on a totally uninitialized project instead of returning
  empty per AC2.2's spirit (the file, by construction, cannot exist without
  `.hb/`, so no assertion is needed to get the right answer).

---

## 2. `hb_sdk/facts.py` — specification

**New file**, structured identically to `state.py`'s section order (helpers,
then `cmd_*` handlers, then `def_cli_facts`).

- **Interfaces / signatures** (all **new**):

  | Symbol | Signature | Contract |
  |---|---|---|
  | `write_facts` | `(content: str) -> Path` | Ensures `.hb/` exists, overwrites `.hb/facts.md` with `content` verbatim, returns the path written. |
  | `read_facts` | `() -> str` | Returns `.hb/facts.md`'s exact contents, or `""` if it doesn't exist (or `.hb/` doesn't exist). |
  | `cmd_facts_write` | `(args: argparse.Namespace) -> None` | Calls `write_facts(args.content)`. |
  | `cmd_facts_read` | `(args: argparse.Namespace) -> None` | Prints `read_facts()` with `end=""` (no injected newline). |
  | `def_cli_facts` | `(subs: Any) -> None` | Registers the `facts` subparser with `write`/`read` actions. |

- **Algorithm / rules:**
  ```python
  def write_facts(content: str) -> Path:
      path_hb().mkdir(parents=True, exist_ok=True)
      p = path_hb_facts()
      progress(f"writing facts to {p.absolute()} ...")
      p.write_text(content)
      return p


  def read_facts() -> str:
      p = path_hb_facts()
      if not p.exists():
          return ""
      return p.read_text()


  def cmd_facts_write(args: argparse.Namespace) -> None:
      write_facts(args.content)


  def cmd_facts_read(args: argparse.Namespace) -> None:
      print(read_facts(), end="")


  def def_cli_facts(subs: Any) -> None:
      p_facts = subs.add_parser("facts", help="Facts store operations")
      facts_subs = p_facts.add_subparsers(dest="facts_command", metavar="<action>")
      facts_subs.required = True

      p_write = facts_subs.add_parser("write", help="Overwrite the facts store with new content")
      p_write.add_argument("content", metavar="<content>")
      p_write.set_defaults(func=cmd_facts_write)

      p_read = facts_subs.add_parser("read", help="Print the current facts store contents")
      p_read.set_defaults(func=cmd_facts_read)
  ```
- **Failure / degradation contract:** missing `.hb/facts.md` (with or without
  `.hb/` itself present) → `read` returns `""`, exit 0, no stderr — never an
  error (AC2.2). `write` never fails on missing parents — it creates them
  (AC3.2).
- **Conflict resolution:** N/A — `write` is a full overwrite by definition
  (AC3.1); no merge/append logic exists to conflict.

`print(..., end="")` is the load-bearing detail for AC6.3: using default
`print()` would append a newline `state_show`-style, which breaks exact
round-trip whenever the caller's content doesn't already end in `\n`.

---

## 3. Integration / wiring

- `common.py`: add one function, `path_hb_facts()`, next to `path_hb_state()`
  (`common.py:83-84`):
  ```python
  def path_hb_facts() -> Path:
      return path_hb() / "facts.md"
  ```
  No existing function in `common.py` is edited.
- `__main__.py`: add one import and one registration call, following the exact
  pattern of every other subcommand:
  ```python
  from .facts import def_cli_facts
  ...
  def_cli_facts(subs)
  ```
  (import alongside the existing `from .state import def_cli_state`; call
  alongside `def_cli_state(subs)`, `__main__.py:8,23`.)
- No build config, dependency manifest, or entry-point script changes — `facts`
  is dispatched through the same `argparse` subparser tree as every other
  subcommand; the `hb-sdk` executable itself (`skills/scripts/hb-sdk`) is
  unchanged.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/facts.py` | **new** — `write_facts`, `read_facts`, `cmd_facts_write`, `cmd_facts_read`, `def_cli_facts` |
| `skills/scripts/hb_sdk/common.py` | **extend** — add `path_hb_facts()`; all existing functions untouched |
| `skills/scripts/hb_sdk/__main__.py` | **extend** — add `facts` import + registration line; existing subcommand registrations untouched |
| `skills/references/facts-template.md` | **new** — guidance doc for agents populating `.hb/facts.md` (purpose, structure suggestion, size-limit guidance per AC5) |
| `skills/references/references-toc.md` | **extend** — one new row for `facts-template.md`, mirroring the `breakdown-subflow.md` row added in `6912b92` |
| `tests/skills/scripts/hb_sdk/helpers.py` | **extend** — add `facts_write()`/`facts_read()` helpers, mirroring `state_record()`/`state_show()` (`helpers.py:109-126`) |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_facts.py` | **new** — tests per AC6 |

No dependency manifest or lockfile changes — `dependencies = []` in
`pyproject.toml` stays empty; no new imports beyond the standard library.

`skills/references/facts-template.md` content:

```markdown
# Facts Store

<!--
  FACTS TEMPLATE — guidance for whichever skill populates `.hb/facts.md` via
  `hb-sdk facts write`. This file is NOT copied into `.hb/facts.md`; it exists
  to be read before writing facts, the same way `ticket-template.md` is read
  before drafting a ticket.

  A fact is a durable, project-level observation worth carrying across tasks —
  not task-scoped context (that belongs in `ticket.md`/`plan.md`) and not a
  transient in-progress note. Prefer short, dated, falsifiable statements over
  prose narrative.

  Size guidance (not programmatically enforced — apply judgement):
  - Target size: <= 100 lines.
  - Hard maximum: 1000 lines.
  - Each line: <= 120 characters.

  When appending would exceed the target, prune stale or superseded facts
  first rather than growing unbounded — `hb-sdk facts write` always overwrites
  the full file, so pruning is just a matter of composing the trimmed content
  before writing it back.
-->
```

---

## 5. Tests

New file `tests/skills/scripts/hb_sdk/test_hb_sdk_facts.py`, mirroring
`test_hb_sdk_state.py`'s section-comment style and driven through the same
`run()`-based helpers (hermetic — real subprocess against a `tmp_path`, no
mocking). Add to `helpers.py`:

```python
def facts_write(cwd: Path, content: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["facts", "write", content], cwd, ok=kwargs.get("ok", True))


def facts_read(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return run(["facts", "read"], cwd, ok=kwargs.get("ok", True))
```

Test cases:

| Test | Asserts |
|---|---|
| `test_facts_read_missing_file_returns_empty` | after `init`, before any write: `facts read` → `returncode == 0`, `stdout == ""` (AC2.1/AC2.2 happy path) |
| `test_facts_read_no_hb_at_all_returns_empty` | **no** `init` call, straight to `facts read` on a bare `tmp_path` → `returncode == 0`, `stdout == ""` (proves `read` never asserts `.hb/`, per the design decision) |
| `test_facts_write_creates_file_when_absent` | after `init`, `facts write "hello"` → `.hb/facts.md` exists with contents `"hello"` (AC3.1/AC3.2, AC6.2) |
| `test_facts_write_creates_hb_dir_when_absent` | **no** `init` call, `facts write "hello"` on a bare `tmp_path` → `.hb/` and `.hb/facts.md` both created, contents `"hello"` (AC3.2's "any missing `.hb/` parent directory" clause) |
| `test_facts_write_then_read_round_trips_exactly` | write a multi-line string with trailing whitespace/no-trailing-newline variants, `facts read` → `result.stdout == content` exactly, byte-for-byte (AC6.3) |
| `test_facts_write_overwrites_prior_content` | write `"A"`, write `"B"`, `facts read` → `stdout == "B"` only, no trace of `"A"` (AC3.1 "overwrites", not appends) |
| `test_facts_write_requires_content_arg` | `facts write` with no positional arg → `returncode != 0` (argparse-enforced required positional) |

- **Non-regression:** `test_hb_sdk_state.py`, `test_hb_sdk_idea.py`,
  `test_hb_sdk_init.py`, `test_hb_sdk_commit.py`, `test_hb_sdk_summarize.py`,
  `test_hb_sdk_task.py` all pass unchanged — nothing in `common.py`,
  `__main__.py`, or the executable's argument-parsing tree is edited in a way
  that touches existing subcommands (only additive registrations).

---

## 6. Verification (after implementation)

1. `uv run pytest` — full suite green, including the new
   `test_hb_sdk_facts.py` and all pre-existing files unchanged.
2. `uv run ruff check .` (per `ruff.toml`) — new files pass lint.
3. Manual exercise in a scratch dir:
   ```bash
   cd /private/tmp/claude-502/.../scratchpad && mkdir factscheck && cd factscheck
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk facts read   # prints nothing, exit 0
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk facts write "- fact one"
   ls .hb/facts.md                                                              # exists
   /Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk facts read   # prints "- fact one"
   ```
4. **Per-AC checks:**
   - AC1: step 3 above shows `.hb/facts.md` created lazily, no separate init
     command was run.
   - AC2.1/AC2.2: `test_facts_read_missing_file_returns_empty` +
     `test_facts_read_no_hb_at_all_returns_empty`.
   - AC3.1/AC3.2: `test_facts_write_creates_file_when_absent` +
     `test_facts_write_creates_hb_dir_when_absent`.
   - AC4: `grep -c "facts.*init" skills/scripts/hb_sdk/facts.py` → `0`; only
     `write`/`read` subparsers exist.
   - AC5: `skills/references/facts-template.md` exists and states the
     100/1000/120 limits as guidance, with no code path in `facts.py`
     enforcing them (confirmed by reading §2 — no length/line checks in
     `write_facts`).
   - AC6.1–AC6.3: the three tests named above.
5. **Invariant check:** `hb-sdk facts write` never raises on a fresh
   `tmp_path` with zero prior state — authoritative check is
   `test_facts_write_creates_hb_dir_when_absent`.
6. **Scope check:** only the files in §4 changed; no edits to `state.py`,
   `idea.py`, `task.py`, `commit.py`, `summarize.py`, `init_cmd.py`, or any
   `hb-task-*`/`hb-status` skill `.md` file.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (`write_facts`), §6 step 4 (AC1) | lazy creation, no init subcommand |
| 2.1 | §2 (`read_facts`/`cmd_facts_read`) | |
| 2.2 | §2 failure/degradation contract, §5 (`test_facts_read_missing_file_returns_empty`, `test_facts_read_no_hb_at_all_returns_empty`) | |
| 3.1 | §2 (`write_facts`), §5 (`test_facts_write_then_read_round_trips_exactly`, `test_facts_write_overwrites_prior_content`) | full overwrite, not append |
| 3.2 | §2 (`write_facts` — `path_hb().mkdir(parents=True, exist_ok=True)`), §5 (`test_facts_write_creates_hb_dir_when_absent`) | |
| 4 | §1 alternatives-rejected, §6 step 4 (AC4) | no `facts init` subparser added |
| 5 | §4 (`facts-template.md` content) | documented, not enforced — confirmed by absence of length checks in §2 |
| 6.1 | §5 (`test_facts_read_missing_file_returns_empty`) | |
| 6.2 | §5 (`test_facts_write_creates_file_when_absent`) | |
| 6.3 | §5 (`test_facts_write_then_read_round_trips_exactly`) | exact byte round-trip via `print(..., end="")` |

---

## 8. Out of scope (per ticket)

- Wiring facts-store reads/updates into `hb-task-step-plan`, `hb-task-plan`, or
  `hb-task-step-execute` — later steps of `northwind/hb-016` consume
  `facts-template.md` and the `hb-sdk facts` CLI; this step only builds them.
- Enforcing the 100/1000/120 size limits in code — `facts-template.md`
  documents them as guidance only; `write_facts` performs no validation.
- Conflict resolution across concurrent writers — `write_facts` is a last-
  writer-wins full overwrite with no locking or merge logic.
