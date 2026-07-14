# Background

The `hashbuild` skill framework's README currently lacks clear top-level guidance on how to get started, and its list of `hb-*` skills has drifted out of sync with the skills actually present on disk (canonical source: `skills/hb-*.md` in this repo — the `~/.claude/skills/hb-*/` copies are just the installed versions). This step brings the README up to date on both fronts.

---

# Acceptance Criteria

1. README includes primary usage guidance recommending that a new project run `hb-init` first, followed by `hb-flow`, as the standard entry point.
2. README's skills reference is updated to include any `hb-*` skill present in `skills/*.md` that is currently missing from the README's list.
