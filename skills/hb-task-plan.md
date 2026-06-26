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

### 3. Load task-level ticket

- read `$TASK_PATH/ticket.md`
- if it does not exist, notify the user: "No task-level `ticket.md` found at `$TASK_PATH/ticket.md`. A task ticket is required to perform gap analysis." and stop

### 4. Discover existing steps

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk task step list <name>
```

- prints the absolute path of each step folder to stdout, one per line, in ascending step-number order
- if an error occurs, surface it verbatim and stop
- for each path in the output:
  - attempt to read `<step_path>/ticket.md`
  - if absent, mark this step as **missing ticket**

### 5. Report missing step tickets

- if any steps are missing `ticket.md`, notify the user which steps have no ticket
- those steps are excluded from gap analysis since their acceptance criteria are unknown

### 6. Gap analysis

- extract the **Acceptance Criteria** section from the task-level `ticket.md`
- for each step that has a `ticket.md`, extract its **Acceptance Criteria** section
- identify task-level criteria not addressed by any existing step
- present a gap report to the user:
  - list each uncovered task-level criterion
  - note which steps, if any, partially address it

### 7. Prompt user

- if no gaps are found: notify the user "All task acceptance criteria appear covered by existing steps." and stop
- otherwise present the gap list and ask: "Would you like to add steps to cover these gaps?"
- if the user declines: ask "How would you like to proceed?" and await their direction; stop this flow

### 8. Create gap-filling steps

For each gap or related group of gaps (keep each step small to medium; target less than 300 estimated lines of changes per step — use the size of surrounding steps as a guide):

1. **Draft ticket**: write a temporary ticket file using [${CLAUDE_SKILL_DIR}/references/ticket-template.md](references/ticket-template.md) as the structural template:
   - **Background**: state which task-level criteria this step addresses and why
   - **Acceptance Criteria**: concrete, checkable conditions that close the identified gap(s)
   - **Out of scope**: criteria deferred to other steps or beyond this step's boundary
   - write the file to a temp path (e.g. `/tmp/hb-task-plan-step-<n>.md`)

2. **Clarify if needed**: if the gap is ambiguous or requires a design decision, prompt the user for clarification before finalising the ticket

3. **Add step**: invoke the `hb-task-step-add` skill:
   - pass `<name>` as the task name
   - pass `--ticket <temp_ticket_path>` to seed the step from the drafted ticket
   - pass `--flavor <slug>` when a concise slug can be derived from the gap being addressed

4. Repeat for each remaining gap or group of gaps

### 9. Report

- list all steps created with their paths and the gaps each one addresses
- if any step failed, surface the error verbatim

### 10. Prompt user

Tell the user:

> Steps ready. `/clear` this conversation, then run `/hb-task-step-plan <name>/0` to create the implementation plan for the first step.
