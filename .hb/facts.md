# Facts Store

- `skills/hb-*.md` is the canonical skill source; `~/.claude/skills/hb-*/` is just the installed copy.
- hb-015/step-5: re-author Jira push logic deleted in step-1 from hb-ticket-discuss.md (recover via git show 7bd2c42).
- hb-ticket-discuss.md allowed-tools omits Read/WebFetch on purpose; don't re-add (rejected in hb-015/step-2).
- Subflows invoked at 2+ points in one skill use caller-contract+prose-follow (like breakdown-subflow), not `!cat`.