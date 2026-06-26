# Step 0 Plan — SDK Data Layer: Step Status and Archive Recent

`hb-sdk summarize` currently emits coarse step lifecycle booleans and a single-entry archive scalar. The status report built from this data can only show "steps pending execution" and "steps with ticket" — it cannot distinguish planned-but-unexecuted from reviewed-and-closed, nor show a history of recent archives. This step replaces the two blunt active-task count fields and the flat `last_archived` scalar with richer lifecycle counts, name lists, and a `recent` archive array, making the data layer ready for the template/skill update in step 1. Change is data-layer only: no skill instructions or status template are modified.

Source ticket: `./ticket.md`. Prior steps (hb-004) shipped the interactive-ticket subflow; the code targeted here (`skills/scripts/hb-sdk`, line 619–762) has not been touched since. This plan targets the code as it exists now.

> **Design decision — where to parse review.md.** The ticket requires knowing whether a review file has open items, but `_StepInfo` is a dataclass constructed in `_summarize_task`. Two choices: (a) parse review.md inside `_summarize_task` and store `has_review: bool` + `review_open: bool` in `_StepInfo`, or (b) store the raw text and parse lazily in a property. Option (a) is chosen: parsing is cheap (one read per step), happens exactly once, and keeps `_StepInfo` free of file paths. The `status` property then derives from five booleans with no further I/O. See §2.

---

## 0. Current-state facts (verified during planning)

Inspected `skills/scripts/hb-sdk` (865 lines) and `tests/skills/scripts/test_hb-sdk.py` (1062 lines). Confirmed live, not assumed.

**`_StepInfo` (line 619–624):** four fields — `name`, `has_ticket`, `has_plan`, `has_execution`. No review detection, no status classification.

**`_TaskInfo` (line 628–649):** properties `steps_pending_execution` (count of steps where `not has_execution`), `steps_with_ticket` (count where `has_ticket`), `next_pending_step` (first name where `not has_execution`). No per-lifecycle breakdown, no name lists.

**`_summarize_task` (line 652–675):** iterates `_list_step_folders`, checks three files per step (`ticket.md`, `plan.md`, `execution-*.md`), constructs `_StepInfo`. Does not check `review.md`.

**`cmd_summarize` (line 678–762):**
- Emits `steps_pending_execution` and `steps_with_ticket` per active task.
- Archive section: tracks only the single highest-mtime folder, emits `"last_archived": "author/task_id"` (flavor stripped) or `null`.
- Uninitialized JSON: `"archive": {"count": 0, "last_archived": null}`.

**Blast radius:** `hb-status.md` skill (the sole consumer of `summarize` output) reads `steps_pending_execution`, `steps_with_ticket`, and `last_archived`. Updating the skill is out of scope for this step (step 1). Removing the old fields will cause step 1's template changes to break until step 1 lands; that is accepted and expected.

**Tests referencing fields being removed:** three tests check `steps_pending_execution` (lines 895, 966, 979); two check `last_archived` (lines 1042, 1051); none check `steps_with_ticket` as a key (the field is emitted but not asserted). All affected tests must be updated.

### 0.1 Impact (before → after)

| Area | Before | After |
|---|---|---|
| `_StepInfo` fields | `name`, `has_ticket`, `has_plan`, `has_execution` | + `has_review`, `review_open`; `status` property |
| `_TaskInfo` properties emitted | `steps_pending_execution`, `steps_with_ticket`, `next_pending_step` | remove first two; + 6 status count props + 2 name-list props; keep `next_pending_step` |
| Step JSON keys | `name`, `has_ticket`, `has_plan`, `has_execution` | + `has_review`, `status` |
| Active-task JSON keys | `steps_pending_execution`, `steps_with_ticket`, ... | remove both; + `steps_skeleton`, `steps_ticketed`, `steps_planned`, `steps_executed`, `steps_review_open`, `steps_reviewed`, `steps_needs_review`, `steps_needs_work` |
| Archive JSON | `{"count": N, "last_archived": "a/id" \| null}` | `{"count": N, "recent": [{author, task_id, task_folder}, ...]}` |
| Uninitialized JSON | `"archive": {"count":0,"last_archived":null}` | `"archive": {"count":0,"recent":[]}` |

### 0.2 Non-regression proof / risk

| Case | Current behavior | Guard |
|---|---|---|
| `has_ticket`, `has_plan`, `has_execution` per step | Emitted, tested | Fields retained unchanged on `_StepInfo`; only new fields added |
| `next_pending_step` logic | "first step with no execution" | Property body unchanged; only the two removed properties are deleted |
| Archive `count` | Integer, tested | `archived_count` accumulation loop unchanged |
| `initialized` flag | Bool, tested | Untouched |
| `total_steps`, `has_ticket` per task | Tested | Untouched |
| `task_path`, `task_folder`, `author`, `task_id` | Tested | Untouched |

Change to existing step detection is additive (one `review.md` existence check appended). The only destructive changes are: removal of `steps_pending_execution` / `steps_with_ticket` from the serialised dict, and replacement of `last_archived` with `recent`. Tests for those three keys are updated in §5.

---

## 1. Design overview

Three independent sub-changes, each with a clear boundary:

**A — `_StepInfo`: review detection + status classification**
Add `has_review: bool` and `review_open: bool` (populated at construction). Add `status` computed property that derives from the five booleans in priority order.

**B — `_TaskInfo`: per-status counts and name lists**
Replace `steps_pending_execution` and `steps_with_ticket` properties with six status-count properties and two name-list properties. Keep `next_pending_step` unchanged.

**C — Archive: replace `last_archived` scalar with `recent` array**
Track up to 5 highest-mtime folders; emit `recent: [{author, task_id, task_folder}]`. The `task_folder` includes flavor (e.g. `hb-004-interactive-ticket-creation`). Update uninitialized fallback to use `"recent": []`.

Each sub-change touches a single function or class block; they compose cleanly because C is independent of A and B.

**Status precedence** (AC 2, evaluated in order, first match wins):

| Tier | Condition | Status |
|---|---|---|
| 1 | `has_review` and `not review_open` | `reviewed` |
| 2 | `has_review` and `review_open` | `review-open` |
| 3 | `has_execution` and `not has_review` | `executed` |
| 4 | `has_plan` and `not has_execution` and `not has_review` | `planned` |
| 5 | `has_ticket` and `not has_plan` and `not has_execution` and `not has_review` | `ticketed` |
| 6 | _(none of the above)_ | `skeleton` |

```
precedence:  reviewed  ≥  review-open  ≥  executed  ≥  planned  ≥  ticketed  ≥  skeleton
(tie-break: impossible — mutually exclusive by construction)
```

**Alternatives considered and rejected:**
- Store parsed `status: str` directly on `_StepInfo` instead of computing it as a property — rejected: a property is cheaper to read and keeps the field derivation visible.
- Accumulate `review_open` inside `_TaskInfo` rather than `_StepInfo` — rejected: review detection belongs in step-level data; `_TaskInfo` should derive from `_StepInfo.status`, not re-read files.
- Keep `steps_pending_execution` as an alias — rejected: AC 7 explicitly removes it.

---

## 2. `_StepInfo` and `_TaskInfo` — specification

### 2.1 `_StepInfo` (refactor, two new fields, one new property)

```python
@dataclass(eq=True)
class _StepInfo:
    name: str
    has_ticket: bool
    has_plan: bool
    has_execution: bool
    has_review: bool      # new: True when review.md exists in step folder
    review_open: bool     # new: True when review.md has ≥1 open status-table item

    @property
    def status(self) -> str:   # new computed property
        if self.has_review:
            return "review-open" if self.review_open else "reviewed"
        if self.has_execution:
            return "executed"
        if self.has_plan:
            return "planned"
        if self.has_ticket:
            return "ticketed"
        return "skeleton"
```

**All existing fields** (`name`, `has_ticket`, `has_plan`, `has_execution`): **unchanged** — label, constructor position, semantics.

### 2.2 Review-file parsing — `_parse_review_open`

**New function**, placed adjacent to `_summarize_task`.

**Algorithm:** iterate lines of `review.md`; skip any line without `|`; split by `|` and strip each segment; skip if fewer than 4 segments (needs at least `''`, col1, col2, trailing); skip if col[2] is empty or matches `_SEPARATOR_RE` (`^[-:]+$`); if `col[2].lower()` is NOT in `REVIEW_CLOSED_STATUSES`, return `True` immediately. If no open row found, return `False`.

```python
REVIEW_CLOSED_STATUSES = frozenset({"addressed", "assessed", "deferred"})
_SEPARATOR_RE = re.compile(r"^[-:]+$")

def _parse_review_open(review_path: Path) -> bool:
    text = review_path.read_text()
    for line in text.splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 4:
            continue
        status_val = cols[2].lower()
        if not status_val or _SEPARATOR_RE.match(status_val):
            continue
        if status_val not in REVIEW_CLOSED_STATUSES:
            return True
    return False
```

**Failure contract:** if `review.md` is unreadable (permissions, encoding), the exception propagates — same as any other file access in the SDK. No silent swallowing.

**Edge cases:**
- Review file exists but contains no table rows → `review_open = False` → status = `reviewed` (AC 2 spec: "review file exists but contains no status-table rows" → `reviewed`).
- Status value not in any known set (e.g. `"pending"`) → treated as open because it is not in `REVIEW_CLOSED_STATUSES`.
- Case: `"ADDRESSED"` → `.lower()` → `"addressed"` → closed. (AC 3 case-insensitive spec.)

### 2.3 `_summarize_task` — additional detection per step

**Edit** (refactor, signature unchanged). Inside the per-step loop, add after the `has_execution` check:

```python
review_path = step_path / "review.md"
has_review = review_path.is_file()
review_open = _parse_review_open(review_path) if has_review else False
```

Pass `has_review=has_review, review_open=review_open` to `_StepInfo(...)`.

### 2.4 `_TaskInfo` — new properties, removed properties

**Remove** `steps_pending_execution` and `steps_with_ticket` properties.

**Add** six count properties and two name-list properties:

```python
@property
def steps_skeleton(self) -> int:
    return sum(1 for s in self.steps if s.status == "skeleton")

@property
def steps_ticketed(self) -> int:
    return sum(1 for s in self.steps if s.status == "ticketed")

@property
def steps_planned(self) -> int:
    return sum(1 for s in self.steps if s.status == "planned")

@property
def steps_executed(self) -> int:
    return sum(1 for s in self.steps if s.status == "executed")

@property
def steps_review_open(self) -> int:
    return sum(1 for s in self.steps if s.status == "review-open")

@property
def steps_reviewed(self) -> int:
    return sum(1 for s in self.steps if s.status == "reviewed")

@property
def steps_needs_review(self) -> list[str]:
    return [s.name for s in self.steps if s.status in ("executed", "review-open")]

@property
def steps_needs_work(self) -> list[str]:
    return [s.name for s in self.steps if s.status in ("skeleton", "ticketed", "planned")]
```

**`next_pending_step`** — body unchanged:

```python
@property
def next_pending_step(self) -> str | None:
    for s in self.steps:
        if not s.has_execution:
            return s.name
    return None
```

### 2.5 `cmd_summarize` — JSON serialization changes

**Step objects** — add `has_review` and `status` keys, keep existing four:

```python
{
    "name": s.name,
    "has_ticket": s.has_ticket,
    "has_plan": s.has_plan,
    "has_execution": s.has_execution,
    "has_review": s.has_review,   # new
    "status": s.status,            # new
}
```

**Active-task objects** — remove `steps_pending_execution` and `steps_with_ticket`; add eight new keys after `total_steps`:

```python
"steps_skeleton": t.steps_skeleton,
"steps_ticketed": t.steps_ticketed,
"steps_planned": t.steps_planned,
"steps_executed": t.steps_executed,
"steps_review_open": t.steps_review_open,
"steps_reviewed": t.steps_reviewed,
"steps_needs_review": t.steps_needs_review,
"steps_needs_work": t.steps_needs_work,
```

**Archive section** — replace the scalar-scan loop with a 5-entry collector:

```python
recent_entries: list[tuple[float, Path]] = []
archive_base = hb / "task" / TASK_FOLDER_ARCHIVE
if archive_base.exists():
    for author_dir in archive_base.iterdir():
        if not author_dir.is_dir():
            continue
        for task_dir in author_dir.iterdir():
            if not task_dir.is_dir():
                continue
            archived_count += 1
            recent_entries.append((task_dir.stat().st_mtime, task_dir))

recent_entries.sort(key=lambda x: x[0], reverse=True)

def _archive_entry(p: Path) -> dict[str, str]:
    tn = _parse_task_name(f"{p.parent.name}/{p.name}")
    return {"author": tn.author, "task_id": tn.task_id, "task_folder": p.name}

recent = [_archive_entry(p) for _, p in recent_entries[:5]]
```

Emit: `"archive": {"count": archived_count, "recent": recent}`.

**Uninitialized fallback:**

```python
"archive": {"count": 0, "recent": []}
```

---

## 3. Integration / wiring

- All changes are within `skills/scripts/hb-sdk` — a single self-contained file.
- No public signatures (CLI arguments, subcommand names) change.
- No new module dependencies — stdlib only.
- `_parse_review_open` is a module-level function, not exported; it is called only from `_summarize_task`.
- The `REVIEW_CLOSED_STATUSES` constant and `_SEPARATOR_RE` are module-level, co-located with `_parse_review_open`.
- No entry-point, build, install, or dependency-manifest changes.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb-sdk` | **edit** — add `REVIEW_CLOSED_STATUSES`, `_SEPARATOR_RE`, `_parse_review_open`; extend `_StepInfo` with `has_review`, `review_open`, `status`; update `_summarize_task` to detect review; replace `_TaskInfo` properties; update `cmd_summarize` serialization |
| `tests/skills/scripts/test_hb-sdk.py` | **edit** — update 5 broken summarize tests; add new summarize tests for status, review parsing, count/list fields, archive recent |

Lockfile: unchanged — no new dependencies.

---

## 5. Tests

Mirrors the existing `test_hb-sdk.py` pattern: `subprocess.run` via the `run()` helper, `tmp_path` fixtures, JSON-parsed stdout assertions. New tests live in the `# ── summarize ──` section alongside existing summarize tests.

### 5.1 Tests to update (breaking changes)

| Existing test | Change needed |
|---|---|
| `test_summarize_not_initialized` | Assert `data["archive"]["recent"] == []`; remove `data["archive"]["last_archived"] is None` |
| `test_summarize_active_task_no_steps` | Remove `steps_pending_execution == 0` assert; assert `steps_skeleton == 0` instead; assert `steps_needs_review == []`, `steps_needs_work == []` |
| `test_summarize_steps_pending_execution` | Remove `steps_pending_execution` assert; check `steps_planned == 2` and `steps_needs_work == ["step-1", "step-2"]` (after step-0 gets execution file) |
| `test_summarize_all_steps_executed` | Remove `steps_pending_execution == 0` assert; assert `steps_executed == 1`, `steps_needs_review == ["step-0"]` |
| `test_summarize_last_archived_by_mtime` | Assert `data["archive"]["recent"][0]["task_id"] == "abc-1"` |
| `test_summarize_last_archived_strips_flavor` | Assert `recent[0]["task_id"] == "abc-1"` and `recent[0]["task_folder"] == "abc-1-add-login"` |

### 5.2 New tests — step status field

```
test_summarize_step_status_skeleton
  setup: step exists but has no ticket.md, plan.md, execution, review.md
  assert: step["status"] == "skeleton", step["has_review"] == False

test_summarize_step_status_ticketed
  setup: step with ticket.md only
  assert: status == "ticketed"

test_summarize_step_status_planned
  setup: step with ticket.md + plan.md
  assert: status == "planned"

test_summarize_step_status_executed
  setup: step with ticket.md + plan.md + execution-*.md
  assert: status == "executed"

test_summarize_step_status_review_open
  setup: step with execution + review.md containing "| R1 | open | desc |"
  assert: status == "review-open", has_review == True

test_summarize_step_status_reviewed_all_closed
  setup: step with execution + review.md with rows all in {addressed, assessed, deferred}
  assert: status == "reviewed"

test_summarize_step_status_reviewed_no_rows
  setup: step with review.md that has no table rows
  assert: status == "reviewed"

test_summarize_step_status_review_case_insensitive
  setup: review.md with "| R1 | ADDRESSED | desc |"
  assert: status == "reviewed"  (ADDRESSED → closed)

test_summarize_step_status_review_mixed
  setup: review.md with one addressed row and one open row
  assert: status == "review-open"

test_summarize_step_has_review_false_without_file
  setup: step with execution but no review.md
  assert: has_review == False, status == "executed"
```

### 5.3 New tests — active-task count and list fields

```
test_summarize_task_count_fields_all_zero
  setup: task with no steps
  assert: all six count fields == 0; steps_needs_review == []; steps_needs_work == []

test_summarize_task_count_fields_mixed
  setup: task with one step at each of 6 statuses (requires multiple steps)
  assert: each count field == 1

test_summarize_steps_needs_review_includes_executed_and_review_open
  setup: task with executed step + review-open step
  assert: steps_needs_review contains both names

test_summarize_steps_needs_work_includes_skeleton_ticketed_planned
  setup: task with one step at each status
  assert: steps_needs_work contains names of skeleton, ticketed, planned steps

test_summarize_steps_needs_review_empty_when_none_qualify
  setup: task with steps in ticketed/planned only
  assert: steps_needs_review == []

test_summarize_steps_needs_work_empty_when_none_qualify
  setup: task with one executed step
  assert: steps_needs_work == []
```

### 5.4 New tests — archive recent

```
test_summarize_archive_recent_empty_when_no_archives
  assert: archive["recent"] == []

test_summarize_archive_recent_single_entry
  setup: archive one task
  assert: len(recent) == 1; recent[0] has keys author, task_id, task_folder

test_summarize_archive_recent_sorted_by_mtime_desc
  setup: archive two tasks; force-utime abc-2 to older mtime
  assert: recent[0]["task_id"] == "abc-1" (newer mtime first)

test_summarize_archive_recent_max_five
  setup: archive 7 tasks
  assert: len(recent) == 5

test_summarize_archive_recent_task_folder_includes_flavor
  setup: archive task with flavor "add-login"
  assert: recent[0]["task_folder"] == "abc-1-add-login"; recent[0]["task_id"] == "abc-1"

test_summarize_archive_recent_author_field
  setup: archive task for author "hasan"
  assert: recent[0]["author"] == "hasan"
```

### 5.5 Non-regression

Existing tests outside `# ── summarize ──` block pass unchanged — they cover `init`, `task create`, `task archive/unarchive`, `task path`, `step add/list/path/number`, `execution-slug`, and `commit write-message-file`. None of those touch `_StepInfo`, `_TaskInfo`, or `cmd_summarize`.

---

## 6. Verification (after implementation)

1. **Full test run:**
   ```bash
   make test
   ```
   All tests must pass (0 failures, 0 errors).

2. **Live smoke — step status on current workspace:**
   ```bash
   cd /home/hkamal/repos/hashbuild
   skills/scripts/hb-sdk summarize | python3 -c "
   import json,sys
   d=json.load(sys.stdin)
   for t in d['active_tasks']:
       print(t['task_folder'], t['steps_needs_work'], t['steps_needs_review'])
   "
   ```
   Should print per-task work/review lists without error.

3. **Per-AC checks:**
   - AC 1 (`has_review` field): test `test_summarize_step_has_review_false_without_file` and `test_summarize_step_status_review_open`.
   - AC 2 (status six values + priority): tests `test_summarize_step_status_*` (7 tests).
   - AC 3 (case-insensitive parsing): `test_summarize_step_status_review_case_insensitive`.
   - AC 4 (six count fields): `test_summarize_task_count_fields_mixed`.
   - AC 5 (name lists): `test_summarize_steps_needs_review_*` and `test_summarize_steps_needs_work_*`.
   - AC 6 (`next_pending_step` unchanged): `test_summarize_steps_pending_execution` (updated).
   - AC 7 (old fields removed): confirm `steps_pending_execution` and `steps_with_ticket` do NOT appear in output:
     ```bash
     skills/scripts/hb-sdk summarize | python3 -c "
     import json,sys
     d=json.load(sys.stdin)
     for t in d['active_tasks']:
         assert 'steps_pending_execution' not in t, 'old field present!'
         assert 'steps_with_ticket' not in t, 'old field present!'
     print('old fields absent — OK')
     "
     ```
   - AC 8 + 9 (archive `recent`): tests `test_summarize_archive_recent_*`.
   - AC 10 (uninitialized uses `recent: []`): `test_summarize_not_initialized` (updated).

4. **Scope check:** only the two files named in §4 should appear in `git diff --name-only`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 `_StepInfo.has_review`, §2.3, §2.5 step JSON | `has_review` field added to dataclass and serialized |
| 2 | §2.1 `_StepInfo.status` property, §1 precedence table | Six values, priority order per ticket |
| 3 | §2.2 `_parse_review_open`, `_SEPARATOR_RE` | `.lower()` + column filter; case-insensitive |
| 4 | §2.4 six count properties on `_TaskInfo`, §2.5 serialization | Derived from `s.status` |
| 5 | §2.4 `steps_needs_review`, `steps_needs_work` properties | Name lists in step-folder-name form |
| 6 | §2.4 `next_pending_step` body unchanged | "no change to existing logic" — confirmed |
| 7 | §2.4 remove `steps_pending_execution` + `steps_with_ticket`, §2.5 | Not emitted in new dict |
| 8 | §2.5 archive section, `recent` key | Shape change documented in §0.1 |
| 9 | §2.5 `_archive_entry` helper, `recent_entries[:5]` | Up to 5, mtime desc, `task_folder` includes flavor |
| 10 | §2.5 uninitialized fallback | `"recent": []` |

---

## 8. Out of scope (per ticket)

- Updating `hb-status.md` skill instructions or the status-template (step 1).
- Adding review detection to any other SDK command (e.g. `task step path`, `commit`).
- Changing how `review.md` files are structured or authored.
- Changing `next_pending_step` behavior or semantics.
