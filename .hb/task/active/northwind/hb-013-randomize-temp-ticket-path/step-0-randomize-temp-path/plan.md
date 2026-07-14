# Step 0 Plan — Randomize the Interactive-Ticket Temp Path

One-paragraph framing: today, `interactive-ticket-subflow.md` always writes an
in-progress ticket draft to the literal path `/tmp/ticket.md`, and both of its
declared callers (`hb-task-create`, `hb-task-step-add`) hardcode that same
fixed path before invoking it. Two sessions running the interactive ticket
flow concurrently collide on this one file — session B's write can clobber
session A's in-flight draft before A finishes reading it back. This step
makes the subflow self-resolve a per-invocation target directory (a
harness-declared session scratch dir when one is detectable, else a
hand-rolled unique dir under `/tmp` via `mktemp -d`), and updates the two
named callers to stop hardcoding `/tmp`. Behavior change only for interactive
mode; skeleton-only and `--ticket <path>`-supplied modes are untouched. Once
this lands, two concurrent interactive-ticket sessions each get their own
writable, non-colliding path.

Source ticket: `./ticket.md`. This is step 0 of `hb-013` — no prior steps to
build on. This plan targets `skills/references/interactive-ticket-subflow.md`,
`skills/hb-task-create.md`, and `skills/hb-task-step-add.md` as they exist
now.

> **Design decision — make `$TARGET_PATH` optional in the subflow's caller
> contract, rather than removing it.** `interactive-ticket-subflow.md`'s own
> header (line 1) claims it is "Shared by `hb-task-create` and
> `hb-task-step-add`" — matching the ticket's Background, which only names
> those two. But `skills/references/describe-ticket-subflow.md:13` (part of
> `hb-ticket-discuss`, not mentioned in the ticket) is a **third, undocumented
> caller** that already resolves its own collision-avoidant `$TARGET_PATH`
> (via a per-loop `$TICKET_SEQ` counter, see §0) and passes it in explicitly.
> If the subflow's contract *required* `$TARGET_PATH` to be absent (letting
> the subflow always self-resolve), this third caller would break. Resolution:
> `$TARGET_PATH` becomes an **optional** caller input — if supplied (as
> `describe-ticket-subflow.md` does), the subflow uses it unchanged and skips
> resolution entirely; if omitted (the new behavior for the two ticket-named
> callers), the subflow resolves one itself. This is zero-touch for the third
> caller and satisfies the ticket's two named callers. See §1 (design) and §7
> (AC traceability).

---

## 0. Current-state facts (verified during planning)

- The hardcoded path appears in exactly three places, confirmed by reading
  each file directly:
  - `skills/references/interactive-ticket-subflow.md:7` (caller-contract doc)
    and `:53`, `:55` (write step) — all reference `$TARGET_PATH`, a value the
    *caller* is documented as responsible for resolving.
  - `skills/hb-task-create.md:55–63` — Step 2, case 3 ("Neither flag —
    interactive mode"): sets `$TARGET_PATH` = `/tmp` literally, passes it to
    the subflow, then hardcodes `$WRITTEN_TICKET` = `/tmp/ticket.md`.
  - `skills/hb-task-step-add.md:56–64` — byte-for-byte the same pattern at the
    same relative lines.
- **Undocumented third caller** (not named in the ticket): `describe-ticket-
  subflow.md:12–13` — `hb-ticket-discuss`'s loop action — sets `$TARGET_PATH`
  = `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` (a fresh subfolder per loop
  iteration, using its own in-memory sequence counter) and *then* follows
  `interactive-ticket-subflow.md` with that value. It does not rely on the
  subflow to resolve anything — it already supplies a non-default
  `$TARGET_PATH`. `load-ticket-subflow.md:79–85` follows the identical
  write-to-`$TARGET_PATH/ticket.md` pattern inline (does not invoke the shared
  subflow, so it is unaffected by this step either way).
- **Permission-glob precedent removes a concern about nested paths.** Both
  named callers' frontmatter restricts file tools to
  `Write(//tmp/*) Write(//private/tmp/*) Read(//tmp/*) Read(//private/tmp/*)
  Edit(//tmp/*) Edit(//private/tmp/*)` (`hb-task-create.md:9`,
  `hb-task-step-add.md:9`). `hb-ticket-discuss.md:12–17` carries the identical
  glob set, yet its `describe-ticket-subflow.md` already writes to a
  **two-segment-deeper** path today (`/tmp/hb-ticket-discuss/ticket-N/
  ticket.md`) without any special-casing — proving `//tmp/*` already matches
  multi-segment paths nested under `/tmp`, not just direct children. A new
  `mktemp -d /tmp/<random>` subdirectory therefore needs **no** `allowed-tools`
  changes in either named caller.
- **No portable env-var signal exists for a harness-declared scratch dir.**
  Checked live in this session: `$TMPDIR` = `/var/folders/.../T/` (the plain
  macOS default), while the actual Claude-Code-provided session scratch
  directory (visible only as in-session "Scratchpad Directory" guidance text)
  is a different path under `/private/tmp/claude-<pid>/...`. So detection
  cannot be a shell/env-var check — it has to be the *agent* (the one
  executing these prose instructions) checking its own operating
  context/instructions for such guidance, which is inherently harness-generic
  phrasing rather than a scriptable probe.
- No automated test exercises these markdown skill/subflow files — confirmed
  via `grep -rln "interactive-ticket-subflow\|TARGET_PATH" tests/` (no
  matches). `tests/skills/scripts/hb_sdk/` covers only the Python `hb_sdk`
  CLI. Verification here is manual/textual (§6), consistent with prior
  doc-only steps (e.g. `hb-016/step-3`).

### 0.1 Impact (before → after)

| Case | Before | After |
|---|---|---|
| `hb-task-create` / `hb-task-step-add`, interactive mode | Always `/tmp/ticket.md` — two concurrent sessions collide | Subflow-resolved path: a harness session-scratch dir if detected, else a fresh `mktemp -d /tmp/hb-ticket.XXXXXXXX` dir — no two invocations share a path |
| `describe-ticket-subflow.md` (`hb-ticket-discuss`) | Supplies its own `$TARGET_PATH` | Unchanged — still supplies its own `$TARGET_PATH`; subflow's new resolution logic never runs for this caller |
| Skeleton-only / `--ticket <path>`-supplied modes (all callers) | Subflow's guard clause (Section A) skips the whole subflow | Unchanged — guard clause untouched, still skips before any path resolution |

Additive/behavior-preserving except for the one targeted case (interactive
mode in the two named callers), which changes from a fixed collision-prone
path to a resolved collision-free one.

### 0.2 Non-regression proof

| Case | Current behavior | Why it can't change |
|---|---|---|
| `describe-ticket-subflow.md` / `load-ticket-subflow.md` | Each resolves and passes its own `$TARGET_PATH` | New subflow logic (§2) only activates when `$TARGET_PATH` is *not* supplied — an explicitly-supplied value always short-circuits it (§1 design decision) |
| Guard clause (Section A: `$TICKET_SUPPLIED` / `$NO_INTERACTIVE`) | Skips subflow entirely for skeleton-only / `--ticket`-supplied modes | Not edited — new resolution step is inserted *after* the existing guard, only reached when the guard already continues |
| Ticket content/structure produced (Sections B–C: prompt, transform rules) | Background / Acceptance Criteria / Out-of-scope derivation | Not edited — only the target *path*, not the write-step content, changes (per ticket's own Out-of-scope) |

Change is confined to path resolution; the guard, prompt, transform, and
write-content logic are untouched.

---

## 1. Design overview

Single linear change with one two-tier precedence for path resolution, added
as a new sub-section inside the already-shared subflow (so it lives in
exactly one place, per AC 3.3):

```
precedence:  harness-declared session scratch dir  >  hand-rolled mktemp fallback
             (tie-break: N/A — mutually exclusive; fallback only runs when no
             harness-declared dir is detected)
```

- **Tier 1 — harness-declared session dir.** Phrased generically in the
  subflow itself: "if the current operating context/instructions document a
  session-specific scratch or temporary directory (any convention — for
  example, some harnesses surface this as in-session 'Scratchpad Directory'
  guidance), use it." This names no single harness's mechanism as
  load-bearing — it is guidance for whichever agent is executing the
  instructions to check its own context, satisfying AC 3 (harness-agnostic).
- **Tier 2 — hand-rolled fallback.** `mktemp -d /tmp/hb-ticket.XXXXXXXX`
  creates a fresh, uniquely-named directory directly under `/tmp` (confirmed
  live: `mktemp /tmp/ticket.XXXXXXXX.md` → `/tmp/ticket.a1B2c3.md`-shaped
  output, exits 0). Six template `X`s give mktemp ~56.8 billion possible
  names, making same-instant collisions between two independent invocations
  effectively impossible.
- Both tiers hand back a **directory** (`$TARGET_PATH`), preserving the
  existing `$TARGET_PATH/ticket.md` write-step contract used identically by
  the third, undocumented caller — this is what makes the change
  contract-compatible with zero edits to that caller.

**Alternatives considered and rejected:**
- *Detect the harness dir via a shell/env-var probe (e.g. check `$TMPDIR` or
  a new convention env var).* Rejected — confirmed live (§0) that `$TMPDIR`
  in this environment is the plain OS default, not the harness's actual
  session scratch dir; no reliable env-var signal exists to probe today, and
  inventing one would itself be a single-product-shaped guess, violating
  AC 3's harness-agnostic requirement.
- *Randomize the filename directly under `/tmp` (e.g. `mktemp
  /tmp/ticket.XXXXXXXX.md`) instead of resolving a directory.* Rejected —
  would require diverging from the `$TARGET_PATH`-is-a-folder contract that
  the third, undocumented caller (`describe-ticket-subflow.md`) already
  depends on, for no benefit once §0's permission-glob precedent showed
  nested directories under `/tmp` need no extra `allowed-tools` grant anyway.
- *Require the ticket's two named callers to resolve `$TARGET_PATH`
  themselves (e.g. each calls its own `mktemp`), keeping the subflow's
  contract mandatory/unchanged.* Rejected — duplicates the same detection
  logic in two call sites instead of one, and contradicts AC 3.3's "documented
  inline where non-obvious" (one inline explanation, not two copies that can
  drift).

---

## 2. `interactive-ticket-subflow.md` — specification

- **Caller contract (edit)** — `$TARGET_PATH` changes from required to
  optional:
  > `$TARGET_PATH` — absolute path to the folder where `ticket.md` will be
  > written. **Optional** — if omitted, the subflow resolves one itself (see
  > Section A.1).
- **Section A (guard clause) — unchanged.** Still the first thing evaluated;
  still skips the entire subflow (including the new Section A.1) for
  `$TICKET_SUPPLIED`/`$NO_INTERACTIVE`.
- **Section A.1 (new)** — "Resolve target path (only if `$TARGET_PATH` was
  not supplied by the caller)":
  - If already set by the caller (non-default contract usage, e.g.
    `describe-ticket-subflow.md`): skip this section entirely, proceed to
    Section B with the caller's value unchanged.
  - Otherwise: apply the Tier 1 → Tier 2 precedence from §1, setting
    `$TARGET_PATH` to whichever directory resolves.
  - **Failure/degradation contract**: `mktemp -d` failing (e.g. `/tmp`
    unwritable) is a hard environment failure outside this subflow's control;
    surface the error verbatim rather than silently retrying or picking an
    unvalidated path.
- **Section D (write step) — unchanged in structure**, still writes
  `$TARGET_PATH/ticket.md`; only the *source* of `$TARGET_PATH` changed.
- **Return value (new)** — the subflow currently documents no return value.
  Add: "Returns `$TARGET_PATH` — the directory actually used (the
  caller-supplied value if one was given, or the value newly resolved in
  Section A.1) — so the caller can build `$TARGET_PATH/ticket.md` for its own
  `--ticket` argument."
- **Header comment (edit)** — correct the now-inaccurate "Shared by
  `hb-task-create` and `hb-task-step-add`" to also name
  `describe-ticket-subflow.md` as a consumer, matching §0's finding.

---

## 3. Integration / wiring

- `hb-task-create.md` Step 2, case 3 (lines 54–63) and `hb-task-step-add.md`
  Step 2, case 3 (lines 55–64): remove the `Set $TARGET_PATH = /tmp` sub-step
  and the `$TARGET_PATH = /tmp` line passed into the subflow invocation;
  invoke the subflow **without** `$TARGET_PATH` (letting Section A.1
  resolve it); read back the subflow's returned `$TARGET_PATH` and build
  `$WRITTEN_TICKET = $TARGET_PATH/ticket.md` from it, replacing the hardcoded
  `/tmp/ticket.md` literal.
- `describe-ticket-subflow.md` / `load-ticket-subflow.md`: **not edited**.
  They already supply their own `$TARGET_PATH`, which the new optional-input
  contract passes through unchanged (§0.2, §1 design decision).
- No `allowed-tools` frontmatter changes in either named caller — the
  existing `//tmp/*` / `//private/tmp/*` globs already cover a nested
  `mktemp -d`-created subdirectory (§0 permission-glob precedent) and already
  cover a harness scratch dir that itself lives under `/private/tmp/*` (the
  observed case in this environment).
- No config, build wiring, entry points, scripts, or dependency manifests
  change — this is prose-instruction editing across three existing markdown
  files; no new file is created.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/interactive-ticket-subflow.md` | **edit** — caller-contract line for `$TARGET_PATH` (optional), new Section A.1 (path resolution), new Return value note after Section D, header comment corrected to name the third caller. Sections B, C, D's content and the guard logic in Section A are otherwise untouched. |
| `skills/hb-task-create.md` | **edit** — Step 2, case 3 (lines 54–63): drop the `$TARGET_PATH = /tmp` sub-step and the hardcoded `/tmp/ticket.md` in `$WRITTEN_TICKET`; invoke the subflow without `$TARGET_PATH` and derive `$WRITTEN_TICKET` from the subflow's returned `$TARGET_PATH`. Steps 1, 3, 4+ and cases 1–2 of Step 2 untouched. |
| `skills/hb-task-step-add.md` | **edit** — identical change to the equivalent lines (55–64). Steps 1, 3, 4+ and cases 1–2 of Step 2 untouched. |

No dependency-manifest or lockfile effects — no `pyproject.toml`, lockfile,
or `hb_sdk` Python source touched; this is a prose/markdown-only change.

---

## 5. Tests

N/A — no automated suite exercises skill/subflow markdown prose (confirmed in
§0; same precedent as prior doc-only steps, e.g. `hb-016/step-3`). Verification
is manual/textual, per §6.

---

## 6. Verification (after implementation)

1. **Diff check**: `git diff skills/references/interactive-ticket-subflow.md
   skills/hb-task-create.md skills/hb-task-step-add.md` shows only the edits
   described in §4 — no change to Sections B/C/D's prompt/transform/write
   *content*, no change to either caller's Step 1, Step 3+, or Step 2 cases
   1–2.
2. **Guard independence check**: re-read Section A in the edited subflow —
   confirm the guard clause (skip on `$TICKET_SUPPLIED`/`$NO_INTERACTIVE`)
   still precedes the new Section A.1, so skeleton-only and
   `--ticket`-supplied invocations never reach path resolution (AC 5).
3. **Fallback-path smoke check**: run `mktemp -d /tmp/hb-ticket.XXXXXXXX`
   twice in a row; confirm both invocations print distinct paths and both
   directories exist under `/tmp` (demonstrates AC 1.1/AC 2's "two sessions
   each get their own path" for the no-harness-dir case).
4. **AC 4 check**: for a resolved `$TARGET_PATH` from step 3, confirm
   `$TARGET_PATH/ticket.md` is a valid, well-formed absolute path ending in
   `ticket.md` and unused as `--ticket` input to `hb-sdk task create --help` /
   `task step add --help` (no new validation errors — the SDK already accepts
   arbitrary `--ticket <path>` values ending `.md`).
5. **Third-caller non-regression check**: re-read
   `describe-ticket-subflow.md:12–13` — confirm it is byte-for-byte unedited
   and still supplies its own `$TARGET_PATH` explicitly (AC 5 extended to the
   undocumented caller, per §0.2).
6. **Scope check**: `git status --short` shows exactly the three files from
   §4 changed; no `.py`, test, or unrelated `.md` file touched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1, 1.1 | §1 (Tier 1 + Tier 2 precedence), §2 (Section A.1) | Verified by §6 step 3 |
| 2 | §2 (Section A.1 replaces the fixed `/tmp/ticket.md`) | Verified by §6 step 1 |
| 3, 3.1, 3.2 | §1 (Tier 1 harness-declared dir, generically phrased; Tier 2 `mktemp` fallback) | Verified by §6 steps 3–4 |
| 3.3 | §2 (documented inline in the subflow's new Section A.1, in one place) | Verified by §6 step 1 (diff shows the doc addition) |
| 4 | §2 (Section D unchanged: always writes `$TARGET_PATH/ticket.md`) | Verified by §6 step 4 |
| 5, 5.1 | §0.2, §3 (guard clause untouched; third caller untouched) | Verified by §6 steps 2, 5 |

---

## 8. Out of scope (per ticket)

- Changing the ticket content/structure produced by the interactive flow
  (Sections B/C) — only the target path changes, per ticket.
- Cleanup/lifecycle management of old temp files or directories beyond what
  `mktemp`/the harness's own scratch-dir lifecycle already provides.
- Fixing the same underlying collision class in `describe-ticket-subflow.md`
  / `load-ticket-subflow.md` (`hb-ticket-discuss`'s own `$TICKET_SEQ`-based
  path, which is unique *within* one conversation but not across concurrent
  sessions that each start their counter at the same value) — this is an
  adjacent, pre-existing issue discovered during planning (§0) but not named
  by this ticket's Background/AC; flagged here rather than silently fixed or
  silently ignored.
