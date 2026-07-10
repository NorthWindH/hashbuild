> **Subflow — facts store read/compose/gate/write.** Shared by `hb-task-step-plan`,
> `hb-task-plan`, `hb-task-step-execute`, and `hb-task-step-review-address`. Part A
> is a plain early read of `.hb/facts.md` for the caller's own use. Part B is a late
> re-read, judged compose, diff gate, and conditional write (with optional
> self-commit) after the caller's own work has had a chance to reveal new facts.

**Caller contract.** Before invoking Part B, the calling skill must have resolved:

- `$CONTEXT_LABEL` — short phrase for what just happened, used only to judge which facts are worth recording (e.g. `"drafting this plan.md"`, `"this execution"`)
- `$SELF_COMMIT` — `true` if Part B must create its own commit for `.hb/facts.md` right after a successful write; `false` if a later step in the caller's own sequence already bundles `.hb/facts.md` into a broader commit
- `$COMMIT_ARGS` — required only when `$SELF_COMMIT` is `true`: the exact `committing.md` invocation (mode, files, `--tag`) to use

#### Part A — Read (early)

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- captures stdout as `$FACTS` (may be empty)
- never errors; if `.hb/facts.md` or `.hb/` itself is missing, proceeds unaffected — no error, no blocking prompt
- the caller takes `$FACTS` into account during its own work: if a fact is relevant, it applies without requiring the fact be restated in the caller's own inputs (ticket, plan, execution, review item, etc.)

#### Part B — Compose, gate, write (late)

```bash
${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts read
```

- captures stdout as `$FACTS_AFTER` (may be empty)
- read [facts-template.md](facts-template.md) for size guidance (target <= 100 lines, hard max 1000 lines, <= 120 chars/line) before composing any changes
- using judgement, based on what `$CONTEXT_LABEL` revealed — including any corrections or clarifications the user gave by interrupting the session (e.g. redirecting a wrong assumption), not only what ended up written into the caller's own output artifact:
  - **prefer dropping** any fact that is trivially re-derivable from current on-disk state rather than keeping it "just in case"
  - remove or correct any fact in `$FACTS_AFTER` found to be stale or incorrect
  - keep each fact short — target <= 120 characters total
  - add new facts only when they correct a planning error or otherwise inform future planning/execution/review, weighed against the size guidance
  - if pruning is needed to stay within guidance, prune stale/superseded facts before adding new ones
- if the composed content differs from `$FACTS_AFTER`:
  ```bash
  ${CLAUDE_SKILL_DIR}/scripts/hb-sdk facts write "<composed content>"
  ```
  - if `$SELF_COMMIT` is `true`: commit now via `$COMMIT_ARGS`, following [committing.md](committing.md)
  - if `$SELF_COMMIT` is `false`: leave `.hb/facts.md` uncommitted for the caller's own later commit step to pick up
- if the composed content is unchanged from `$FACTS_AFTER`: skip the write entirely (and, when `$SELF_COMMIT` is `true`, skip the commit too) — no-op

**Failure/degradation contract:** missing facts store never blocks either part; an unchanged compose result is a clean no-op, not an error.

**Return value:** none (side-effecting only) — the caller consumes only `$FACTS`/`$FACTS_AFTER` themselves.
