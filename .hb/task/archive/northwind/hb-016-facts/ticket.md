# Background

During ticket planning and step execution, project-specific facts are being constantly
forgotten — for example, the fact that skills live in the project under `./skills`. This
forces repeated re-discovery of the same information across tasks and steps. Hashbuild
needs a persistent, size-bounded store of project facts that is read during planning and
execution, and kept current afterward.

---

# Acceptance Criteria

1. A project facts store exists that persists facts across planning and execution
   invocations.
2. The facts store is read during all planning steps (e.g. `hb-task-step-plan`,
   `hb-task-plan`) and all execution steps (e.g. `hb-task-step-execute`).
3. The facts store is size-bounded:
    1. Target size is <= 100 lines.
    2. Hard maximum is 1000 lines.
    3. Each line is <= 120 characters.
4. After execution, the facts store is re-read and:
    1. Facts found to be incorrect or outdated are deleted or updated.
    2. New facts are added only when necessary, weighed against the size limits in AC3.
5. The store supports the motivating example end-to-end: a fact stating that skills live
   in the project under `./skills` can be recorded, read back during a later
   planning/execution invocation, and updated or removed if it becomes stale.

---

# Out of scope

- Hard enforcement (e.g. failing a command) of the size limits in AC3 — the agent applies
  judgement to stay within them rather than the tooling rejecting overage.
- Conflict resolution across multiple tasks/steps editing the facts store concurrently.
