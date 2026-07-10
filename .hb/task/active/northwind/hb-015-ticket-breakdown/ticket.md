# Background

Two skills already handle related but disconnected pieces of ticket work: `hb-ticket-discuss` (interactive, single-shot creation of one standalone ticket) and `hb-task-plan` (analyzes a task's acceptance criteria against existing step tickets and creates steps to cover gaps — i.e. a breakdown flow, but scoped to task→step). We want to generalize ticket breakdown into a reusable capability, and turn `hb-ticket-discuss` from a single-shot flow into a persistent loop that can discuss, create, break down, manage, and push any number of tickets held in context across iterations.

---

# Acceptance Criteria

## A. Loop structure

1. `hb-ticket-discuss` operates as a loop rather than a single-shot flow: it does not exit after one action, but returns to a menu of next actions until the user chooses to exit.
2. At the start of each iteration, the skill presents:
    1. The currently active ticket, if any.
    2. The number of tickets currently held in context.
    3. The ids (or identifying summaries) of all tickets in context.
    4. The list of available next actions.
3. At any iteration, any number of tickets can be held in context; at most one ticket is `active` at a time.

## B. Actions

Each of the following is selectable via natural language at any loop iteration:

4. **Load ticket** — load a ticket from a source (text file, an available MCP such as Jira, web access, or any other means available to the agent harness); the loaded ticket is added to context and becomes recallable by natural-language description of its summary/content, or by an identifier in its name/content; it becomes the active ticket.
5. **Describe ticket** — create a new ticket (via the existing interactive ticket-creation flow) and add it to context; it becomes the active ticket.
6. **Breakdown ticket** — decompose a ticket into child tickets, loading each into context:
    1. Read the ticket's acceptance criteria.
    2. Read the acceptance criteria of any existing child tickets.
    3. Identify and present coverage gaps.
    4. If there are no gaps, stop and return to the top-level action list without creating tickets.
    5. If there are gaps, propose a high-level breakdown of the gaps into candidate tickets; loop presenting the proposal and accepting user confirmation or requested changes until the user confirms.
    6. Once confirmed, create the proposed tickets one at a time: for each, present the drafted ticket and loop accepting confirmation or requested changes until confirmed, then move to the next; when none remain, return to the top-level action list.
7. **Clear ticket(s)** — remove one, several, or all tickets from context (including the active ticket, if targeted).
8. **Push ticket(s)** — push one or more tickets to an available destination (e.g. Jira via MCP, or file), using the existing push procedure (including optional Jira Idea linking for pushed Epics); creating the ticket if it doesn't exist or updating it if it does; when multiple tickets are targeted, loop through pushing each, stopping early if the user requests it.
9. **Exit** — leave the loop, summarizing the number and ids of tickets left in context and the actions taken during the session, and prompt the user to `/clear` the conversation.

## C. Structure and reuse

10. The updated `hb-ticket-discuss` skill remains easy to read: the loop and its actions are split across multiple reference subflow files rather than inlined in one large skill file.
11. The "breakdown" logic (gap analysis against acceptance criteria, proposal-and-confirm, per-ticket create-and-confirm) is extracted into a single shared subflow used by both `hb-ticket-discuss`'s breakdown action and `hb-task-plan`'s existing task→step breakdown, so the two skills do not maintain duplicate breakdown logic.

---

# Out of scope

- Changes to `hb-task-plan`'s behavior beyond having it consume the shared breakdown subflow (its task→step scoping and step-creation mechanics are not otherwise altered).
- Adding new MCP/source integrations beyond what's already available to the agent harness (Jira via existing MCP, file, web); this ticket wires the loop's actions to existing means, not new ones.
