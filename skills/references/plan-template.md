# Step N Plan — <Concise Change Name>

<!--
  PLAN TEMPLATE — a `plan.md` is the executable design for ONE atomic step of a
  larger ticket. It is written AFTER the step's acceptance criteria (`ticket.md`)
  and BEFORE any code. Its job: make execution mechanical — name the exact files,
  symbols, signatures, rules, and shell/test-checkable verification, so whoever
  executes it (human or agent) makes no design decisions of their own.

  Principles, in priority order:
  1. Evidence over assertion. Every load-bearing claim cites something real:
     file:line, a verified count, an observed input/output shape. "Confirmed live,
     not assumed."
  2. Specific over abstract. Real symbol names and signatures, not "a function
     that does X."
  3. Explicit boundaries. Say what does NOT change as clearly as what does.
  4. Traceable. Every acceptance criterion maps to a section, a test, and a
     verification step.

  Fill every section. If a section genuinely doesn't apply, keep the heading and
  write "N/A — <reason>" rather than deleting it silently. Use tables wherever the
  content is enumerable (tiers, precedence, file changes, AC mapping). Adapt the
  build/test/verify commands to this project's actual toolchain.
-->

One-paragraph framing: what this step changes and why. Lead with the **motivating
case** — a concrete, currently-failing (or missing) behavior and how it fails
today — then the **general class** it represents (with a count or scope if known),
and the headline scope boundary in one sentence (e.g. "behavior change only, no
new public API" / "additive, no existing callers affected"). End with the single
externally observable effect once this lands.

Source ticket: `./ticket.md`. Builds on the **shipped** work from prior steps
(`<paths/components this step extends>`) and the state they left behind. This plan
targets the code as it exists **now**.

> **Design decision — <the one choice that needs defending>.** When the ticket
> contains an internal tension (two criteria that pull against each other), or
> when this plan deviates from the ticket's framing based on what the code/data
> actually shows, surface it here up front: state the tension, the chosen
> resolution, the single guard or precondition that makes the resolution correct,
> and pointers to §1 (design) and the AC-traceability table (§<n>). Deviations
> must be evidence-driven and explicit — never silent.

---

## 0. Current-state facts (verified during planning)

Ground the plan in reality. State what you inspected (which files, which
data/fixtures, which runtime behavior) and that these facts are **confirmed, not
assumed**. Give the exact command or location for anything a reviewer would want
to re-check. Each fact listed here should be load-bearing for a decision later in
the plan — if it doesn't drive a choice, cut it. Typically covers:

- The exact current behavior/shape this step keys on, with a **concrete example**
  (real input → real output, or real code at `file:line`).
- The single chokepoint(s) where the change must land, and the **blast radius**
  (who calls the code being changed).
- Counts/bounds that size the work (how many cases match, how many are edge cases
  or must be excluded).
- Any **confusable / noise** cases the change must NOT affect, and the rule that
  distinguishes signal from noise.
- The ground truth for any conflict or ambiguous case the ticket cares about.

### 0.1 Impact (before → after)

State the current baseline (a metric, a count, a behavior) and the precise
expected change. A small before/after table for each affected case class is ideal.
Be explicit about the *kind* of change: additive-only, behavior-preserving
refactor, or output-altering — each carries a different regression risk.

### 0.2 Non-regression proof / risk (when the change could touch existing behavior)

If the step could alter behavior that is already correct, prove it can't — or name
the risk you can only *verify* (not prove) and defer it to a concrete check in
§Verification. Enumerate at-risk cases in a table (`case | current behavior | why
it can't change`) and name the guard protecting each. A change that is purely
additive can state that and skip the table.

---

## 1. Design overview

The shape of the solution before the file-level detail.

- If the change introduces **ordered alternatives** (first match wins, or a
  precedence among sources/strategies), show them as a table and/or a precedence
  chain, and state the **tie-break** and any **suppression/gating invariant** being
  preserved or extended:

  | Tier / strategy | Trigger | Result | New? |
  |---|---|---|---|
  | … | … | … | … |

  ```
  precedence:  highest  ≥  …  ≥  lowest        (tie-break: <deterministic rule>)
  ```

- If it's a single linear change, describe the new control flow / data flow in a
  few sentences or a small diagram.

End with **Alternatives considered and rejected** — each with a one-line reason
(wrong layer, breaks an invariant, higher cost for no gain, fails an AC, etc.).
This is where you show the chosen design wasn't the only option.

---

## 2. <Core component> — specification

The new or changed unit(s), one concern per unit (mirror the codebase's existing
conventions and idioms). For each, give:

- **Data model / types** — the structures involved, with field-level intent.
- **Interfaces / signatures** — exact names and shapes, each with a one-line
  contract. Mark each as **new**, **refactor (signature preserved)**, or
  **unchanged** — the "unchanged" labels are what let you claim existing callers
  and tests are unaffected.
- **Algorithm / rules** — the precise logic: the matching/parsing/transformation
  rules, ordering, dedup keys, edge-case handling. Tables for any enumerable
  grammar or mapping.
- **Failure / degradation contract** — behavior on missing, malformed, or
  unexpected input (e.g. skip-and-continue, return empty + no error, fail loudly).
  State it explicitly so it's testable.
- **Conflict resolution** — the deterministic rule when multiple candidates or
  sources collide.

Show real code for the load-bearing parts; pseudocode is fine for mechanical loops
whose contract is already unambiguous.

---

## 3. Integration / wiring

How the new unit connects to existing code, with explicit "changes" vs. "untouched"
boundaries:

- The exact call sites edited (function, and the line/expression replaced).
- Whether public signatures are preserved, and the reason (usually: keep existing
  callers and tests green).
- Whether configuration, build wiring, entry points, scripts, or dependency
  manifests change. If the step is self-contained (no wiring change), say so and
  explain why that's possible.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `<path>` | **new** / **edit** / **extend** — one-line summary; name what within it stays untouched |
| … | … |

Call out dependency-manifest or lockfile effects, and assert what must remain
unchanged (e.g. "lockfile unchanged — no new dependency").

---

## 5. Tests

Match the project's existing test framework, layout, and style (note which
existing test file you're mirroring). State the fixture strategy (in-memory,
temp dir, recorded fixtures — prefer hermetic over live-environment). Group by
unit; for each, name the test cases and what each asserts. Cover at minimum:

- **Happy path** for each variant the change introduces.
- **The motivating case** and any specific scenarios the ticket enumerates.
- **Conflict / precedence / determinism**.
- **Negative cases** — inputs that must NOT trigger the new behavior (guards
  against over-matching).
- **Failure / degradation** — malformed or missing input behaves per the §2 contract.
- **Non-regression** — name the existing suites that must pass **unchanged**, and
  why this change is additive to them.

---

## 6. Verification (after implementation)

Numbered, copy-pasteable, and checkable by a person or CI. Adapt commands to the
project toolchain. A typical sequence:

1. **Build + static checks + full test run** are clean/green.
2. **Capture a pre-change baseline** of any artifact/output you'll diff for
   non-regression (snapshot it before regenerating).
3. **Exercise the real change** end-to-end (run the app / regenerate the artifact /
   trigger the path).
4. **Per-AC checks** — a concrete, observable check that directly demonstrates each
   acceptance criterion (the motivating case now behaves correctly; expected
   counts/values; a before/after diff showing *only* the intended change).
5. **Invariant checks** — assert the structural invariants the change must preserve
   (schema, required fields, value domains, no unintended side effects). Note which
   check is authoritative (usually the test suite) vs. a quick smoke.
6. **Scope check** — only the intended files changed; name what must stay untouched.

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §<n> | |
| … | … | |

Every acceptance criterion from `ticket.md` maps to a concrete section — and,
ideally, to a test (§5) and a verification step (§6). This table is the contract
that the plan actually covers the ticket.

---

## 8. Out of scope (per ticket)

Bullet the boundaries — what this step deliberately does **not** do: adjacent cases
deferred to follow-up steps, things that are *reported/flagged* rather than
*changed*, and any standing exclusions inherited from the ticket or prior steps.
