# Background

Lays the groundwork for AC1 & AC3 of the parent ticket (`northwind/hb-016`): a
persistent, size-bounded facts store. This step establishes the storage file plus
the `hb-sdk` CLI surface (`read`/`write`) that later steps (wiring facts into
planning and execution) will consume.

---

# Acceptance Criteria

1. A facts store file exists at `.hb/facts.md`, created lazily (no separate
   `init` step or subcommand).
2. `hb-sdk facts read`:
    1. prints the current contents of `.hb/facts.md` to stdout when the file
       exists.
    2. prints an empty response (no error) when `.hb/facts.md` does not exist.
3. `hb-sdk facts write`:
    1. accepts the new full contents of the store and overwrites
       `.hb/facts.md`.
    2. creates `.hb/facts.md` if it does not already exist. If `.hb/` itself
       does not exist, `facts write` dies (matching `hb-sdk state`'s existing
       behavior via `path_hb_asserted()`) rather than creating it.
4. No `hb-sdk facts init` subcommand is added — the file is created lazily via
   `write`, matching the pattern of `read`/`write` already used by `hb-sdk state`.
5. The facts store's format documents, as guidance for the agent populating it,
   the size limits from the parent ticket's AC3 — target size <= 100 lines, hard
   maximum 1000 lines, each line <= 120 characters — without programmatically
   enforcing them.
6. Tests cover:
    1. `read` on a missing file returns an empty result, not an error.
    2. `write` creates the file when absent.
    3. `write` then `read` round-trips the written content exactly.

---

# Out of scope

- Wiring facts-store reads/updates into `hb-task-step-plan`, `hb-task-plan`, or
  `hb-task-step-execute` — later steps.
- Enforcing the size limits in code (explicitly out of scope per the parent
  ticket — the agent applies judgement instead).
- Conflict resolution across concurrent writers (explicitly out of scope per the
  parent ticket).
