# Background

When the facts store CLI (planned/added in earlier steps of this task) writes updates to `facts.md`, those changes must be committed along with the rest of a skill's changes — otherwise facts updates could be silently left uncommitted. `committing.md` is the shared committing reference injected by every `hb-*` skill that commits, so documenting the rule there propagates it to all of them without touching each skill individually.

---

# Acceptance Criteria

1. `committing.md`'s staging step (`1. Stage relevant files ONLY`) notes that if a skill's execution updated `facts.md`, the updated `facts.md` must be included among the relevant files added to the commit.
2. The note is general — it does not name a specific skill — so it applies uniformly to every `hb-*` skill that references `committing.md` for its commit step.
