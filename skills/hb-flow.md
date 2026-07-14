---
name: hb-flow
argument-hint: "[--help] [<natural language request>]"
description: >
  /hb-flow [--help] [<natural language request>]

  Report where the active task/step left off and the recommended next action, then
  interpret a natural-language reply, confirm the resolved hb-* skill invocation with
  the user, and invoke it directly — including calls-to-action other than the
  currently recommended one.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Skill
---

# hb-flow

Report where the active task/step left off and the recommended next action, then interpret a natural-language reply, confirm the resolved `hb-*` skill invocation, and invoke it directly via the `Skill` tool — never re-deriving or duplicating the target skill's own logic.

## Inputs

| Parameter                    | Required | Description                                                                                                                                          |
| ---------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<natural language request>` | no       | Freeform description of what to do next (e.g. "execute this step", "archive this task"). If omitted, asked for interactively after the state report. |
| `help`, `--help`, `-h`       | no       | Print help and exit.                                                                                                                                 |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Gather state

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state show --format md
${CLAUDE_SKILL_DIR}/scripts/hb-sdk state next-action --format md
```

- capture the first command's output as `$LAST_ACTION`, the second's as `$NEXT_ACTIONS`
- if `$NEXT_ACTIONS` reports stage `not_initialized`, tell the user to run `/hb-init` first and stop
- if `$NEXT_ACTIONS` reports stage `no_active_tasks`, tell the user to run `/hb-task-create` and stop

### 3. Report

In plain language, report:

- where things left off (`$LAST_ACTION`, or "no prior recorded action" if it printed `No recorded state.`)
- the recommended next action(s) from `$NEXT_ACTIONS` — one block per active task, as printed

### 4. Prompt for intent

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- capture stdout as `$FACTS` (may be empty); never errors — if `.hb/facts.md` or `.hb/` itself is missing, proceed unaffected
- take `$FACTS` into account when framing example phrasings or interpreting the reply below (e.g. a fact naming a step already in flight can shape which example actions are surfaced), without requiring the user to restate it

If the initial invocation already carried a freeform request (the text after any flags), use it as the reply. Otherwise ask "What would you like to do?" and list 3-4 example phrasings drawn from the Action Registry (Step 5). Await the reply.

### 5. Resolve intent

Match the reply against the Action Registry below using semantic match, not exact keywords:

| Action                | Target skill                                                                                                                       | Args shape                    | Example phrasings                                                   |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------- |
| Create a new task     | `hb-task-create`                                                                                                                   | `<author/task-id> [--flavor <slug>]` | "create a new task", "start a task for X"                    |
| Plan task into steps  | `hb-task-plan`                                                                                                                     | `<task_ref>`                  | "plan this task", "break it into steps"                             |
| Add a step            | `hb-task-step-add`                                                                                                                 | `<task_ref> [--flavor <slug>]`| "add a step", "add another step"                                    |
| Plan a step           | `hb-task-step-plan`                                                                                                                | `<task_ref>/<step_n>`         | "plan the next step", "let's plan it", "go back and re-plan step 2" |
| Execute a step        | `hb-task-step-execute`                                                                                                             | `<task_ref>/<step_n>`         | "execute this step", "run the plan"                                 |
| Start/continue review | `hb-task-step-review-address` (default) or `hb-task-step-review-init` (only if the user explicitly wants to just seed `review.md`) | `<task_ref>/<step_n>`         | "let's review", "review this step", "just create review.md"         |
| Move to the next step | whichever skill/args `$NEXT_ACTIONS`'s `review_or_next`/`steps_complete` choices resolve to                                        | as printed in `$NEXT_ACTIONS` | "move on", "next step"                                              |
| Archive task          | `hb-task-archive`                                                                                                                  | `<task_ref>`                  | "archive this task", "close it out"                                 |
| Unarchive task        | `hb-task-unarchive`                                                                                                                | `<task_ref>`                  | "unarchive it", "restore this task"                                 |

On no confident match: ask a clarifying question and re-prompt (return to Step 4) — never guess.

### 6. Resolve target task/step

- If the reply names a task/step ref explicitly, validate it:
  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk task path <task_ref>
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step number <task_ref>/<step_n>
  ```
  Surface any SDK error verbatim and re-prompt (return to Step 4) rather than treating it as resolved.
- Otherwise derive it from data already gathered. Fetch it first if not already available this turn:

  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk summarize --format json
  ```

  - task-level actions ("plan task", "add a step", "archive", "unarchive"): if exactly one active task, use it; if more than one and none named, ask which one (never silently pick one)
  - "plan a step": the first step with `has_ticket=true, has_plan=false`; if the first pending step has no ticket, say so instead of resolving to it
  - "execute a step": the first step with `has_plan=true, has_execution=false`
  - "review": the first entry in `steps_needs_review`

- If still ambiguous, ask a clarifying question (return to Step 4) instead of guessing.
- If the target skill is `hb-task-create` or `hb-task-step-add`, derive a `--flavor <slug>` from the user's reply (lowercase, hyphen-separated, `[a-z-]` only) and include it in the resolved args. The user can drop or edit it at the Step 7 confirmation.

### 7. Confirm

State the exact resolved invocation (`/hb-<skill> <args>`, matching the target skill's real `argument-hint` shape) and ask the user to confirm it.

- **Declines / asks for something different:** ask what to change and return to Step 5 with the new information. Do not invoke anything.
- **Confirms:** proceed to Step 8.

### 8. Invoke

Call the `Skill` tool with `skill = <target-skill-name>` (from Step 5's Action Registry) and `args = <resolved args string>` (the same string a user would type after the slash command, e.g. `northwind/hb-014-execution-state/step-3-hb-flow-skill`). This runs the target skill within the current session per the `Skill` tool's own contract — its own commit / prompt-user / state-record steps run as part of that invocation. `hb-flow` performs no separate commit or `hb-sdk state record` call of its own.

## Output

Report the resolved invocation and confirm it ran (or, if the user declined/re-routed, report the final outcome of whichever action was ultimately confirmed and invoked). If `.hb/` is not initialized or has no active tasks, report that and stop before any Action Registry matching. If any `hb-sdk` command fails, surface the error verbatim to the caller.
