# Background

hb-016 added a project-level facts store (`.hb/facts.md`, written via `hb-sdk facts write`) and wired it into planning and execution skills. The shared `structure.md` reference doc, which documents the `.hb/` folder layout, was never updated to mention it, leaving the file undocumented for anyone consulting that reference.

---

# Acceptance Criteria

1. `structure.md` lists `facts.md` as a top-level file in `.hb/` (alongside `task/`), with a one-line description of its purpose (persistent, project-level facts store).
2. `structure.md` notes that `facts.md` is created/maintained via `hb-sdk facts write`, consistent with how other generated files (e.g. `ticket.md`, `plan.md`) note their creators.
3. The "Structure Examples" tree diagram(s) are updated to include `facts.md` so the examples stay consistent with the prose description.
