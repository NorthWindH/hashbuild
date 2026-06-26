# Background

Hashbuild currently supports tasks and steps as its primary work objects. A lighter-weight object is needed for capturing ideas — quick, unstructured notes (a single line or a few lines) that can eventually be promoted into tasks or task steps. This ticket introduces an "idea" concept stored per-author in `.hb/idea/<author>/ideas.json`, managed through four new skills (`hb-idea-add`, `hb-idea-remove`, `hb-idea-list`, `hb-idea-promote`) backed by new `hb-sdk idea` subcommands.

---

# Acceptance Criteria

1. Ideas are stored in `.hb/idea/<author>/ideas.json`; each idea has an index-based ID in the form `<author>/<index>`.
2. `hb-idea-add <author>` accepts a required `<author>` positional arg, prompts the user to enter freeform idea content, persists the idea via `hb-sdk idea add`, and prints the resulting `<author>/<index>` ID.
3. `hb-idea-remove <author>/<index>` accepts an idea ID positional arg and drops that idea via `hb-sdk idea remove`.
4. `hb-idea-list` supports three invocation forms:
    1. No arg — presents all ideas from all authors.
    2. `<author>` — presents all ideas from that author.
    3. `<author>/<index>` — presents the single matching idea.
5. `hb-idea-promote <author>/<index> <target>` promotes an idea to a task or task step:
    1. If `<target>` is `<author>/<task_id>`, seeds `hb-task-create` interactive mode with the idea's content.
    2. If `<target>` is `<author>/<task_id>/step-n`, seeds `hb-task-step-add` interactive mode with the idea's content.
    3. In both cases the user may expand on the content before the ticket is written, then the idea is removed via `hb-sdk idea remove`.
6. All five skills are backed by new `hb-sdk` subcommands: `idea add`, `idea remove`, `idea show` (accepting optional `<author>` and `<author>/<index>` args to scope the result), and `idea set-content`.
7. `hb-idea-list` output format is governed by a new `idea-list-template.md` reference file so that presentation is consistent across invocation forms.
8. `README.md` is updated to document the four new skills (`hb-idea-add`, `hb-idea-remove`, `hb-idea-list`, `hb-idea-promote`) — purpose, arguments, and example usage.
9. `skills/references/structure.md` is updated to document the idea file location (`.hb/idea/<author>/ideas.json`) and the structure of the ideas JSON (shape of each idea entry and the `<author>/<index>` ID scheme).
10. `hb-idea-edit <author>/<index>` allows interactive reformulation of an existing idea:
    1. Seeds the interactive session with the idea's current content.
    2. Prompts the user to describe freeform what they want to do with the content.
    3. Applies the requested changes and presents the reformulated content for confirmation.
    4. On confirmation, persists the updated content via `hb-sdk idea set-content`.

---

# Out of scope

- Bulk promotion or bulk removal of multiple ideas at once.
