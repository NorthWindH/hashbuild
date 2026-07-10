# Step 1 Plan — Loop skeleton: Describe + Exit actions

This step turns `hb-ticket-discuss` from a single-shot flow (create one ticket,
optionally push, exit) into a persistent loop skeleton that holds tickets in
in-conversation context and offers a menu of next actions each iteration —
proving the loop shape with the two simplest actions, **Describe ticket** and
**Exit**, before later steps in this task append **Load**, **Breakdown**,
**Clear**, and **Push** without needing to touch the loop's core iteration
logic. Scope boundary: this step establishes the loop's control flow and
in-conversation ticket-entry model once, and wires exactly two actions to it —
no other action's behavior is implemented here. The single externally
observable effect: running `/hb-ticket-discuss` now returns to a menu after
Describe instead of exiting, and only exits when the user picks Exit.

Source ticket: `./ticket.md`. This is the first step of `hb-015`, executed
after `step-0-breakdown-subflow` (already shipped — extracted
`references/breakdown-subflow.md` from `hb-task-plan.md`, per that step's
execution summary). This plan targets `skills/hb-ticket-discuss.md` (156
lines) and the reference files under `skills/references/` as they exist now;
`breakdown-subflow.md` is not touched by this step (it has no consumer here —
Breakdown is step-3's job).

> **Design decision — where does the "add more actions later" extension point
> live?** Task-ticket AC 2.4 requires "later steps add more to this menu
> without needing to revisit this structure," and step tickets 2/3/4/5 each
> independently promise their action "lives in its own reference subflow
> file" and updates `references-toc.md` — implying a single, stable place to
> register a new action without editing the loop's iteration control flow.
> Putting that registry inside `hb-ticket-discuss.md` itself would violate
> this step's own AC 9 ("no action logic inlined" — a routing table is
> arguably initialization data, but keeping it there would still mean every
> later step edits the main skill file). Instead, the **Action Registry**
> (name → dispatch subflow, one row per action) lives inside the new
> `references/ticket-loop-subflow.md`, as its own lettered section (§B),
> separate from the iteration algorithm (§C–E). Later steps append one row
> there plus their own subflow file; `ticket-loop-subflow.md`'s Sections C–E
> (present state, dispatch, loop-continue) never change. See §1 and the
> AC-traceability table (§7).

---

## 0. Current-state facts (verified during planning)

- `skills/hb-ticket-discuss.md` is 156 lines, single-shot, 8 steps: 1 Help
  check, 2 Generate standalone ticket (calls
  `interactive-ticket-subflow.md`, then an inline **Review loop**,
  lines 57–62), 3 Detect Jira MCP & collect NL description, 4 NL resolution
  & confirmation loop, 5 Push to Jira, 6 Offer Jira Idea link, 7 Emit ticket
  (fallback), 8 Prompt user, plus an `## Output` section (lines 154–156).
  `grep -n "hb-sdk\|\.hb/"` returns zero `hb-sdk` calls and only prose
  references to `.hb/` stating nothing is written there — confirmed this
  skill has no facts-store or `.hb/`-write concerns to preserve or extend.
- `references/interactive-ticket-subflow.md` (73 lines): caller contract
  `$TARGET_PATH` / `$TICKET_SUPPLIED` / `$NO_INTERACTIVE`; Sections A (guard),
  B (prompt), C (transform, using `ticket-template.md`), D (write to
  `$TARGET_PATH/ticket.md`). Already reused unmodified by `hb-task-create`
  and `hb-task-step-add`; this step adds a **third** consumer
  (`describe-ticket-subflow.md`) without editing it — matches the step
  ticket's explicit "same transform/write logic as today."
- `references/breakdown-subflow.md` (52 lines, shipped in step-0) is the
  sibling shared-subflow this task already established the shape for:
  opening blockquote naming purpose + consumers, a **Caller contract** list
  of `$VAR`s, lettered Sections (A, B, C…), a **Failure/degradation
  contract** paragraph, and (where relevant) a **Return value** paragraph.
  The two new subflow files in this step mirror that same shape for
  consistency across all of `hb-ticket-discuss`'s subflows.
- `references/references-toc.md` (16 lines) lists one row per reference file
  read by any skill; step-0 added `breakdown-subflow.md`'s row directly
  after `interactive-ticket-subflow.md`'s. This step adds 3 more rows the
  same way.
- `hb-ticket-discuss.md`'s frontmatter `allowed-tools` already grants
  `Write`/`Read`/`Edit` under both `/tmp` and `/private/tmp` — sufficient for
  the new per-ticket scratch paths this step introduces (still under
  `/tmp`); no frontmatter tool-permission change is needed.
- Task-ticket AC 3 and this step's ticket AC 3 both specify the ticket-entry
  model as exactly three things: content, id/summary, active flag — verified
  consistent wording between the task-level and step-level tickets.
- Later steps' tickets already assume this step's extension point: step-2
  (Load) AC 7, step-3 (Breakdown) AC 6, step-4 (Clear) AC 7, and step-5
  (Push) AC 6 each independently state their action "lives in its own
  reference subflow file, following the [established] pattern" and updates
  `references-toc.md` accordingly — none of them mention editing
  `hb-ticket-discuss.md`'s Steps or `ticket-loop-subflow.md`'s iteration
  logic, confirming the registry-row extension point (§1) is what they rely
  on.

### 0.1 Impact (before → after)

| Aspect | Before | After |
|---|---|---|
| Control flow | `hb-ticket-discuss.md` runs Steps 1–8 once, top to bottom, then ends (push or emit, then exits). | `hb-ticket-discuss.md` reduces to Help check → Initialize loop state → inject `ticket-loop-subflow.md`, which runs its own present→dispatch→loop-continue cycle until Exit. |
| Ticket lifecycle | Exactly one ticket is created, then the skill either pushes it or prints it, and exits — no context persists. | Any number of tickets accumulate in `$TICKET_CONTEXT` across iterations; at most one is `active`; only Exit ends the session. |
| Actions available | Implicit, hardcoded: create → (maybe push) → exit. | An explicit menu (Describe ticket, Exit for this step) presented every iteration, selectable via natural language. |
| Push / Jira flow | Inline, Steps 3–6 of `hb-ticket-discuss.md`. | **Unchanged in this step** — still inline, dead code path-wise unreachable from the new loop until step-5 wires a Push action; the Jira MCP tools and NL-resolution logic are not deleted, only temporarily orphaned (see §8 Out of scope). |

This is a **restructuring, not a rewrite of ticket-creation logic**:
`interactive-ticket-subflow.md`'s transform/write rules are reused verbatim;
what changes is what happens before and after that call.

### 0.2 Non-regression proof / risk

| Case | Current behavior | Why it can't change |
|---|---|---|
| Ticket content transform (Rule 1 transcribe / Rule 2 derive) | Defined in `interactive-ticket-subflow.md` Section C | File is not edited by this step; `describe-ticket-subflow.md` calls it with the same three caller-contract variables `hb-ticket-discuss.md` used to pass directly |
| Review/confirm-or-revise loop before a ticket is considered final | Inline in `hb-ticket-discuss.md` Step 2 (lines 57–62) | Ported verbatim into `describe-ticket-subflow.md` §3 (same 4 numbered sub-steps, same wording), per step ticket AC 5 ("preserved from the current single-shot flow") |
| Push / NL-resolution / Idea-link logic (current Steps 3–6) | Fully inline in `hb-ticket-discuss.md` | Left byte-for-byte in place in this step (see §8) — not reachable from the new loop yet, but not deleted or altered; step-5 relocates it into its own subflow file later |

Risk deferred to verification (§6): confirming the orphaned Steps 3–6 content
doesn't silently execute or get referenced by the new Steps 1–3, since
nothing in the rewritten file should call it until step-5.

---

## 1. Design overview

Three new/changed pieces, one concern per unit:

| Piece | Role |
|---|---|
| `hb-ticket-discuss.md` (rewritten) | Help check, initialize loop state (`$TICKET_CONTEXT = []`, `$TICKET_SEQ = 0`, `$ACTION_LOG = []`), inject `ticket-loop-subflow.md`. No action logic. |
| `references/ticket-loop-subflow.md` (new) | Owns the ticket-entry model (§A), the Action Registry — the extension point (§B) — and the iteration cycle: present state (§C) → NL dispatch to the matched action's subflow (§D) → log + loop back (§E). |
| `references/describe-ticket-subflow.md` (new) | The Describe action: wraps `interactive-ticket-subflow.md` with a fresh scratch path, re-runs the ported review loop, then adds the result to `$TICKET_CONTEXT` as active. |
| `references/exit-ticket-loop-subflow.md` (new) | The Exit action: summarizes remaining context + the session's action log, prompts `/clear`, signals loop termination. |

```
hb-ticket-discuss.md
  └─ inject → ticket-loop-subflow.md   (owns: entry model, action registry, iteration)
                 ├─ dispatch → describe-ticket-subflow.md
                 └─ dispatch → exit-ticket-loop-subflow.md
```

Later steps (Load, Breakdown, Clear, Push) each add one row to
`ticket-loop-subflow.md`'s §B registry and one new sibling subflow file — the
same shape as Describe/Exit here — without touching §A/§C/§D/§E.

**Ticket-entry model (§A of the new subflow, defined once)**: each entry is
`{ id_or_summary, content, active }`:
- `content` — the **full verbatim text** of the ticket (read back from the
  scratch file immediately after it's written), not a path reference. This
  keeps `$TICKET_CONTEXT` self-contained per the step ticket's out-of-scope
  note ("tickets live only in the loop's in-conversation model... scratch
  files under `/tmp` as needed") — the `/tmp` file is a mechanical artifact
  of reusing `interactive-ticket-subflow.md`'s write step, not the source of
  truth.
- `id_or_summary` — a short human-identifying label. For Describe (no
  external id exists yet), derive it from the ticket's Background: the first
  clause/sentence, truncated to roughly 8 words.
- `active` — boolean; at most one entry has `active: true` at any time.
- **Extensibility note**: this triple is the contract every later action
  reuses unmodified (task AC 3 / step AC 3). Later steps may attach
  *additional* optional fields to an entry for their own bookkeeping (e.g.
  step-3's Breakdown action anticipates a parent-ticket reference) — that is
  additive, not a redefinition, and doesn't require revisiting this step.

**Scratch-path collision avoidance**: `$TICKET_SEQ` is a loop-scoped counter,
incremented once per new entry created by any action (Describe today; Load
and Breakdown's per-child materialize later). Describe uses
`/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ/` as `$TARGET_PATH`, guaranteeing
each call to `interactive-ticket-subflow.md` gets a fresh, non-colliding
folder — no shell/`mktemp` access is available or needed (`hb-ticket-discuss`'s
`allowed-tools` grants no generic Bash tool; the increment is pure
conversational state).

**Alternatives considered and rejected:**
- Action registry table inside `hb-ticket-discuss.md` itself: rejected — AC 9
  requires the main skill file carry no action logic, and it would mean
  every later step edits the main file instead of only adding a subflow.
- Storing only a path reference (not verbatim content) in each entry:
  rejected — leaves `$TICKET_CONTEXT` dependent on `/tmp` files surviving for
  the rest of the session, contradicting the "lives only in the
  in-conversation model" contract and complicating later Clear/Push actions
  that need the text directly.
- A single shared file for both Describe and Exit (permitted by AC 8's
  "shared small file" escape hatch): rejected — Describe wraps a whole
  existing subflow with a review loop while Exit is a short summarize-and-stop;
  keeping them separate matches the "default to separate files" instruction
  and the one-file-per-action pattern step-2 through step-5 must also follow.

---

## 2. Component specification

### 2.1 `references/ticket-loop-subflow.md` — new

- **Opening blockquote**: names purpose ("owns per-iteration state
  presentation, NL action dispatch, and the return-to-top control flow") and
  that later steps extend it only via §B.
- **Caller contract**: `$TICKET_CONTEXT` (mutable list, caller initializes
  `[]`), `$TICKET_SEQ` (mutable int, caller initializes `0`), `$ACTION_LOG`
  (mutable list of strings, caller initializes `[]`).
- **§A Ticket entry model**: the `{id_or_summary, content, active}` contract
  and extensibility note, as specified in §1 above.
- **§B Action Registry** — a table, one row per available action:

  | Action | Selectable via (examples) | Dispatch subflow |
  |---|---|---|
  | Describe ticket | "describe a ticket", "create a new one", "let's write a ticket for X" | `describe-ticket-subflow.md` |
  | Exit | "exit", "I'm done", "end the session" | `exit-ticket-loop-subflow.md` |

  This is the single edit point later steps use to add Load / Breakdown /
  Clear / Push rows.
- **§C Present state** (start of every iteration):
  1. Active ticket's `id_or_summary`, or "No active ticket" if none/empty
     context.
  2. Count of tickets in `$TICKET_CONTEXT`.
  3. Numbered list of every entry's `id_or_summary`.
  4. Available actions from §B (name + one-line description), then: "What
     would you like to do?"
- **§D Dispatch**: match the user's freeform reply against §B's action names
  and example phrasings (semantic match, not exact keyword — satisfies task
  AC 4 / step AC 4). Ambiguous or unmatched replies: ask a clarifying
  question and re-prompt without re-running all of §C. On a confident match:
  invoke the matched subflow, passing `$TICKET_CONTEXT` and `$TICKET_SEQ` by
  reference (mutated in place by the callee).
- **§E Log + loop continue**: when the dispatched action subflow returns
  (every action except Exit returns control here), append one line to
  `$ACTION_LOG` describing what happened (e.g. `"Described ticket: <label>"`),
  then return to §C. Exit does not return here — it ends the loop itself (see
  2.3) and control passes back up through this subflow's own return to
  `hb-ticket-discuss.md`.
- **Failure/degradation contract**: empty `$TICKET_CONTEXT` at the first
  iteration is valid (§C shows "No tickets in context yet"); unrecognized
  action replies re-prompt, never error; no iteration cap.

### 2.2 `references/describe-ticket-subflow.md` — new

- **Opening blockquote**: names purpose and that it's invoked only via the
  Action Registry.
- **Caller contract**: `$TICKET_CONTEXT`, `$TICKET_SEQ` (both mutable,
  in/out).
- **Behavior**:
  1. Increment `$TICKET_SEQ`; set `$TARGET_PATH` =
     `/tmp/hb-ticket-discuss/ticket-$TICKET_SEQ`.
  2. Follow `interactive-ticket-subflow.md` with `$TARGET_PATH`,
     `$TICKET_SUPPLIED = false`, `$NO_INTERACTIVE = false` — writes
     `$TARGET_PATH/ticket.md`.
  3. **Review loop** (ported verbatim from today's `hb-ticket-discuss.md`
     Step 2, lines 57–62): read and display `$TARGET_PATH/ticket.md` in
     full; ask "Does this ticket look right? Reply **yes**... or describe
     any changes"; **yes** → break; otherwise re-run only Sections C
     (Transform) and D (Write) of `interactive-ticket-subflow.md` with the
     feedback, then repeat this loop.
  4. On confirm: read back `$TARGET_PATH/ticket.md`'s full text as
     `$content`; derive `$id_or_summary` from its Background's first
     clause/sentence (≤ ~8 words).
  5. Unset `active` on every existing `$TICKET_CONTEXT` entry; append
     `{id_or_summary: $id_or_summary, content: $content, active: true}`.
  6. Return to caller with outcome string `"Described ticket: $id_or_summary"`.
- **Failure/degradation contract**: identical to
  `interactive-ticket-subflow.md`'s own (guard clause behavior is N/A here
  since this subflow always calls it with both flags `false`).

### 2.3 `references/exit-ticket-loop-subflow.md` — new

- **Opening blockquote**: names purpose (ends the loop; never discards a
  ticket).
- **Caller contract**: `$TICKET_CONTEXT`, `$ACTION_LOG` (read-only here).
- **Behavior**:
  1. Compose a summary: count and `id_or_summary` of every entry still in
     `$TICKET_CONTEXT`; the full `$ACTION_LOG` (actions taken this session).
  2. Present the summary to the user.
  3. Tell the user to `/clear` the conversation when ready.
  4. Signal loop termination — this subflow (and `ticket-loop-subflow.md`
     above it) returns to `hb-ticket-discuss.md`, which then ends; no further
     iterations run.
- **Failure/degradation contract**: N/A — no external calls, no failure
  mode; empty `$TICKET_CONTEXT`/`$ACTION_LOG` summarize as "0 tickets left in
  context" / "no actions taken."

Conflict resolution: N/A across all three files — no competing sources to
arbitrate at this step (Describe and Exit are mutually exclusive dispatch
targets, matched independently in §2.1's §D).

---

## 3. Integration / wiring

- `skills/hb-ticket-discuss.md` Steps section is fully replaced:
  1. **Help check** — unchanged wording, still `[${CLAUDE_SKILL_DIR}/references/skill-help.md]`.
  2. **Initialize loop** — set `$TICKET_CONTEXT = []`, `$TICKET_SEQ = 0`,
     `$ACTION_LOG = []`.
  3. **Inject loop subflow** — follow
     `[${CLAUDE_SKILL_DIR}/references/ticket-loop-subflow.md]`, passing the
     three variables above.
- Frontmatter `allowed-tools` is **unchanged** — no new tool needed; existing
  `/tmp` and `/private/tmp` Write/Read/Edit grants cover the new
  `hb-ticket-discuss/ticket-N/` scratch subpaths, and the 5 Jira MCP tool
  entries remain listed even though the loop can't reach them yet (Push
  isn't wired until step-5; removing them now and re-adding them later would
  be pure churn — see §8).
- Frontmatter `description:` and the file's opening H1 prose (lines 4–11,
  26–28) are reworded to describe the loop generally — "a persistent,
  multi-turn loop... selecting actions (e.g. describe, exit) via natural
  language" — rather than enumerating the full eventual action set (Load,
  Breakdown, Clear, Push don't exist yet) or repeating the old single-shot
  claim (now false). Using "e.g." avoids rewriting this line again in each
  of steps 2–5 purely to append one more action name.
- The `## Output` section (currently lines 154–156, push/emit-specific) is
  reworded to point at the loop's own reporting: on Exit, the summary
  produced by `exit-ticket-loop-subflow.md`; errors from any step surfaced
  verbatim, unchanged framing from today.
- No other file's call sites change. `interactive-ticket-subflow.md` and
  `breakdown-subflow.md` are read, not edited. `hb-task-create.md`,
  `hb-task-step-add.md`, and `hb-task-plan.md` do not reference
  `hb-ticket-discuss.md` and are unaffected.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/hb-ticket-discuss.md` | **edit** — Steps section replaced (Help check / Initialize loop / Inject loop subflow, ~3 steps instead of 8); frontmatter `description:`, opening H1 prose, and `## Output` reworded per §3; frontmatter `allowed-tools` untouched; today's Steps 3–6 (Jira push/NL-resolution/Idea-link) content is **not deleted** — see §8 |
| `skills/references/ticket-loop-subflow.md` | **new** — entry model (§A), Action Registry (§B), iteration/dispatch/loop-continue (§C–E) |
| `skills/references/describe-ticket-subflow.md` | **new** — Describe action; wraps `interactive-ticket-subflow.md`, ports the review loop verbatim, adds result to context as active |
| `skills/references/exit-ticket-loop-subflow.md` | **new** — Exit action; summary + `/clear` prompt + loop termination signal |
| `skills/references/references-toc.md` | **edit** — 3 new rows (one per new file above), placed after the existing `breakdown-subflow.md` row |

No dependency-manifest or lockfile in this repo's skill layer;
`interactive-ticket-subflow.md`, `breakdown-subflow.md`, and every
`hb-task-*` skill file are untouched.

---

## 5. Tests

Markdown skill-definition files, no application test suite — "tests" means
dry-run trace verification against the edited/new files' text, matching the
style used for step-0 of this same task.

- **Happy path — Describe then Exit**: trace a first run: `$TICKET_CONTEXT`
  starts empty → §C shows "No tickets in context yet" + the two-action menu
  → user says "describe a ticket" (not an exact "Describe ticket" match) →
  §D matches Describe → `describe-ticket-subflow.md` runs
  `interactive-ticket-subflow.md`, review loop confirms on first pass, entry
  added active → §E logs it, loops to §C, now shows 1 ticket, it active →
  user says "I'm done" → Exit matches, summary shows 1 ticket + one log
  line, prompts `/clear`.
- **Revision loop inside Describe**: trace a run where the user replies with
  corrections instead of "yes" at the review step — confirm only Sections C
  and D of `interactive-ticket-subflow.md` re-run (not the guard or prompt
  sections), and the loop repeats until an explicit "yes."
- **Multiple tickets, active-flag exclusivity**: trace two consecutive
  Describe calls — confirm the first entry's `active` flips to `false` when
  the second is added, and `$TICKET_SEQ`-derived scratch paths
  (`ticket-1/`, `ticket-2/`) don't collide.
- **NL dispatch, non-exact match**: confirm §D's matching handles phrasings
  like "let's write a ticket for the auth refactor" and "end the session"
  without requiring the literal menu labels (task AC 4 / step AC 4).
- **Exit never discards**: confirm `exit-ticket-loop-subflow.md`'s summary
  step never removes entries from `$TICKET_CONTEXT` before or after running —
  it only reads it (step AC 6 / task AC 9).
- **Non-regression**: `interactive-ticket-subflow.md` and
  `breakdown-subflow.md` are unread-as-edited (only referenced) by this
  step; confirm via `git diff` that neither appears modified. Confirm the
  orphaned Steps 3–6 content, if left in place per §8, is not referenced
  from anywhere in the new Steps 1–3 or from `ticket-loop-subflow.md`.

---

## 6. Verification (after implementation)

1. `git diff --stat` shows exactly the 5 files listed in §4 changed/added.
2. Read `skills/hb-ticket-discuss.md` end to end: confirm it contains only
   Help check / Initialize loop / Inject loop subflow, no inline action
   logic, and an updated `## Output` section.
3. Read `skills/references/ticket-loop-subflow.md` end to end: confirm the
   opening blockquote + caller contract shape matches
   `interactive-ticket-subflow.md:1-9` / `breakdown-subflow.md:1-11`'s
   pattern, and Sections A–E are all present.
4. `grep -n "^###\|^####" skills/references/describe-ticket-subflow.md
   skills/references/exit-ticket-loop-subflow.md` — confirm each file's
   structure matches its §2 spec above.
5. `grep -n "hb-sdk\|^Bash" skills/hb-ticket-discuss.md
   skills/references/ticket-loop-subflow.md
   skills/references/describe-ticket-subflow.md
   skills/references/exit-ticket-loop-subflow.md` — confirm zero matches
   (no `hb-sdk`/Bash dependency introduced; scratch-path sequencing is pure
   conversational state, per §1).
6. `grep -n "breakdown-subflow\|describe-ticket-subflow\|exit-ticket-loop-subflow\|ticket-loop-subflow" skills/references/references-toc.md`
   — confirm exactly one row per new file (3 rows total added).
7. Per-AC check: for each of this step's ACs 1–10 (§7), point to the exact
   section that satisfies it.
8. Scope check (`git status --short`): only the 5 files in §4 changed; no
   edits to `interactive-ticket-subflow.md`, `breakdown-subflow.md`, any
   `hb-task-*.md`, or anything under `.hb/`.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2.1 (§C–E of `ticket-loop-subflow.md`) | Loop returns to §C after every non-Exit action; only Exit ends it |
| 2.1 | §2.1 §C.1 | Active ticket's `id_or_summary`, or "No active ticket" |
| 2.2 | §2.1 §C.2 | Count of `$TICKET_CONTEXT` |
| 2.3 | §2.1 §C.3 | Numbered list of every entry's `id_or_summary` |
| 2.4 | §2.1 §C.4 + §B | Menu from the Action Registry; later steps append rows, not structure |
| 3 | §1 entry model; §2.2 step 5 | Model defined once; Describe unsets prior `active` before appending |
| 4 | §2.1 §D | Semantic match against Action Registry phrasings, not exact keyword |
| 5 | §2.2 | Wraps `interactive-ticket-subflow.md`; review loop ported verbatim; adds to context as active |
| 6 | §2.3 | Summarizes count + ids + `$ACTION_LOG`; prompts `/clear`; never removes entries |
| 7 | §2.1 (whole file) | Iteration logic isolated in its own subflow file |
| 8 | §2.2, §2.3 (two files) | Describe and Exit each in their own subflow file, per the "default to separate" instruction |
| 9 | §3 (rewired Steps) | `hb-ticket-discuss.md` reduced to help/init/inject only |
| 10 | §4 (`references-toc.md` row) | 3 new rows added |

---

## 8. Out of scope (per ticket)

- Load, Breakdown, Clear, and Push actions — later steps in this task; the
  Action Registry (§2.1 §B) has exactly two rows after this step.
- Persisting context to `.hb/` — `$TICKET_CONTEXT` lives only in-conversation
  (plus the mechanical `/tmp` scratch files `describe-ticket-subflow.md`
  produces via `interactive-ticket-subflow.md`).
- Any change to the existing NL-driven Jira push flow: today's Steps 3–6
  content (Detect Jira MCP, NL resolution, Push, Idea link) is left in place
  verbatim in this step rather than deleted, since step-5 is scoped to
  relocate it into its own Push subflow(s) and rewire it as a loop action —
  deleting it now and re-authoring it in step-5 would be pure churn and
  risks losing fidelity to today's proven wording. It is simply unreachable
  from the new loop until step-5 lands (verified in §6.5's grep and the
  non-regression trace in §5).
