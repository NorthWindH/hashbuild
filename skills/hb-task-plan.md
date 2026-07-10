---
name: hb-task-plan
argument-hint: "[--help] <author/task-id>"
arguments: task_id
description: >
  /hb-task-plan [--help] <author/task-id>

  Analyze a task's acceptance criteria against existing step tickets to identify coverage gaps, then optionally create additional steps to fill them.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/hb-sdk *) Bash(git *) Bash(find *) Read Write
---

# hb-task-plan

Compares the task-level `ticket.md` acceptance criteria against each step's `ticket.md` to surface gaps, then interactively creates new steps to fill them.

## Inputs

| Parameter              | Required | Description                                                                                                                                           |
| ---------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | yes\*    | Task name in `author/abc-123` or `author/abc-123-optional-flavor` format. See [${CLAUDE_SKILL_DIR}/references/structure.md](references/structure.md). |
| `help`, `--help`, `-h` | no       | Print help and exit. \*Not required when help is requested.                                                                                           |

## Reference Files

!`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md`

## Steps

### 1. Help check

If the first argument is `help`, `--help`, or `-h`: follow [${CLAUDE_SKILL_DIR}/references/skill-help.md](references/skill-help.md). Stop.

### 2. Resolve task path

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task path <name>
```

- prints the absolute path of the task folder to stdout; capture as `$TASK_PATH`
- if an error occurs, surface it verbatim and stop

### 3. Read facts store

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- captures stdout as `$FACTS` (may be empty)
- never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds unaffected — no error, no blocking prompt

### 4. Load task-level ticket

- read `$TASK_PATH/ticket.md`
- if it does not exist, notify the user: "No task-level `ticket.md` found at `$TASK_PATH/ticket.md`. A task ticket is required to perform gap analysis." and stop

### 5. Discover existing steps

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step list <name>
```

- prints the absolute path of each step folder to stdout, one per line, in ascending step-number order
- if an error occurs, surface it verbatim and stop
- for each path in the output:
  - attempt to read `<step_path>/ticket.md`
  - if absent, mark this step as **missing ticket**

### 6. Report missing step tickets

- if any steps are missing `ticket.md`, notify the user which steps have no ticket
- those steps are excluded from gap analysis since their acceptance criteria are unknown

### 7. Breakdown via shared subflow

- set the caller contract:
  - `$PARENT_LABEL` = `<name>` (the task name)
  - `$PARENT_CRITERIA` = the task ticket's **Acceptance Criteria** section (from Step 4)
  - `$CHILDREN` = each Step-5-discovered step that has a `ticket.md`, labeled by its step path, with its **Acceptance Criteria** section
  - `$MATERIALIZE_CHILD` = "invoke `hb-task-step-add` with `<name>` as the task name, `--ticket <temp_ticket_path>` to seed the step from the drafted ticket, and `--flavor <slug>` when a concise slug can be derived from the gap being addressed; capture the printed step path"
  - `$FACTS` = the facts captured in Step 3 — drafted step tickets should reflect known facts without requiring them restated in `$PARENT_CRITERIA`
- Follow [${CLAUDE_SKILL_DIR}/references/breakdown-subflow.md](references/breakdown-subflow.md) with the above.

### 8. Update facts store

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- captures stdout as `$FACTS_AFTER` (may be empty)
- read [${CLAUDE_SKILL_DIR}/references/facts-template.md](references/facts-template.md) for size guidance (target <= 100 lines, hard max 1000 lines, <= 120 chars/line) before composing any changes
- using judgement, based on what gap analysis and breakdown revealed — including any corrections or clarifications the user gave by interrupting this session (e.g. redirecting a wrong assumption), not only what ended up written into a drafted step ticket:
  - remove or correct any fact in `$FACTS_AFTER` found to be stale or incorrect
  - add new facts discovered during breakdown only when likely to matter for future planning, execution, or review, weighed against the size guidance
  - if pruning is needed to stay within guidance, prune stale/superseded facts before adding new ones
- if the composed content differs from `$FACTS_AFTER`:
  1. ```bash
     ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts write "<composed content>"
     ```
  2. create a task-level commit by following [${CLAUDE_SKILL_DIR}/references/committing.md](references/committing.md) including only `.hb/facts.md`, mode `task`, `--tag task-plan`
- if the composed content is unchanged from `$FACTS_AFTER`, skip both the write and the commit — no-op

### 9. Report

- list all steps created with their paths and the gaps each one addresses
- if any step failed, surface the error verbatim

### 10. Prompt user

Tell the user:

> Steps ready. `/clear` this conversation, then run `/hb-task-step-plan <name>/0` to create the implementation plan for the first step.
