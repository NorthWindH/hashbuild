# Background

Ten `hb-*` skills each end with a "Prompt user" step that hard-codes the exact next slash command(s) the user should run next, e.g.:

- `skills/hb-task-plan.md:97` — "run `/hb-task-step-plan <name>/0`..."
- `skills/hb-init.md:48` — "run `/hb-task-create`..."
- `skills/hb-task-archive.md:57` — "run `/hb-status`... or `/hb-task-create`..."
- `skills/hb-task-unarchive.md:53` — "run `/hb-status`... or `/hb-task-step-add`..."
- `skills/hb-task-step-review-init.md:45` — "run `/hb-task-step-review-address <step_ref>`..."
- `skills/hb-task-step-review-address.md:237` — "run `/hb-task-step-add <name>` then `/hb-task-step-plan`... run `/hb-task-archive <name>`..."
- `skills/hb-task-step-add.md:82` and `:86` — "run `/hb-task-step-plan <step_ref>`..."
- `skills/hb-task-step-execute.md:97` — "run `/hb-task-step-review-address <step_ref>`... run `/hb-task-step-review-init <step_ref>`... run `/hb-task-step-add <name>`..."
- `skills/hb-task-step-plan.md:83` — "run `/hb-task-step-execute <step_ref>`..."
- `skills/hb-task-create.md:80` and `:84` — "run `/hb-task-plan <name>`... run `/hb-task-step-add <name>`..."

Now that `/hb-flow` (`skills/hb-flow.md`) exists as the single entry point that reads `.hb` state and routes the user to the right next `hb-*` skill (via its Action Registry and `hb-sdk state next-action`), each skill re-deriving and hard-coding its own next-step guidance is redundant with — and can drift out of sync with — `hb-flow`'s routing logic. It also bypasses the `/clear`-then-`/hb-flow` pattern this task (`northwind/hb-014-execution-state`) is establishing (see step-4: install-time hook nudging `/hb-flow` on new session/clear).

---

# Acceptance Criteria

1. Each of the ten "Prompt user" call-to-action messages listed above is rewritten to tell the user to `/clear` the conversation, then invoke `/hb-flow` — rather than naming a specific next `hb-*` skill/command.
2. Messages retain any outcome-specific context worth surfacing (e.g. "Step added with ticket" vs. "Step added" in `hb-task-step-add`, or the reminder that review is iterative in `hb-task-step-review-address`), only the hard-coded next-command portion is replaced.
3. `hb-flow.md` itself is left unchanged (it is the routing target, not a caller) — its own Action Registry already covers every transition being removed from the other skills.
4. No skill's "Prompt user" step is left calling out a specific next `hb-*` skill by name/command as the primary call to action; `/hb-flow` is uniformly the pointed-to next step across all ten files.

---

# Out of scope

- Changing `hb-flow`'s own resolution/routing logic (Action Registry, `hb-sdk state next-action` output format).
- Any change to skills outside the ten "Prompt user" call-to-action sites listed in Background.
