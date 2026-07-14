# Step 4 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-4-REVIEW-1 | ✅ Addressed — hook now emits `systemMessage` JSON so the message renders to the user |
| STEP-4-REVIEW-2 | ✅ Addressed — hook entries now matched by stable marker, upgraded/removed in place regardless of command-text changes |
| STEP-4-REVIEW-3 | ⏭️ Deferred — no second hook exists yet to validate a generic marker against; revisit when one is added |
| STEP-4-REVIEW-4 | ✅ Addressed — removed the incorrect empty-dict guard from `HookUpdateResult.flush()` |

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

### STEP-4-REVIEW-3: Simplify hook marker for reuse across more hooks

- **file(s):** `install` (around `HB_FLOW_HOOK_MARKER` definition, line ~72)
- The current hook marker string is more complex than it needs to be. Reviewer suggests simplifying it to something like `[hashbuild]` so the same marker convention can be reused across more hook types in the future, not just the SessionStart hook.
- **source:** `TODO REVIEW` in commit `1f57291f3da9e2abd5059ac053d6f9d315522425` — delete comment from source file after addressing

**Resolution:** Checked whether any active task plans a second hook (searched `.hb/task/active/**/*.md` for hook-related work) — none do; `install` currently registers exactly one hook (`SessionStart`). Simplifying `HB_FLOW_HOOK_MARKER` to a generic `[hashbuild]`-style token now would be speculative: there's no second hook's command text to validate the new marker against, and the current marker (`"run /hb-flow to see what to do next."`) already does its one job — uniquely identifying the hb-flow SessionStart entry regardless of which `HB_FLOW_HOOK_COMMAND` variant is installed. Not changing it now; revisit marker design if/when a second hook type is actually added, at which point the right generic form can be chosen with a real second use case to validate against instead of guessing.

Disposition: **Deferred**

---

### STEP-4-REVIEW-4: `HookUpdateResult.flush()` dies on a legitimately empty settings dict

- **file(s):** `install` (`HookUpdateResult.flush()`, around line 318)
- `flush()` calls `die()` whenever `updated_settings` is falsy. This incorrectly fires when `uninstall()` legitimately empties the settings dict down to `{}` — e.g. a `settings.json` that contained only the hb-flow hook entry. This guard predates the systemMessage/idempotency fix from STEP-4-REVIEW-1/2 and is unrelated to it; it was flagged there as a follow-up rather than fixed in place.
- **source:** `TODO REVIEW` in commit `cc992cf46a9d2ed0b8d87e5c04a1c1368d428756` — delete comment from source file after addressing

**Resolution:** Confirmed the bug is real and reachable: `HookPatcher.uninstall()` deletes the `hooks` key entirely once `SessionStart` and its matcher group are both empty, so `updated_settings` legitimately becomes `{}` when a `settings.json` contained only the hb-flow hook. Both call sites (`run_install`/`run_uninstall`) already gate `flush()` behind `if not result: skip`, so by the time `flush()` runs, `__bool__` has already confirmed a real change occurred — the emptiness guard inside `flush()` was redundant in the success path and actively wrong in this one legitimate edge case. Removed the `if not self.updated_settings: die(...)` guard from `HookUpdateResult.flush()` entirely; it now unconditionally writes `updated_settings` to disk. Verified with a standalone script: uninstalling a `settings.json` containing only the hb-flow hook now writes `{}` instead of dying. `SettingsUpdateResult.flush()` (the sibling class for permission patching) keeps its own identical-looking guard as-is — its `updated_settings` can never actually go empty, since `data.setdefault("permissions", {})` / `data.setdefault("permission", {})` always leaves at least one key behind, so there's no matching bug there and no reason to touch it for this item.

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
