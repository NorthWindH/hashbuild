# Background

`./install` (repo root) installs hashbuild skills into detected LLM harnesses and idempotently patches each harness's `settings.json` with read permissions (see `SettingsPatcher` in `install`). It has no equivalent step for hooks: today, nothing reminds a user to run `/hb-flow` when they start a new Claude Code session or run `/clear`, even though `/hb-flow` is the intended entry point for resuming hashbuild work.

---

# Acceptance Criteria

1. `./install` adds a hook to the Claude harness's `settings.json` that fires on new-session start and on `/clear`, and whose message tells the user to invoke `/hb-flow` to work with hashbuild.
2. The hook installation is idempotent: running `./install` repeatedly does not duplicate the hook entry, mirroring the existing idempotent behavior of `SettingsPatcher`/`_check_symlink` for skills and permissions.
3. `./install --uninstall` removes the hook cleanly, without disturbing unrelated hooks a user may have configured.
4. The confirm-before-write UX already used for permission patching (`_confirm("  Apply? [Y/n] ")`) is followed for the hook write, or any deviation is explicitly justified.

---

# Out of scope

- Hook support for the OpenCode harness, unless OpenCode is confirmed to support an equivalent hook mechanism.
- Any change to `/hb-flow`'s own behavior.
