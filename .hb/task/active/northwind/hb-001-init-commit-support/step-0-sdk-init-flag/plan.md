# Step 0 Plan — SDK subparser modes for `commit write-message-file`

`hb-init` needs to generate an SDK-authored commit message before any task exists, but `hb-sdk commit write-message-file` today requires `--task`, making that impossible. The solution is to replace the single flat-flag command with three subparser modes (`plain`, `task`, `task-step`), letting argparse enforce per-mode requirements natively — no manual validation guards needed. This is a breaking interface change: all existing call sites must be updated from the flat-flag form to the explicit-mode form. Once this lands, `hb-init` calls `hb-sdk commit write-message-file plain --short "initialize hashbuild"`, and all other hb-* skills call `task` or `task-step` mode explicitly.

Source ticket: `./ticket.md`. No prior steps — this is step 0.

---

## 0. Current-state facts (verified during planning)

Inspected `skills/scripts/hb-sdk` (836 lines). All facts confirmed live.

**Current argparse definition (`hb-sdk:797–814`):**
- `--task`: `required=True`
- `--step`: optional `int`
- `--short`: `required=True`
- `--long`: optional

**Current `cmd_commit_write_message_file` (`hb-sdk:772–789`):** single function; unconditionally dereferences `args.task` and `args.short`; no mode branching.

**Observed failure (confirmed):**
```
$ hb-sdk commit write-message-file --short "initialize hashbuild"
error: the following arguments are required: --task
exit: 2
```

**Existing call sites for `commit write-message-file`** (confirmed by grep):

| Location | Current form | New form |
|---|---|---|
| `skills/references/committing.md` (example) | `--task <t> [--step <n>] --short <d>` | `task --task <t> --short <d>` / `task-step --task <t> --step <n> --short <d>` |
| `tests/skills/scripts/test_hb-sdk.py:718–758` | 3 tests, flat-flag form | updated to subparser mode |

Skill files do not call the SDK directly — they follow `committing.md` as protocol. `committing.md` is updated in step 1 scope. No other hard-coded flat-flag call sites exist (confirmed by grep).

**Blast-radius scan:**
```bash
grep -r "commit write-message-file" skills/ tests/
```
Every match must be migrated.

**Test suite:** 3 existing tests for `commit write-message-file` — all flat-flag form, all must be updated.

### 0.1 Impact (before → after)

| Invocation | Before | After |
|---|---|---|
| `plain --short "init hb"` | exit 2 (`--task` required) | exit 0, `hb: init hb\n` |
| `plain --short "x" --long "y"` | exit 2 | exit 0, `hb: x\n\ny\n` |
| `plain --task <t> --short "x"` | N/A | exit 2, argparse: unrecognized arguments |
| `plain --step 0 --short "x"` | N/A | exit 2, argparse: unrecognized arguments |
| `task --task <t> --short "d"` | (was `--task <t> --short "d"`) exit 0 | exit 0, **identical output** |
| `task --short "d"` (missing `--task`) | exit 2, `--task` required | exit 2, argparse: `--task` required |
| `task --task <t> --step 2 --short "d"` | N/A | exit 2, argparse: unrecognized arguments |
| `task-step --task <t> --step 2 --short "d"` | (was `--task <t> --step 2 --short "d"`) exit 0 | exit 0, **identical output** |
| `task-step --task <t> --short "d"` (missing `--step`) | exit 0, wrong subject silently | exit 2, argparse: `--step` required |
| `--task <t> --short "d"` (old flat form) | exit 0 | exit 2, argparse: mode required |

**Breaking change:** the last row — all callers using the old flat form must be updated.

### 0.2 Non-regression proof / risk

Output produced by `task` and `task-step` modes is byte-identical to the old flat-flag invocations for the same inputs. The only risk is unmigrated call sites.

| At-risk case | Risk | Guard |
|---|---|---|
| Skill files with flat-flag calls | Silent break at skill execution time | Blast-radius grep; confirmed none beyond `committing.md` |
| `committing.md` example | Doc mismatch | Updated in step 1; dependency noted |
| Test suite flat-flag tests | Tests fail | All 3 existing tests updated to subparser form |

---

## 1. Design overview

`write-message-file` becomes a subparser group with three modes. Each mode gets its own argparse parser with only its own flags defined — argparse enforces required flags and rejects unrecognized ones natively. No cross-mode validation guards exist in the function body.

**Mode dispatch table:**

| Mode | `--task` | `--step` | `--short` | `--long` | Subject |
|---|---|---|---|---|---|
| `plain` | not defined | not defined | required | optional | `hb: <short>` |
| `task` | required | not defined | required | optional | `<task_id>: <short>` |
| `task-step` | required | required | required | optional | `<task_id>/step-<n>: <short>` |

"Not defined" means argparse rejects the flag as `unrecognized arguments` — no application-level guard needed.

**Existing SDK subparser depth for context:**
```
hb-sdk
  ├── init
  ├── task
  │     └── [archive, unarchive, path, create, step]
  │               └── [add, path, number, list, execution-slug]
  ├── summarize
  └── commit
        └── write-message-file          ← adds subparser level here
                  └── [plain, task, task-step]
```
This adds one level consistent with the existing `task → step → ...` pattern.

**Alternatives considered and rejected:**

| Alternative | Reason rejected |
|---|---|
| `--init` flag | Caller intent implicit; `--short` silently ignored; not extensible |
| `--no-task` flag | Partially implicit; adds a flag rather than a mode |
| Optional `--task`, no new flag | Forgetting `--task` silently wrong; `task` vs `task-step` ambiguous |
| Positional `mode` arg on flat parser | Requires manual `_die()` guards for all per-mode constraints; subparser does this for free |

---

## 2. New units — specification

### 2.1 Parser wiring (`_def_cli_commit`)

```python
def _def_cli_commit(subs: typing.Any) -> None:
    p_commit = subs.add_parser("commit", help="Commit operations")
    commit_subs = p_commit.add_subparsers(dest="commit_command", metavar="<action>")
    commit_subs.required = True

    p_wmf = commit_subs.add_parser(
        "write-message-file", help="Write commit message to a temp file; prints path"
    )
    wmf_subs = p_wmf.add_subparsers(dest="wmf_mode", metavar="<mode>")
    wmf_subs.required = True

    p_plain = wmf_subs.add_parser("plain", help="SDK-level commit (no task)")
    p_plain.add_argument("--short", required=True, metavar="<desc>", help='One-line description')
    p_plain.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_plain.set_defaults(func=cmd_commit_wmf_plain)

    p_task = wmf_subs.add_parser("task", help="Task-level commit")
    p_task.add_argument("--task", required=True, metavar="<task>", help="Fully-qualified task name")
    p_task.add_argument("--short", required=True, metavar="<desc>", help='One-line description')
    p_task.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_task.set_defaults(func=cmd_commit_wmf_task)

    p_task_step = wmf_subs.add_parser("task-step", help="Step-level commit")
    p_task_step.add_argument("--task", required=True, metavar="<task>", help="Fully-qualified task name")
    p_task_step.add_argument("--step", required=True, type=int, metavar="<n>", help="Step number")
    p_task_step.add_argument("--short", required=True, metavar="<desc>", help='One-line description')
    p_task_step.add_argument("--long", metavar="<desc>", help="Longer explanation (optional)")
    p_task_step.set_defaults(func=cmd_commit_wmf_task_step)
```

### 2.2 Shared helper — **new**

```python
def _commit_write_message_file(subject: str, long: str | None) -> None:
    message = subject + "\n"
    if long:
        message += "\n" + long + "\n"
    fd, path = tempfile.mkstemp(prefix="hb-commit-", suffix=".txt")
    with open(fd, "w") as f:
        f.write(message)
    print(path)
```

### 2.3 Mode functions — **new** (replace `cmd_commit_write_message_file`)

```python
def cmd_commit_wmf_plain(args: argparse.Namespace) -> None:
    _commit_write_message_file(f"hb: {args.short}", args.long)


def cmd_commit_wmf_task(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.task)
    _commit_write_message_file(f"{tn.task_id}: {args.short}", args.long)


def cmd_commit_wmf_task_step(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.task)
    _commit_write_message_file(f"{tn.task_id}/step-{args.step}: {args.short}", args.long)
```

**Failure contract** — all enforced by argparse, exit 2:

| Condition | Argparse error |
|---|---|
| `plain` + `--task` or `--step` | `unrecognized arguments: --task` / `--step` |
| `task` + no `--task` | `the following arguments are required: --task` |
| `task` + `--step` | `unrecognized arguments: --step` |
| `task-step` + no `--task` | `the following arguments are required: --task` |
| `task-step` + no `--step` | `the following arguments are required: --step` |
| No mode given | `the following arguments are required: <mode>` |

---

## 3. Integration / wiring

`cmd_commit_write_message_file` is deleted. Replaced by `_commit_write_message_file` (helper) and three mode functions. Each mode function is wired via `set_defaults(func=...)` — dispatch in `main()` (`args.func(args)`) requires no changes.

`_def_cli_commit` is rewritten per §2.1; the existing `p_wmf` block (lines 797–814) is replaced entirely.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — delete `cmd_commit_write_message_file`; add `_commit_write_message_file` helper and three mode functions; rewrite `_def_cli_commit` per §2.1 |
| `tests/skills/scripts/test_hb-sdk.py` | **edit** — update 3 existing tests to subparser form; add 9 new tests (§5) |
| Any skill file with hard-coded flat-flag call | **edit** — confirmed none beyond `committing.md`, which is step 1 scope |

No new dependencies. No lockfile effects.

---

## 5. Tests

Mirrors existing test style: subprocess via `run()`, `tmp_path` fixture. Error assertions check `returncode != 0` and that relevant flag name appears in stderr (argparse always names the flag).

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

**Existing tests — updated (output assertions unchanged, invocation updated):**

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
| `test_commit_wmf_plain_rejects_task` | `plain --task hasan/abc-1 --short "x"` → exit 2; `--task` in stderr |
| `test_commit_wmf_plain_rejects_step` | `plain --step 0 --short "x"` → exit 2; `--step` in stderr |
| `test_commit_wmf_task_requires_task` | `task --short "x"` → exit 2; `--task` in stderr |
| `test_commit_wmf_task_rejects_step` | `task --task hasan/abc-1 --step 2 --short "x"` → exit 2; `--step` in stderr |
| `test_commit_wmf_task_step_requires_task` | `task-step --step 2 --short "x"` → exit 2; `--task` in stderr |
| `test_commit_wmf_task_step_requires_step` | `task-step --task hasan/abc-1 --short "x"` → exit 2; `--step` in stderr |
| `test_commit_wmf_no_mode_errors` | `--task hasan/abc-1 --short "x"` (old flat form) → exit 2 |

**Non-regression:** the 3 updated existing tests (same output assertions, new invocation form) are the authoritative guard that `task` and `task-step` output is unchanged.

---

## 6. Verification (after implementation)

1. **Full test suite green:**
   ```bash
   cd /home/hkamal/repos/hashbuild && python -m pytest tests/ -v
   ```

2. **Blast-radius grep — no unmigrated call sites:**
   ```bash
   grep -r "commit write-message-file" skills/ tests/
   # every match must have a mode word as the next token
   ```

3. **Per-AC checks:**

   AC 1 — subparser modes visible in help:
   ```bash
   python skills/scripts/hb-sdk commit write-message-file --help
   # shows: <mode>  {plain,task,task-step}
   python skills/scripts/hb-sdk commit write-message-file plain --help
   # shows only --short, --long
   python skills/scripts/hb-sdk commit write-message-file task-step --help
   # shows --task, --step, --short, --long
   ```

   AC 2 — plain mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file plain --short "initialize hashbuild")
   cat "$FILE"   # → "hb: initialize hashbuild\n"
   python skills/scripts/hb-sdk commit write-message-file plain --task foo/abc-1 --short "x"
   # → exit 2, "unrecognized arguments: --task"
   ```

   AC 3 — task mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file task --task hasan/abc-1 --short "add login")
   cat "$FILE"   # → "abc-1: add login\n"
   python skills/scripts/hb-sdk commit write-message-file task --short "x"
   # → exit 2, "--task" required
   python skills/scripts/hb-sdk commit write-message-file task --task hasan/abc-1 --step 2 --short "x"
   # → exit 2, "unrecognized arguments: --step"
   ```

   AC 4 — task-step mode:
   ```bash
   FILE=$(python skills/scripts/hb-sdk commit write-message-file task-step --task hasan/abc-1 --step 2 --short "add login")
   cat "$FILE"   # → "abc-1/step-2: add login\n"
   python skills/scripts/hb-sdk commit write-message-file task-step --task hasan/abc-1 --short "x"
   # → exit 2, "--step" required
   ```

   AC 5 — call site migration:
   ```bash
   grep -r "commit write-message-file" skills/ tests/
   # no flat-flag form remains
   ```

4. **Scope check:** `git diff --name-only` shows only `hb-sdk` and `test_hb-sdk.py`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — subparser modes | §2.1 (wmf subparser group), §5 (`test_commit_wmf_no_mode_errors`), §6 AC 1 | |
| 2 — plain mode | §2.3 `cmd_commit_wmf_plain`, §5 `test_commit_wmf_plain_*`, §6 AC 2 | |
| 2.1 — plain rejects `--task`/`--step` | §2.1 (`p_plain` has neither defined); argparse enforces | |
| 2.2 — `--short` required, `--long` optional | §2.1 `p_plain` definition | |
| 2.3 — subject `hb: <short>` | §2.3 `f"hb: {args.short}"` | |
| 3 — task mode | §2.3 `cmd_commit_wmf_task`, §5 `test_commit_wmf_task_*`, §6 AC 3 | |
| 3.1 — `--task` required, `--step` forbidden | §2.1 `p_task` definition; argparse enforces both | |
| 3.2 — `--short` required, `--long` optional | §2.1 `p_task` definition | |
| 3.3 — subject `<task_id>: <short>` | §2.3 `f"{tn.task_id}: {args.short}"` | |
| 4 — task-step mode | §2.3 `cmd_commit_wmf_task_step`, §5 `test_commit_wmf_task_step_*`, §6 AC 4 | |
| 4.1 — `--task` and `--step` required | §2.1 `p_task_step` definition; argparse enforces | |
| 4.2 — `--short` required, `--long` optional | §2.1 `p_task_step` definition | |
| 4.3 — subject `<task_id>/step-<n>: <short>` | §2.3 `f"{tn.task_id}/step-{args.step}: {args.short}"` | |
| 5 — all call sites migrated | §4 (confirmed no hard-coded skill calls), §5 (updated existing tests), §6 AC 5 | `committing.md` deferred to step 1 |

---

## 8. Out of scope (per ticket)

- Changes to `hb-init` skill (`skills/hb-init.md`) — deferred to step 1
- Changes to `committing.md` example invocation — deferred to step 1
- Changes to any other `hb-sdk` subcommand
