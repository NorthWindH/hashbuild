# Background

Hashbuild currently supports tasks and steps as its primary work objects. A lighter-weight object is needed for capturing ideas — quick, unstructured notes (a single line or a few lines) that can eventually be promoted into tasks. This ticket introduces an "idea" concept stored per-author in `.hb/idea/<author>/ideas.json`, managed through four new skills (`hb-idea-add`, `hb-idea-remove`, `hb-idea-list`, `hb-idea-promote`) backed by new `hb-sdk idea` subcommands.

---

# Acceptance Criteria

1. Ideas are stored in `.hb/idea/<author>/ideas.json`; each idea has an index-based ID in the form `<author>/<index>`.
2. `hb-idea-add <author>` accepts a required `<author>` positional arg, prompts the user to enter freeform idea content, persists the idea via `hb-sdk idea add`, and prints the resulting `<author>/<index>` ID.
3. `hb-idea-remove <author>/<index>` accepts an idea ID positional arg and drops that idea via `hb-sdk idea remove`.
4. `hb-idea-list` supports three invocation forms:
    1. No arg — presents all ideas from all authors.
    2. `<author>` — presents all ideas from that author.
    3. `<author>/<index>` — presents the single matching idea.
5. `hb-idea-promote <author>/<index> <author>/<task_id>` promotes an idea to a task by seeding `hb-task-create` interactive mode with the idea's content (the user may expand on it before the ticket is written), then removes the idea from the listing via `hb-sdk idea remove`.
6. All four skills are backed by new `hb-sdk` subcommands: `idea add`, `idea remove`, and `idea show` (accepting optional `<author>` and `<author>/<index>` args to scope the result).
7. `hb-idea-list` output format is governed by a new `idea-list-template.md` reference file so that presentation is consistent across invocation forms.

---

# Out of scope

- In-place editing of existing ideas (update/replace).
- Bulk promotion or bulk removal of multiple ideas at once.
