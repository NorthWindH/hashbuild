# Facts Store

<!--
  FACTS TEMPLATE — guidance for whichever skill populates `.hb/facts.md` via
  `hb-sdk facts write`. This file is NOT copied into `.hb/facts.md`; it exists
  to be read before writing facts, the same way `ticket-template.md` is read
  before drafting a ticket.

  A fact is a durable, project-level observation worth carrying across tasks —
  not task-scoped context (that belongs in `ticket.md`/`plan.md`) and not a
  transient in-progress note. Prefer short, dated, falsifiable statements over
  prose narrative.

  A fact earns its place only if it would change how a *future* planning,
  execution, or review step reasons or acts. Before adding one, ask "which
  future step reads this and does something differently because of it?" — if
  the honest answer is "none, it's just a record that something happened,"
  drop it. Two categories that reliably fail this test and should NOT be
  added, however tempting during execution:
  - **Shipped/status announcements** ("X now exists", "Y was added with Z
    tool") — this is already the git log and the execution summary's job;
    restating it here adds no new information a future step could act on.
  - **Messages meant for the human right now** ("test this next", "this is
    unverified, try it in a fresh session") — these belong in the skill's own
    user-facing output (its "Prompt user" step or final report), not the
    facts store. The facts store is read by future *skill invocations*, not
    relayed to a person as a to-do.

  Size guidance (not programmatically enforced — apply judgement):
  - Target size: <= 100 lines.
  - Hard maximum: 1000 lines.
  - Each line: <= 120 characters.

  When appending would exceed the target, prune stale or superseded facts
  first rather than growing unbounded — `hb-sdk facts write` always overwrites
  the full file, so pruning is just a matter of composing the trimmed content
  before writing it back.
-->
