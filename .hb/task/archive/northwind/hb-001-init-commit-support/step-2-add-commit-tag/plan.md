# Step 2 Plan — Add `--tag` flag to `commit write-message-file`

`git log` on a task branch shows subjects like `hb-001/step-2: add routes` with no indication of which lifecycle phase produced the commit. Fix: add optional `--tag <tag>` to `task` and `task-step` modes in `commit write-message-file`. When set, the tag is injected as `(tag)` immediately after the colon-space separator in the subject. Skills are then updated to pass their designated tag at every `commit write-message-file` call site. The change is purely additive — no existing caller is affected, no existing subject format changes.

Source ticket: `./ticket.md`. Builds on step-1 (`hb-init` SDK/committing.md wiring) which shipped `skills/scripts/hb-sdk` and `skills/references/committing.md` in their current form. This plan targets the code as it stands now.

---

## 0. Current-state facts (verified during planning)

### 0.1 SDK `commit write-message-file` — confirmed live

File: `skills/scripts/hb-sdk`

| Symbol | Line | Current behavior |
|---|---|---|
| `cmd_commit_wmf_task` | 786–788 | `f"{tn.task_id}: {args.short}"` — no tag |
| `cmd_commit_wmf_task_step` | 791–793 | `f"{tn.task_id}/step-{args.step}: {args.short}"` — no tag |
| `cmd_commit_wmf_plain` | 782–783 | `f"hb: {args.short}"` — no tag (stays that way) |
| `p_task` argparse | 812–815 | `--task`, `--short`, `--long` only |
| `p_task_step` argparse | 817–823 | `--task`, `--step`, `--short`, `--long` only |

Neither `task` nor `task-step` CLI parsers expose `--tag`. Passing `--tag` to any mode today would fail with argparse's "unrecognized arguments" error.

### 0.2 `committing.md` — confirmed live

File: `skills/references/committing.md`, lines 71–101.

Mode table has no `--tag` column. No example shows `--tag` usage.

### 0.3 Skill commit steps — confirmed live

All 8 in-scope skill files delegate entirely to `committing.md` and pass no tag:

| Skill | Commit step wording | Commits |
|---|---|---|
| `hb-task-archive.md:47` | "create a non-step commit by following committing.md" | 1 |
| `hb-task-unarchive.md:47` | "create a non-step commit by following committing.md" | 1 |
| `hb-task-create.md:50` | "create a non-step commit by following committing.md" | 1 |
| `hb-task-step-add.md:52` | "create a step commit by following committing.md" | 1 |
| `hb-task-step-plan.md:54` | "create a step commit by following committing.md" | 1 |
| `hb-task-step-execute.md:64` | "create a step commit by following committing.md" | 1 |
| `hb-task-step-review-init.md:54` | "create a step commit by following committing.md" | 1 |
| `hb-task-step-review-address.md` | references committing.md at lines 85, 158, 201 | 3 |

### 0.4 Tests — confirmed live

File: `tests/skills/scripts/test_hb-sdk.py`

`commit_write_message_file` helper (line 75–85): accepts `task`, `step`, `short`, `long` kwargs — no `tag` kwarg. Existing `commit write-message-file` tests cover basic task/task-step/plain subjects, `--long`, and forbidden-flag rejection. No `--tag` coverage exists.

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `task` without `--tag` | `hb-001: short` | unchanged |
| `task` with `--tag step-add` | error (unknown arg) | `hb-001: (step-add) short` |
| `task-step` without `--tag` | `hb-001/step-2: short` | unchanged |
| `task-step` with `--tag step-plan` | error (unknown arg) | `hb-001/step-2: (step-plan) short` |
| `plain` with `--tag` | error (unknown arg) | same: error (unknown arg) |
| invalid tag value | N/A | non-zero exit, error on stderr |

Change type: **additive-only** for the no-tag path (zero behavior change); new behavior is gated behind the `--tag` flag.

### 0.2 Non-regression proof

The `--tag` argument is optional with `default=None`. Both `cmd_commit_wmf_task` and `cmd_commit_wmf_task_step` branch only when `args.tag` is truthy. All existing callers (skills, tests) that omit `--tag` hit the same `else` branch as today — same subject format, same return value. Change is fully additive.

---

## 1. Design overview

Three layers of change:

1. **SDK** — new `TAG_RE` constant; `--tag` optional arg on `task`/`task-step` parsers; `_validate_tag` helper; conditional injection in both command functions.
2. **`committing.md`** — mode table gains an optional `--tag` column; two new examples.
3. **Skill files** — each in-scope commit step gains a `--tag <value>` instruction.

Subject injection rule:

```
task:       <task_id>: (<tag>) <short>
task-step:  <task_id>/step-<n>: (<tag>) <short>
```

Tag injected immediately after `": "`, wrapped in parentheses. When `--tag` is absent, subject is identical to today.

**Alternatives considered and rejected:**

- Encoding tags in `committing.md`'s mode table and having skills infer the tag — wrong layer; skills need explicit per-skill tags and `committing.md` can't know which skill is calling it.
- Adding `--tag` to `plain` mode — explicitly forbidden by AC 4; `plain` is task-free and tags are per-lifecycle-skill.

---

## 2. SDK — specification

### 2.1 New constant

```python
TAG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
```

Placed after `STEP_EXTRA_RE` at module level (line 26). Matches valid slugs per AC 3:

| Value | Result |
|---|---|
| `foo`, `foo-bar`, `step-add`, `task-archive` | valid |
| `Foo` | invalid (capital) |
| `foo_bar` | invalid (underscore) |
| `-foo`, `foo-`, `foo--bar`, `foo bar` | invalid |

### 2.2 `_validate_tag(tag: str) -> None` — **new**

```python
def _validate_tag(tag: str) -> None:
    if not TAG_RE.match(tag):
        _die(
            f"error: invalid --tag value '{tag}'\n"
            "  must match [a-z][a-z0-9]*(-[a-z0-9]+)*\n"
            "  (lowercase letters and digits, hyphens allowed between segments)"
        )
```

Contract: calls `_die` (prints to stderr, exits non-zero) for any non-conforming value. Called before subject assembly so the error message is clear.

### 2.3 Updated `cmd_commit_wmf_task` — **refactor (signature preserved)**

```python
def cmd_commit_wmf_task(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.task)
    if args.tag:
        _validate_tag(args.tag)
        _commit_write_message_file(f"{tn.task_id}: ({args.tag}) {args.short}", args.long)
    else:
        _commit_write_message_file(f"{tn.task_id}: {args.short}", args.long)
```

The `else` branch is byte-for-byte identical to today's body — zero behavior change when `--tag` is absent.

### 2.4 Updated `cmd_commit_wmf_task_step` — **refactor (signature preserved)**

```python
def cmd_commit_wmf_task_step(args: argparse.Namespace) -> None:
    tn = _parse_task_name(args.task)
    if args.tag:
        _validate_tag(args.tag)
        _commit_write_message_file(f"{tn.task_id}/step-{args.step}: ({args.tag}) {args.short}", args.long)
    else:
        _commit_write_message_file(f"{tn.task_id}/step-{args.step}: {args.short}", args.long)
```

### 2.5 Argparse updates — **edit**

Add to `p_task` parser (after `--long`):

```python
p_task.add_argument("--tag", metavar="<tag>", help="Optional lifecycle tag; injected as (tag) in subject")
```

Add to `p_task_step` parser (after `--long`):

```python
p_task_step.add_argument("--tag", metavar="<tag>", help="Optional lifecycle tag; injected as (tag) in subject")
```

`plain` parser: no change — argparse rejects `--tag` automatically as an unrecognized argument, satisfying AC 4.

### 2.6 `--long` interaction

`_commit_write_message_file(subject, long)` appends `long` to the message body unchanged. `--tag` only affects `subject`. AC 5 is satisfied structurally — no extra logic needed.

---

## 3. Integration / wiring

All changes are self-contained within existing call patterns:

- `cmd_commit_wmf_task` and `cmd_commit_wmf_task_step` are the sole consumers of `_commit_write_message_file` for their respective modes. No other callers in the SDK.
- The `args.tag` attribute is `None` by default (argparse `add_argument` without `required=True`). The `if args.tag:` guard means all paths that don't pass `--tag` are unaffected.
- No configuration, build wiring, entry points, or dependency manifests change. The SDK is a single self-contained script with no imports beyond stdlib.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — add `TAG_RE` constant; add `_validate_tag`; add `--tag` to `p_task` and `p_task_step` parsers; update `cmd_commit_wmf_task` and `cmd_commit_wmf_task_step` with tag branch |
| `skills/references/committing.md` | **edit** — add optional `--tag` column to mode table for `task` and `task-step` rows; add two `--tag` examples |
| `skills/hb-task-archive.md` | **edit** — commit step: add `--tag task-archive` instruction |
| `skills/hb-task-unarchive.md` | **edit** — commit step: add `--tag task-unarchive` instruction |
| `skills/hb-task-create.md` | **edit** — commit step: add `--tag task-create` instruction |
| `skills/hb-task-step-add.md` | **edit** — commit step: add `--tag step-add` instruction |
| `skills/hb-task-step-plan.md` | **edit** — commit step: add `--tag step-plan` instruction |
| `skills/hb-task-step-execute.md` | **edit** — commit step: add `--tag step-execute` instruction |
| `skills/hb-task-step-review-init.md` | **edit** — commit step: add `--tag step-review` instruction |
| `skills/hb-task-step-review-address.md` | **edit** — all 3 commit call sites: add `--tag step-review` instruction |
| `tests/skills/scripts/test_hb-sdk.py` | **edit** — add `tag` kwarg to `commit_write_message_file` helper; add 7 new test functions |

Lockfile: unchanged — no new dependency. `hb-init.md`, `hb-status.md`, `hb-task-plan.md` untouched per AC 8.

---

## 5. Tests

Mirror the style of existing `test_commit_write_message_file_*` tests (file: `tests/skills/scripts/test_hb-sdk.py`, section starting at line 728). Fixture strategy: `tmp_path` (pytest built-in), same as existing suite.

### 5.1 Helper update

Add `tag` kwarg to `commit_write_message_file`:

```python
if tag := kwargs.get("tag"):
    args += ["--tag", tag]
```

### 5.2 New test cases

**Happy path — task with tag:**
```
test_commit_wmf_task_with_tag
  input:  mode=task, task=hasan/abc-1, tag=step-add, short=add routes
  assert: subject line == "abc-1: (step-add) add routes\n"
```

**No-tag unchanged — task:**
```
test_commit_wmf_task_without_tag_unchanged
  input:  mode=task, task=hasan/abc-1, short=add routes  (no tag)
  assert: subject line == "abc-1: add routes\n"   (same as today)
```

**Happy path — task-step with tag:**
```
test_commit_wmf_task_step_with_tag
  input:  mode=task-step, task=hasan/abc-1, step=2, tag=step-plan, short=write plan
  assert: subject line == "abc-1/step-2: (step-plan) write plan\n"
```

**No-tag unchanged — task-step:**
```
test_commit_wmf_task_step_without_tag_unchanged
  input:  mode=task-step, task=hasan/abc-1, step=2, short=write plan  (no tag)
  assert: subject line == "abc-1/step-2: write plan\n"   (same as today)
```

**plain rejects --tag:**
```
test_commit_wmf_plain_rejects_tag
  input:  mode=plain, short=init, tag=foo  (via raw run() call — helper doesn't forward tag to plain)
  assert: returncode != 0
```

**Invalid tag — uppercase:**
```
test_commit_wmf_invalid_tag_uppercase
  input:  mode=task, task=hasan/abc-1, tag=Foo, short=x
  assert: returncode != 0 and "invalid" in stderr
```

**Invalid tag — underscore:**
```
test_commit_wmf_invalid_tag_underscore
  input:  mode=task, task=hasan/abc-1, tag=foo_bar, short=x
  assert: returncode != 0 and "invalid" in stderr
```

**Non-regression:** All existing tests in the `commit write-message-file` section (lines 731–803) pass unmodified. They don't pass `--tag`, so they hit the unchanged `else` branch.

---

## 6. Verification (after implementation)

1. **Full test run:**
   ```bash
   python -m pytest tests/skills/scripts/test_hb-sdk.py -v
   ```
   All existing tests green; all 7 new tests green.

2. **task with tag — end-to-end:**
   ```bash
   python skills/scripts/hb-sdk commit write-message-file task \
     --task northwind/hb-001-init-commit-support \
     --tag step-plan \
     --short "add plan"
   # read the output path and assert:
   cat <output_path>
   # expected: "hb-001: (step-plan) add plan\n"
   ```

3. **task-step with tag — end-to-end:**
   ```bash
   python skills/scripts/hb-sdk commit write-message-file task-step \
     --task northwind/hb-001-init-commit-support \
     --step 2 \
     --tag step-execute \
     --short "execute step"
   cat <output_path>
   # expected: "hb-001/step-2: (step-execute) execute step\n"
   ```

4. **plain rejects tag:**
   ```bash
   python skills/scripts/hb-sdk commit write-message-file plain \
     --tag foo --short "x"
   # expected: non-zero exit
   ```

5. **Invalid tag exits non-zero with error:**
   ```bash
   python skills/scripts/hb-sdk commit write-message-file task \
     --task northwind/hb-001 --tag Foo --short "x"
   # expected: non-zero exit; stderr contains "invalid"
   ```

6. **Scope check:**
   ```bash
   git diff --name-only
   ```
   Only the 11 files listed in §4 appear. `hb-init.md`, `hb-status.md`, `hb-task-plan.md` do not appear.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| A.1a — task with `--tag` → `(t) short` | §2.3, §5 `test_commit_wmf_task_with_tag` | |
| A.1b — task without `--tag` → unchanged | §2.3 else-branch, §5 `test_commit_wmf_task_without_tag_unchanged` | |
| A.2a — task-step with `--tag` → `(t) short` | §2.4, §5 `test_commit_wmf_task_step_with_tag` | |
| A.2b — task-step without `--tag` → unchanged | §2.4 else-branch, §5 `test_commit_wmf_task_step_without_tag_unchanged` | |
| A.3 — slug validation, non-zero exit on invalid | §2.1 `TAG_RE`, §2.2 `_validate_tag`, §5 two invalid-tag tests | |
| A.4 — plain rejects `--tag` | §2.5 argparse (plain has no `--tag` param), §5 `test_commit_wmf_plain_rejects_tag` | argparse handles automatically |
| A.5 — `--tag` valid alongside `--long` | §2.6, implicit in happy-path tests (long unaffected) | |
| B.6 — mode table updated | §4 `skills/references/committing.md` | |
| B.7 — examples for task and task-step | §4 `skills/references/committing.md` | |
| C (skills pass correct tags) | §4 all 8 skill file edits | |
| D.9a — task + valid tag | §5 `test_commit_wmf_task_with_tag` | |
| D.9b — task without tag | §5 `test_commit_wmf_task_without_tag_unchanged` | |
| D.9c — task-step + valid tag | §5 `test_commit_wmf_task_step_with_tag` | |
| D.9d — task-step without tag | §5 `test_commit_wmf_task_step_without_tag_unchanged` | |
| D.9e — plain rejects tag | §5 `test_commit_wmf_plain_rejects_tag` | |
| D.9f — invalid tag exits non-zero | §5 two invalid-tag tests | |
| D.10 — existing tests unchanged | §6 step 1 | |

---

## 8. Out of scope (per ticket)

- Restricting which specific tag values are allowed for a given skill (any valid slug accepted).
- Adding `--tag` to `plain` mode.
- Changing `--long` body format.
- Updating execution or review artifacts to surface the tag.
- Modifying `hb-init.md`, `hb-status.md`, `hb-task-plan.md`.
