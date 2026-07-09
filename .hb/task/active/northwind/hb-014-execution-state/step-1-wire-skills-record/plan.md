# Step 1 Plan — Wire `hb-sdk state record` into the 8 state-changing skills

This step wires the previously-shipped `hb-sdk state record`/`hb-sdk state show`
primitive (added in step-0) into the 8 `hb-*` skills whose `.md` files currently
never call it — today `${CLAUDE_SKILL_DIR}/scripts/hb_sdk/state.py` exists and is
unit-tested (`tests/skills/scripts/hb_sdk/test_hb_sdk_state.py`) but no skill
invokes it, so `.hb/.state.ignore.json` is never written and `hb-sdk state show`
always reports "No recorded state." even after running e.g. `/hb-task-create`.
This is a **prose-instruction change only** — every edit lands in `skills/*.md`
front-matter/body; no `hb_sdk` Python module changes. Scope boundary: additive
only — every existing step's behavior, wording of error messages, and commit
mechanics are unchanged; the only new externally observable effect is that
`.hb/.state.ignore.json` (gitignored, per `ensure_gitignore_entry`) reflects the
last-executed skill/ref/outcome/timestamp after each of the 8 skills runs.

Source ticket: `./ticket.md`. Builds on the **shipped** `hb-sdk state record`/
`hb-sdk state show` CLI and `write_state`/`read_state` (`skills/scripts/hb_sdk/state.py`,
delivered in `hb-014/step-0`) and the existing 8 skill `.md` files as they exist
**now** (`skills/hb-task-create.md`, `hb-task-step-add.md`, `hb-task-step-plan.md`,
`hb-task-step-execute.md`, `hb-task-step-review-init.md`,
`hb-task-step-review-address.md`, `hb-task-archive.md`, `hb-task-unarchive.md`).

> **Design decision — three exemptions from "record failure on every documented
> stop."** The ticket (AC3) allows exempting error paths that "stop before any
> task/step is resolved," and says to add failure-recording "where practical."
> Three concrete calls, made from reading the actual `.md` flows and
> `hb_sdk/task.py`:
>
> 1. **Single-atomic-call skills** (`hb-task-create`, `hb-task-step-add`,
>    `hb-task-archive`, `hb-task-unarchive`) each have exactly one documented
>    error path, and it's the *same* `hb-sdk` call that both resolves and
>    mutates the task/step (e.g. `hb-sdk task create` validates the name AND
>    creates the folder in one shot). Nothing is confirmed to exist before that
>    call succeeds, so — same class as the ticket's own "invalid task name"
>    example — these are fully exempt. Result: these 4 skills get **only** a
>    success-path record step, no failure path.
> 2. **The shared `review-init-subflow.md`** (injected into both
>    `hb-task-step-review-init` and `hb-task-step-review-address`) is explicitly
>    documented as side-effect-free ("Contains no side effects (no user
>    notification, no commit)"). Adding a state-write inside it would break that
>    documented contract for both callers asymmetrically. Its two internal stops
>    (step-ref-not-found; drifted `review.md`) are therefore exempt — documented
>    inline in both skills' new record step so the exemption is traceable, not
>    silent.
> 3. Everywhere else, if a step already resolved a task+step ref (via
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
  wired into `skills/scripts/hb_sdk/__main__.py` via `def_cli_state`. CLI:
  `hb-sdk state record --skill <name> --outcome <outcome> --timestamp <ts> [--task <ref>] [--step <ref>]`
  (all of `--skill`, `--outcome`, `--timestamp` required; `--task`/`--step`
  optional, free-form strings — no format validation). `write_state` fully
  **overwrites** `.hb/.state.ignore.json` each call (flat record, no history) —
  confirmed at `skills/scripts/hb_sdk/state.py:11-17`.
- `hb-sdk task step number <step_ref>` (used already in
  `hb-task-step-review-address.md` §2 and the shared `review-init-subflow.md`
  §A) is a pure string-format parser (`_parse_step_ref`,
  `skills/scripts/hb_sdk/task.py:206-225`) — it does **not** touch disk, so it's
  safe to call for ref-derivation without any existence risk, including right
  after a step folder was just created.
- **None of the 8 skills currently allow a bare shell `date` call.** Checked
  every front-matter `allowed-tools:` line:

  | Skill | Current `allowed-tools` (Bash entries) | `date` already allowed? |
  |---|---|---|
  | `hb-task-create` | `Bash(hb-sdk *) Bash(git *)` | No |
  | `hb-task-step-add` | `Bash(hb-sdk *) Bash(git *)` | No |
  | `hb-task-step-plan` | `Bash(hb-sdk *) Bash(git *)` | No |
  | `hb-task-step-execute` | `Bash(hb-sdk *) Bash(git *) Bash(*)` | **Yes** (`Bash(*)`) |
  | `hb-task-step-review-init` | `Bash(hb-sdk *) Bash(git *)` | No |
  | `hb-task-step-review-address` | `Bash(hb-sdk *) Bash(git *) Bash(*)` | **Yes** (`Bash(*)`) |
  | `hb-task-archive` | `Bash(hb-sdk *) Bash(git *)` | No |
  | `hb-task-unarchive` | `Bash(hb-sdk *) Bash(git *)` | No |

  AC2 requires the timestamp to come from a shell `date` call (keeping
  `hb-sdk` itself deterministic, per the prior step's design). This means 6 of
  8 skills need one new front-matter entry — `Bash(date *)` — a minimal,
  scoped grant matching the codebase's existing per-binary permission style
  (`Bash(git *)`, `Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *)`). This was not
  called out in the ticket; it's a necessary consequence of AC2 discovered by
  reading the actual front-matter.
- `.hb/.state.ignore.json` is gitignored (`ensure_gitignore_entry`,
  `skills/scripts/hb_sdk/common.py:87-106`, wired from `hb-init`). Confirmed via
  `git log`: commit `62f7d87` renamed the state file specifically to
  `.state.ignore.json` for this reason. **Consequence: the new record step never
  needs `git add`/commit** — it's a side effect entirely outside git, so it
  cannot interact with any skill's existing "Commit" step or its file-staging
  rules. Ordering relative to Commit is therefore a documentation nicety, not a
  functional constraint — placed last (after Prompt user) in every skill, per
  the ticket's own phrasing ("after its existing terminal steps").
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
| Run any of the 8 skills to completion | `.hb/.state.ignore.json` untouched; `hb-sdk state show` unaffected | Exactly one `hb-sdk state record --outcome success ...` call at the very end; `hb-sdk state show` reflects that skill/ref |
| `hb-task-step-execute` when `plan.md` is missing | Aborts with existing error message only | Records `--outcome failure` (task+step ref) immediately before the same, unchanged abort message |
| `hb-task-step-review-address` when no review concerns exist yet (§5.7), or an ID conflict is unresolvable (§6) | Stops with existing message only | Records `--outcome failure` (task+step ref) immediately before the same, unchanged stop message |
| The 4 single-atomic-call skills' error paths; the shared review subflow's 2 internal stops | No record | Still no record — exempt by design (see decision box above) |

Kind of change: purely additive (new steps + new bullets inserted before
existing stop text; front-matter gains one new `Bash(date *)` entry in 6
files). No existing instruction's wording, ordering among *existing* steps, or
commit/prompt behavior changes.

### 0.2 Non-regression proof

Purely additive — nothing removed, no existing bullet's text edited, no
existing step renumbered out of its current position (new steps are always
appended after the last existing step, or inserted as new bullets *before* an
existing stop's unchanged text). Risk table:

| Case | Current behavior | Why it can't change |
|---|---|---|
| Existing error/abort message text (step-execute §3, review-address §5.7/§6) | Exact wording documented in ticket AC3/AC5 | New record call is a preceding instruction, not a text edit — the abort/stop sentence is copied verbatim |
| Existing `allowed-tools` entries (`hb-sdk *`, `git *`, `Bash(*)`, `Read`/`Write`/`Edit`) | Unchanged | Only a new entry (`Bash(date *)`) is appended; nothing removed, so no existing permission narrows |
| Commit step file-staging | Unchanged | State file is gitignored (§0 above) — record step never touches `git add`/`git status`, so it cannot add unrelated files to a commit |
| `hb_sdk` Python behavior (`state.py`, `task.py`) | Unchanged | Zero code changes in this step — verified by `tests/skills/scripts/hb_sdk/test_hb_sdk_state.py` and `test_hb_sdk_task.py` staying green with no edits |

---

## 1. Design overview

One new instruction shape, "Record execution state," gets inserted at exactly
one place per skill (the true end, after Commit/Prompt), plus 0–2 new "record
failure, then stop" insertions per skill where a documented stop already
exists after a ref was resolved. No branching/precedence logic is introduced —
this is a fixed sequence per skill:

```
[existing skill flow, unchanged] → [resolve $TASK_REF / $N if not already available]
  → (only at pre-existing documented stops that occur after refs are resolved:
      date → hb-sdk state record --outcome failure → existing stop, unchanged)
  → [flow reaches its natural end] → date → hb-sdk state record --outcome success → done
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

- *Have `hb-sdk state record` generate its own timestamp internally* — rejected: AC2 explicitly requires the agent-supplied `date` call so `hb-sdk` stays deterministic (the prior step's design decision); also out of scope (no `hb_sdk` code changes).
- *Add the state-write inside `review-init-subflow.md`* — rejected: breaks the subflow's documented "no side effects" contract for both callers; see design-decision box.
- *Record failure at every documented stop, including the 4 single-atomic-call skills' resolution errors* — rejected: no task/step is confirmed to exist at that point (same class as "invalid task name," which the ticket itself exempts); AC3's "where practical" is the escape hatch used here.
- *Derive `$N` for `hb-task-step-add` by regex-parsing the folder basename inline* — rejected in favor of reusing `hb-sdk task step number` (already the established pattern in review-init/review-address) — keeps parsing logic centralized in `hb_sdk`, not duplicated in prose.

---

## 2. Recording step — specification

**Shape (all 8 skills, success case):**

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```
- capture stdout as `$TS`

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill <skill-name> --outcome success --task "<task-ref>" [--step "<step-ref>"] --timestamp "$TS"
```
- `<skill-name>` is the literal skill name (front-matter `name:` value, e.g. `hb-task-create`)
- `--step` included only for the 5 step-scoped skills
- reached only if every prior step completed without hitting a documented stop

**Shape (failure insertions — only at the 3 non-exempt stops):**

Inserted as new bullets/sub-steps immediately before the existing stop text,
which is otherwise copied verbatim:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"   # capture as $TS
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state record --skill <skill-name> --outcome failure --task "<task-ref>" --step "<step-ref>" --timestamp "$TS"
# then: <existing stop text, unchanged>
```

**Ref derivation rules (new, reused across skills):**

| Ref | Rule |
|---|---|
| Task ref, when input is `<name>` | Use `<name>` verbatim (already the exact string used elsewhere for `--task` in commit messages, e.g. `committing.md`'s `hb-001-init-commit-support` example) |
| Task ref, when input is `step_ref` | `step_ref` with the trailing `/<step_n>` segment removed (mirrors `_parse_step_ref`'s own `ref.rsplit("/", 1)` in `hb_sdk/task.py:207`) |
| Step ref, when `step_ref` is the skill input | `hb-sdk task step number <step_ref>` (already the established pattern — used in `hb-task-step-review-address.md` §2 and `review-init-subflow.md` §A) |
| Step ref, for `hb-task-step-add` (input is `<name>`, no `step_ref`) | Basename of the step folder path captured in its existing §3, then `hb-sdk task step number <name>/<basename>` |

**Failure/degradation contract:** if the flow stops at any *other* point not
listed in the table in §1 (e.g. an unexpected tool error mid-step, or a
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

- All edits are to `skills/*.md` prose/front-matter only. No call sites in
  `hb_sdk` Python code change.
- Front-matter `allowed-tools:` gains one new space-separated entry,
  `Bash(date *)`, appended after the existing `Bash(git *)` entry, in:
  `hb-task-create.md`, `hb-task-step-add.md`, `hb-task-step-plan.md`,
  `hb-task-step-review-init.md`, `hb-task-archive.md`, `hb-task-unarchive.md`.
  `hb-task-step-execute.md` and `hb-task-step-review-address.md` already carry
  `Bash(*)` — no change needed there.
- No build/dependency/lockfile effects — these are markdown files consumed
  directly by the skill runner; nothing to compile.
- `review-init-subflow.md` (the shared, injected subflow) is **not edited** —
  see design decision.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-task-create.md` | **edit** — append `Bash(date *)` to `allowed-tools`; add new `### 6. Record execution state` (success-only) after existing `### 5. Prompt user`, before `## Output` |
| `skills/hb-task-step-add.md` | **edit** — append `Bash(date *)` to `allowed-tools`; add new `### 6. Record execution state` (success-only, derives `$N` via `hb-sdk task step number`) after existing `### 5. Prompt user` |
| `skills/hb-task-step-plan.md` | **edit** — append `Bash(date *)` to `allowed-tools`; extend `### 2. Resolve step folder` with `$N`/`$TASK_REF` capture; add new `### 7. Record execution state` (success-only) after existing `### 6. Prompt user` |
| `skills/hb-task-step-execute.md` | **edit** — extend `### 2. Resolve step folder` with `$N`/`$TASK_REF` capture; insert failure-record bullets into `### 3. Read plan`'s existing abort path (text unchanged otherwise); add new `### 8. Record execution state` (success-only) after existing `### 7. Prompt user`. No `allowed-tools` change — already has `Bash(*)` |
| `skills/hb-task-step-review-init.md` | **edit** — append `Bash(date *)` to `allowed-tools`; add new `### 7. Record execution state` (success-only, derives `$TASK_REF` inline; `$N` already available from the shared subflow) after existing `### 6. Commit` |
| `skills/hb-task-step-review-address.md` | **edit** — extend `### 2. Resolve step folder` with `$TASK_REF` capture (`$N` already captured there); insert failure-record bullets into step 5's existing item 7 stop and step 6's existing ambiguous-conflict stop (text unchanged otherwise); add new `### 11. Record execution state` (success-only) after existing `### 10. Prompt user`. No `allowed-tools` change — already has `Bash(*)` |
| `skills/hb-task-archive.md` | **edit** — append `Bash(date *)` to `allowed-tools`; add new `### 5. Record execution state` (success-only) after existing `### 4. Prompt user` |
| `skills/hb-task-unarchive.md` | **edit** — append `Bash(date *)` to `allowed-tools`; add new `### 5. Record execution state` (success-only) after existing `### 4. Prompt user` |
| `skills/references/review-init-subflow.md` | **untouched** — deliberately, per design decision (shared, documented side-effect-free) |
| `skills/scripts/hb_sdk/*.py` | **untouched** — out of scope per ticket |

No dependency-manifest or lockfile changes — none exist for this project's
markdown-only skill definitions.

---

## 5. Tests

This step edits agent-facing skill instructions (markdown prose), not
executable code — there is no unit-test framework for `.md` skill flows (the
existing `tests/skills/scripts/hb_sdk/*.py` suite covers only `hb_sdk` Python,
which is untouched here). Verification is therefore a live dry-run of each
skill exercising the paths in §1's table, checked against `hb-sdk state show`.

Fixture strategy: use a scratch task under `.hb/task/active/` (the existing
`northwind/hb-014-execution-state` task itself, or a disposable throwaway task
created for the dry-run, cleaned up after) so runs are hermetic and don't
pollute unrelated task history. Cases to exercise (mapped to §6 below):

- **Happy path**, one per skill: run each of the 8 skills to completion; after
  each, `hb-sdk state show --format md` must show that skill's name, the
  correct ref(s), and `Outcome: success`.
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
- **Non-regression**: `tests/skills/scripts/hb_sdk/test_hb_sdk_task.py`,
  `test_hb_sdk_state.py`, `test_hb_sdk_commit.py`, `test_hb_sdk_init.py`,
  `test_hb_sdk_idea.py`, `test_hb_sdk_summarize.py` must all stay green
  unmodified — this step makes zero `hb_sdk` code changes.

---

## 6. Verification (after implementation)

1. Run the full pytest suite (`pytest tests/`) — must be unchanged/green,
   confirming zero regressions in `hb_sdk` (this step touches no Python).
2. Capture the pre-change baseline: run `hb-sdk state show --format json`
   before touching any skill file — expect `{}` (no prior record), or note
   whatever is currently there, to diff against post-change runs.
3. For each of the 8 skills, in a scratch task/step: run it to a normal
   completion, then run `hb-sdk state show --format md` and confirm `Skill:`,
   `Task:`, `Step:` (where applicable), and `Outcome: success` match
   expectations from §2's ref-derivation table.
4. Per-AC checks:
   - AC1/AC1.1/AC1.2: grep each of the 8 `.md` files for the new
     `state record` invocation; confirm step-scoped ones pass both `--task`
     and `--step`, task-scoped ones pass `--task` only.
   - AC2: grep for the `date -u +"%Y-%m-%dT%H:%M:%SZ"` capture preceding each
     `state record` call; confirm `hb_sdk/state.py` has no new
     `datetime.now()`-style call (still deterministic).
   - AC3: exercise the 3 non-exempt failure paths (§5's negative/failure
     cases) and confirm `failure` is recorded; exercise the exempt paths and
     confirm nothing is recorded — both documented explicitly in the relevant
     skill files (grep for "exempt").
   - AC4: covered by step 3 above.
   - AC5: diff each edited skill file against its pre-change version — every
     existing line of prose/commands must appear unchanged; only new
     lines/steps and the one new `allowed-tools` entry are added.
5. Invariant check: `.hb/.state.ignore.json` remains valid JSON with exactly
   the 5 keys `skill`/`outcome`/`timestamp`/`task`/`step` after every run
   (matches `state.py:29-37`'s `cmd_state_record` shape) — spot-check with
   `hb-sdk state show --format json`.
6. Scope check: `git diff --stat` shows changes only under `skills/*.md` (the
   8 files in §4) — no changes under `skills/scripts/hb_sdk/`,
   `skills/references/review-init-subflow.md`, or `tests/`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2, §4 (all 8 files) | Exact CLI shape and per-skill file changes |
| 1.1 | §2 ref-derivation table, §4 (5 step-scoped files) | `--task` + `--step` both included |
| 1.2 | §2 ref-derivation table, §4 (3 task-scoped files) | `--task` only |
| 2 | §2 (`date -u ...` capture), §0 (allowed-tools gap + fix) | Timestamp from shell `date`, `hb_sdk` untouched |
| 3 | §1 design-decision box, §1 table, §4 (step-execute §3, review-address §5.7/§6) | 3 non-exempt insertions; 3 documented exemption classes |
| 4 | §5 happy-path cases, §6 step 3 | `state show` reflects skill/ref/outcome after each of the 8 |
| 5 | §0.2 non-regression table, §6 step 4 (AC5 diff check) | Additive-only; existing text/behavior byte-identical |

---

## 8. Out of scope (per ticket)

- Any change to `hb_sdk/state.py` or the `state` CLI itself — already shipped
  in `hb-014/step-0`.
- Deriving or displaying a recommended next action from the recorded state —
  deferred to the next step.
- `hb-init`, `hb-status`, `hb-ticket-discuss` — excluded per the ticket's
  Background (no task/step execution state to record).
- Editing `skills/references/review-init-subflow.md` — deliberately untouched
  to preserve its documented side-effect-free contract (see design decision).
