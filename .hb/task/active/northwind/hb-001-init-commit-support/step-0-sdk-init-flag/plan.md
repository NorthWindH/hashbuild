# Step 0 Plan — SDK positional `MODE` for `commit write-message-file`

`hb-init` needs to generate an SDK-authored commit message before any task exists, but `hb-sdk commit write-message-file` today requires `--task`, making that impossible. The solution is to restructure the command around an explicit positional `MODE` argument (`plain`, `task`, `task-step`) that makes caller intent unambiguous and allows argparse to enforce per-mode requirements rather than relying on implicit flag absence. This is a breaking interface change: all existing call sites must be updated from the flat-flag form to the explicit-mode form. Once this lands, `hb-init` calls `hb-sdk commit write-message-file plain --short "initialize hashbuild"`, and all other hb-* skills call `task` or `task-step` mode explicitly.

Source ticket: `./ticket.md`. No prior steps — this is step 0.

---

## 0. Current-state facts (verified during planning)

Inspected `skills/scripts/hb-sdk` (836 lines). All facts confirmed live.

**Current argparse definition (`hb-sdk:797–814`):**
- `--task`: `required=True`
- `--step`: optional `int`
- `--short`: `required=True`
- `--long`: optional

**Current `cmd_commit_write_message_file` (`hb-sdk:772–789`):** unconditionally dereferences `args.task` and `args.short`; no branching on mode.

**Observed failure (confirmed):**
```
$ hb-sdk commit write-message-file --short "initialize hashbuild"
error: the following arguments are required: --task
exit: 2
```

**Existing call sites for `commit write-message-file`:**

All calls currently use the flat-flag form. The following must be migrated:

| Location | Current form | New form |
|---|---|---|
| `skills/references/committing.md` (example) | `--task <t> [--step <n>] --short <d>` | `task --task <t> --short <d>` / `task-step --task <t> --step <n> --short <d>` |
| `skills/scripts/hb-sdk` test suite (`tests/skills/scripts/test_hb-sdk.py:718–758`) | 3 tests calling flat-flag form | updated to explicit mode |

Skill files (`hb-task-step-plan.md`, etc.) do not call the SDK directly — they reference `committing.md` as the protocol. `committing.md` is updated in step 1 scope; skill call sites that hard-code the SDK call must be found and updated here.

**Blast radius scan:**
```bash
grep -r "commit write-message-file" skills/ tests/
```
Covers all call sites. Update every match.

**Test suite:** 3 existing tests for `commit write-message-file` — all use flat-flag form, all must be updated.

### 0.1 Impact (before → after)

| Invocation | Before | After |
|---|---|---|
| `plain --short "init hb"` | exit 2 (`--task` required) | exit 0, `hb: init hb\n` |
| `plain --short "x" --long "y"` | exit 2 | exit 0, `hb: x\n\ny\n` |
| `plain --task <t> --short "x"` | N/A (mode didn't exist) | exit 1, `--task not valid in plain mode` |
| `plain --step 0 --short "x"` | N/A | exit 1, `--step not valid in plain mode` |
| `task --task <t> --short "d"` | (was: `--task <t> --short "d"`) exit 0, `<task_id>: d\n` | exit 0, identical output |
| `task --short "d"` (missing `--task`) | exit 2, `--task` required | exit 1, `--task required in task mode` |
| `task --task <t> --step 2 --short "d"` | N/A (step accepted but mode not separate) | exit 1, `--step not valid in task mode` |
| `task-step --task <t> --step 2 --short "d"` | (was: `--task <t> --step 2 --short "d"`) exit 0, `<task_id>/step-2: d\n` | exit 0, identical output |
| `task-step --task <t> --short "d"` (missing `--step`) | exit 0, `<task_id>: d\n` (silent wrong) | exit 1, `--step required in task-step mode` |
| `--task <t> --short "d"` (old flat form) | exit 0 | exit 2, argparse error (mode missing) |

The last row is the breaking change: all callers using the old flat form must be updated.

### 0.2 Non-regression proof / risk

The output produced by `task` and `task-step` modes is identical to the old flat-flag invocations for the same inputs. The only risk is call sites that are not updated. The blast-radius grep (§0) is the authoritative check — every match must be migrated.

| At-risk case | Risk | Guard |
|---|---|---|
| Skill files calling flat-flag form | Silent break at skill execution time | Grep all call sites; update all |
| `committing.md` example | Doc mismatch | Updated in step 1; plan notes the dependency |
| Test suite flat-flag tests | Tests fail after change | All 3 existing tests updated to new form |

---

## 1. Design overview

Add `mode` as a required positional argument with `choices=["plain", "task", "task-step"]` to the `write-message-file` subparser. `--task` and `--step` become optional in argparse (default `None`); per-mode validation enforces their presence or absence in the function body. `--short` stays `required=True` globally.

**Mode dispatch table:**

| Mode | `--task` | `--step` | `--short` | `--long` | Subject |
|---|---|---|---|---|---|
| `plain` | forbidden | forbidden | required | optional | `hb: <short>` |
| `task` | required | forbidden | required | optional | `<task_id>: <short>` |
| `task-step` | required | required | required | optional | `<task_id>/step-<n>: <short>` |

**Alternatives considered and rejected:**

| Alternative | Reason rejected |
|---|---|
| `--init` flag (original plan) | Caller intent implicit; `--short` silently ignored; not extensible |
| `--no-task` flag | Caller intent still partially implicit; adds a flag rather than a mode |
| Optional `--task` with no new flag | Forgetting `--task` is silently wrong; `task` vs `task-step` distinction still implicit |

---

## 2. `cmd_commit_write_message_file` — specification

**Signature:** unchanged (`args: argparse.Namespace`).

**New field:** `args.mode` (`str`, one of `"plain"`, `"task"`, `"task-step"`) — **new**.

**Modified argparse fields:**
- `args.task`: `required=False`, default `None` — was `required=True`
- `args.step`: unchanged (already optional)
- `args.short`: `required=True` — unchanged
- `args.long`: unchanged

**Algorithm:**

```python
def cmd_commit_write_message_file(args: argparse.Namespace) -> None:
    if args.mode == "plain":
        if args.task is not None:
            _die("error: --task is not valid in plain mode")
        if args.step is not None:
            _die("error: --step is not valid in plain mode")
        subject = f"hb: {args.short}"

    elif args.mode == "task":
        if args.task is None:
            _die("error: --task is required in task mode")
        if args.step is not None:
            _die("error: --step is not valid in task mode")
        tn = _parse_task_name(args.task)
        subject = f"{tn.task_id}: {args.short}"

    elif args.mode == "task-step":
        if args.task is None:
            _die("error: --task is required in task-step mode")
        if args.step is None:
            _die("error: --step is required in task-step mode")
        tn = _parse_task_name(args.task)
        subject = f"{tn.task_id}/step-{args.step}: {args.short}"

    message = subject + "\n"
    if args.long:
        message += "\n" + args.long + "\n"

    fd, path = tempfile.mkstemp(prefix="hb-commit-", suffix=".txt")
    with open(fd, "w") as f:
        f.write(message)
    print(path)
```

**Failure contract (per mode):**

| Condition | Exit | Stderr |
|---|---|---|
| `plain` + `--task` | non-zero | `--task is not valid in plain mode` |
| `plain` + `--step` | non-zero | `--step is not valid in plain mode` |
| `task` + no `--task` | non-zero | `--task is required in task mode` |
| `task` + `--step` | non-zero | `--step is not valid in task mode` |
| `task-step` + no `--task` | non-zero | `--task is required in task-step mode` |
| `task-step` + no `--step` | non-zero | `--step is required in task-step mode` |
| No `mode` positional | exit 2 (argparse) | usage error |

---

## 3. Integration / wiring

`_def_cli_commit` changes:
- Add `mode` positional with `choices=["plain", "task", "task-step"]` before the flag arguments
- Change `--task` from `required=True` to `required=False`

No other functions reference `cmd_commit_write_message_file`. All skill call sites go through shell invocations; those are updated in §4.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — `_def_cli_commit`: add `mode` positional, set `--task` to `required=False`. Rewrite `cmd_commit_write_message_file` per §2. |
| `tests/skills/scripts/test_hb-sdk.py` | **edit** — update 3 existing `commit write-message-file` tests to use explicit mode; add 9 new tests for `plain` mode and per-mode error cases (§5). |
| Any skill file containing `commit write-message-file` without a mode | **edit** — insert the appropriate mode (`task` or `task-step`) after `write-message-file`. Identified by blast-radius grep. |

`committing.md` example invocation is in step 1 scope; noted here as a known pending update.

No new dependencies. No lockfile effects.

---

## 5. Tests

Mirrors existing test style: subprocess via `run()`, `tmp_path` fixture.

**Updated helper:**

```python
def commit_write_message_file(cwd: Path, mode: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["commit", "write-message-file", mode]
    if task := kwargs.get("task"):
        args += ["--task", task]
    if (step := kwargs.get("step")) is not None:
        args += ["--step", str(step)]
    if short := kwargs.get("short"):
        args += ["--short", short]
    if long := kwargs.get("long"):
        args += ["--long", long]
    return run(args, cwd, ok=kwargs.get("ok", True))
```

**Existing tests — updated (output unchanged, invocation updated):**

| Test | Old call | New call |
|---|---|---|
| `test_commit_write_message_file_basic` | `--task hasan/abc-1 --short "add login page"` | `task --task hasan/abc-1 --short "add login page"` |
| `test_commit_write_message_file_with_step` | `--task hasan/abc-1 --step 2 --short "..."` | `task-step --task hasan/abc-1 --step 2 --short "..."` |
| `test_commit_write_message_file_with_long` | `--task hasan/abc-1 --short "..." --long "..."` | `task --task hasan/abc-1 --short "..." --long "..."` |

**New tests:**

| Test | What it asserts |
|---|---|
| `test_commit_wmf_plain_basic` | `plain --short "init hb"` → exit 0; file = `hb: init hb\n` |
| `test_commit_wmf_plain_with_long` | `plain --short "x" --long "y"` → `hb: x\n\ny\n` |
| `test_commit_wmf_plain_rejects_task` | `plain --task hasan/abc-1 --short "x"` → non-zero; "not valid in plain mode" |
| `test_commit_wmf_plain_rejects_step` | `plain --step 0 --short "x"` → non-zero; "not valid in plain mode" |
| `test_commit_wmf_task_requires_task` | `task --short "x"` → non-zero; "required in task mode" |
| `test_commit_wmf_task_rejects_step` | `task --task hasan/abc-1 --step 2 --short "x"` → non-zero; "not valid in task mode" |
| `test_commit_wmf_task_step_requires_task` | `task-step --step 2 --short "x"` → non-zero; "required in task-step mode" |
| `test_commit_wmf_task_step_requires_step` | `task-step --task hasan/abc-1 --short "x"` → non-zero; "required in task-step mode" |
| `test_commit_wmf_no_mode_errors` | `--task hasan/abc-1 --short "x"` (old flat form) → exit 2 |

**Non-regression:** the 3 updated existing tests (same assertions, new invocation form) are the authoritative guard that `task` and `task-step` output is unchanged.

---

## 6. Verification (after implementation)

1. **Full test suite green:**
   ```bash
   cd /home/hkamal/repos/hashbuild && python -m pytest tests/ -v
   ```

2. **Blast-radius grep confirms no unmigrated call sites:**
   ```bash
   grep -r "commit write-message-file" skills/ tests/
   # every match must include a mode word as the next token
   ```

3. **Per-AC checks:**

   AC 1 — positional MODE accepted:
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --help
   # usage shows: MODE {plain,task,task-step}
   ```

   AC 2 — plain mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file plain --short "initialize hashbuild")
   cat "$FILE"   # → "hb: initialize hashbuild\n"
   python skills/scripts/hb-sdk commit write-message-file plain --task foo/abc-1 --short "x"
   # → non-zero exit
   ```

   AC 3 — task mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file task --task hasan/abc-1 --short "add login")
   cat "$FILE"   # → "abc-1: add login\n"
   python skills/scripts/hb-sdk commit write-message-file task --short "x"
   # → non-zero; "--task is required in task mode"
   python skills/scripts/hb-sdk commit write-message-file task --task hasan/abc-1 --step 2 --short "x"
   # → non-zero; "--step is not valid in task mode"
   ```

   AC 4 — task-step mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file task-step --task hasan/abc-1 --step 2 --short "add login")
   cat "$FILE"   # → "abc-1/step-2: add login\n"
   python skills/scripts/hb-sdk commit write-message-file task-step --task hasan/abc-1 --short "x"
   # → non-zero; "--step is required in task-step mode"
   ```

   AC 5 — call site migration:
   ```bash
   grep -r "commit write-message-file" skills/ tests/
   # confirm no flat-flag form remains
   ```

4. **Scope check:** `git diff --name-only` shows only `hb-sdk`, `test_hb-sdk.py`, and any migrated skill files.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — positional MODE accepted | §2 (`mode` positional, `choices`), §4, §5 (`test_commit_wmf_no_mode_errors`) | |
| 2 — plain mode behavior | §2 (`plain` branch), §5 (`test_commit_wmf_plain_*`), §6 AC 2 check | |
| 2.1 — plain rejects `--task`/`--step` | §2 guards, `_plain_rejects_task`, `_plain_rejects_step` | |
| 2.2 — `--short` required, `--long` optional | `--short` stays `required=True` in argparse; `--long` unchanged | |
| 2.3 — subject `hb: <short>` | §2 `subject = f"hb: {args.short}"` | |
| 3 — task mode behavior | §2 (`task` branch), §5 (`test_commit_wmf_task_*`), §6 AC 3 check | |
| 3.1 — `--task` required, `--step` forbidden | §2 guards, `_task_requires_task`, `_task_rejects_step` | |
| 3.2 — `--short` required, `--long` optional | argparse global; unchanged | |
| 3.3 — subject `<task_id>: <short>` | §2 `task` branch | |
| 4 — task-step mode behavior | §2 (`task-step` branch), §5 (`test_commit_wmf_task_step_*`), §6 AC 4 check | |
| 4.1 — `--task` and `--step` both required | §2 guards, `_task_step_requires_task`, `_task_step_requires_step` | |
| 4.2 — `--short` required, `--long` optional | argparse global; unchanged | |
| 4.3 — subject `<task_id>/step-<n>: <short>` | §2 `task-step` branch | |
| 5 — all call sites migrated | §4 (blast-radius grep), §5 (updated existing tests), §6 AC 5 check | `committing.md` example deferred to step 1 |

---

## 8. Out of scope (per ticket)

- Changes to `hb-init` skill (`skills/hb-init.md`) — deferred to step 1
- Changes to `committing.md` example invocation — deferred to step 1
- Changes to any other `hb-sdk` subcommand
