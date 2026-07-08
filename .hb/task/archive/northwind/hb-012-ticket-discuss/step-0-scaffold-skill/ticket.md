# Background

This is the first step of `hb-012-ticket-discuss`. The task delivers a new
`hb-ticket-discuss` skill that runs hashbuild's interactive ticket-creation flow
to produce a **standalone** ticket (one that does not belong to any hashbuild
task or step), and later pushes it to Jira.

This step scaffolds that skill and wires up ticket generation only. It addresses
task acceptance criteria 1, 2, 3, and the structural half of 5. The interactive
flow already exists as the shared subflow at
`skills/references/interactive-ticket-subflow.md` (reused today by
`hb-task-create` and `hb-task-step-add`); the key design point for this step is
that the subflow is driven with `$TARGET_PATH` pointing at a scratch location
(e.g. `/tmp`) and **no** `hb-sdk task` calls, so nothing is written into a task
or step folder. Jira integration is deferred to step 1.

---

# Acceptance Criteria

1. A new skill file exists at `skills/hb-ticket-discuss.md`.
2. Its frontmatter matches sibling `hb-*` skills: a `name`, `argument-hint`,
   `description` (leading with the `/hb-ticket-discuss [--help] ...` usage line),
   and an `allowed-tools` line scoped consistently with siblings.
3. The skill body follows the sibling structure: a `## Inputs` table, a
   `## Reference Files` section, and numbered `## Steps`.
4. Step 1 of the skill is a help check: when the first argument is `help`,
   `--help`, or `-h`, it follows `references/skill-help.md` and stops.
5. The skill reuses the existing
   `skills/references/interactive-ticket-subflow.md` (it references that file
   rather than duplicating the prompt/transform/write logic), driving it with
   `$TARGET_PATH` set to a scratch path so the generated `ticket.md` is
   **standalone**.
6. The skill makes **no** `hb-sdk task` calls and creates **no** task or step
   folder; the generated ticket lives only at the scratch path.
7. After generating the ticket, the skill emits the ticket content to stdout
   (the copy-paste output path; this is also the fallback that step 1 will keep
   when no Jira MCP is available).
8. Running `/hb-ticket-discuss --help` prints help and stops without generating a
   ticket.

---

# Out of scope

- Any Jira / Atlassian MCP integration — deferred to step 1.
- Changes to the shared `interactive-ticket-subflow.md` or to
  `hb-task-create` / `hb-task-step-add` beyond what is strictly required to reuse
  the subflow standalone (ideally none).
- Registering the skill anywhere beyond creating the skill file itself.
