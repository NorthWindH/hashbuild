# Step 1 Plan — Wire `hb-sdk state record` into the 8 state-changing skills

This step wires the previously-shipped `hb-sdk state record`/`hb-sdk state show`
primitive (added in step-0) into the 8 `hb-*` skills whose `.md` files currently
never call it — today `${CLAUDE_SKILL_DIR}/scripts/hb_sdk/state.py` exists and is
unit-tested (`tests/skills/scripts/hb_sdk/test_hb_sdk_state.py`) but no skill
invokes it, so `.hb/.state.ignore.json` is never written and `hb-sdk state show`
always reports "No recorded state." even after running e.g. `/hb-task-create`.
Mostly a **prose-instruction change** (`skills/*.md`), plus one small, ticket-
sanctioned code change: `hb-sdk state record` now generates its own timestamp
(local time, timezone-aware) instead of requiring the caller to supply one —
this drops the need for any skill to shell out to `date` or gain a new
`Bash(date *)` permission, which the original design would have required on 6
of the 8 skills. Scope boundary: additive for the 8 skills (existing behavior,
error-message wording, and commit mechanics unchanged); the `--timestamp` CLI
flag is removed from `hb-sdk state record` (a real, but ticket-scoped, contract
change — see AC2 and the ticket's Out-of-scope note permitting exactly this).
The only new externally observable effect: `.hb/.state.ignore.json` (gitignored,
per `ensure_gitignore_entry`) reflects the last-executed skill/ref/outcome/
timestamp after each of the 8 skills runs.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-sdk state record`/
`hb-sdk state show` CLI and `write_state`/`read_state` (`skills/scripts/hb_sdk/state.py`,
delivered in `hb-014/step-0`) and the existing 8 skill `.md` files as they exist
**now** (`skills/hb-task-create.md`, `hb-task-step-add.md`, `hb-task-step-plan.md`,
`hb-task-step-execute.md`, `hb-task-step-review-init.md`,
`hb-task-step-review-address.md`, `hb-task-archive.md`, `hb-task-unarchive.md`).

> **Design decision — four things worth defending.**
>
> 1. **Timestamp source moved from caller to `hb-sdk` itself** (this plan
>    supersedes an earlier revision of this same plan, which had skills call
>    `date -u ...` and pass `--timestamp`). That earlier design required a new
>    `Bash(date *)` permission on 6 of the 8 skills' front-matter and added an
>    LLM-followable-but-error-prone step (capture stdout, format it right,
>    remember to pass it through) for no benefit — `hb-sdk` can call
>    `datetime.now()` itself. AC2 (revised) makes this the required design;
>    the ticket's Out-of-scope note explicitly carves this one code change back
>    into scope. Per AC2, the generated timestamp is **local time,
>    timezone-aware — not UTC** (matches the existing convention already used
>    by `cmd_task_step_execution_slug`, `hb_sdk/task.py:380`:
>    `datetime.now().astimezone()`; this is a *different* existing convention
>    than `hb_sdk/task.py`'s `created_at`/`ticket_written_at` fields, which use
>    `datetime.now(timezone.utc)` — the ticket picked the local-time one).
> 2. **Single-atomic-call skills** (`hb-task-create`, `hb-task-step-add`,
>    `hb-task-archive`, `hb-task-unarchive`) each have exactly one documented
>    error path, and it's the *same* `hb-sdk` call that both resolves and
>    mutates the task/step (e.g. `hb-sdk task create` validates the name AND
>    creates the folder in one shot). Nothing is confirmed to exist before that
>    call succeeds, so — same class as the ticket's own "invalid task name"
>    example — these are fully exempt. Result: these 4 skills get **only** a
>    success-path record step, no failure path.
> 3. **The shared `review-init-subflow.md`** (injected into both
>    `hb-task-step-review-init` and `hb-task-step-review-address`) is explicitly
>    documented as side-effect-free ("Contains no side effects (no user
>    notification, no commit)"). Adding a state-write inside it would break that
>    documented contract for both callers asymmetrically. Its two internal stops
>    (step-ref-not-found; drifted `review.md`) are therefore exempt — documented
>    inline in both skills' new record step so the exemption is traceable, not
>    silent.
> 4. Everywhere else, if a step already resolved a task+step ref (via
>    `hb-sdk task step path`/`task step number`) and *then* has a documented
>    "notify and stop" — `hb-task-step-execute` §3 (`plan.md` missing),
>    `hb-task-step-review-address` §5.7 (no review concerns) and §6 (ambiguous
>    review ID) — a `failure` record is inserted immediately before the
>    existing stop text, verbatim-unchanged otherwise.
>
> See §1 for the per-skill table and the AC-traceability table (§7) for how each
> AC maps here.

---

## 0. Current-state facts (verified during planning)

- `skills/scripts/hb_sdk/state.py` defines `cmd_state_record` / `cmd_state_show`,
  wired into `skills/scripts/hb_sdk/__main__.py` via `def_cli_state`. Today the
  CLI is `hb-sdk state record --skill <name> --outcome <outcome> --timestamp <ts> [--task <ref>] [--step <ref>]`
  with `--skill`/`--outcome`/`--timestamp` all `required=True`
  (`state.py:63-69`) and `cmd_state_record` copying `args.timestamp` verbatim
  into the record (`state.py:29-37`). **This step removes `--timestamp` as a
  CLI flag entirely** and has `cmd_state_record` generate it internally.
  `write_state` fully **overwrites** `.hb/.state.ignore.json` each call (flat
  record, no history) — unaffected by this change.
- The local-timezone-aware pattern AC2 asks for already exists in this
  codebase: `cmd_task_step_execution_slug` (`hb_sdk/task.py:378-381`) uses
  `datetime.now().astimezone().strftime(...)`. `state.py` will follow the same
  `datetime.now().astimezone()` call, formatted with `.isoformat()` (no
  filename-safety constraint here, so no need for `task.py`'s custom
  `%Y-%m-%dT%H-%M-%S%z` strftime — plain ISO 8601 is fine and matches
  `hb_sdk/task.py`'s other timestamp fields' use of `.isoformat()`).
- `hb-sdk task step number <step_ref>` (used already in
  `hb-task-step-review-address.md` §2 and the shared `review-init-subflow.md`
  §A) is a pure string-format parser (`_parse_step_ref`,
  `skills/scripts/hb_sdk/task.py:206-225`) — it does **not** touch disk, so it's
  safe to call for ref-derivation without any existence risk, including right
  after a step folder was just created.
- **Removing `--timestamp` ripples into the existing test suite** — every
  call site in `tests/skills/scripts/hb_sdk/test_hb_sdk_state.py` currently
  passes an explicit `timestamp="2026-01-01T00:00:00Z"` and asserts it round-
  trips exactly; one test (`test_state_record_requires_timestamp`) asserts
  omitting it is an *error*. Both must change — enumerated exactly in §5.
  `tests/skills/scripts/hb_sdk/helpers.py`'s `state_record()` wrapper
  (lines 109-121) also has a `--timestamp` pass-through block to remove.
- `.hb/.state.ignore.json` is gitignored (`ensure_gitignore_entry`,
  `skills/scripts/hb_sdk/common.py:87-106`, wired from `hb-init`). Confirmed via
  `git log`: commit `62f7d87` renamed the state file specifically to
  `.state.ignore.json` for this reason. **Consequence: the new record step never
  needs `git add`/commit** — it's a side effect entirely outside git, so it
  cannot interact with any skill's existing "Commit" step or its file-staging
  rules. Ordering relative to Commit is therefore a documentation nicety, not a
  functional constraint — placed last (after Prompt user) in every skill, per
  the ticket's own phrasing ("after its existing terminal steps").
- No skill's front-matter `allowed-tools:` needs to change under the revised
  design — the previous plan revision needed a new `Bash(date *)` grant on 6
  of the 8 skills; with `hb-sdk` self-generating the timestamp, every skill's
  new `state record` call still goes through the already-allowed
  `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)` entry, present in all 8.
- Ref availability per skill at the point a record step would run (what each
  skill's existing flow already resolves, verified by reading each `.md`):

  | Skill | Input | Task ref available how | Step ref (`$N`) available how |
  |---|---|---|---|
  | `hb-task-create` | `<name>` (task-scoped) | `<name>` verbatim | n/a |
  | `hb-task-step-add` | `<name>` (task-scoped, but creates a step) | `<name>` verbatim | **new** — folder basename from §3, then `hb-sdk task step number <name>/<basename>` |
  | `hb-task-step-plan` | `step_ref` | **new** — `step_ref` minus trailing `/<step_n>` | **new** — `hb-sdk task step number <step_ref>` added to §2 |
  | `hb-task-step-execute` | `step_ref` | **new** — same derivation, added to §2 | **new** — same, added to §2 |
  | `hb-task-step-review-init` | `step_ref` | **new** — derived in the new final step | already `$N` (from shared subflow §A) |
  | `hb-task-step-review-address` | `step_ref` | **new** — derivation added to §2 | already `$N` (from §2, pre-existing) |
  | `hb-task-archive` | `<name>` (task-scoped) | `<name>` verbatim | n/a |
  | `hb-task-unarchive` | `<name>` (task-scoped) | `<name>` verbatim | n/a |

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `hb-sdk state record` CLI | `--timestamp <ts>` required, caller-supplied | `--timestamp` flag removed; `cmd_state_record` generates local-time, timezone-aware ISO 8601 internally |
| Run any of the 8 skills to completion | `.hb/.state.ignore.json` untouched; `hb-sdk state show` unaffected | Exactly one `hb-sdk state record --outcome success ...` call (no `--timestamp`) at the very end; `hb-sdk state show` reflects that skill/ref plus a fresh timestamp |
| `hb-task-step-execute` when `plan.md` is missing | Aborts with existing error message only | Records `--outcome failure` (task+step ref) immediately before the same, unchanged abort message |
| `hb-task-step-review-address` when no review concerns exist yet (§5.7), or an ID conflict is unresolvable (§6) | Stops with existing message only | Records `--outcome failure` (task+step ref) immediately before the same, unchanged stop message |
| The 4 single-atomic-call skills' error paths; the shared review subflow's 2 internal stops | No record | Still no record — exempt by design (see decision box above) |
| Any skill's `allowed-tools` front-matter | — | **Unchanged** — no new permission needed under the revised (self-generated timestamp) design |

Kind of change: additive for the 8 skill `.md` files (new steps + new bullets
inserted before existing stop text; no existing instruction's wording,
ordering, or front-matter changes). One narrow, ticket-sanctioned **breaking**
change to `hb-sdk state record`'s CLI surface (`--timestamp` removed) — the
only caller today is this same set of 8 skills (none of which exist yet in
committed form), and the test suite, both updated together in this step.

### 0.2 Non-regression proof

| Case | Current behavior | Why it can't change |
|---|---|---|
| Existing error/abort message text (step-execute §3, review-address §5.7/§6) | Exact wording documented in ticket AC3/AC5 | New record call is a preceding instruction, not a text edit — the abort/stop sentence is copied verbatim |
| Existing `allowed-tools` entries in all 8 skills | Unchanged | Self-generated timestamp needs no new shell command — nothing to grant |
| Commit step file-staging | Unchanged | State file is gitignored (§0 above) — record step never touches `git add`/`git status`, so it cannot add unrelated files to a commit |
| `hb-sdk state record`'s `--skill`/`--outcome`/`--task`/`--step` behavior | Unchanged | Only `--timestamp` is removed and its value's *source* changes; the other four fields, `write_state`'s overwrite semantics, and `state show` are untouched (verified by `test_hb_sdk_state.py` tests not covering `--timestamp` staying green with no edits) |
| Other `hb_sdk` modules (`task.py`, `commit.py`, `idea.py`, `init_cmd.py`, `summarize.py`) | Unchanged | Zero edits to any file outside `state.py` and its own test file (§4) |

This is not a purely-additive step (unlike the 8 `.md` files) — it does
deliberately break `--timestamp` callers. The risk is fully contained because
the only callers are the 8 skills being edited in lockstep and the test suite
being updated in lockstep, both in this same step/commit sequence.

---

## 1. Design overview

One new instruction shape, "Record execution state," gets inserted at exactly
one place per skill (the true end, after Commit/Prompt), plus 0–2 new "record
failure, then stop" insertions per skill where a documented stop already
exists after a ref was resolved. No `date`/timestamp handling appears in any
skill file — that responsibility now lives entirely in `hb-sdk`:

```
[existing skill flow, unchanged] → [resolve $TASK_REF / $N if not already available]
  → (only at pre-existing documented stops that occur after refs are resolved:
      hb-sdk state record --outcome failure ... → existing stop, unchanged)
  → [flow reaches its natural end] → hb-sdk state record --outcome success ... → done
```

| Skill | New failure-record insertion(s) | New success-record step | New `$TASK_REF`/`$N` capture needed |
|---|---|---|---|
| `hb-task-create` | none (exempt) | new final step | none — uses `<name>` directly |
| `hb-task-step-add` | none (exempt) | new final step | yes — `$N` via `hb-sdk task step number <name>/<basename>` |
| `hb-task-step-plan` | none (exempt) | new final step | yes — both, added to §2 |
| `hb-task-step-execute` | §3 (`plan.md` missing) | new final step | yes — both, added to §2 |
| `hb-task-step-review-init` | none (exempt, shared subflow) | new final step | `$TASK_REF` only — `$N` already exists |
| `hb-task-step-review-address` | §5.7, §6 | new final step | `$TASK_REF` only, added to §2 — `$N` already exists |
| `hb-task-archive` | none (exempt) | new final step | none — uses `<name>` directly |
| `hb-task-unarchive` | none (exempt) | new final step | none — uses `<name>` directly |

**Alternatives considered and rejected:**

- *Have the invoking skill obtain the timestamp via a shell `date` call and
  pass `--timestamp`* — this was the prior revision of this plan; rejected per
  the ticket's revised AC2: it required a new `Bash(date *)` permission on 6
  of 8 skills and is an extra LLM-followable step that's easy to get wrong
  (capture, format, remember to pass through) for a value `hb-sdk` can trivially
  generate itself, deterministically, in one place.
- *Generate the timestamp as UTC (`datetime.now(timezone.utc)`, matching
  `hb_sdk/task.py`'s `created_at`)* — rejected: the ticket's AC2 explicitly
  asks for local time, timezone-aware, matching the *other* existing
  convention in this codebase (`cmd_task_step_execution_slug`).
  Timezone-aware ISO 8601 preserves the offset either way, so `state show`
  output remains unambiguous.
- *Add the state-write inside `review-init-subflow.md`* — rejected: breaks the
  subflow's documented "no side effects" contract for both callers; see design-
  decision box.
- *Record failure at every documented stop, including the 4 single-atomic-call
  skills' resolution errors* — rejected: no task/step is confirmed to exist at
  that point (same class as "invalid task name," which the ticket itself
  exempts); AC3's "where practical" is the escape hatch used here.
- *Derive `$N` for `hb-task-step-add` by regex-parsing the folder basename
  inline* — rejected in favor of reusing `hb-sdk task step number` (already the
  established pattern in review-init/review-address) — keeps parsing logic
  centralized in `hb_sdk`, not duplicated in prose.

---

## 2. Recording step — specification

### 2.1 `hb-sdk state record` CLI change (`skills/scripts/hb_sdk/state.py`)

- **Signature**, marked by change type:
  - `cmd_state_record(args) -> None` — **refactor (signature preserved)**; body
    changes (see below).
  - CLI flags: `--skill` (unchanged, required), `--outcome` (unchanged,
    required), `--task`/`--step` (unchanged, optional) — **`--timestamp`
    removed** (was required).
- **Algorithm**: replace `"timestamp": args.timestamp` with
  `"timestamp": datetime.now().astimezone().isoformat()`, computed at call
  time, inside `cmd_state_record`. Requires `from datetime import datetime`
  added to `state.py`'s imports (not currently imported there).
- **Failure/degradation contract**: unchanged — `write_state` still requires
  `.hb/` to exist (`path_hb_asserted()`) and dies with the existing message if
  not; nothing about the timestamp change alters that path.

```python
# skills/scripts/hb_sdk/state.py
from datetime import datetime  # new import
...
def cmd_state_record(args: argparse.Namespace) -> None:
    record = {
        "skill": args.skill,
        "outcome": args.outcome,
        "timestamp": datetime.now().astimezone().isoformat(),
        "task": args.task,
        "step": args.step,
    }
    write_state(record)
...
def def_cli_state(subs: Any) -> None:
    ...
    p_record.add_argument("--skill", required=True, metavar="<name>")
    p_record.add_argument("--outcome", required=True, metavar="<outcome>")
    # --timestamp argument removed
    p_record.add_argument("--task", metavar="<ref>")
    p_record.add_argument("--step", metavar="<ref>")
```

### 2.2 Skill-side shape (all 8 skills, success case)

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill <skill-name> --outcome success --task "<task-ref>" [--step "<step-ref>"]
```
- `<skill-name>` is the literal skill name (front-matter `name:` value, e.g. `hb-task-create`)
- `--step` included only for the 5 step-scoped skills
- reached only if every prior step completed without hitting a documented stop
- no timestamp argument — `hb-sdk` fills it in

### 2.3 Skill-side shape (failure insertions — only at the 3 non-exempt stops)

Inserted as new bullets/sub-steps immediately before the existing stop text,
which is otherwise copied verbatim:

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill <skill-name> --outcome failure --task "<task-ref>" --step "<step-ref>"
# then: <existing stop text, unchanged>
```

### 2.4 Ref derivation rules (new, reused across skills)

| Ref | Rule |
|---|---|
| Task ref, when input is `<name>` | Use `<name>` verbatim (already the exact string used elsewhere for `--task` in commit messages, e.g. `committing.md`'s `hb-001-init-commit-support` example) |
| Task ref, when input is `step_ref` | `step_ref` with the trailing `/<step_n>` segment removed (mirrors `_parse_step_ref`'s own `ref.rsplit("/", 1)` in `hb_sdk/task.py:207`) |
| Step ref, when `step_ref` is the skill input | `hb-sdk task step number <step_ref>` (already the established pattern — used in `hb-task-step-review-address.md` §2 and `review-init-subflow.md` §A) |
| Step ref, for `hb-task-step-add` (input is `<name>`, no `step_ref`) | Basename of the step folder path captured in its existing §3, then `hb-sdk task step number <name>/<basename>` |

**Failure/degradation contract:** if the flow stops at any *other* point not
listed in §1's table (e.g. an unexpected tool error mid-step, or a
user-declined prompt inside `committing.md`'s own subflow), no record is
written for that invocation — this is the existing, unchanged behavior
(matches AC3's "where practical": only the documented stops enumerated in §1
are touched).

**Conflict resolution:** N/A — `write_state` overwrites unconditionally; at
most one record call fires per invocation (every failure insertion is itself a
terminal stop, so success and failure recording are mutually exclusive within
one run).

---

## 3. Integration / wiring

- `skills/scripts/hb_sdk/state.py`: one function body edit (`cmd_state_record`)
  and one CLI-argument removal (`--timestamp`), plus a new `datetime` import.
  No other `hb_sdk` module changes.
- All 8 skill edits are to `skills/*.md` prose only. No `allowed-tools`
  front-matter changes anywhere (the self-generated-timestamp design needs no
  new shell permission).
- No build/dependency/lockfile effects — markdown files are consumed directly
  by the skill runner; `state.py` needs no new dependency (`datetime` is
  stdlib, already imported elsewhere in `hb_sdk`).
- `review-init-subflow.md` (the shared, injected subflow) is **not edited** —
  see design decision.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/scripts/hb_sdk/state.py` | **edit** — remove `--timestamp` CLI arg; `cmd_state_record` generates `datetime.now().astimezone().isoformat()` internally; add `datetime` import |
| `tests/skills/scripts/hb_sdk/helpers.py` | **edit** — remove the `--timestamp` pass-through block from `state_record()` (lines 115-116) |
| `tests/skills/scripts/hb_sdk/test_hb_sdk_state.py` | **edit** — remove all `timestamp=...` kwargs from `state_record()` calls; delete `test_state_record_requires_timestamp`; replace exact-timestamp-string assertions with format/timezone-awareness checks (full list in §5) |
| `skills/hb-task-create.md` | **edit** — add new `### 6. Record execution state` (success-only) after existing `### 5. Prompt user`, before `## Output` |
| `skills/hb-task-step-add.md` | **edit** — add new `### 6. Record execution state` (success-only, derives `$N` via `hb-sdk task step number`) after existing `### 5. Prompt user` |
| `skills/hb-task-step-plan.md` | **edit** — extend `### 2. Resolve step folder` with `$N`/`$TASK_REF` capture; add new `### 7. Record execution state` (success-only) after existing `### 6. Prompt user` |
| `skills/hb-task-step-execute.md` | **edit** — extend `### 2. Resolve step folder` with `$N`/`$TASK_REF` capture; insert failure-record bullet into `### 3. Read plan`'s existing abort path (text unchanged otherwise); add new `### 8. Record execution state` (success-only) after existing `### 7. Prompt user` |
| `skills/hb-task-step-review-init.md` | **edit** — add new `### 7. Record execution state` (success-only, derives `$TASK_REF` inline; `$N` already available from the shared subflow) after existing `### 6. Commit` |
| `skills/hb-task-step-review-address.md` | **edit** — extend `### 2. Resolve step folder` with `$TASK_REF` capture (`$N` already captured there); insert failure-record bullets into step 5's existing item 7 stop and step 6's existing ambiguous-conflict stop (text unchanged otherwise); add new `### 11. Record execution state` (success-only) after existing `### 10. Prompt user` |
| `skills/hb-task-archive.md` | **edit** — add new `### 5. Record execution state` (success-only) after existing `### 4. Prompt user` |
| `skills/hb-task-unarchive.md` | **edit** — add new `### 5. Record execution state` (success-only) after existing `### 4. Prompt user` |
| `skills/references/review-init-subflow.md` | **untouched** — deliberately, per design decision |
| `skills/scripts/hb_sdk/task.py`, `commit.py`, `idea.py`, `init_cmd.py`, `summarize.py` | **untouched** — out of scope |

No dependency-manifest or lockfile changes.

---

## 5. Tests

Two kinds of test surface here: the existing `hb_sdk` pytest suite (needs
updating because of the `--timestamp` CLI change) and a live dry-run of the 8
edited skill `.md` flows (no test framework exists for those — same as the
prior revision of this plan).

**`tests/skills/scripts/hb_sdk/test_hb_sdk_state.py` — exact edits:**

| Test | Change |
|---|---|
| `test_state_record_writes_json_file` | drop `timestamp=` kwarg; replace the dict-equality assertion's timestamp expectation with: pop `"timestamp"` from `data` before comparing the other 4 keys, then assert `datetime.fromisoformat(data["timestamp"]).tzinfo is not None` |
| `test_state_record_with_task_and_step` | drop `timestamp=` kwarg; no other change (doesn't assert on timestamp) |
| `test_state_record_overwrites_prior_record` | drop `timestamp=` kwarg from both calls; no other change |
| `test_state_record_no_hb` | drop `timestamp=` kwarg |
| `test_state_record_requires_skill` | drop `timestamp=` kwarg |
| `test_state_record_requires_outcome` | drop `timestamp=` kwarg |
| `test_state_record_requires_timestamp` | **delete** — the flag no longer exists, so there's nothing to require |
| `test_state_show_json_after_record` | drop `timestamp=` kwarg; replace `assert data["timestamp"] == "..."` with the same `fromisoformat`/`tzinfo` check as above |
| `test_state_show_md_after_record` | drop `timestamp=` kwarg; replace `assert "2026-01-01T00:00:00Z" in result.stdout` with a regex check that a `Timestamp: <non-empty ISO-looking value>` line is present, e.g. `re.search(r"Timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result.stdout)` |
| `test_state_json_not_reported_by_git_status` | drop `timestamp=` kwarg |

Add one new test: **`test_state_record_generates_own_timestamp`** — call
`state_record(tmp_path, skill="skill-a", outcome="success")` with no timestamp
at all, assert it succeeds (`returncode == 0`), and assert the recorded
`timestamp` parses via `datetime.fromisoformat` with a non-`None` `tzinfo`
(proves both "self-generated" and "timezone-aware, not naive UTC").

**Skill `.md` dry-run cases** (fixture strategy: a scratch task under
`.hb/task/active/`, disposable, cleaned up after):

- **Happy path**, one per skill: run each of the 8 skills to completion; after
  each, `hb-sdk state show --format md` must show that skill's name, the
  correct ref(s), `Outcome: success`, and a non-empty `Timestamp:` line.
- **The motivating case**: run `hb-task-step-execute` against a step with no
  `plan.md` — confirm `Outcome: failure` is recorded with correct task+step
  refs, and the abort message text is byte-identical to the current
  (pre-change) message.
- **Review-address failure paths**: run `hb-task-step-review-address` against
  a step whose `review.md` has no filled-in concerns — confirm `failure` is
  recorded before the "no review concerns yet" message. Construct (or find/
  simulate) an ambiguous-ID case for §6's conflict stop and confirm the same.
- **Negative cases (exemptions must NOT record)**: run `hb-task-create` with
  an invalid name, `hb-task-step-add`/`hb-task-archive`/`hb-task-unarchive`
  against a nonexistent task, and `hb-task-step-review-init` against a step
  ref that doesn't exist — confirm `.hb/.state.ignore.json` is untouched (or
  unchanged from its pre-run value) in every case.
- **Non-regression**: `test_hb_sdk_task.py`, `test_hb_sdk_commit.py`,
  `test_hb_sdk_init.py`, `test_hb_sdk_idea.py`, `test_hb_sdk_summarize.py` must
  all stay green **unmodified** — this step's only Python edits are in
  `state.py` and its own test file.

---

## 6. Verification (after implementation)

1. Run the full pytest suite (`pytest tests/`) — `test_hb_sdk_state.py` reflects
   the edits in §5 and passes; all other test files stay green unmodified.
2. Capture the pre-change baseline: run `hb-sdk state show --format json`
   before touching any skill file — expect `{}` (no prior record), or note
   whatever is currently there, to diff against post-change runs.
3. For each of the 8 skills, in a scratch task/step: run it to a normal
   completion, then run `hb-sdk state show --format md` and confirm `Skill:`,
   `Task:`, `Step:` (where applicable), `Outcome: success`, and a populated
   `Timestamp:` match expectations from §2's ref-derivation table.
4. Per-AC checks:
   - AC1/AC1.1/AC1.2: grep each of the 8 `.md` files for the new
     `state record` invocation; confirm step-scoped ones pass both `--task`
     and `--step`, task-scoped ones pass `--task` only, and none pass
     `--timestamp`.
   - AC2: confirm `state.py`'s CLI has no `--timestamp` argument
     (`hb-sdk state record --help` should not list it); confirm
     `cmd_state_record` uses `datetime.now().astimezone()` (local,
     timezone-aware), not `datetime.now(timezone.utc)`; confirm no skill `.md`
     file contains a `date` shell invocation or a new `Bash(date *)`
     front-matter entry.
   - AC3: exercise the 3 non-exempt failure paths (§5's failure cases) and
     confirm `failure` is recorded; exercise the exempt paths and confirm
     nothing is recorded — both documented explicitly in the relevant skill
     files (grep for "exempt").
   - AC4: covered by step 3 above (skill/ref/outcome/timestamp all present).
   - AC5: diff each edited skill file against its pre-change version — every
     existing line of prose/commands must appear unchanged; only new
     lines/steps are added (no `allowed-tools` changes at all this revision).
5. Invariant check: `.hb/.state.ignore.json` remains valid JSON with exactly
   the 5 keys `skill`/`outcome`/`timestamp`/`task`/`step` after every run, and
   `timestamp` always parses as a timezone-aware ISO 8601 string — spot-check
   with `hb-sdk state show --format json` piped through
   `python3 -c "import json,sys,datetime; d=json.load(sys.stdin); assert datetime.datetime.fromisoformat(d['timestamp']).tzinfo"`.
6. Scope check: `git diff --stat` shows changes only under `skills/*.md`,
   `skills/scripts/hb_sdk/state.py`, and
   `tests/skills/scripts/hb_sdk/{helpers.py,test_hb_sdk_state.py}` — no changes
   under `skills/references/review-init-subflow.md` or any other `hb_sdk`
   module/test file.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.2/§2.3, §4 (all 8 skill files) | Exact CLI shape (no `--timestamp`) and per-skill file changes |
| 1.1 | §2.4 ref-derivation table, §4 (5 step-scoped files) | `--task` + `--step` both included |
| 1.2 | §2.4 ref-derivation table, §4 (3 task-scoped files) | `--task` only |
| 2 | §2.1 (`state.py` change), §0 (existing local-tz convention), §6 step 4 | Self-generated, local-time, timezone-aware; no skill shells out or needs new permissions |
| 3 | §1 design-decision box, §1 table, §4 (step-execute §3, review-address §5.7/§6) | 3 non-exempt insertions; 3 documented exemption classes |
| 4 | §5 happy-path cases, §6 step 3 | `state show` reflects skill/ref/outcome/timestamp after each of the 8 |
| 5 | §0.2 non-regression table, §6 step 4 (AC5 diff check) | Additive-only for the 8 skills; existing text/behavior byte-identical |

---

## 8. Out of scope (per ticket)

- Changes to `hb-sdk state`'s `--skill`/`--outcome`/`--task`/`--step` handling,
  or to `hb-sdk state show` — already delivered in `hb-014/step-0`. (Only the
  timestamp source moves from caller-supplied to self-generated, per AC2 —
  the one code change this step makes.)
- Deriving or displaying a recommended next action from the recorded state —
  deferred to the next step.
- `hb-init`, `hb-status`, `hb-ticket-discuss` — excluded per the ticket's
  Background (no task/step execution state to record).
- Editing `skills/references/review-init-subflow.md` — deliberately untouched
  to preserve its documented side-effect-free contract (see design decision).
