# Background

With SDK idea subcommands in place (step-0), this step adds the three core idea skills (`hb-idea-add`, `hb-idea-remove`, `hb-idea-list`) and the `idea-list-template.md` reference file that governs list output format.

---

# Acceptance Criteria

1. `hb-idea-add <author>` is a new skill file at `skills/hb-idea-add.md`:
    1. Accepts a required `<author>` positional argument.
    2. Prompts the user to enter freeform idea content (multi-line input accepted).
    3. Calls `hb-sdk idea add <author> <content>` to persist the idea.
    4. Prints the resulting `<author>/<index>` ID to the user.
    5. Exits with a clear error if `<author>` is omitted.
2. `hb-idea-remove <author>/<index>` is a new skill file at `skills/hb-idea-remove.md`:
    1. Accepts a required `<author>/<index>` positional argument.
    2. Calls `hb-sdk idea remove <author>/<index>`.
    3. Confirms removal to the user; surfaces SDK errors verbatim.
3. `hb-idea-list` is a new skill file at `skills/hb-idea-list.md`:
    1. Supports three invocation forms (no arg, `<author>`, `<author>/<index>`).
    2. Calls `hb-sdk idea show` with the appropriate argument for each form.
    3. Renders the result using `idea-list-template.md` for consistent presentation.
    4. Prints a friendly "no ideas found" message when the result set is empty.
4. `skills/references/idea-list-template.md` is created and defines the output format for all three invocation forms of `hb-idea-list`; each idea entry shows at minimum its ID and content.
5. All three skills include a `--help` / `-h` flag that prints usage and exits.

---

# Out of scope

- `hb-idea-promote` and `hb-idea-edit` — deferred to step-2 and step-3.
- `README.md` and `structure.md` documentation updates — deferred to step-4.
- Bulk operations — excluded per task ticket.
