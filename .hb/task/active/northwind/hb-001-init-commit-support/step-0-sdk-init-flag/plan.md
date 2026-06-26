# Step 0 Plan — SDK `--init` flag for `commit write-message-file`

`hb-init` needs to generate an SDK-authored commit message before any task exists, but `hb-sdk commit write-message-file` requires `--task`, making that impossible. Running `hb-sdk commit write-message-file --init` today fails with: `error: the following arguments are required: --task, --short` (exit 2). This is the only callsite blocked by the missing flag; all other hb-* skills already have a task in scope when they commit. The change is purely additive — a new flag path through a single function, no existing argument shapes change. Once this lands, `hb-init` can call `hb-sdk commit write-message-file --init` and receive a valid commit message file without supplying `--task`.

Source ticket: `./ticket.md`. No prior steps — this is step 0 and the first change to the SDK for this task.

> **Design decision — `--short` semantics in `--init` mode.** AC 1.2 fixes the subject to `hb: initialize hashbuild`; AC 1.3 says `--short` remains valid and optional alongside `--init`. These pull against each other: a fixed subject has no slot for a user-supplied short description. Resolution: in `--init` mode, `--short` is accepted (no error) but has no effect — it is silently ignored. The fixed subject is authoritative. `--long` is accepted and appended as a body paragraph if provided, matching normal behavior. This is the only interpretation consistent with both ACs: "valid and optional" means it does not error, not that it produces observable output. See §1 and §7.

---

## 0. Current-state facts (verified during planning)

Inspected `skills/scripts/hb-sdk` (the single SDK file, 836 lines). All facts below are confirmed live, not assumed.

**`cmd_commit_write_message_file` — current implementation (`hb-sdk:772-789`):**
```python
def cmd_commit_write_message_file(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.task)          # args.task always set; None would crash here
    task_id = tn.task_id
    prefix = task_id
    if args.step is not None:
        prefix += f"/step-{args.step}"
    subject = f"{prefix}: {args.short}"
    message = subject + "\n"
    if args.long:
        message += "\n" + args.long + "\n"
    fd, path = tempfile.mkstemp(prefix="hb-commit-", suffix=".txt")
    with open(fd, "w") as f:
        f.write(message)
    print(path)
```

**Argparse definition for `write-message-file` (`hb-sdk:797-814`):**
- `--task`: `required=True`
- `--step`: optional `int`
- `--short`: `required=True`
- `--long`: optional

**Observed failure (confirmed by running the command):**
```
$ hb-sdk commit write-message-file --init
usage: hb-sdk commit write-message-file [-h] --task <task> [--step <n>] --short <desc> [--long <desc>]
hb-sdk commit write-message-file: error: the following arguments are required: --task, --short
exit: 2
```
`--init` is unrecognized; argparse reports it as unknown and also flags the missing required args.

**Blast radius of `cmd_commit_write_message_file`:**  
No other Python code calls this function — it is only reached via `args.func(args)` after argparse dispatch. Skills call it via shell (`hb-sdk commit write-message-file`). Three shell call sites in `committing.md` and skill files, all using `--task`. No callers pass `--init` today (the flag does not exist yet).

**Test suite (`tests/skills/scripts/test_hb-sdk.py:718-758`):**  
Three existing tests for `commit write-message-file`: basic (task + short), with step, with long. All invoke via subprocess. No test exercises `--init`.

### 0.1 Impact (before → after)

| Invocation | Before | After |
|---|---|---|
| `--init` (alone) | exit 2, argparse error | exit 0, file with `hb: initialize hashbuild\n` |
| `--init --long "reason"` | exit 2 | exit 0, file with `hb: initialize hashbuild\n\nreason\n` |
| `--init --short "x"` | exit 2 | exit 0, file with `hb: initialize hashbuild\n` (short ignored) |
| `--init --task <t>` | exit 2 | exit 1, descriptive error |
| `--init --step 0` | exit 2 | exit 1, descriptive error |
| `--task <t> --short <d>` | exit 0, file with `<task_id>: <d>\n` | identical — no change |
| `--task <t> --step 2 --short <d>` | exit 0, file with `<task_id>/step-2: <d>\n` | identical |
| `--task <t> --short <d> --long <l>` | exit 0, file with subject + body | identical |
| `--short` without `--task` or `--init` | exit 2, `--task` required | exit 1, `--task` required (error text may differ slightly) |

Change is additive for `--init` paths; behavior-preserving for all `--task` paths.

### 0.2 Non-regression proof

The change affects `--task` paths in two ways: (a) `--task` becomes `required=False` in argparse, and (b) `--short` becomes `required=False` in argparse. Both are immediately re-validated in `cmd_commit_write_message_file` when `--init` is absent. The guard: `if not is_init and args.task is None: _die(...)` and `if not is_init and args.short is None: _die(...)`. Existing callers all pass `--task` and `--short`, so they hit neither guard.

| At-risk case | Current behavior | Why it can't change |
|---|---|---|
| `--task <t> --short <d>` | exit 0, correct message | `--task`/`--short` still parsed; same code path after `is_init=False` branch |
| `--task <t>` without `--short` | exit 2 from argparse | Still exits non-zero; guard in `cmd_` fires with `_die` instead; error text is "error: --short is required..." |
| No args at all | exit 2 from argparse | `--task` and `--short` both absent; `is_init` also absent; hits the `--task` required guard |

The three existing tests (`test_commit_write_message_file_basic`, `_with_step`, `_with_long`) exercise the must-not-change paths and serve as non-regression.

---

## 1. Design overview

Add `--init` as a boolean flag to the `write-message-file` subparser. Change `--task` and `--short` from `required=True` to `required=False` (default `None`). In `cmd_commit_write_message_file`, branch on `args.init`:

```
if --init:
    guard: --task must be None  →  _die if not
    guard: --step must be None  →  _die if not
    subject = "hb: initialize hashbuild"
    (--short is accepted but ignored)
else:
    guard: --task must not be None  →  _die if None
    guard: --short must not be None  →  _die if None
    (existing logic unchanged)
```

Message assembly is shared: `subject + "\n"` + optional `"\n" + long + "\n"`.

**Alternatives considered and rejected:**

| Alternative | Reason rejected |
|---|---|
| `argparse.add_mutually_exclusive_group` for `--init`/`--task` | Can't express the 3-way constraint (`--init` forbids both `--task` and `--step`) cleanly; manual validation is more readable and already needed for `--short` |
| Separate `write-init-message-file` subcommand | Duplicates the temp-file scaffolding; `committing.md` would need two code paths; higher surface area for no gain |
| Keep `--task required=True`, derive init from a sentinel value like `--task=init` | Conflates a real task name with a sentinel; fragile |

---

## 2. `cmd_commit_write_message_file` — specification

**Signature:** unchanged (`args: argparse.Namespace`) — **refactor (signature preserved)**.

**New flag:** `args.init` (`bool`, `store_true`, default `False`) — **new**.

**Modified fields in `args`:**
- `args.task`: type `str | None`, default `None` — changed from required to optional in argparse; validated in body.
- `args.short`: type `str | None`, default `None` — changed from required to optional in argparse; validated in body.

**Algorithm:**

```python
def cmd_commit_write_message_file(args: argparse.Namespace) -> None:
    is_init = args.init  # new bool flag

    if is_init:
        if args.task is not None:
            _die("error: --init and --task are mutually exclusive")
        if args.step is not None:
            _die("error: --init and --step are mutually exclusive")
        subject = "hb: initialize hashbuild"
    else:
        if args.task is None:
            _die("error: --task is required when --init is not passed")
        if args.short is None:
            _die("error: --short is required when --init is not passed")
        tn = _parse_task_name(args.task)
        task_id = tn.task_id
        prefix = task_id
        if args.step is not None:
            prefix += f"/step-{args.step}"
        subject = f"{prefix}: {args.short}"

    message = subject + "\n"
    if args.long:
        message += "\n" + args.long + "\n"

    fd, path = tempfile.mkstemp(prefix="hb-commit-", suffix=".txt")
    with open(fd, "w") as f:
        f.write(message)
    print(path)
```

**Failure contract:**
- `--init` + `--task` → non-zero exit, `error: --init and --task are mutually exclusive` on stderr
- `--init` + `--step` → non-zero exit, `error: --init and --step are mutually exclusive` on stderr
- Neither `--init` nor `--task` → non-zero exit, `error: --task is required when --init is not passed` on stderr
- `--task` without `--short` (and no `--init`) → non-zero exit, `error: --short is required when --init is not passed` on stderr

---

## 3. Integration / wiring

No wiring changes. `cmd_commit_write_message_file` is invoked only via `args.func(args)` at `hb-sdk:831`. The subparser registration in `_def_cli_commit` changes two argument attributes (`required=False`) and adds one new argument (`--init`). No other file references this function.

Public CLI interface: `hb-sdk commit write-message-file` — the interface gains `--init` (additive); no existing flag is removed or renamed.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — modify `_def_cli_commit`: set `--task` and `--short` to `required=False`; add `--init` as `store_true`. Rewrite `cmd_commit_write_message_file` to branch on `args.init` per §2. All other functions untouched. |
| `tests/skills/scripts/test_hb-sdk.py` | **extend** — add new test cases for `--init` path (§5). Existing tests unchanged. |

No new dependencies. No lockfile effects. No build wiring changes.

---

## 5. Tests

Mirrors the existing test style in `tests/skills/scripts/test_hb-sdk.py`: subprocess calls via the `run()` helper, `tmp_path` fixture, assertions on stdout/stderr/returncode.

**Helper (new):**
```python
def commit_write_message_file(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["commit", "write-message-file"]
    if kwargs.get("init"):
        args.append("--init")
    if task := kwargs.get("task"):
        args += ["--task", task]
    if step := kwargs.get("step"):
        args += ["--step", str(step)]
    if short := kwargs.get("short"):
        args += ["--short", short]
    if long := kwargs.get("long"):
        args += ["--long", long]
    return run(args, cwd, ok=kwargs.get("ok", True))
```

**New test cases:**

| Test | What it asserts |
|---|---|
| `test_commit_wmf_init_basic` | `--init` alone → exit 0; file contains `hb: initialize hashbuild\n` |
| `test_commit_wmf_init_with_long` | `--init --long "reason"` → file contains `hb: initialize hashbuild\n\nreason\n` |
| `test_commit_wmf_init_short_accepted` | `--init --short "x"` → exit 0; file contains `hb: initialize hashbuild\n` (short ignored) |
| `test_commit_wmf_init_rejects_task` | `--init --task "hasan/abc-1"` → non-zero exit; `--init and --task are mutually exclusive` in stderr |
| `test_commit_wmf_init_rejects_step` | `--init --step 0` → non-zero exit; `--init and --step are mutually exclusive` in stderr |
| `test_commit_wmf_no_init_no_task_errors` | Neither `--init` nor `--task` → non-zero exit; `--task is required` in stderr |
| `test_commit_wmf_task_without_short_errors` | `--task "hasan/abc-1"` no `--short` → non-zero exit; `--short is required` in stderr |

**Non-regression:** `test_commit_write_message_file_basic`, `test_commit_write_message_file_with_step`, `test_commit_write_message_file_with_long` must pass unchanged. These are the authoritative guard for the `--task` path.

---

## 6. Verification (after implementation)

1. **Run full test suite:**
   ```bash
   cd /home/hkamal/repos/hashbuild && python -m pytest tests/ -v
   ```
   Must be green. Zero regressions.

2. **Exercise `--init` happy path directly:**
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --init
   # → prints a path; cat that path → "hb: initialize hashbuild\n"
   ```

3. **Per-AC checks:**

   AC 1 — `--init` accepted as alternative to `--task`:
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --init
   # exit 0; path printed
   ```

   AC 1.1 — mutual exclusion errors:
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --init --task hasan/abc-1
   # exit non-zero; stderr: "mutually exclusive"
   python skills/scripts/hb-sdk commit write-message-file --init --step 0
   # exit non-zero; stderr: "mutually exclusive"
   ```

   AC 1.2 — fixed subject:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file --init)
   cat "$FILE"
   # → "hb: initialize hashbuild\n"
   ```

   AC 1.3 — `--short`/`--long` optional alongside `--init`:
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --init --short "ignored" && echo OK
   FILE=$(python skills/scripts/hb-sdk commit write-message-file --init --long "body text")
   cat "$FILE"
   # → "hb: initialize hashbuild\n\nbody text\n"
   ```

   AC 2 — existing `--task` invocations unchanged:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file --task hasan/abc-1 --short "add login")
   cat "$FILE"
   # → "abc-1: add login\n"
   FILE=$(python skills/scripts/hb-sdk commit write-message-file --task hasan/abc-1 --step 2 --short "add login")
   cat "$FILE"
   # → "abc-1/step-2: add login\n"
   ```

4. **Scope check:** Only `skills/scripts/hb-sdk` and `tests/skills/scripts/test_hb-sdk.py` should appear in `git diff --name-only`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `--init` accepted as alternative to `--task` | §2 (`args.init` flag, `is_init` branch), §4, §5 (`test_commit_wmf_init_basic`), §6 AC 1 check | |
| 1.1 — `--init` + `--task` or `--step` is hard error | §2 (guards in `is_init` branch), §5 (`test_commit_wmf_init_rejects_task`, `_rejects_step`), §6 AC 1.1 check | |
| 1.2 — subject is `hb: initialize hashbuild` | §2 (`subject = "hb: initialize hashbuild"`), §5 (`test_commit_wmf_init_basic`), §6 AC 1.2 check | |
| 1.3 — `--short`/`--long` valid and optional with `--init` | §2 (design decision: `--short` silently ignored, `--long` appended), §5 (`test_commit_wmf_init_short_accepted`, `_with_long`), §6 AC 1.3 check | `--short` does not error; `--long` appends body |
| 2 — all existing `--task` invocations unchanged | §2 (`else` branch: identical logic), §0.2, §5 (non-regression tests), §6 AC 2 check | Three existing tests are the authoritative guard |

---

## 8. Out of scope (per ticket)

- Changes to `hb-init` skill (`skills/hb-init.md`) — deferred to step 1
- Changes to `committing.md` (`skills/references/committing.md`) — deferred to step 1
- Changes to any other `hb-sdk` subcommand
