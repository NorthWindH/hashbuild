# Step N Execution — <Concise Change Name>

<!--
  EXECUTION TEMPLATE — an execution summary is the record of what actually
  happened when a `plan.md` was carried out. It is written AFTER the code is
  shipped and verified, and is the durable answer to "what landed, did it match
  the plan, and how do we know it works?"

  It is a factual report, not a re-plan. Its value is in three things:
  1. Ground truth — what was actually built, with real symbol/file names and real
     before→after numbers (not the plan's estimates).
  2. Honest deltas — every deviation from the plan, why it happened, and why the
     result is still correct (or what was deferred). Silence here is a defect.
  3. Evidence — verification output a reviewer can trust, mapping back to the
     acceptance criteria.

  Name the file `execution-<ISO-8601 timestamp slug>.md` so multiple executions of the
  same step are ordered and distinct. Fill every section; if one doesn't apply,
  write "None" / "N/A — <reason>" rather than dropping it. Adapt all toolchain
  commands to this project.
-->

**Executed:** <ISO-8601 timestamp slug>
**Plan:** `./plan.md` · **Ticket:** `./ticket.md`
**Commit / Branch:** `<sha or branch>` — *<commit subject, if applicable>*
**Result:** <✅ Complete — all acceptance criteria met, gates green | ⚠️ Partial — see deviations | ❌ Blocked>

---

## Outcome

A few sentences: what shipped and the headline effect. Lead with the **motivating
case** from the plan now resolved (the concrete before→after), then the **general
result** with the key metric stated as `baseline → after`. State the scope
boundary that held (e.g. "additive only — no pre-existing behavior changed";
"behavior change only — no public API/config change"). One line on gate status
(tests green, build/lint clean).

---

## What was built / changed

The actual implementation, by file. Use real symbol names. Mark each file
**new** / **edit** / **extend**, and — critically — name what within touched
files (and which whole files/modules) was left **unchanged**, since that's what
backs the non-regression claim.

| File | Change |
|---|---|
| `<path>` | **new** / **edit** — one-line summary; note what stays untouched |
| … | … |

State dependency-manifest / lockfile effects (or "no new dependency; manifests
unchanged"). For larger changes, optionally add a short **Design as built**
paragraph describing the design that actually landed (tiers, control flow, guards)
when it's worth capturing distinct from the plan's design.

---

## Deviations from plan

The most important section. For each deviation: **what** the plan said, **what was
done instead**, **why** (the trigger — a compile error, a wrong result on real
input, an order-dependence, a missed edge case), and **why the result is still
correct** (or how it was covered by a new test). If a deviation changed a count or
outcome, reconcile it explicitly.

Write **"None of substance"** (with any trivial in-flight fixes noted) when the
implementation followed the plan — but only after genuinely checking. Common honest
deltas worth recording even when small:
- estimates in the plan vs. actual counts (and why they differ);
- a guard/refinement added during execution that the plan didn't foresee;
- a plan-anticipated side effect that didn't materialize (and why).

---

## Verification

The evidence the change works and conforms. Adapt commands to the toolchain. A
gate table plus targeted per-criterion checks:

| Check | Result |
|---|---|
| Build | <pass/clean> |
| Full test suite | <pass> |
| Static analysis / lint | <clean> |
| Formatter | <clean> |
| End-to-end run / artifact regeneration | <exit 0 / produced> |
| Scope check (only intended files changed) | <confirmed> |

Then the **per-AC / per-behavior checks** with *actual observed output* pasted in
(the motivating case behaving correctly; before→after metric table; a diff showing
only the intended change; invariant checks reading zero/empty). Quote real output,
not a paraphrase — this is what makes the summary auditable.

```
<paste the actual command output that demonstrates the criterion>
```

---

## Acceptance-criteria status

State which ACs are satisfied and point to the plan's traceability table. If any
AC is partial or interpreted (e.g. an approximate-count criterion), say so plainly
and explain why the result is still spec-faithful.

---

## Tests added

List the new/changed test cases by name, each with the one behavior it locks down
(happy path, motivating case, conflict/determinism, negative/guard case, safe
degradation, deviation guard). Confirm the existing suites that were required to
pass **unchanged** did so.

---

## Honest notes (optional)

Caveats a future reader deserves: where the heuristic/change is correct in design
but its practical benefit isn't demonstrated by the current data; pre-existing
quirks observed but deliberately left alone (with why); anything surprising about
the real environment. Keep it honest — this is where over-claiming gets corrected.

---

## Follow-up raised / Deferred / Out of scope

Work this step surfaced or deliberately left for later: follow-up tickets created
(with pointers), items the plan deferred to a subsequent step, and residue that is
*reported/flagged* rather than fixed here. Link the next step's ticket where one
was spun off.
