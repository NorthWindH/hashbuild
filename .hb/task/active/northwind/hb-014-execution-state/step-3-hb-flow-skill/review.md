# Step 3 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-3-REVIEW-1 | ✅ Addressed — added "Create a new task" → `hb-task-create` row to Action Registry |
| STEP-3-REVIEW-2 | ✅ Addressed — added `--flavor` to args shape + Step 6 derivation guidance |
| STEP-3-REVIEW-3 | ✅ Assessed — kept as-is, no channel exists to pass facts through the `Skill` tool call and target skills already read facts themselves |
| STEP-3-REVIEW-4 | ✅ Addressed — added `hb-sdk facts read` at start of Step 4 to inform prompt framing |
| STEP-3-REVIEW-5 | ✅ Addressed — fixed the real bug in `hb-flow.md`'s STEP-3-REVIEW-2 resolution instead of adding an unneeded flag |
| STEP-3-REVIEW-6 | ✅ Addressed — added inline `hb-sdk facts read` to both skills' Step 2, mirroring hb-flow's own facts-read pattern rather than joining facts-write-subflow |

---

## Notes

### STEP-3-REVIEW-1: Register hb-task-create in the Action Registry

- **file(s):** `skills/hb-flow.md` (Step 5, Action Registry)
- The Action Registry table in Step 5 lists actions like "Plan task into steps", "Add a step", etc. but does not include an entry routing to `hb-task-create` (creating a brand-new task). Add a row for it so `/hb-flow` can route "create a task" style requests.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing
- **Resolution:** Added a "Create a new task" row to the Action Registry table, routing to `hb-task-create` with args shape `<author/task-id> [--flavor <slug>]` and example phrasings "create a new task", "start a task for X". Disposition: **Addressed**.

---

### STEP-3-REVIEW-2: Derive flavor from user's natural language in step-add/task-create

- **file(s):** `skills/hb-flow.md` (Step 5, near Action Registry)
- When `/hb-flow` routes to `hb-task-step-add` or `hb-task-create`, those skills should always derive their `--flavor` from the user's provided natural-language request rather than leaving it unset/interactive. The user can still drop or update the derived flavor during that skill's own confirmation step.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing
- **Resolution:** Added `[--flavor <slug>]` to the "Create a new task" and "Add a step" rows' Args shape column, and added a bullet to Step 6 (Resolve target task/step) instructing `hb-flow` to derive a `--flavor <slug>` from the user's reply when the target skill is `hb-task-create` or `hb-task-step-add`, editable by the user at the Step 7 confirmation. Disposition: **Addressed**.

---

### STEP-3-REVIEW-3: Read facts store before invoking target skill

- **file(s):** `skills/hb-flow.md` (Step 8, Invoke)
- Step 8 (Invoke) currently calls the `Skill` tool directly without first reading `.hb/facts.md`. Add a step to read the facts store so relevant facts are available/passed along to the invoked skill.
- **source:** `TODO REVIEW` in commit `580febe85456354e3b9d610d224d0641dbb9378c` — delete comment from source file after addressing
- **Resolution:** No change made. The `Skill` tool only takes a skill name and an args string (the same string a user would type after the slash command) — there's no channel for `hb-flow` to hand facts content to the invoked skill through that call. Per `facts-write-subflow.md`, the facts store is already read as Part A by the four skills that consume it (`hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address`) as their own first step, run within the same session right after `hb-flow` invokes them. Having `hb-flow` read `.hb/facts.md` itself first would be a no-op duplication of logic already owned by the target skill, which conflicts with `hb-flow`'s stated design ("never re-deriving or duplicating the target skill's own logic"). Disposition: **Assessed**.

---

### STEP-3-REVIEW-4: Read facts store before asking user for next step

- **file(s):** `skills/hb-flow.md` (Step 4, Prompt for intent)
- Before Step 4 asks "What would you like to do?" (or consumes an initial freeform request), `hb-flow` should read `.hb/facts.md` for its own use. Facts may help it inform which next-action suggestions to surface or how to interpret the user's reply, without needing to pass anything to the invoked skill.
- **Resolution:** Added a `hb-sdk facts read` call at the start of Step 4, capturing output as `$FACTS`, with guidance to take it into account when framing example phrasings or interpreting the reply — distinct from STEP-3-REVIEW-3, since this use is entirely internal to `hb-flow`'s own reasoning and doesn't require passing anything through the `Skill` tool call. Disposition: **Addressed**.

---

### STEP-3-REVIEW-5: Add --flavor flag to hb-task-create

- **file(s):** `skills/hb-task-create.md` (Inputs)
- `hb-task-create` should gain a `--flavor <slug>` flag, similar to `hb-task-step-add`'s, so that `hb-flow`'s STEP-3-REVIEW-2 resolution (which added `[--flavor <slug>]` to `hb-task-create`'s args shape in the Action Registry) is actually backed by a real flag on the target skill.
- **source:** `TODO REVIEW` in commit `988249a14954ac148f95df887937e2d7c5bccbb5` — delete comment from source file after addressing
- **Resolution:** Did not add a `--flavor` flag to `hb-task-create` — its premise doesn't hold. `hb-sdk task create` takes a fully-qualified `<author/task-id>` name where the flavor (`task_extra`) is already part of the name string (e.g. `author/abc-123-some-stuff`, per `structure.md`); `hb-task-step-add` needs a separate `--flavor` flag only because the SDK assigns the step number itself, so the caller can't pre-embed the flavor into a step ref. The actual bug was in `hb-flow.md`'s STEP-3-REVIEW-2 resolution, which incorrectly gave `hb-task-create` a `[--flavor <slug>]` args-shape entry it doesn't support. Fixed there instead: reverted the Action Registry's "Create a new task" row to plain `<author/task-id>`, and updated the Step 6 derivation bullet so `hb-flow` appends the derived slug directly onto the task-id for `hb-task-create` while still passing a separate `--flavor` for `hb-task-step-add`. Disposition: **Addressed** (in `hb-flow.md`, not `hb-task-create.md`).

---

### STEP-3-REVIEW-6: Read fact store before proceeding in hb-task-create and hb-task-step-add

- **file(s):** `skills/hb-task-create.md` (Step 1/2 boundary), `skills/hb-task-step-add.md` (Step 1/2 boundary)
- Both skills should read the facts store (`.hb/facts.md`) before proceeding past the help check, so relevant facts (e.g. naming conventions, past rejected approaches) can inform ticket seeding / interactive prompts.
- **source:** `TODO REVIEW` in commit `6ca33ea3eae94ec63bfe4e22779efe2ab92a2691` — delete comment from source file after addressing
- **Resolution:** Added an inline `hb-sdk facts read` call at the top of Step 2 in both `hb-task-create.md` and `hb-task-step-add.md`, capturing `$FACTS` for use during interactive ticket derivation. Did not wire these into `facts-write-subflow.md` (whose "Shared by" scope is explicitly `hb-task-step-plan`, `hb-task-plan`, `hb-task-step-execute`, `hb-task-step-review-address`) — those four skills produce judgment-laden artifacts (plans, execution notes, review resolutions) that can also *surface* new facts worth writing back (Part B). `hb-task-create`/`hb-task-step-add` mostly transcribe or derive `ticket.md` directly from the user's own words via `interactive-ticket-subflow.md`, with no comparable write-back moment — so a read-only inline call, matching the precedent `hb-flow.md` set for STEP-3-REVIEW-4, is the right-sized fix. Disposition: **Addressed**.

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
