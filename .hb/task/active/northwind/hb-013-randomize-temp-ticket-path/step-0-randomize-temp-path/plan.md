# Step 0 Plan — Randomize the Interactive-Ticket Temp Path

One-paragraph framing: today, `interactive-ticket-subflow.md` always writes an
in-progress ticket draft to the literal path `/tmp/ticket.md`, and every real
caller hardcodes its own fixed/predictable path before invoking it —
`hb-task-create`/`hb-task-step-add` hardcode `/tmp` directly, while
`hb-ticket-discuss`'s `describe-ticket-subflow.md`/`load-ticket-subflow.md`
hardcode `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ`, a path that is unique
only *within* one conversation (`$TICKET_SEQ` starts at `0` in every session).
Two sessions running either flow concurrently can collide — session B's write
clobbers session A's in-flight draft before A finishes reading it back. This
step makes the subflow always self-resolve a fresh per-invocation target
directory (a harness-declared session scratch dir when one is detectable,
else a hand-rolled unique dir under `/tmp` via `mktemp -d`), removes
`$TARGET_PATH` from the subflow's caller contract entirely (no caller
resolves or supplies it anymore), and updates all four real call sites plus
the now-dead `$TICKET_SEQ` threading behind two of them. Behavior change only
for interactive-ticket-drafting flows; skeleton-only and `--ticket
<path>`-supplied modes are untouched. Once this lands, no two
interactive-ticket-drafting invocations — from either skill family — share a
path.

Source ticket: `./ticket.md`. This is step 0 of `hb-013` — no prior steps to
build on. This plan targets `skills/references/interactive-ticket-subflow.md`,
`skills/hb-task-create.md`, `skills/hb-task-step-add.md`,
`skills/references/describe-ticket-subflow.md`,
`skills/references/load-ticket-subflow.md`,
`skills/references/ticket-loop-subflow.md`, and `skills/hb-ticket-discuss.md`
as they exist now.

> **Design decision — remove `$TARGET_PATH` from the subflow's caller
> contract entirely, rather than making it optional.** `interactive-ticket-
> subflow.md`'s own header (line 1) claims it is "Shared by `hb-task-create`
> and `hb-task-step-add`" — matching the ticket's original Background. But
> `describe-ticket-subflow.md:13` (part of `hb-ticket-discuss`, not originally
> named) is a **third caller** that resolves its own `$TARGET_PATH` via a
> per-loop `$TICKET_SEQ` counter (see §0) — and shares the identical
> cross-session collision risk this ticket was filed for (ticket AC 6, added
> during plan discussion once this was surfaced). Rather than special-casing
> the subflow to accept either a caller-supplied or a self-resolved
> `$TARGET_PATH` (needed only if some caller were left on the old scheme),
> **every** real caller is brought onto self-resolution in this same step —
> so the caller-supplied branch would never execute and doesn't need to exist.
> `$TARGET_PATH` drops out of the caller contract entirely; the subflow always
> resolves it in the new Section A.1. `$TICKET_SEQ`, whose sole repo-wide
> purpose (confirmed by `grep -rn "TICKET_SEQ" skills/`) was building that
> now-obsolete path, is removed as dead state from every file that threaded
> it. See §1 (design) and §7 (AC traceability).

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
- **A third real caller shares the same collision class** (not named in the
  ticket's original Background, added as AC 6 during plan discussion):
  `describe-ticket-subflow.md:12–13` — `hb-ticket-discuss`'s loop action —
  sets `$TARGET_PATH` = `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` (a fresh
  subfolder per loop iteration, using its own in-memory sequence counter,
  initialized to `0` in every session by `hb-ticket-discuss.md:48`) and
  *then* follows `interactive-ticket-subflow.md` with that value. Two
  concurrent `hb-ticket-discuss` sessions both compute `ticket-1` on their
  first action — the identical cross-session collision the ticket was filed
  for. `load-ticket-subflow.md:79–85` (§E, shared by its file/Jira/web
  sources) follows the identical `$TICKET_SEQ`-based pattern inline (does not
  invoke the shared subflow for path construction, but writes to the same
  colliding path shape) and shares the same fix.
- **`$TICKET_SEQ` is dead state once its one job is gone.** Repo-wide
  `grep -rn "TICKET_SEQ" skills/` (7 hits, confirmed) shows its only use
  anywhere is constructing the `$TARGET_PATH` above in
  `describe-ticket-subflow.md` and `load-ticket-subflow.md`; it is otherwise
  just threaded through `ticket-loop-subflow.md`'s caller contract/dispatch
  and initialized in `hb-ticket-discuss.md:48`. Once path resolution moves
  into the subflow, `$TICKET_SEQ` has no remaining reader and should be
  removed rather than left as unused threaded state.
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
| `describe-ticket-subflow.md` / `load-ticket-subflow.md` (`hb-ticket-discuss`) | `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ` — unique within one conversation, collides across concurrent sessions (both start at `ticket-1`) | Same subflow-resolved path as above — collision-free across sessions; `$TICKET_SEQ` removed as dead state |
| Skeleton-only / `--ticket <path>`-supplied modes (all callers) | Subflow's guard clause (Section A) skips the whole subflow | Unchanged — guard clause untouched, still skips before any path resolution |

Additive/behavior-preserving except for the targeted cases (interactive mode
across all three ticket-drafting entry points), which change from a fixed or
per-conversation-only-unique path to a resolved, cross-session collision-free
one.

### 0.2 Non-regression proof

| Case | Current behavior | Why it can't change |
|---|---|---|
| Guard clause (Section A: `$TICKET_SUPPLIED` / `$NO_INTERACTIVE`) | Skips subflow entirely for skeleton-only / `--ticket`-supplied modes | Not edited — new resolution step is inserted *after* the existing guard, only reached when the guard already continues |
| Ticket content/structure produced (Sections B–C: prompt, transform rules) | Background / Acceptance Criteria / Out-of-scope derivation | Not edited — only the target *path*, not the write-step content, changes (per ticket's own Out-of-scope) |
| `ticket-loop-subflow.md`'s Action Registry, present/dispatch/log-loop-continue (§B–§E) | Load/Describe/Exit actions, semantic-match dispatch | Not edited beyond dropping `$TICKET_SEQ` from the caller-contract bullet list and the one "passing ... by reference" sentence in §D — the registry, dispatch matching, and logging logic are untouched |
| `describe-ticket-subflow.md`'s Review loop (step 3) / `load-ticket-subflow.md`'s source classification (§A–§D) | Re-run Sections C/D on user corrections; classify file/Jira/web sources | Not edited — only each subflow's own `$TARGET_PATH`-construction line changes; review-loop and source-classification logic are untouched |

Change is confined to path resolution (and the dead `$TICKET_SEQ` state it
leaves behind); the guard, prompt, transform, write-content, and loop-dispatch
logic are untouched everywhere.

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
- Both tiers hand back a **directory** (`$TARGET_PATH`), matching the
  `$TARGET_PATH/ticket.md` write-step contract every real caller already
  expects — this is what makes the change a drop-in replacement for each
  caller's own prior path-construction line.
- All four real call sites resolve `$TARGET_PATH` via the same one mechanism,
  documented in exactly one place (§2's Section A.1): `hb-task-create`,
  `hb-task-step-add`, and `describe-ticket-subflow.md` reach it by invoking
  the subflow with no `$TARGET_PATH`; `load-ticket-subflow.md` reaches it by
  borrowing Section A.1 inline, the same way it already borrows §C/§D without
  invoking the subflow as a whole (§2.1).

**Alternatives considered and rejected:**
- *Detect the harness dir via a shell/env-var probe (e.g. check `$TMPDIR` or
  a new convention env var).* Rejected — confirmed live (§0) that `$TMPDIR`
  in this environment is the plain OS default, not the harness's actual
  session scratch dir; no reliable env-var signal exists to probe today, and
  inventing one would itself be a single-product-shaped guess, violating
  AC 3's harness-agnostic requirement.
- *Randomize the filename directly under `/tmp` (e.g. `mktemp
  /tmp/ticket.XXXXXXXX.md`) instead of resolving a directory.* Rejected —
  would require diverging from the `$TARGET_PATH`-is-a-folder contract every
  real caller already expects, for no benefit once §0's permission-glob
  precedent showed nested directories under `/tmp` need no extra
  `allowed-tools` grant anyway.
- *Keep `$TARGET_PATH` as an optional caller-supplied input (self-resolve only
  when omitted), leaving `describe-ticket-subflow.md`/`load-ticket-subflow.md`
  on their own `$TICKET_SEQ`-based scheme.* This was the original plan before
  AC 6 was added. Rejected now — once every real caller is being updated
  anyway (§0, AC 6), a caller-supplied branch would never execute, so keeping
  it would be unused complexity; removing `$TARGET_PATH` from the contract
  entirely is simpler and leaves no caller on the still-collision-prone
  scheme.
- *Require each of the four call sites to resolve `$TARGET_PATH` themselves
  (e.g. each calls its own `mktemp`), keeping the subflow's contract
  unchanged.* Rejected — duplicates the same detection logic across four call
  sites instead of one, and contradicts AC 3.3's "documented inline where
  non-obvious" (one inline explanation, not four copies that can drift).

---

## 2. `interactive-ticket-subflow.md` — specification

- **Caller contract (edit)** — `$TARGET_PATH` is **removed** from the caller
  contract entirely (no caller resolves or passes it anymore). Remaining
  contract inputs (`$TICKET_SUPPLIED`, `$NO_INTERACTIVE`) are unchanged.
- **Section A (guard clause) — unchanged.** Still the first thing evaluated;
  still skips the entire subflow (including the new Section A.1) for
  `$TICKET_SUPPLIED`/`$NO_INTERACTIVE`.
- **Section A.1 (new)** — "Resolve target path" — runs unconditionally
  whenever Section A continues (no caller-supplied branch to check):
  apply the Tier 1 → Tier 2 precedence from §1, setting `$TARGET_PATH` to
  whichever directory resolves.
  - **Failure/degradation contract**: `mktemp -d` failing (e.g. `/tmp`
    unwritable) is a hard environment failure outside this subflow's control;
    surface the error verbatim rather than silently retrying or picking an
    unvalidated path.
- **Section D (write step) — unchanged in structure**, still writes
  `$TARGET_PATH/ticket.md`; only the *source* of `$TARGET_PATH` changed.
- **Return value (new)** — the subflow currently documents no return value.
  Add: "Returns `$TARGET_PATH` — the directory resolved in Section A.1 — so
  the caller can build `$TARGET_PATH/ticket.md` for its own use (e.g. a
  `--ticket` argument, or a read-back per `ticket-loop-subflow.md`'s ticket
  entry model)."
- **Header comment (edit)** — correct the now-inaccurate "Shared by
  `hb-task-create` and `hb-task-step-add`" to name all real consumers:
  `hb-task-create`, `hb-task-step-add`, and `hb-ticket-discuss`'s
  `describe-ticket-subflow.md`/`load-ticket-subflow.md`.

---

## 2.1 `$TICKET_SEQ` removal — specification

Once no caller constructs `$TARGET_PATH` from `$TICKET_SEQ` (§2), `$TICKET_SEQ`
has no remaining reader (§0's repo-wide grep confirms this is its only use).
Remove it as dead state:

- `ticket-loop-subflow.md` — drop the `$TICKET_SEQ` bullet from the caller
  contract (line 10); in §D's dispatch sentence (line 59), "passing
  `$TICKET_CONTEXT` and `$TICKET_SEQ` by reference" → "passing
  `$TICKET_CONTEXT` by reference".
- `describe-ticket-subflow.md` — drop the `$TICKET_SEQ` bullet from the
  caller contract (line 8); step 1 (line 12) "Increment `$TICKET_SEQ`. Set
  `$TARGET_PATH` = ..." → simply follow `interactive-ticket-subflow.md` (no
  `$TARGET_PATH` passed) and use its returned value for the rest of the
  section.
- `load-ticket-subflow.md` — **does not `Follow` the subflow at all** (unlike
  `describe-ticket-subflow.md`); it only borrows specific sections inline
  (§C's transform rules, §D's write structure), by design, since it already
  has `$RAW_CONTENT` from a file/Jira/URL and must never trigger the
  subflow's own Section A guard or Section B prompt. So its fix borrows
  Section A.1 the same way it already borrows §C/§D, rather than invoking the
  subflow as a whole: drop the `$TICKET_SEQ` bullet from the caller contract
  (line 10); drop the `$TICKET_SEQ` clause from the "(no entry added,
  `$TICKET_SEQ` unchanged)" aside in §B step 1 (line 30) (the rest of the
  sentence — no entry added on a zero-match resolve — is unaffected); §E step
  2 (lines 79–81) "Increment `$TICKET_SEQ`. Set `$TARGET_PATH` = ..." →
  "Apply `interactive-ticket-subflow.md` §A.1's resolution logic to set
  `$TARGET_PATH`" (same borrowed-section pattern as step 1's §C reference).
- `hb-ticket-discuss.md` — Step 2 (line 48): drop `$TICKET_SEQ` = `0` from
  the `Set` statement; Step 3 (line 52): drop `$TICKET_SEQ` from the list of
  values passed to `ticket-loop-subflow.md`.

No other file references `$TICKET_SEQ` (confirmed by the same repo-wide grep,
§0) — `exit-ticket-loop-subflow.md` and `ticket-template.md` have zero hits.

---

## 3. Integration / wiring

- `hb-task-create.md` Step 2, case 3 (lines 54–63) and `hb-task-step-add.md`
  Step 2, case 3 (lines 55–64): remove the `Set $TARGET_PATH = /tmp` sub-step
  and the `$TARGET_PATH = /tmp` line passed into the subflow invocation;
  invoke the subflow **without** `$TARGET_PATH` (letting Section A.1
  resolve it); read back the subflow's returned `$TARGET_PATH` and build
  `$WRITTEN_TICKET = $TARGET_PATH/ticket.md` from it, replacing the hardcoded
  `/tmp/ticket.md` literal.
- `describe-ticket-subflow.md`: edited per §2.1 — stops constructing
  `$TARGET_PATH` from `$TICKET_SEQ` and instead invokes
  `interactive-ticket-subflow.md` (as it already does, `Follow`ing the whole
  subflow) with no `$TARGET_PATH`, using its returned value for the rest of
  the section exactly as before (review loop, read-back, `$TICKET_CONTEXT`
  append — all unchanged, per §0.2).
- `load-ticket-subflow.md`: edited per §2.1 — stops constructing
  `$TARGET_PATH` from `$TICKET_SEQ` and instead borrows the subflow's new
  §A.1 resolution logic inline, matching its existing pattern of borrowing
  §C/§D without invoking Sections A/B (it never wants the subflow's own guard
  or interactive prompt to run, since it already has `$RAW_CONTENT`).
- `ticket-loop-subflow.md` / `hb-ticket-discuss.md`: edited per §2.1 to stop
  threading `$TICKET_SEQ` — the Action Registry, dispatch matching, present/
  log-loop-continue behavior, and the skill's own Steps 1/4 (help, output) are
  untouched.
- No `allowed-tools` frontmatter changes anywhere — `hb-task-create.md` and
  `hb-task-step-add.md`'s existing `//tmp/*` / `//private/tmp/*` globs already
  cover a nested `mktemp -d`-created subdirectory (§0 permission-glob
  precedent) and already cover a harness scratch dir under `/private/tmp/*`
  (the observed case in this environment); `hb-ticket-discuss.md` carries the
  identical glob set already and needs no change either, since it's the same
  resolution mechanism.
- No config, build wiring, entry points, scripts, or dependency manifests
  change — this is prose-instruction editing across seven existing markdown
  files; no new file is created.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/interactive-ticket-subflow.md` | **edit** — `$TARGET_PATH` removed from the caller contract, new Section A.1 (unconditional path resolution), new Return value note after Section D, header comment corrected to name all real consumers. Sections B, C, D's content and the guard logic in Section A are otherwise untouched. |
| `skills/hb-task-create.md` | **edit** — Step 2, case 3 (lines 54–63): drop the `$TARGET_PATH = /tmp` sub-step and the hardcoded `/tmp/ticket.md` in `$WRITTEN_TICKET`; invoke the subflow without `$TARGET_PATH` and derive `$WRITTEN_TICKET` from the subflow's returned `$TARGET_PATH`. Steps 1, 3, 4+ and cases 1–2 of Step 2 untouched. |
| `skills/hb-task-step-add.md` | **edit** — identical change to the equivalent lines (55–64). Steps 1, 3, 4+ and cases 1–2 of Step 2 untouched. |
| `skills/references/describe-ticket-subflow.md` | **edit** — per §2.1: drop `$TICKET_SEQ` from the caller contract; step 1 stops constructing `$TARGET_PATH`, invokes the subflow without it, and uses its returned value. Steps 2–6 (review loop, read-back, `$TICKET_CONTEXT` append, return) untouched. |
| `skills/references/load-ticket-subflow.md` | **edit** — per §2.1: drop `$TICKET_SEQ` from the caller contract; drop its clause from §B step 1's failure aside; §E step 2 stops constructing `$TARGET_PATH` from `$TICKET_SEQ` and instead borrows the subflow's new §A.1 resolution logic inline (does **not** `Follow` the subflow as a whole — same borrowed-section pattern as its existing §C reference in step 1). §§A–D (source classification) and §E steps 1, 3–7 untouched. |
| `skills/references/ticket-loop-subflow.md` | **edit** — per §2.1: drop `$TICKET_SEQ` from the caller contract and from §D's "passing ... by reference" sentence. §§A, B, C, E (entry model, Action Registry, present, log+continue) untouched. |
| `skills/hb-ticket-discuss.md` | **edit** — per §2.1: Step 2 drops `$TICKET_SEQ` from its `Set` statement; Step 3 drops `$TICKET_SEQ` from the values passed to `ticket-loop-subflow.md`. Step 1 (help) and Output section untouched. |

No dependency-manifest or lockfile effects — no `pyproject.toml`, lockfile,
or `hb_sdk` Python source touched; this is a prose/markdown-only change
across seven skill/reference files.

---

## 5. Tests

N/A — no automated suite exercises skill/subflow markdown prose (confirmed in
§0; same precedent as prior doc-only steps, e.g. `hb-016/step-3`). Verification
is manual/textual, per §6.

---

## 6. Verification (after implementation)

1. **Diff check**: `git diff` on all seven files from §4 shows only the edits
   described there — no change to Sections B/C/D's prompt/transform/write
   *content*, no change to either `hb-task-*` caller's Step 1/Step 3+/Step 2
   cases 1–2, no change to `ticket-loop-subflow.md`'s Action Registry or
   `describe-ticket-subflow.md`/`load-ticket-subflow.md`'s review-loop/source-
   classification logic.
2. **Guard independence check**: re-read Section A in the edited subflow —
   confirm the guard clause (skip on `$TICKET_SUPPLIED`/`$NO_INTERACTIVE`)
   still precedes the new Section A.1, so skeleton-only and
   `--ticket`-supplied invocations never reach path resolution (AC 5).
3. **Fallback-path smoke check**: run `mktemp -d /tmp/hb-ticket.XXXXXXXX`
   twice in a row; confirm both invocations print distinct paths and both
   directories exist under `/tmp` (demonstrates AC 1.1/AC 2/AC 6's "two
   sessions each get their own path" for the no-harness-dir case).
4. **AC 4 check**: for a resolved `$TARGET_PATH` from step 3, confirm
   `$TARGET_PATH/ticket.md` is a valid, well-formed absolute path ending in
   `ticket.md` and usable as `--ticket` input to `hb-sdk task create --help` /
   `task step add --help` (no new validation errors — the SDK already accepts
   arbitrary `--ticket <path>` values ending `.md`).
5. **`$TICKET_SEQ` removal check**: `grep -rn "TICKET_SEQ" skills/` returns
   zero matches (AC 6.1) — confirms no file was left half-migrated.
6. **`hb-ticket-discuss` non-regression check**: re-read
   `ticket-loop-subflow.md` §§A–E and `describe-ticket-subflow.md`/
   `load-ticket-subflow.md` end-to-end — confirm the Action Registry, entry
   model, review loop, and source classification (§0.2) read identically to
   before except for the `$TARGET_PATH`/`$TICKET_SEQ` lines named in §4.
7. **Scope check**: `git status --short` shows exactly the seven files from
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
| 5, 5.1 | §0.2, §3 (guard clause untouched) | Verified by §6 step 2 |
| 6 | §2.1, §3, §4 (`describe-ticket-subflow.md`/`load-ticket-subflow.md` moved onto the same Tier 1/Tier 2 resolution as the other callers) | Verified by §6 steps 3, 6 |
| 6.1 | §2.1 (`$TICKET_SEQ` removed from `ticket-loop-subflow.md`, `describe-ticket-subflow.md`, `load-ticket-subflow.md`, `hb-ticket-discuss.md`) | Verified by §6 step 5 |

---

## 8. Out of scope (per ticket)

- Changing the ticket content/structure produced by the interactive flow
  (Sections B/C) — only the target path changes, per ticket.
- Cleanup/lifecycle management of old temp files or directories beyond what
  `mktemp`/the harness's own scratch-dir lifecycle already provides.
- Any other simplification of `hb-ticket-discuss`'s ticket-entry model,
  Action Registry, or source-classification logic (§§A–D of
  `load-ticket-subflow.md`, entry model/registry of `ticket-loop-subflow.md`)
  beyond the `$TARGET_PATH`/`$TICKET_SEQ` change this step makes — those are
  unrelated to the collision fix and untouched (§0.2).
