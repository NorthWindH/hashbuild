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

  Size guidance (not programmatically enforced — apply judgement):
  - Target size: <= 100 lines.
  - Hard maximum: 1000 lines.
  - Each line: <= 120 characters.

  When appending would exceed the target, prune stale or superseded facts
  first rather than growing unbounded — `hb-sdk facts write` always overwrites
  the full file, so pruning is just a matter of composing the trimmed content
  before writing it back.
-->
