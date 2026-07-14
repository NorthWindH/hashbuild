# Step 4 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-4-REVIEW-1 | ✅ Addressed — hook now emits `systemMessage` JSON so the message renders to the user |
| STEP-4-REVIEW-2 | ✅ Addressed — hook entries now matched by stable marker, upgraded/removed in place regardless of command-text changes |

---

## Notes

### STEP-4-REVIEW-1: SessionStart hook message not showing to user

- **file(s):** `install` (around `HB_FLOW_HOOK_COMMAND` / SessionStart hook registration, line ~61)
- The `HB_FLOW_HOOK_COMMAND` SessionStart hook (`startup|clear` matcher) is supposed to print `hashbuild: run /hb-flow to see what to do next.` to the user, but it isn't being presented. Reviewer points to the hook input/output reference (`https://code.claude.com/docs/en/hooks#hook-input-and-output`) as something to check — possibly the hook's stdout isn't being surfaced as `additionalContext`/user-visible output per the documented hook I/O contract.
- **source:** `TODO REVIEW` in commit `4058f34cf9e118d7c1e7ac157409ed35f651b7c1` — delete comment from source file after addressing

**Resolution:** Confirmed via the Claude Code hooks docs: for a `SessionStart` hook, plain stdout on exit 0 is added as *context for Claude* only — it is never rendered to the user in the transcript. Making a message user-visible requires JSON output with a top-level `systemMessage` field. Changed `HB_FLOW_HOOK_COMMAND` in `install` from a plain `echo 'hashbuild: ...'` to `echo '{"systemMessage": "hashbuild: run /hb-flow to see what to do next."}'`, verified the shell command emits valid JSON and that `ruff check`/`ruff format --check` pass. Existing installs will pick up the new command on their next `install` run (the hook is matched by exact command string, so this is a superseding re-install, not an in-place settings.json patch).

Disposition: **Addressed**

---

### STEP-4-REVIEW-2: Hook install/reinstall/uninstall idempotency broken by system-message change

- **file(s):** `install` (`HookPatcher`, `_find_hook_entry`, `HB_FLOW_HOOK_COMMAND`, around lines 61-63, 341-393)
- `_find_hook_entry` matches an existing hook entry by exact equality against the current `HB_FLOW_HOOK_COMMAND` string. STEP-4-REVIEW-1 changed that constant's content (plain `echo` → `echo` of `systemMessage` JSON). Any user who already has the old-format command installed in their `settings.json` will, on the next `install` run, fail to match it as "already present" and get a second, duplicate `SessionStart` hook entry added alongside the stale old-format one — rather than a clean upgrade. `uninstall` has the same problem in reverse: it only removes entries matching the *current* `HB_FLOW_HOOK_COMMAND`, so it can't clean up an old-format entry left behind after a partial/failed upgrade.
- **source:** `TODO REVIEW` in commit `aaad330bab7c7638be185f47f761a1f4b0a410ef` — delete comment from source file after addressing

**Resolution:** Confirmed the bug: `HookPatcher._find_hook_entry` matched an existing entry by exact equality against `HB_FLOW_HOOK_COMMAND`. Changing that constant (as STEP-4-REVIEW-1 just did) meant `install()` would fail to recognize an already-installed old-format entry, appending a duplicate rather than upgrading it, and `uninstall()` would only ever remove entries matching the *current* command text, leaving old-format entries orphaned forever. Fixed by introducing `HB_FLOW_HOOK_MARKER` (a stable substring present in every command variant) and matching on that instead of exact command equality: `_find_hook_entry` now identifies the hb-flow hook by marker regardless of its exact command text. `install()` now upgrades an existing entry's `command` field in place when the marker matches but the text differs (new `hook_updated` result flag), instead of adding a duplicate; a no-op when already current. `uninstall()` now cleanly removes any hb-flow hook entry regardless of which command-text version it's running, since it reuses the same marker-based lookup. Verified with a standalone script covering: (1) an old-format entry upgraded in place by `install()`, (2) a second `install()` run being a true no-op, (3) `uninstall()` removing the entry cleanly while preserving unrelated `settings.json` content. Also updated the CLI messaging (`install` mode) to say "will be updated" vs "will be added" so the confirmation prompt reflects what's actually happening.

While verifying, found an unrelated pre-existing bug: `HookUpdateResult.flush()` calls `die()` whenever `updated_settings` is falsy, which incorrectly fires when `uninstall()` legitimately empties the settings dict down to `{}` (e.g. a `settings.json` containing only the hb-flow hook). Left a `TODO REVIEW` comment at the `flush()` definition (`install`, near line 316) for a follow-up pass rather than fixing here — it's out of scope for the systemMessage/idempotency concern this item covers.

Disposition: **Addressed**

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
