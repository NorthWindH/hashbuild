# Facts Store

- \`skills/hb-*.md\` is the canonical skill source; \`~/.claude/skills/hb-*/\` is just the installed copy.
- hb-015/step-5: re-author Jira push logic deleted in step-1 from hb-ticket-discuss.md (recover via git show 7bd2c42).
- hb-ticket-discuss.md allowed-tools omits Read/WebFetch on purpose; don't re-add (rejected in hb-015/step-2).
- Subflows invoked at 2+ points in one skill use caller-contract+prose-follow (like breakdown-subflow), not \`!cat\`.
- lint/format gates: use \`uv run ruff check\`/\`uv run ruff format --check\` (plain \`ruff\` binary isn't on PATH).
- hb-014/step-3: archive guard dropped entirely (unarchive is trivial) — not implemented in hb-flow or hb-task-archive.
- hb-014/step-3: hb-flow's Skill tool call has no channel to pass facts to invoked skill; don't add a facts-read step there (rejected in review).
- hb-014/step-3: hb-flow reads facts store for its own use before Step 4 (prompt) to help inform next-action framing.
- Task flavor is embedded in \`<author/task-id>\` name string (no \`--flavor\` flag on \`hb-task-create\`); only \`hb-task-step-add\` has a separate \`--flavor\` flag, since the SDK assigns the step number itself.
- Claude Code SessionStart hooks: plain stdout is context-only, never user-visible; use JSON \`{"systemMessage": "..."}\` to show the user a message.
- \`install\`'s \`HookPatcher\` matches hb-flow's hook entry via \`HB_FLOW_HOOK_MARKER\` (stable substring), not exact command equality, so \`HB_FLOW_HOOK_COMMAND\` text can change without breaking install/uninstall idempotency.
- \`README.md\` at repo root is a symlink to \`skills/references/README.md\`; edit the real target path, not the symlink.
- allowed-tools glob \`//tmp/*\` matches nested multi-segment paths under /tmp too (proven by hb-ticket-discuss's existing writes); no glob widening needed for deeper /tmp subdirs.
- \`load-ticket-subflow.md\` never \`Follow\`s \`interactive-ticket-subflow.md\` — it only borrows specific sections (§A.1, §C, §D) inline, since it must not trigger that subflow's own guard/prompt. \`describe-ticket-subflow.md\` does \`Follow\` it fully.
- hb-015/step-2's plan.md is stale: describes \`$TICKET_SEQ\` + a Read/WebFetch/Bash(find) widening that never shipped — for this task, trust live files over old step plan.md text.
- breakdown-subflow.md's \`$MATERIALIZE_CHILD\` ("invoke hb-task-step-add ...") means invoke the skill via the Skill tool, not call \`hb-sdk task step add\` directly — direct SDK calls skip hb-task-step-add's own facts-read/commit/state-record steps.