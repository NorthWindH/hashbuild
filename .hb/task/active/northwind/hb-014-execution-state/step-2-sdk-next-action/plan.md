# Step 2 Plan — `hb_sdk/next_action.py`: shared next-action derivation + `hb-sdk state next-action`

Today, "what should I do next?" is answered by `hb_sdk/summarize.py`'s `_next_action`
(`summarize.py:140-172`), which re-derives a plain string purely from file-presence
booleans on each active task's steps. It has two problems the task ticket calls out:
it doesn't implement the exact five-stage lifecycle in the task ticket's Background
(in particular it never recommends `/clear`, and it has no notion of the AC 3.4/3.5
*branching* choices — review-vs-next-step, add/update/archive), and it returns a
pre-joined string that only `summarize`'s own markdown renderer can consume — nothing
else (e.g. the `hb-flow` skill in step-3) can reuse it. This step extracts and
upgrades that logic into a new `hb_sdk/next_action.py` module that returns structured
data, exposes it via a new `hb-sdk state next-action [--format json|md]` CLI command,
and refactors `summarize.py` to render from the same structured data instead of its
own string-returning function. Scope boundary: this is a **behavior-changing
refactor** of one section of `summarize`'s markdown output (the "## Next Action"
block gains `/clear` reminders and richer branching content; every other section of
`summarize`'s output — tables, task details, archive — is untouched) plus a **purely
additive** new CLI surface. The single externally observable effect once this
lands: `hb-sdk state next-action` returns a stage/message/choices structure for every
active task (and a global fallback when none exist or `.hb/` is uninitialized), and
`hb-sdk summarize --format md`'s Next Action section reflects the same stage/message
content instead of its own ad hoc string.

Source ticket: `./ticket.md`. Builds on the **shipped** work from steps 0-1
(`hb_sdk/state.py`'s `write_state`/`read_state`/`state record`/`state show`, and all
8 `hb-*` skills now calling `state record` after they run) — this step is the first
consumer of the persisted record beyond raw display. This plan targets `hb_sdk` as it
exists on `master` today (commit `8a93fad`).

> **Design decision — how "move to the next step" (AC 3.4) and "all steps done"
> (AC 3.5) interact when the most-recently-executed step is also the *last* step.**
> AC 3.4 frames the post-execution choice as a strict binary: review this step, or
> move to the next step. But when the just-executed step has no `plan.md`-successor
> (it's the last step in the task), "moving to the next step" has nothing concrete to
> point at — the only thing left to recommend *is* AC 3.5's add-steps/update-plan/
> archive choice. Rather than inventing a vague third label ("see what's next") or
> silently picking one of AC 3.5's three options, §2's `_resolve` helper detects this
> overlap by recursing on the remaining step slice: if the recursive result is itself
> a branching stage (no single next command), its choices are **flattened into** the
> current stage's choice list instead of being wrapped behind one "move on" label. So
> the last-step-not-yet-reviewed case surfaces all four real options at once (review,
> add, update, archive) — never fewer than the truth, never a fabricated label. This
> also means the same recursion transparently produces the right answer when a
> *non-terminal* step is next (the common case: "move to the next step" gets one
> concrete invocation, e.g. `/hb-task-step-plan <ref>/step-3`). See §2's `_resolve`
> and the AC-traceability table (§7, AC 2.4/2.5).

---

## 0. Current-state facts (verified during planning)

- `hb_sdk/summarize.py:140-172` (`_next_action`) is the only next-action logic today.
  It takes the whole `_build_data(...)` output dict, and for each active task: emits
  "add ticket.md" if the task itself has no ticket; else "add steps" if zero steps or
  no step has a ticket; else, **per step**, emits one message for every step lacking a
  plan (`"Run /hb-task-step-plan ..."`) or execution (`"Run /hb-task-step-execute
  ..."`) — so a task with two non-contiguous unplanned steps gets two separate
  bullets today, not one. It never mentions `/clear`. It appends a fixed "review
  steps, archive task, or add more steps" sentence once, only when *every* step has
  `has_execution=True`, without checking review state at all. This step **narrows**
  the per-step case to a single "next blocking step" (per AC 2.2/2.3's "the next
  unplanned step" / "that step" wording — singular, not "every gap") and **adds**
  review-awareness to the terminal case. This is a deliberate behavior change from
  "list every gap" to "recommend the next one", justified by the ticket's own
  singular phrasing; existing tests asserting the old multi-bullet/no-`/clear`/
  review-blind text are updated in §5, not preserved byte-for-byte (ticket AC 6 asks
  for "equivalent in content... and additionally reflects" the new branching — not
  byte-identical to the old, review-blind string).
- `_build_data` (`summarize.py:249-323`, called at `summarize.py:327`) is the sole
  producer of the per-task/step status dict the ticket's AC 1 says this step's
  function must consume. It is currently module-private (leading underscore) and
  used only inside `summarize.py`. Its per-step dicts already carry every boolean
  this step needs: `has_ticket`, `has_plan`, `has_execution`, `has_review`, and
  `status` (one of `skeleton`/`ticketed`/`planned`/`executed`/`review-open`/
  `reviewed`, computed by `_StepInfo.status`, `summarize.py:47-57`). Steps arrive
  pre-sorted ascending by step number (`list_step_folders`, `task.py:243-254`, used
  at `summarize.py:112`), so "the next unplanned step" is simply "the first step in
  the list matching the gap condition" — no re-sorting needed.
- `hb_sdk/state.py` (`write_state`/`read_state`/`cmd_state_record`/`cmd_state_show`/
  `def_cli_state`) is the only precedent for a JSON-backed record. `read_state()`
  (`state.py:21-27`) calls `path_hb_asserted()` first, which **dies** (`die(...)`,
  `common.py:28-30`, exit 1) if `.hb/` doesn't exist — this is correct for `state
  show`'s own contract (`test_state_show_no_hb`) but is the **wrong** behavior for
  the new `next-action` command, which per AC 3 must gracefully report "run
  `/hb-init`" (parity with `_next_action`'s existing not-initialized branch,
  `summarize.py:141-142`) rather than dying. §4 handles this with an explicit
  `path_hb().exists()` guard before calling `read_state()`.
- `hb_sdk/__main__.py:1-28` wires each command group with one `def_cli_*(subs)` call,
  alphabetized by module name (`init_cmd, task, summarize, commit, idea, state,
  facts` per current source order — actually `commit, idea, init_cmd, summarize,
  task` imports then `state`, `facts` appended at the end per `git log`; the two
  newest additions were appended, not re-alphabetized). `next_action.py` needs no
  entry here at all — it exposes no `def_cli_*` of its own; its CLI surface is the
  new `next-action` subcommand added to `state.py`'s existing `state` subparser group
  (ticket AC 1.4: "`hb-sdk state next-action`", not a new top-level command).
- No circular-import risk once responsibilities are split correctly: `next_action.py`
  must only accept already-computed `data`/`state` dicts as plain parameters — it
  must **not** import `summarize.py` (summarize.py will import `next_action.py` per
  AC 5, so the reverse import would cycle). `state.py`'s new `next-action` subcommand
  is the one place that needs both `build_data` (from `summarize.py`) and
  `compute_next_action` (from `next_action.py`) — `state.py` importing both creates
  no cycle since neither `summarize.py` nor `next_action.py` imports `state.py`.
- Tests run via `uv run pytest` from repo root (`Makefile:4`); all existing
  `hb_sdk` test files use the same hermetic-subprocess pattern
  (`tests/skills/scripts/hb_sdk/helpers.py`'s `run(args, cwd, ok=...)` wrapping the
  `hb-sdk` CLI script) — no in-memory/unit-level imports of `hb_sdk` modules in any
  existing test file. This step's new test file follows the same convention rather
  than importing `next_action` functions directly, for consistency with
  `test_hb_sdk_state.py`/`test_hb_sdk_summarize.py`.

### 0.1 Impact (before → after)

| Aspect | Before | After |
|---|---|---|
| `hb_sdk/next_action.py` | Does not exist | New module: `Choice`/`NextAction` dataclasses, `next_action_for_task`, `compute_next_action`, `to_dict`, `render_md_lines` |
| `hb_sdk/summarize.py` | `_next_action(data) -> str`; `_build_data` module-private | `_next_action` deleted; `_build_data` renamed `build_data` (now cross-module public); `_render_md` renders the "## Next Action" section from `next_action.compute_next_action(None, data)` |
| `hb_sdk/state.py` | `state` subcommands: `record`, `show` | + `next-action` subcommand (`cmd_state_next_action`) |
| `hb-sdk summarize --format md` Next Action section | One bullet per task; per-step gaps listed individually; no `/clear`; terminal case is a fixed sentence, review-blind | One bullet per task (singular "next blocking step"); explicit `/clear` reminders for plan/execute stages; terminal case is review-aware and offers add/update/archive as distinct sub-bullets when applicable |
| `hb-sdk` CLI surface | `init`, `task`, `summarize`, `commit`, `idea`, `state {record,show}`, `facts` | + `state next-action [--format json|md]` |

This is an **output-altering** change to one specific, well-scoped section of
`summarize --format md` (the content of "## Next Action" changes; the section
heading, its position, and every other section are unchanged) plus a **purely
additive** new CLI surface (`next-action`) and new module (`next_action.py`).

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why/how it's preserved or deliberately changed |
|---|---|---|
| `summarize --format json` shape | Full per-task/step dict, consumed by CLI/tests | **Unchanged** — `build_data` (renamed from `_build_data`) returns byte-identical dict shape/keys; only the function's name and importability change, not its return value. `cmd_summarize`'s JSON branch is untouched. |
| `summarize` Task table (S/T/P/E/RO/R columns), Task Details, Archive sections | Rendered by `_render_md` from `build_data`'s counts | **Unchanged** — none of these sections read `_next_action`'s output; only the final "## Next Action" block is touched. |
| `.hb-task.json` / step file layout, `task.py`, `commit.py`, `idea.py`, `facts.py` | N/A | **Untouched** — this step only edits `summarize.py`, `state.py`, adds `next_action.py`, and their test files. |
| `summarize --format md` "## Next Action" exact text | Old `_next_action` string (no `/clear`, review-blind terminal case, per-step gap enumeration) | **Deliberately changed**, per ticket AC 6 ("equivalent in content... and additionally reflects" new branching) and the Background's explicit `/clear` requirement (AC 3.1-3.3) — not byte-identical. §5 updates the one existing test (`test_summarize_format_md_next_action_all_steps_executed`) whose exact-substring assertion no longer matches; all other existing Next Action tests use substrings (`"/hb-task-step-plan"`, `"ticket.md"`, `"/hb-init"`, `"/hb-task-create"`) that remain true under the new messages unchanged. |

---

## 1. Design overview

Three-module split, each with one job:

| Component | Owns | New? |
|---|---|---|
| `hb_sdk/next_action.py` | `Choice`/`NextAction` data model; the pure per-task stage derivation (`next_action_for_task`); the multi-task/global orchestration (`compute_next_action`); JSON/markdown rendering helpers shared by both consumers | **new** |
| `hb_sdk/summarize.py` | `build_data` (renamed, now public); `_render_md`'s "## Next Action" section calls into `next_action.py` instead of its own `_next_action` | **refactor** (rename + one call-site swap; everything else unchanged) |
| `hb_sdk/state.py` | new `next-action` subcommand: reads state (guarded), calls `summarize.build_data`, calls `next_action.compute_next_action`, prints via `next_action`'s JSON/md renderers | **extend** |

**Precedence chain** (evaluated top-to-bottom inside `next_action_for_task`/
`_resolve`, first match wins — this *is* the "single next blocking step" rule):

```
precedence (highest → lowest):
  task has no ticket.md                          > stage: no_ticket
  a step has no ticket.md                         > stage: step_needs_ticket   (earliest such step)
  a step has ticket.md but no plan.md             > stage: plan_step           (earliest such step)   — AC 2.2
  a step has plan.md but no execution-*.md        > stage: execute_step       (earliest such step)   — AC 2.3
  a step has execution-*.md and (no review.md
    or review.md has an open item)                > stage: review_or_next    (earliest such step)   — AC 2.4
  no steps at all (task just ticketed)             > stage: plan_task                                  — AC 2.1
  every step executed, and every review.md closed  > stage: steps_complete                             — AC 2.5
tie-break: "earliest such step" = lowest step number, since list_step_folders already
  returns steps in ascending order (task.py:243-254) — first match in iteration order wins,
  no separate sort needed.
```

`no_ticket`/`step_needs_ticket`/`plan_task`/`plan_step`/`execute_step` are terminal,
single-invocation stages. `review_or_next`/`steps_complete` are the two *branching*
stages the ticket's AC 1 calls out ("for the two branching stages, a list of
choices"). `plan_task` and `steps_complete` share one implementation path (see §2):
both are "the step list, walked in order, is exhausted" — the only difference is
*why* it's exhausted (zero steps ever existed vs. every step is done), which is
threaded through as a parameter rather than duplicated as two separate functions.

**Alternatives considered and rejected:**

- *Keep emitting one bullet per step-with-a-gap (today's behavior).* Rejected — AC
  2.2/2.3 explicitly say "the next unplanned step" / "that step" (singular). A
  single deterministic recommendation is also what makes the two branching stages
  (which must each pick *one* current step to center the choices on) well-defined.
- *Have `next_action_for_task` accept `state` too, so per-task derivation could special-case "this is the task the user was just working on."* Rejected — every one of the five stages is fully determined by file-presence state already; threading `state` into the per-task function would add a parameter no branch reads, violating the "no defensive/unused code" convention. `state` is accepted (per AC 1) only at the top-level `compute_next_action`, where it has one real, testable use: ordering (see below).
- *Ignore `state` entirely (treat the AC 1 signature requirement as vestigial).* Rejected — `state`'s `task`/`step` fields are the one piece of information that lets multi-task output front-load "the task the user just worked on" rather than an arbitrary (directory-iteration) order. `compute_next_action` uses it for exactly this: if `state["task"]` names a still-active task, that task's entry is moved first in the returned list; otherwise order is unchanged (existing active-task iteration order, same as `summarize`'s table today).
- *Make `next_action.py` call `summarize.build_data()` itself* (so `compute_next_action` only needs `state`, not `data`). Rejected — would force `next_action.py` to import `summarize.py`, which must import `next_action.py` back for AC 5's refactor: a circular import. Keeping `data` as a plain parameter (computed once by whichever caller needs it) avoids the cycle entirely and matches AC 1's literal wording ("takes... the per-task/step status data already computed by `_summarize_task`/`_build_data`").
- *Represent "move to the next step" as a nested `NextAction` inside the `Choice`.* Rejected — AC 1 specifies choices have "a label and the corresponding skill invocation" (a flat string), not a nested structure. The recursion in `_resolve` (see the Design decision callout above) resolves any nested branching **before** building the `Choice` list, so `choices` stays one level deep for both consumers (CLI JSON and markdown rendering) and for step-3's `hb-flow` skill that will consume this JSON next.

---

## 2. `hb_sdk/next_action.py` — specification

**Data model** (all **new**):

```python
@dataclass
class Choice:
    label: str        # human-readable action name, e.g. "Review this step"
    invocation: str    # exact command to run, e.g. "/hb-task-step-review-init author/task-id/step-2"

@dataclass
class NextAction:
    stage: str                        # one of the 7 stage identifiers in §1's precedence chain
    message: str                      # human-readable recommendation; always set
    invocation: str | None = None     # set for the 5 non-branching stages; None for the 2 branching stages
    choices: list[Choice] | None = None  # set for review_or_next/steps_complete; None otherwise
```

Exactly one of `invocation`/`choices` is non-`None` for every stage except the two
global fallback stages (`not_initialized`, `no_active_tasks`), which set neither
(message-only, matching `_next_action`'s existing text for those cases — no runnable
single command to attach).

**Interfaces / signatures** (all **new**):

```python
def next_action_for_task(task: dict[str, Any]) -> NextAction:
    """Derive the single next-action stage for one active-task dict, as shaped by
    `summarize.build_data()`'s `active_tasks[i]` entries (must contain at least
    `author`, `task_folder`, `has_ticket`, `steps` — where each step dict has
    `name`, `has_ticket`, `has_plan`, `has_execution`, `has_review`, `status`)."""

def compute_next_action(
    state: dict[str, Any] | None, data: dict[str, Any]
) -> list[tuple[str | None, NextAction]]:
    """Top-level orchestration consumed by both `state.py`'s `next-action` command
    and `summarize.py`'s renderer. `data` is `summarize.build_data()`'s output.
    Returns a list of (task_ref, NextAction) pairs:
    - a single `(None, NextAction(stage="not_initialized", ...))` if `data["initialized"]` is False
    - a single `(None, NextAction(stage="no_active_tasks", ...))` if there are no active tasks
    - otherwise one `(f"{author}/{task_folder}", next_action_for_task(t))` pair per
      active task, in `data["active_tasks"]` order, EXCEPT: if `state` is not None and
      `state.get("task")` matches one of those refs exactly, that pair is moved to the
      front of the list (stable order otherwise)."""

def to_dict(ref: str | None, na: NextAction) -> dict[str, Any]:
    """JSON-serializable shape: {"task": ref, "stage": ..., "message": ...,
    "invocation": ..., "choices": [{"label":..., "invocation":...}, ...] | None}."""

def render_md_lines(na: NextAction) -> list[str]:
    """Markdown bullet lines for one NextAction: `- {message}`, plus one
    `  - {label}: `{invocation}`` line per choice when `choices` is set. Does not
    include the task ref — every `message` already embeds it (see §2 algorithm), so
    a separate prefix would duplicate it."""
```

**Algorithm / rules** (the precedence chain from §1, implemented as one recursive
helper so `plan_task`/`steps_complete` — both "step list exhausted" — share code,
and so `review_or_next`'s "move to the next step" choice can resolve what's
actually next without a second, parallel implementation):

```python
def _resolve(steps: list[dict], ref: str, on_exhausted: str) -> NextAction:
    for i, s in enumerate(steps):
        if not s["has_ticket"]:
            return NextAction(
                stage="step_needs_ticket",
                message=f"Add `ticket.md` to `{ref}/{s['name']}` or run `/hb-task-step-add {ref}`.",
            )
        if not s["has_plan"]:
            inv = f"/hb-task-step-plan {ref}/{s['name']}"
            return NextAction(
                stage="plan_step",
                message=f"Run `/clear`, then `{inv}` to plan the next step.",
                invocation=inv,
            )
        if not s["has_execution"]:
            inv = f"/hb-task-step-execute {ref}/{s['name']}"
            return NextAction(
                stage="execute_step",
                message=f"Run `/clear`, then `{inv}` to execute the plan.",
                invocation=inv,
            )
        if not s["has_review"] or s["status"] == "review-open":
            review_inv = (
                f"/hb-task-step-review-init {ref}/{s['name']}"
                if not s["has_review"]
                else f"/hb-task-step-review-address {ref}/{s['name']}"
            )
            review_choice = Choice("Review this step", review_inv)
            move_on = _resolve(steps[i + 1:], ref, on_exhausted="steps_complete")
            if move_on.invocation is not None:
                rest = [Choice("Move to the next step", move_on.invocation)]
            else:
                rest = move_on.choices or []
            return NextAction(
                stage="review_or_next",
                message=f"Step `{ref}/{s['name']}` is executed — review it or move on.",
                choices=[review_choice, *rest],
            )
    if on_exhausted == "plan_task":
        inv = f"/hb-task-plan {ref}"
        return NextAction(
            stage="plan_task",
            message=f"Run `/clear`, then `{inv}` to plan `{ref}` into steps.",
            invocation=inv,
        )
    return NextAction(
        stage="steps_complete",
        message=f"All steps for `{ref}` are executed and reviewed — add more steps, update the plan, or archive.",
        choices=[
            Choice("Add more steps", f"/hb-task-step-add {ref}"),
            Choice("Update the plan", f"/hb-task-plan {ref}"),
            Choice("Archive the task", f"/hb-task-archive {ref}"),
        ],
    )


def next_action_for_task(task: dict[str, Any]) -> NextAction:
    ref = f"{task['author']}/{task['task_folder']}"
    if not task["has_ticket"]:
        return NextAction(
            stage="no_ticket",
            message=f"Add `ticket.md` to `{ref}` with Background and Acceptance Criteria.",
        )
    return _resolve(task["steps"], ref, on_exhausted="plan_task")
```

`compute_next_action`:

```python
def compute_next_action(state, data):
    if not data["initialized"]:
        return [(None, NextAction(stage="not_initialized", message="Run `/hb-init` to initialize the workspace.", invocation="/hb-init"))]
    active = data["active_tasks"]
    if not active:
        return [(None, NextAction(stage="no_active_tasks", message="Start a new task with `/hb-task-create <author/task-id>`."))]
    entries = [(f"{t['author']}/{t['task_folder']}", next_action_for_task(t)) for t in active]
    wanted = state.get("task") if state else None
    if wanted is not None:
        idx = next((i for i, (ref, _) in enumerate(entries) if ref == wanted), None)
        if idx is not None and idx != 0:
            entries.insert(0, entries.pop(idx))
    return entries
```

**Failure/degradation contract:** `next_action_for_task`/`_resolve` assume `data`'s
shape is exactly what `build_data` produces (no defensive key-checking — same
convention as every other `hb_sdk` module, which trusts its own internal producers).
`compute_next_action` never raises for `state=None` or a `state["task"]` that names
no active task (falls through to unchanged order) — a stale/foreign task ref in
state is not an error, just a no-op for ordering purposes.

**Conflict resolution:** N/A for stage selection (deterministic precedence, first
match wins per §1). For task ordering, the only "conflict" is state naming a task
that no longer exists/isn't active — resolved by leaving order unchanged (see above).

---

## 3. `hb_sdk/summarize.py` / `hb_sdk/state.py` — integration

**`summarize.py` changes:**

- Rename `_build_data` → `build_data` (module-public now that `state.py` needs to
  call it too; return value, parameter, and body are **completely unchanged** — a
  pure rename). Update its two call sites in this file (definition + `cmd_summarize`
  at line 327).
- Delete `_next_action` (`summarize.py:140-172`) entirely.
- In `_render_md` (`summarize.py:175-246`), replace:
  ```python
  lines += ["", "---", "", "## Next Action", ""]
  lines.append(_next_action(data))
  ```
  with:
  ```python
  lines += ["", "---", "", "## Next Action", ""]
  for ref, na in next_action.compute_next_action(None, data)
      lines += next_action.render_md_lines(na)
  ```
  (`state=None` here — `summarize` has no access to, and no need for, the persisted
  last-executed-action record; it only needs `next_action_for_task`'s file-state
  derivation, so passing `None` is correct and exercises `compute_next_action`'s
  `state is None` path, already covered by §1's "ignore `state` entirely" fallback.)
- Add `from . import next_action` to the import block.
- `cmd_summarize`'s JSON branch (`summarize.py:326-331`) is **untouched** — JSON
  output shape is unaffected by this step (AC 7: "no regression to the existing JSON
  schema fields").

**`state.py` changes:**

- Add `cmd_state_next_action(args)`:
  ```python
  def cmd_state_next_action(args: argparse.Namespace) -> None:
      state = read_state() if path_hb().exists() else None
      data = build_data(path_hb())
      entries = compute_next_action(state, data)
      if args.format == "md":
          for ref, na in entries:
              print("\n".join(render_md_lines(na)))
      else:
          print(json.dumps([to_dict(ref, na) for ref, na in entries], indent=2))
  ```
  The `path_hb().exists()` guard is the fix for the "wrong die path" fact noted in
  §0: `read_state()` itself is untouched (still dies via `path_hb_asserted()` for its
  own direct callers, `state show`), but `next-action` only calls it once we already
  know `.hb/` exists, so the not-initialized case flows through `build_data`'s
  existing graceful handling instead of hitting `read_state`'s `die`.
- Add imports: `from .common import path_hb` (alongside the existing
  `path_hb_asserted`, `path_hb_state`, `progress` import), `from .summarize import
  build_data`, `from .next_action import compute_next_action, render_md_lines,
  to_dict`.
- In `def_cli_state`, add a third subparser after `show`:
  ```python
  p_na = state_subs.add_parser("next-action", help="Print derived next action for active task(s)")
  p_na.add_argument("--format", choices=["json", "md"], default="json")
  p_na.set_defaults(func=cmd_state_next_action)
  ```

**Wiring boundary:** `__main__.py` is **untouched** — `next-action` is a subcommand
of the existing `state` command group, not a new top-level command, so no new
`def_cli_*` registration is needed there.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/next_action.py` | **new** — `Choice`, `NextAction`, `_resolve`, `next_action_for_task`, `compute_next_action`, `to_dict`, `render_md_lines` |
| `skills/scripts/hb_sdk/summarize.py` | **edit** — rename `_build_data`→`build_data`; delete `_next_action`; `_render_md`'s Next Action block now calls `next_action.compute_next_action`/`render_md_lines`; add `next_action` import. Everything else (dataclasses, `_parse_review_open`, table/details/archive rendering, `cmd_summarize`, `def_cli_summarize`) untouched. |
| `skills/scripts/hb_sdk/state.py` | **edit** — add `cmd_state_next_action`, new `next-action` subparser in `def_cli_state`; add imports for `path_hb`, `build_data`, `compute_next_action`/`render_md_lines`/`to_dict`. `write_state`, `read_state`, `cmd_state_record`, `cmd_state_show` untouched. |
| `tests/skills/scripts/hb_sdk/helpers.py` | **extend** — add `state_next_action(cwd, **kwargs)` wrapper (`["state", "next-action"]` + optional `--format`), mirroring `state_show`'s shape |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_next_action.py` | **new** — full test suite for `state next-action`, all 7 stages + ordering + JSON/md format |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_summarize.py` | **edit** — update `test_summarize_format_md_next_action_all_steps_executed`'s assertion (see §5); all other tests in this file unchanged |

No dependency-manifest or lockfile changes — `next_action.py` uses only stdlib
(`dataclasses`, `typing`), matching every other `hb_sdk` module.

---

## 5. Tests

Framework/layout: `pytest`, mirroring `test_hb_sdk_state.py`'s structure (plain
functions, `tmp_path` fixture, section-comment dividers per stage, hermetic
CLI-subprocess calls via `helpers.py` — no in-memory imports of `hb_sdk` internals,
consistent with every existing `hb_sdk` test file per §0's fact).

**`helpers.py` addition:**

```python
def state_next_action(cwd: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    args = ["state", "next-action"]
    if fmt := kwargs.get("format"):
        args += ["--format", fmt]
    return run(args, cwd, ok=kwargs.get("ok", True))
```

**`test_hb_sdk_next_action.py` — new, grouped by stage (mirrors §1's precedence
chain, one section per row):**

- *not initialized / no active tasks (AC 3)*
  - `test_next_action_not_initialized`: no `init` at all; `state_next_action(tmp_path, format="json")`; assert single entry, `task is None`, `stage == "not_initialized"`, `"/hb-init"` in `message`.
  - `test_next_action_no_active_tasks`: `init` only; assert `stage == "no_active_tasks"`, `"/hb-task-create"` in `message`.
- *no_ticket*
  - `test_next_action_task_no_ticket`: `task_create` with no ticket; assert `stage == "no_ticket"`, `task == "hasan/abc-1"`, `"ticket.md"` in `message`.
- *step_needs_ticket*
  - `test_next_action_step_needs_ticket`: `task_create` (with ticket) + `task_step_add`, then delete `step-0/ticket.md`; assert `stage == "step_needs_ticket"`.
- *plan_task (AC 2.1)*
  - `test_next_action_stage_plan_task`: `task_create` with ticket, zero steps; assert `stage == "plan_task"`, `invocation == "/hb-task-plan hasan/abc-1"`, `"/clear"` in `message`.
- *plan_step (AC 2.2)*
  - `test_next_action_stage_plan_step`: + `task_step_add` (ticketed, unplanned); assert `stage == "plan_step"`, `invocation == "/hb-task-step-plan hasan/abc-1/step-0"`, `"/clear"` in `message`.
  - `test_next_action_stage_plan_step_picks_earliest`: 3 steps added, `step-0` executed (has plan+execution), `step-1`/`step-2` ticketed-only; assert stage picks `step-1` (not `step-2`).
- *execute_step (AC 2.3)*
  - `test_next_action_stage_execute_step`: step has `plan.md`, no execution; assert `stage == "execute_step"`, `invocation` names the right step, `"/clear"` in `message`.
- *review_or_next (AC 2.4)*
  - `test_next_action_stage_review_or_next_no_review_file`: single step executed, no `review.md`; assert `stage == "review_or_next"`, first choice label `"Review this step"` with `/hb-task-step-review-init` invocation, and (since there's no next step) the remaining choices are the *flattened* `steps_complete` triple (`"Add more steps"`, `"Update the plan"`, `"Archive the task"`) — 4 choices total.
  - `test_next_action_stage_review_or_next_open_review`: step executed + `review.md` with an open item; assert review choice uses `/hb-task-step-review-address`.
  - `test_next_action_stage_review_or_next_has_next_step`: 2 steps — `step-0` executed/no review, `step-1` ticketed-only (unplanned); assert `step-0`'s stage choices are exactly 2: `"Review this step"` + `"Move to the next step"` whose invocation is `/hb-task-step-plan .../step-1` (not flattened, since a concrete single next action exists).
- *steps_complete (AC 2.5)*
  - `test_next_action_stage_steps_complete`: single step executed + `review.md` with all items closed; assert `stage == "steps_complete"`, exactly 3 choices (`"Add more steps"`/`"Update the plan"`/`"Archive the task"`), no `"Review this step"` choice present.
- *ordering by `state` (AC 1's use of the persisted record)*
  - `test_next_action_orders_state_task_first`: two active tasks (`hasan/abc-1`, `hasan/abc-2`); `state_record(task="hasan/abc-2", ...)`; assert `entries[0]["task"] == "hasan/abc-2"`.
  - `test_next_action_state_unknown_task_no_reorder`: `state_record(task="hasan/does-not-exist", ...)`; assert order unchanged (matches `data["active_tasks"]` order).
  - `test_next_action_no_state_default_order`: no `state record` call at all; assert order matches `data["active_tasks"]` order (no crash on `state=None`).
- *`--format` (parity with `state show`/`summarize`)*
  - `test_next_action_format_default_is_json` / `test_next_action_format_md_renders_message`: default-format round-trips as JSON; `--format md` output contains the stage's message text and, for a branching stage, its choice labels as sub-bullets.

**`test_hb_sdk_summarize.py` edit:**

- `test_summarize_format_md_next_action_all_steps_executed` (single step, executed,
  no `review.md`): this now hits `review_or_next` (not the old fixed sentence),
  because AC 2.4's condition (`has_execution` and `not has_review`) fires before AC
  2.5's. Replace the assertion `"review steps, archive task, or add more steps" in
  result.stdout` with assertions matching the new, richer content: `"Review this
  step"`, `"Add more steps"`, `"Update the plan"`, `"Archive the task"` all present
  in `result.stdout` (demonstrating the flattened 4-choice output this step adds,
  satisfying AC 6's "additionally reflects the new... branching choices"). No other
  test in this file changes.

**Non-regression:** every other existing test in `test_hb_sdk_summarize.py` keeps
passing unmodified — they either assert on `--format json` fields untouched by this
step, or use substrings (`"/hb-task-step-plan"`, `"/hb-task-step-execute"`,
`"ticket.md"`, `"/hb-init"`, `"/hb-task-create"`) that remain true under the new
messages. All of `test_hb_sdk_state.py`, `test_hb_sdk_task.py`,
`test_hb_sdk_commit.py`, `test_hb_sdk_idea.py`, `test_hb_sdk_init.py` are unaffected
(no shared function they call changes signature or behavior — `read_state`/
`write_state`/`cmd_state_record`/`cmd_state_show` are all untouched).

---

## 6. Verification (after implementation)

1. **Full test run is green:** `uv run pytest` (or `.venv/bin/python -m pytest
   tests/ -q`) from repo root — all existing suites plus the new
   `test_hb_sdk_next_action.py` pass, and the one updated summarize assertion
   passes.
2. **Manual round-trip, fresh temp dir, all 7 stages:**
   ```bash
   cd "$(mktemp -d)"
   HB=/home/hkamal/repos/hashbuild/skills/scripts/hb-sdk
   $HB init
   $HB state next-action --format md   # expect: "no_active_tasks" text, /hb-task-create
   $HB task create hasan/abc-1 --ticket <ticket-with-Background-and-AC.md>
   $HB state next-action --format md   # expect: plan_task, mentions /clear and /hb-task-plan
   $HB task step add hasan/abc-1
   $HB state next-action --format md   # expect: plan_step, mentions /clear and /hb-task-step-plan .../step-0
   # ... progressively touch plan.md / execution-*.md / review.md under step-0 to walk
   # through execute_step -> review_or_next -> steps_complete, re-running
   # `$HB state next-action --format json` after each to inspect stage/choices.
   ```
3. **Per-AC checks:** walk §7's traceability table; confirm each row's named test
   passes and (for the manual-only rows) the command sequence above shows the
   expected stage/message/choices.
4. **Invariant checks:** every `NextAction` has a non-empty `message`; exactly one
   of `invocation`/`choices` is set except the two global fallback stages (assert
   this invariant directly in a test — `test_next_action_invariant_one_of_invocation_or_choices`
   — by inspecting every stage's JSON output across the fixtures already built for
   the per-stage tests). `summarize --format json`'s schema is byte-identical to
   before (diff a captured baseline JSON from `master` against post-change output
   for the same fixture task, confirming the rename to `build_data` changed nothing
   observable).
5. **Scope check:** `git diff --stat` shows only the files in §4 — no changes to
   `task.py`, `commit.py`, `idea.py`, `common.py`, `facts.py`, `__main__.py`, or any
   skill Markdown (wiring `hb-flow` to consume this is step-3, out of scope here).

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 (`next_action.py` module; function takes state + data; returns stage/message/choices) | §2 | `next_action_for_task`/`compute_next_action`; `Choice`/`NextAction` dataclasses |
| 2.1 (zero steps → plan_task) | §2 `_resolve` (`on_exhausted="plan_task"` base case) | `test_next_action_stage_plan_task` |
| 2.2 (ticket, no plan → plan_step, next unplanned step) | §2 `_resolve` | `test_next_action_stage_plan_step`, `_picks_earliest` |
| 2.3 (plan, no execution → execute_step) | §2 `_resolve` | `test_next_action_stage_execute_step` |
| 2.4 (execution, no/open review → review_or_next choice) | §2 `_resolve` branching case + Design decision callout | `test_next_action_stage_review_or_next_*` (3 tests) |
| 2.5 (all executed + reviewed-closed → steps_complete choice) | §2 `_resolve` (`on_exhausted="steps_complete"` base case) | `test_next_action_stage_steps_complete` |
| 3 (no active tasks → existing "start a new task" parity) | §2 `compute_next_action` | `test_next_action_no_active_tasks`, message text matches `_next_action`'s old string verbatim |
| 4 (`hb-sdk state next-action [--format json|md]`) | §3 `state.py` changes | `test_next_action_format_default_is_json`, `_format_md_renders_message`, plus all per-stage tests (run through the CLI) |
| 5 (`_next_action` replaced; no duplicated derivation logic in `summarize.py`) | §3 `summarize.py` changes | `_next_action` deleted; `_render_md` calls `next_action.compute_next_action`/`render_md_lines` exclusively |
| 6 (`summarize --format md` Next Action equivalent + reflects new branching) | §3, §5 | Existing substring-based tests still pass; `test_summarize_format_md_next_action_all_steps_executed` updated to assert the new branching content |
| 7 (`summarize --format json` schema no regression) | §3 (`build_data` rename, body unchanged) | No existing JSON-shape test changes; §6 step 4's baseline-diff check |
| 8 (manual exercise of all 5 ticket stages + step_needs_ticket/no_ticket continuity) | §6 step 2 | Manual command sequence; also covered automatically by every per-stage test in §5 |

---

## 8. Out of scope (per ticket)

- The `hb-flow` skill that presents this data conversationally and handles
  natural-language navigation — deferred to step-3 (`step-3-hb-flow-skill`).
- Changing how/when skills call `hb-sdk state record` — already delivered in
  step-1; no skill Markdown is touched by this step.
- Any change to the existing "S/T/P/E/RO/R" table rendering, Task Details, or
  Archive sections in `_render_md` — only the Next Action section changes.
- A history/log of past next-action derivations — `compute_next_action` is a pure
  function of the *current* file state plus the single latest `state` record; no
  new persistence is introduced by this step.
