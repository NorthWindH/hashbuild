# Background

With all five idea skills implemented (steps 0–3), this step updates the two documentation files that describe the hashbuild framework to users and skills: `README.md` gets entries for each new skill, and `skills/references/structure.md` gets the idea storage location and JSON shape.

---

# Acceptance Criteria

1. `README.md` is updated to document all five new skills (`hb-idea-add`, `hb-idea-remove`, `hb-idea-list`, `hb-idea-promote`, `hb-idea-edit`):
    1. Each entry states the skill's purpose, its argument(s), and at least one example invocation.
    2. The entries appear in a logical location within the existing README structure (alongside or after the existing skill listings).
2. `skills/references/structure.md` is updated to document the idea storage layer:
    1. File location: `.hb/idea/<author>/ideas.json`.
    2. Shape of each idea entry (fields: `index`, `content`, and any additional fields added in step-0).
    3. The `<author>/<index>` ID scheme.
3. No other files are modified; existing README and structure.md content is preserved.

---

# Out of scope

- Changes to skill files or the SDK — all implementation is complete in steps 0–3.
- `idea-list-template.md` — created in step-1.
