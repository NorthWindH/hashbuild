# Step 0 Plan — Facts Store (`hb-sdk facts read`/`write`)

This step adds a persistent facts store: a single markdown file at `.hb/facts.md`
plus an `hb-sdk facts read`/`facts write` CLI surface. Today there is no
`facts.md` at all — the only precedent for a project-level `.hb/`-adjacent file
is the JSON state file (`hb_sdk/state.py`, `.hb/.state.ignore.json`), and `facts`
follows its `path_hb_asserted()` contract exactly: both `read` and `write` die
if `.hb/` itself doesn't exist. This is a purely additive change — one new
module, one new `common.py` helper, one new reference doc — that does not touch
`state.py`, `idea.py`, or any existing subcommand. The externally observable
effect: after this lands, `hb-sdk facts write "<content>"` followed by
`hb-sdk facts read` round-trips arbitrary text through `.hb/facts.md`, in any
project that has already run `hb-sdk init`.

Source ticket: `./ticket.md`. This is the first step of `northwind/hb-016`; there
is no prior step to build on. This plan targets the codebase as it exists now,
at `skills/scripts/hb_sdk/`.

> **Design decision — `facts` mirrors `state`'s `path_hb_asserted()` contract
> exactly; only the file itself is lazy.** AC4 says `facts` matches "the
> pattern of `read`/`write` already used by `hb-sdk state`" (`state.py:14,24`),
> and AC3.2 (amended) confirms `.hb/` itself is not `facts`'s responsibility to
> create — if `.hb/` is missing, `facts write` dies via `path_hb_asserted()`
> just like `write_state()` does. The only thing that stays lazy, per AC1/AC4,
> is `.hb/facts.md` itself: no `facts init` subcommand exists to pre-create it,
> so `write` creates the file (not the directory) on first use. This keeps
> `facts.py` a near-verbatim structural copy of `state.py` — see §2 and the
> AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- No `facts.md` or `facts.py` exists anywhere in the repo today (confirmed via
  `grep -ril facts skills/` — the only hit is the word "facts" in
  `plan-template.md`'s own section heading, unrelated).
- `hb_sdk/state.py` is the closest existing precedent for a `.hb/`-scoped
  persistence subcommand, and `facts` follows it directly:
  - `write_state()` (`state.py:12-18`) calls `path_hb_asserted()` then
    `p.write_text(json.dumps(record, indent=2) + "\n")` — **dies if `.hb/`
    missing**. `write_facts` does the same, minus the JSON encoding.
  - `read_state()` (`state.py:21-27`) calls `path_hb_asserted()` then returns
    `None` if the state file itself doesn't exist. `read_facts` deliberately
    does **not** copy the `path_hb_asserted()` call: AC2 (unchanged by this
    amendment) only specifies behavior for a missing `.hb/facts.md`, not a
    missing `.hb/` — and `read` has no directory to create, so there's nothing
    for it to assert against. It checks `path_hb_facts().exists()` directly and
    returns `""` if not, which is also correct when `.hb/` itself is absent (a
    facts file trivially can't exist without its parent directory).
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
  `Path.cwd() / ".hb"`), which is what lets `read_facts` check
  `path_hb_facts().exists()` directly without asserting `.hb/` first.
- Tests live in `tests/skills/scripts/hb_sdk/`, one file per subcommand module
  (`test_hb_sdk_state.py`, `test_hb_sdk_idea.py`, etc.), driven through
  `helpers.py`'s `run()` (`helpers.py:14-25`), which shells out to the real
  `hb-sdk` executable via `subprocess.run([sys.executable, str(SDK), *args],
  cwd=cwd, ...)` — no in-process mocking. `test_hb_sdk_state.py` is the closest
  structural mirror (happy path → overwrite semantics → missing-`.hb/` error
  case → missing-input/error cases); `facts write`'s missing-`.hb/` test mirrors
  `test_state_record_no_hb` (`test_hb_sdk_state.py:60-63`) directly, while
  `facts read` gets its own no-`.hb/` test asserting the opposite (no error).
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
| `.hb/` does not exist, run `hb-sdk facts read` | command does not exist | prints nothing, exit 0 (facts file trivially absent too) |
| `.hb/` does not exist, run `hb-sdk facts write "..."` | command does not exist | dies via `path_hb_asserted()`, exit 1, same message as `hb-sdk state record` in the same situation |
| `.hb/` exists, `.hb/facts.md` does not, run `hb-sdk facts write "..."` | command does not exist | creates `.hb/facts.md` with the given content, exit 0 |
| `.hb/facts.md` exists with content A, run `hb-sdk facts write "B"` then `read` | n/a | prints exactly `B` (full overwrite, not append) |

Purely additive: no existing command, file, or test changes behavior.

### 0.2 Non-regression proof

Additive-only — new module (`facts.py`), new `common.py` function, new
`__main__.py` registration line, new reference doc, new test file. No existing
function signature or call site is edited. `state.py` and `idea.py` are read
for pattern-matching only, not modified.

---

## 1. Design overview

Single linear addition, mirroring the `state` subcommand's structure closely —
`write` copies `write_state()`'s `path_hb_asserted()` contract verbatim; `read`
deliberately does not, per §0's note:

| Aspect | `state` (existing) | `facts` (this step) |
|---|---|---|
| Storage format | JSON object | raw text (markdown) |
| Missing `.hb/`, `write` | dies via `path_hb_asserted()` | dies via `path_hb_asserted()` — same as `state` |
| Missing `.hb/`, `read` | dies via `path_hb_asserted()` | returns `""` — does not assert `.hb/` exists |
| Missing file (`.hb/` present) | `read` returns `None`, caller formats | `read` prints empty string directly |
| Content input | structured `--skill`/`--outcome`/... flags | one positional `content` string (mirrors `idea`) |

Control flow:
- `facts write <content>` → `path_hb_asserted()` (dies if `.hb/` missing) →
  overwrite `.hb/facts.md` with `content` verbatim (no injected header, no
  trailing-newline normalization) → exit 0.
- `facts read` → if `.hb/facts.md` exists, print its exact contents (no added
  newline); else print nothing → exit 0. No `.hb/` assertion — nothing to
  create, and a missing `.hb/` implies a missing facts file anyway.

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
- *Have `facts write` create `.hb/` itself if absent* — this was the original
  design; superseded by the AC3.2 amendment, which instead accepts `state.py`'s
  existing die-on-missing-`.hb/` behavior for `write` rather than adding
  directory-creation logic not asked for anywhere else in the codebase.
- *Also call `path_hb_asserted()` in `facts read`* — rejected: AC2 was not
  amended and only specifies behavior relative to the facts file, not `.hb/`
  itself; asserting would add a new failure mode (dying on read in a totally
  uninitialized project) beyond what AC2.2 requires.

---

## 2. `hb_sdk/facts.py` — specification

**New file**, structured identically to `state.py`'s section order (helpers,
then `cmd_*` handlers, then `def_cli_facts`).

- **Interfaces / signatures** (all **new**):

  | Symbol | Signature | Contract |
  |---|---|---|
  | `write_facts` | `(content: str) -> Path` | Asserts `.hb/` exists (dies via `path_hb_asserted()` if not), overwrites `.hb/facts.md` with `content` verbatim, returns the path written. |
  | `read_facts` | `() -> str` | Returns `.hb/facts.md`'s exact contents, or `""` if it doesn't exist (or `.hb/` doesn't exist) — no assertion. |
  | `cmd_facts_write` | `(args: argparse.Namespace) -> None` | Calls `write_facts(args.content)`. |
  | `cmd_facts_read` | `(args: argparse.Namespace) -> None` | Prints `read_facts()` with `end=""` (no injected newline). |
  | `def_cli_facts` | `(subs: Any) -> None` | Registers the `facts` subparser with `write`/`read` actions. |

- **Algorithm / rules:** (module imports `from .common import path_hb_asserted,
  path_hb_facts, progress`, mirroring `state.py`'s import line at `state.py:9`)
  ```python
  def write_facts(content: str) -> Path:
      path_hb_asserted()
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
  error (AC2.2). `write` dies with exit 1 and `path_hb_asserted()`'s standard
  message if `.hb/` itself is missing (AC3.2, amended) — it only lazily
  creates the file, never the directory.
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
| `test_facts_write_no_hb_dies` | **no** `init` call, `facts write "hello"` on a bare `tmp_path`, `ok=False` → `returncode != 0`, `".hb/" in result.stderr` — mirrors `test_state_record_no_hb` (`test_hb_sdk_state.py:60-63`) (AC3.2, amended) |
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
   HB=/Users/hasan.kamal-al-deen/repos/hashbuild/skills/scripts/hb-sdk
   $HB facts read                        # no .hb/ yet: prints nothing, exit 0
   $HB facts write "- fact one"; echo $? # no .hb/ yet: dies, non-zero exit
   $HB init                              # creates .hb/
   $HB facts read                        # prints nothing, exit 0
   $HB facts write "- fact one"
   ls .hb/facts.md                       # exists
   $HB facts read                        # prints "- fact one"
   ```
4. **Per-AC checks:**
   - AC1: step 3 above shows `.hb/facts.md` created lazily by `write` once
     `.hb/` exists — no separate `facts init` command was run or needed.
   - AC2.1/AC2.2: `test_facts_read_missing_file_returns_empty` +
     `test_facts_read_no_hb_at_all_returns_empty`.
   - AC3.1/AC3.2: `test_facts_write_creates_file_when_absent` +
     `test_facts_write_no_hb_dies`.
   - AC4: `grep -c "facts.*init" skills/scripts/hb_sdk/facts.py` → `0`; only
     `write`/`read` subparsers exist.
   - AC5: `skills/references/facts-template.md` exists and states the
     100/1000/120 limits as guidance, with no code path in `facts.py`
     enforcing them (confirmed by reading §2 — no length/line checks in
     `write_facts`).
   - AC6.1–AC6.3: the three tests named above.
5. **Invariant check:** `hb-sdk facts write` and `hb-sdk state record` behave
   identically on a fresh `tmp_path` with no `.hb/` — both die via
   `path_hb_asserted()` with the same `.hb/`-mentioning stderr message.
   Authoritative check is `test_facts_write_no_hb_dies` compared against
   `test_state_record_no_hb`.
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
| 3.2 | §2 (`write_facts` — `path_hb_asserted()`), §5 (`test_facts_write_no_hb_dies`) | amended — dies like `state`, does not create `.hb/` |
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
