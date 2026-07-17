# Background

<!--
  TICKET TEMPLATE — a ticket defines WHAT one step must achieve and HOW we'll know
  it's done. It is the source of truth the plan, execution, and review all trace
  back to. It is written BEFORE the plan, and it owns exactly two things: the
  motivation (Background) and the contract (Acceptance Criteria).

  A ticket says WHAT and WHY, not HOW. Name the behavior, the evidence, and the
  pass/fail criteria — leave the implementation design to `plan.md`. (Pointing at a
  specific file/function the change must touch is fine when it's part of the
  contract; describing the algorithm to write there is the plan's job.)

  Scale the prose to the change. A small, self-evident step is a one-line Background
  plus a short numbered AC list — do not pad it. A step that hinges on a non-obvious
  discovery, a conflict to resolve, or a class of cases earns a rich Background with
  evidence and verified examples. Let the difficulty set the length.

  The one rule that doesn't scale down: every acceptance criterion must be concrete
  and checkable. "Handles X correctly" is not a criterion; "input A produces output
  B; malformed input is skipped without error" is.

  Verbosity limits, every section (a lettered sub-heading — `## A.`, `## B.`, … —
  counts as its own section for this cap): prefer bullets/numbered items over prose
  paragraphs. Cap paragraphs at 3 sentences, bullets/list items at 1 sentence each,
  sentences at 120 characters, and bullets per section at 5 — split or summarize
  rather than exceed these.

  Keep the three top-level headings (`# Background`, `# Acceptance Criteria`,
  `# Out of scope`). Add `# Goal` when a one-line statement of intent helps. Adapt
  any toolchain references to this project.
-->

State the motivation. For a small step this can be a single line:

- <one-sentence statement of what we need and why>

For a step that needs justifying, write the fuller story — include only the
elements that actually apply:

- **Prior state / what came before** — what earlier steps built, the current
  behavior or metric this step changes (cite it: a count, a file:line, an observed
  output). Establishes the baseline.
- **The problem / gap** — what's wrong or missing today, concretely, with a
  reproduction or example of the bad behavior.
- **The motivating case** — one specific input that fails now and must work after
  (the case the acceptance criteria will pin down exactly).
- **The key discovery / approach** — when the step hinges on a non-obvious insight
  (a signal that exists on disk, a structural pattern), state it and the **evidence**
  that it's real (what you inspected, counts, verified examples). A table of
  verified examples is ideal:

  | input | … | expected resolution |
  |---|---|---|
  | … | … | … |

- **Conflicts / ambiguity to handle** — known hard cases the solution must get
  right (collisions, drift, precedence between sources), each with the ground-truth
  answer. These become acceptance criteria.

---

# Goal

<!-- Optional. A one-to-three sentence statement of what this step achieves, when
that crisp framing helps orient the reader before the criteria. Omit for small
steps where Background already makes it obvious. -->

<concise statement of the intended outcome>

---

# Acceptance Criteria

A numbered list of concrete, checkable conditions. For a small step, a flat list is
right. For a larger step, group criteria under lettered headings (`## A. <theme>`,
`## B. <theme>`, …) — common themes that recur:

- **The core behavior / feature** — what the change must do, including exact
  output/schema/format where that's part of the contract (columns, flags, modes,
  values, ordering).
- **Specific cases that must resolve exactly** — the verified examples from
  Background, restated as pass/fail assertions (input X → output Y, verbatim).
- **Conflict / precedence handling** — the deterministic rule for collisions and
  the canonical regression that proves it.
- **Safe degradation** — behavior when the input/signal is absent or malformed
  (skip, empty result, no error) — stated so it's testable.
- **Invariants preserved** — properties from prior steps that must still hold on
  the regenerated output (schema invariants, no-empty-field rules, gating rules,
  specific prior cases that must not regress).
- **Tests** — the change is covered by tests (prefer hermetic fixtures over the
  live environment); existing suites pass **unchanged** as a non-regression guard;
  name the specific cases/edges to cover.
- **Measurement** — the observable, after-the-fact check that the goal landed
  (a metric moves in the expected direction; the motivating case now behaves
  correctly; counts match an expectation).

Write criteria as conditions, with nested sub-points where one criterion has parts:

1. <top-level criterion — a checkable condition>
    1. <sub-condition / detail>
    2. <sub-condition / detail>
2. <next criterion>

---

# Out of scope

<!-- Include for any non-trivial step; omit only when truly nothing needs fencing
off. -->

Bullet what this step deliberately does **not** do — so the plan and review don't
expand the contract:

- adjacent cases or signals **deferred** to a follow-up step (point to it);
- things that are **reported/flagged** rather than changed here;
- data/files that must **not** be mutated;
- standing exclusions inherited from prior steps or the ticket's framing.
