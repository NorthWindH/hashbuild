# Step 4 Plan — Move Status Rendering into hb-sdk

The `hb-status` skill currently calls `hb-sdk summarize` (JSON only), reads `status-template.md`, and renders the report itself. A consumer of the SDK that wants the rendered status view must re-implement that rendering. This step moves the rendering into `hb-sdk summarize --format md` so the skill becomes a thin passthrough and the template file can be retired. The change is additive: omitting `--format` leaves JSON output unchanged, so no existing callers break. The single externally observable effect is that `hb-sdk summarize --format md` emits a ready-to-display markdown status report equivalent to the report `hb-status` produces today.

Source ticket: `./ticket.md`. This step builds on the shipped work from steps 0–2 (JSON schema stable, status-template and hb-status column display finalized in steps 1–2; step 3 was dropped). The plan targets the code as it exists now.

> **Design decision — render in `summarize.py` vs. a new subcommand.** The ticket frames this as a flag on `summarize` rather than a separate `render` or `status` subcommand. The code confirms this is the correct layer: `cmd_summarize` already builds the complete data dict; adding a `--format` branch requires zero new data-gathering logic and keeps the public API surface minimal. A separate subcommand would duplicate the data-gathering path for no gain. Chosen: `--format {json,md}` flag on `summarize`. See §1 and §7.

---

## 0. Current-state facts (verified during planning)

- **`summarize.py:234-237`** — `def_cli_summarize` registers the `summarize` subparser with no flags and sets `func=cmd_summarize`. Confirmed: no `--format` flag exists.
- **`summarize.py:140-231`** — `cmd_summarize` has two branches: (a) uninitialized early-return (`lines 140-154`) printing a fixed JSON object, (b) initialized path (`lines 156-231`) building active-task and archive data then calling `print(json.dumps(..., indent=2))`. Both branches print JSON and nothing else.
- **Sole caller** — `hb-status.md:36` is the only file that calls `hb-sdk summarize`:
  ```
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize
  ```
  Confirmed by `grep -r "hb-sdk summarize" skills/`.
- **`hb-status.md` steps 2–4** — step 2 captures JSON, step 3 reads `status-template.md`, step 4 renders and outputs the report. The rendering rules are specified in step 4 prose and the `## Next Action` decision tree is in the template file's comment block.
- **`status-template.md` references** — two files reference it: `skills/hb-status.md` (steps 3-4) and `skills/references/references-toc.md` (row 12). After updating `hb-status.md`, neither skill needs the template, enabling deletion.
- **`helpers.py:68-69`** — `summarize()` test helper calls `run(["summarize"], cwd)`. No `--format` kwarg exists; must be added to let tests cover both modes.
- **No existing `plan.md`** — confirmed, `step-4-sdk-render/` contains only `ticket.md`.

### 0.1 Impact (before → after)

| Caller / artifact | Before | After |
|---|---|---|
| `hb-sdk summarize` (no flag) | JSON output | JSON output — **identical** |
| `hb-sdk summarize --format json` | flag invalid → non-zero exit | JSON output — same as default |
| `hb-sdk summarize --format md` | flag invalid → non-zero exit | Rendered markdown status report |
| `hb-status.md` | 4-step skill (gather JSON → read template → render) | 1-step passthrough: run `--format md`, emit stdout |
| `skills/references/status-template.md` | exists, 93 lines | deleted |

This is an additive change for the flag and a behavior-preserving refactor for `hb-status`.

### 0.2 Non-regression proof

| At-risk case | Current behavior | Guard |
|---|---|---|
| `hb-sdk summarize` (no flag) | prints JSON | `default="json"` in argparse; JSON path unchanged |
| Existing summarize tests (31 tests) | all pass against JSON output | JSON branch is the existing `print(json.dumps(...))` — untouched |
| `hb-status` skill output | renders markdown report | After update, skill invokes `--format md` which must produce identical content; verified in §6 |

---

## 1. Design overview

**Control flow for `cmd_summarize` after this step:**

```
cmd_summarize(args)
  │
  ├── build data dict (identical for both formats)
  │     ├── uninitialized? → {"initialized": false, "active_tasks": [], "archive": ...}
  │     └── initialized?   → full data dict (existing logic)
  │
  └── branch on args.format
        ├── "json" → print(json.dumps(data, indent=2))   ← existing path, unchanged
        └── "md"   → print(_render_md(data))             ← new path
```

The existing early-return at `summarize.py:154` (uninitialized JSON case) must be restructured into the unified `data` construction so that `--format md` can also handle the uninitialized case correctly.

**`_render_md(data)` output structure (mirrors `status-template.md`):**

```
# Hashbuild Status

## Initialization
<one line>

---

## Active Tasks        ← omitted entirely when active_tasks is empty
**Legend:**
...
| table |
### Task Details       ← omitted when no task has non-empty needs_review or needs_work

---

## Archive             ← omitted entirely when archive.recent is empty
...

---

## Next Action
<one sentence>
```

**Alternatives considered and rejected:**

| Alternative | Reason rejected |
|---|---|
| New `render` or `status` subcommand | Duplicates data-gathering path; bigger surface; contradicts ticket framing |
| Separate `_render.py` module | Unnecessary indirection for ~80 lines of rendering logic; keep in `summarize.py` |
| Keep rendering in `hb-status.md` skill | Contradicts the ticket goal (AC 5) |

---

## 2. `summarize.py` — specification

### 2.1 Flag addition — `def_cli_summarize`

**New** — add to `def_cli_summarize` after `p.set_defaults(func=cmd_summarize)`:

```python
p.add_argument(
    "--format",
    choices=["json", "md"],
    default="json",
    help="Output format: json (default) or md (rendered markdown)",
)
```

**Contract:** argparse handles invalid values (`--format xml`) with a non-zero exit and usage message — no explicit error handling needed.

### 2.2 Refactor `cmd_summarize`

**Refactor (behavior preserved for json branch)** — restructure to build `data` dict first, then branch:

```python
def cmd_summarize(args: argparse.Namespace) -> None:
    hb = path_hb()

    if not hb.exists():
        data = {"initialized": False, "active_tasks": [], "archive": {"count": 0, "recent": []}}
    else:
        # ... existing data-gathering logic unchanged ...
        data = {
            "initialized": True,
            "active_tasks": [...],
            "archive": {...},
        }

    if args.format == "md":
        print(_render_md(data))
    else:
        print(json.dumps(data, indent=2))
```

The existing data-gathering logic (lines 156-231) moves into the `else:` branch unchanged — no behavioral change to JSON output.

### 2.3 `_render_md(data: dict) -> str` — new function

**New** — private function. Renders the full markdown status report from the data dict.

**Algorithm:**

```
lines = []
append "# Hashbuild Status", ""
append "## Initialization", ""
if initialized:
    append "`.hb/` initialized"
else:
    append "`.hb/` not found — run `/hb-init` to set up"

if active_tasks non-empty:
    append "", "---", "", "## Active Tasks", ""
    append "**Legend:**", ""
    append "Step count in each status:", ""
    append "> S = Skeleton · T = Ticketed · P = Planned · E = Executed · RO = Review Open · R = Reviewed"
    append ""
    append table header and separator
    for each task:
        append table row  (see count-cell rule below)
    has_details = any task has non-empty steps_needs_review or steps_needs_work
    if has_details:
        append "", "### Task Details"
        for each task with non-empty needs_review or needs_work:
            append "", "- `author/task_folder`:"
            if needs_review: append "  - **Needs review:** `step-a`, `step-b`"
            if needs_work:   append "  - **Needs work:** `step-a`, `step-b`"

if archive.recent non-empty:
    append "", "---", "", "## Archive", ""
    append f"**Archived Tasks:** `{count}`"
    append "", "**Recently Archived Tasks:**", ""
    for each entry: append "- `author/task_folder`"

append "", "---", "", "## Next Action", ""
append _next_action(data)

return "\n".join(lines) + "\n"
```

**Count-cell rule:** for each of S / T / P / E / RO / R columns — cell is `—` when the value is 0, else `str(value)`. Total column always shows `str(total_steps)`.

**Ticket column:** `✓` when `has_ticket` is true, `✗` otherwise.

**Failure contract:** `_render_md` assumes a structurally valid data dict (matching the JSON schema from `hb-status.md:42-80`). It does not validate; malformed input causes a `KeyError`/`TypeError` that propagates to `cmd_summarize` — acceptable since the dict is always constructed internally.

### 2.4 `_next_action(data: dict) -> str` — new function

**New** — private helper. Implements the decision tree from `status-template.md § Next Action` comment, evaluated in order:

```
1. not initialized            → "Run `/hb-init` to initialize the workspace."
2. any task lacks ticket.md   → "Add `ticket.md` to `<ref>`..."
3. any task has ticket but (no steps OR no steps with ticket.md)
                              → "Add steps to `<ref>` with `/hb-task-plan <ref>` or `/hb-task-step-add <ref>`."
4. any step lacks ticket.md   → "Add `ticket.md` to `<ref>/<step>` or run `/hb-task-step-add <ref>`."
5. any step has ticket but no plan.md
                              → "Run `/hb-task-step-plan <ref>/<step>` to plan the next step."
6. any step has plan.md but no execution-*.md
                              → "Run `/hb-task-step-execute <ref>/<step>` to execute the plan."
7. all steps of any active task have executions
                              → "All steps executed for `<ref>` — archive with `/hb-task-archive <author>/<task_id>` or add more steps with `/hb-task-step-add <ref>`."
8. no active tasks            → "Start a new task with `/hb-task-create <author/task-id>`."
fallback                      → "Review workspace state."
```

`<ref>` is `author/task_folder`. Archive command uses `author/task_id` (without flavor) per convention.

---

## 3. Integration / wiring

**`skills/hb-status.md`** — steps 2, 3, and 4 are replaced by a single step:

```
### 2. Render and output status report

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize --format md
```

- captures stdout and writes it directly to the user
- if the command fails, surface the error verbatim and stop
```

The `allowed-tools` frontmatter already allows `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` — no change needed.

**No other wiring changes.** `__main__.py` already imports and calls `def_cli_summarize(subs)` — the new flag is self-registering via argparse.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/summarize.py` | **edit** — add `--format` flag to `def_cli_summarize`; restructure `cmd_summarize` to build `data` dict before branching on format; add `_render_md` and `_next_action` private functions (~80 lines new); JSON path logic untouched |
| `skills/hb-status.md` | **edit** — replace steps 2–4 (gather JSON, read template, render) with single `hb-sdk summarize --format md` invocation; remove `status-template.md` reference from step 3; update the `## Reference Files` section to remove the template row |
| `skills/references/references-toc.md` | **edit** — remove `status-template.md` row (row 12 of 15) |
| `skills/references/status-template.md` | **delete** — no longer referenced by any skill file after the above edits |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_summarize.py` | **extend** — add `# ── --format flag ──` test group at end of file |
| `tests/skills/scripts/hb_sdk/helpers.py` | **edit** — update `summarize()` to pass `--format <value>` when `format` kwarg provided |

No new dependencies. Lockfile unchanged. `hb_sdk/__main__.py`, `commit.py`, `common.py`, `init_cmd.py`, `task.py` — all untouched.

---

## 5. Tests

Mirror style of `test_hb_sdk_summarize.py` (temp dir, subprocess via helpers). All tests are hermetic (no live `.hb/`).

**`helpers.py` update:**

```python
def summarize(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["summarize"]
    if fmt := kwargs.get("format"):
        args += ["--format", fmt]
    return run(args, cwd, ok=kwargs.get("ok", True))
```

**New test group `# ── --format flag ──` in `test_hb_sdk_summarize.py`:**

| Test | What it asserts |
|---|---|
| `test_summarize_format_default_is_json` | Omit `--format`; `json.loads(result.stdout)` succeeds — non-regression |
| `test_summarize_format_json_explicit` | `--format json`; `json.loads(result.stdout)` succeeds; same keys as default |
| `test_summarize_format_md_returns_non_json` | `--format md`; `json.loads(result.stdout)` raises — output is not JSON |
| `test_summarize_format_invalid_exits_nonzero` | `--format xml`; `ok=False`; `result.returncode != 0` |
| `test_summarize_format_md_not_initialized` | `--format md`, no init; stdout contains "`.hb/` not found" |
| `test_summarize_format_md_initialized` | init, `--format md`; stdout contains "`.hb/` initialized" |
| `test_summarize_format_md_no_active_tasks_section_absent` | init, no tasks, `--format md`; "## Active Tasks" NOT in stdout |
| `test_summarize_format_md_active_task_in_table` | init + task, `--format md`; `author/task_folder` in stdout |
| `test_summarize_format_md_count_dash_when_zero` | init + task with 0 skeleton steps, `--format md`; `| — |` appears in stdout |
| `test_summarize_format_md_count_nonzero` | init + task + step, `--format md`; `| 1 |` appears (ticketed count) |
| `test_summarize_format_md_needs_review_in_details` | init + task + executed step, `--format md`; "Needs review" in stdout |
| `test_summarize_format_md_archive_section_present` | init + archived task, `--format md`; "## Archive" in stdout |
| `test_summarize_format_md_archive_section_absent` | init no archives, `--format md`; "## Archive" NOT in stdout |
| `test_summarize_format_md_next_action_not_initialized` | no init, `--format md`; "## Next Action" and "/hb-init" in stdout |
| `test_summarize_format_md_next_action_no_tasks` | init no tasks, `--format md`; "/hb-task-create" in stdout |
| `test_summarize_format_md_next_action_task_no_ticket` | init + task (no ticket), `--format md`; "ticket.md" in stdout |
| `test_summarize_format_md_next_action_step_needs_plan` | init + task + ticketed step (no plan), `--format md`; "/hb-task-step-plan" in stdout |
| `test_summarize_format_md_next_action_step_needs_execution` | init + task + planned step (no exec), `--format md`; "/hb-task-step-execute" in stdout |

**Non-regression:** all 31 existing summarize tests use `summarize(cwd)` (no `format` kwarg) — they exercise the default JSON path and remain fully intact.

---

## 6. Verification (after implementation)

1. **Full test run:** `cd tests/skills/scripts && python -m pytest hb_sdk/ -v` — all tests green (existing 31 + new ~18).

2. **Smoke — JSON default unchanged:**
   ```bash
   cd /home/hkamal/repos/hashbuild
   skills/scripts/hb-sdk summarize | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK:', d['initialized'])"
   # → OK: True
   ```

3. **Smoke — `--format json` explicit:**
   ```bash
   skills/scripts/hb-sdk summarize --format json | python3 -c "import json,sys; d=json.load(sys.stdin); print('keys:', list(d.keys()))"
   # → keys: ['initialized', 'active_tasks', 'archive']
   ```

4. **Smoke — `--format md` produces markdown:**
   ```bash
   skills/scripts/hb-sdk summarize --format md | head -5
   # → # Hashbuild Status
   #    (empty line)
   # → ## Initialization
   ```

5. **Per-AC checks (run against live workspace):**

   | AC | Check |
   |---|---|
   | 1 | `hb-sdk summarize --help` shows `--format {json,md}` |
   | 2 | `hb-sdk summarize` (no flag) produces valid JSON — same as before |
   | 3 | `hb-sdk summarize --format json` output equals `hb-sdk summarize` output: `diff <(hb-sdk summarize) <(hb-sdk summarize --format json)` → empty |
   | 4 | `hb-sdk summarize --format md` contains all four sections: `## Initialization`, `## Active Tasks`, `## Next Action` visible; `## Archive` present (live workspace has 5 archived tasks) |
   | 5 | `hb-status` skill output (via Claude) visually matches prior output — same table, same legend, same next action |
   | 6 | `ls skills/references/status-template.md` → "No such file"; `grep -r status-template skills/` → no matches |

6. **Scope check:** `git diff --name-only` shows only the 6 intended files. `hb_sdk/__main__.py` unchanged; no new dependency introduced.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 — `--format {json,md}` flag | §2.1 `def_cli_summarize` | argparse `choices=["json","md"]` |
| 2 — omit `--format` → JSON unchanged | §2.1 `default="json"` | Non-regression proven in §0.2; tested by existing 31 tests + `test_summarize_format_default_is_json` |
| 3 — `--format json` same as default | §2.2 `cmd_summarize` | JSON branch is unchanged path; verified by `diff` in §6 |
| 4 — `--format md` renders full report | §2.3 `_render_md`, §2.4 `_next_action` | All sections covered; tested by md test group |
| 5 — `hb-status.md` simplified to passthrough | §3 wiring | Skill steps 2–4 replaced by single SDK call |
| 6 — `status-template.md` deleted | §4 file changes | Removed from `references-toc.md`; file deleted; verified in §6 scope check |

---

## 8. Out of scope (per ticket)

- Changes to the JSON schema emitted by `hb-sdk summarize`.
- Changes to any other `hb-sdk` subcommands or flags.
- Styling or content changes to the rendered markdown beyond matching the current `hb-status` output — the `_render_md` function targets equivalence, not improvement.
