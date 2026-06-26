# Background

This step adds `hb-idea-edit` — a skill for interactively reformulating the content of an existing idea. The user describes what they want to change, the skill applies the change and presents the result for confirmation, and on confirmation persists the updated content via `hb-sdk idea set-content`.

---

# Acceptance Criteria

1. `hb-idea-edit <author>/<index>` is a new skill file at `skills/hb-idea-edit.md`.
2. Accepts a required `<author>/<index>` positional argument; exits non-zero with a clear error if the idea does not exist.
3. Fetches the idea's current content via `hb-sdk idea show <author>/<index>` and displays it to the user.
4. Prompts the user to describe freeform what they want to change about the content (e.g. "make it more concise", "reframe as a problem statement").
5. Applies the requested changes and presents the reformulated content to the user for confirmation before persisting.
6. On confirmation, calls `hb-sdk idea set-content <author>/<index> <new_content>` to persist the update; confirms success to the user.
7. If the user rejects the reformulation, prompts them to describe what to change and repeats from step 4; the loop continues until the user confirms or cancels.
8. If the user cancels at any point, the idea content is left unchanged.
9. The skill includes a `--help` / `-h` flag that prints usage and exits.

---

# Out of scope

- `README.md` and `structure.md` updates — deferred to step-4.
- Bulk editing of multiple ideas — excluded per task ticket.
