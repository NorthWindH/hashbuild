# Background

`hb-sdk` has no `idea` subcommands or storage support. This step adds the data layer: the `.hb/idea/<author>/ideas.json` file format and the four SDK subcommands (`idea add`, `idea remove`, `idea show`, `idea set-content`) that all idea skills will call. Skills built in later steps depend on these subcommands existing and being correct.

---

# Acceptance Criteria

1. Ideas are stored in `.hb/idea/<author>/ideas.json`; the file is created on first write and the `.hb/idea/<author>/` directory is created if absent.
2. Each entry in `ideas.json` is a JSON object with at minimum two fields: `index` (int, monotonically increasing, never reused) and `content` (str). Additional metadata fields are allowed but not required.
3. `hb-sdk idea add <author> <content>` appends a new idea entry, assigns the next available index, and prints the resulting ID in the form `<author>/<index>` to stdout.
4. `hb-sdk idea remove <author>/<index>` removes the matching entry from `ideas.json`; exits non-zero with a clear error message if the ID does not exist.
5. `hb-sdk idea show` supports three forms:
    1. No extra arg — prints all ideas from all authors as JSON array.
    2. `<author>` — prints all ideas for that author as JSON array.
    3. `<author>/<index>` — prints the single matching idea as a JSON object; exits non-zero if not found.
6. `hb-sdk idea set-content <author>/<index> <new_content>` replaces the `content` field of the matching entry; exits non-zero if the ID does not exist.
7. All subcommands surface a clear error and exit non-zero when `.hb/` is not initialized.
8. Existing `hb-sdk` subcommands and their behaviour are unchanged.

---

# Out of scope

- Skill files (`hb-idea-add`, etc.) — deferred to step-1 through step-3.
- `idea-list-template.md` reference file — deferred to step-1.
- Bulk operations — excluded per task ticket.
