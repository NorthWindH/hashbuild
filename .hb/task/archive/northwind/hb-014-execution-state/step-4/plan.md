# Step 4 Plan — Install-time SessionStart hook nudging `/hb-flow`

`./install` today patches each detected harness's `settings.json` with read
permissions (`SettingsPatcher`) but has no equivalent for hooks, so nothing
reminds a user to run `/hb-flow` when they start a new Claude Code session or
run `/clear` — even though `/hb-flow` (shipped in step-3) is the intended entry
point for resuming hashbuild work. This step is additive only: it adds one new
hook-patching code path to `install`, guarded to the Claude harness only
(`--harness claude`/auto-detected), with no changes to any `hb-*` skill or to
`/hb-flow` itself.

Source ticket: `./ticket.md`. Builds on the **shipped** `/hb-flow` skill from
step-3 (`skills/hb-flow.md`) — this step only wires an install-time nudge
toward it, and does not touch its internals. This plan targets `install` as it
exists **now** (473 lines, no hook logic).

> **Design decision — gate the hook's message on `.hb/` existing in the
> session's cwd.** The ticket's Background only asks for a message nudging
> `/hb-flow`, without mentioning a gate. But `HARNESSES[Claude].path_settings`
> (`install:50`) is `~/.claude/settings.json` — a single **global**,
> not-per-project file. A hook written there fires on *every* Claude Code
> session and every `/clear`, in *every* project on the machine, not just
> hashbuild-enabled repos. Un-gated, this becomes a standing nag in every
> unrelated project the user ever opens. `hb_sdk/common.py:51`
> (`Path.cwd() / ".hb"`) confirms the project's own convention for "is
> hashbuild active here": exact-cwd check, no upward search. The hook command
> mirrors that exact check before printing anything, so it stays silent
> outside hashbuild-initialized directories. This is evidence-driven scope
> narrowing, not scope creep: it satisfies AC1's message-on-fire requirement
> while avoiding a footgun the ticket didn't anticipate because it was
> reasoning per-repo, not global-settings scope. See §2 for the exact command
> and §7 for AC traceability.

---

## 0. Current-state facts (verified during planning)

- `install` is a single 473-line script at the repo root; `HARNESSES` (`install:45-58`)
  is a module-level dict computed at import time from `Path.home()`, so tests can
  override it per-process via the `HOME` env var before invoking the script.
- Only `HarnessKey.Claude` has a real, confirmed `settings.json` hook mechanism;
  `HarnessKey.OpenCode`'s hook support is unconfirmed and explicitly out of scope
  per `ticket.md`'s "Out of scope" section.
- `SettingsPatcher` (`install:189-291`) is the existing precedent for
  settings.json patching: a class holding harness + inputs, an `install()`/
  `uninstall()` pair each returning a `*UpdateResult` dataclass (added/removed
  diff + the full mutated settings dict), with a `flush()` that writes JSON back
  to disk. `run_install`/`run_uninstall` (`install:352-424`) own the
  confirm-before-write UX (`_confirm`, `install:294-299`) and the actual
  `result.flush()` call — the patcher classes themselves never write to disk or
  prompt.
- `_confirm` (`install:294-299`) already treats `EOFError` (no stdin, e.g. under
  test/CI) as an implicit "yes" — this is what lets tests run `install`
  non-interactively today for skill/permission installs, and the same property
  is what will let hook-patch tests run non-interactively too.
- Live-fetched Claude Code hooks reference (code.claude.com/docs/en/hooks)
  confirms: `SessionStart` supports matcher values `startup`, `resume`,
  `clear`, `compact`; a matcher string `"startup|clear"` fires on both new
  sessions and `/clear`. For `SessionStart` specifically, plain (non-JSON)
  stdout from a `type: "command"` hook is automatically surfaced as context —
  no `hookSpecificOutput` envelope is required. This is independently
  confirmed by this very session's own transcript: a GSD plugin `SessionStart`
  hook's plain-echoed staleness warning appeared verbatim as a
  "SessionStart hook additional context" system-reminder at conversation
  start, with no JSON wrapping.
- No test file exists yet for `install` (`tests/` only has
  `tests/skills/scripts/hb_sdk/`); this step is the first to add install
  coverage.

### 0.1 Impact (before → after)

| | Before | After |
|---|---|---|
| `install` on Claude harness | patches `permissions.allow` only | also patches `hooks.SessionStart` with one matcher-group entry |
| New Claude Code session / `/clear`, cwd has `.hb/` | no reminder | prints `hashbuild: run /hb-flow to see where things left off.` as session-start context |
| New Claude Code session / `/clear`, cwd has no `.hb/` | no reminder | still no reminder (gated, see Design decision) |
| `./install --uninstall` | removes permission entries only | also removes the hb-flow hook entry, leaving any unrelated hooks untouched |

Purely additive: no existing `install` behavior (skill symlinking, permission
patching) changes shape.

### 0.2 Non-regression proof

Additive-only change — the new hook-patch block is a separate code path from
`SettingsPatcher`, invoked as its own confirm/flush cycle after the existing
permission-patch block completes (§3). It never touches
`data["permissions"]`/`data["permission"]`, so existing permission-patch
behavior and its tests (once added) are unaffected. The one shared risk is JSON
round-tripping the same `settings.json`: this is proven safe because the hook
block re-reads the file fresh from disk *after* the permission block's own
flush (or skip) completes, rather than reusing the permission block's in-memory
dict — so the two blocks cannot clobber each other's writes.

---

## 1. Design overview

Single linear addition, no ordered-alternatives/precedence table needed:

1. `run_install`/`run_uninstall`, after the existing per-harness permission
   block, gain a second block: `if harness is HARNESS_CLAUDE and settings_path
   is not None:` construct a `HookPatcher`, call `.install()`/`.uninstall()`,
   show the diff, confirm, flush — mirroring the permission block's shape
   exactly.
2. `HookPatcher` reads `settings.json` fresh, finds or creates the
   `hooks.SessionStart` matcher-group whose `matcher == "startup|clear"`,
   and appends/removes exactly one hook entry identified by its literal
   `command` string — never touching other matcher-groups, other events, or
   other hooks a user configured within the same matcher-group.

**Alternatives considered and rejected:**

- **Reuse `SettingsPatcher` directly.** Rejected — its `_update`/`_permission_entries`
  are shaped around a flat allow-list of strings (`permissions.allow` /
  `permission.read`); hooks are a nested `event → matcher-group → hook-entry`
  structure with idempotency-by-content-match, not string-membership. Forcing
  both into one class would need a parallel branch inside every method just to
  keep them apart — more coupling for no shared logic.
- **Generalize `HookPatcher` to also support OpenCode now.** Rejected —
  OpenCode's hook schema is unconfirmed and explicitly out of scope; a
  same-shaped `match self._harness` branch (like `SettingsPatcher`'s) would
  require inventing an untested OpenCode hook format, which is exactly the
  kind of speculative future-proofing to avoid.
- **Write a separate hook script file, symlinked like skills.** Rejected — the
  entire hook body is a single portable `[ -d .hb ] && echo '...'; true`
  one-liner; a script file (plus new symlink-management/uninstall-cleanup
  code) would be pure overhead for a one-line command.
- **No `.hb/` gate (print unconditionally on every session).** Rejected — see
  Design decision above: `~/.claude/settings.json` is global, so this would
  nag in every unrelated project.

---

## 2. `HookPatcher` — specification

**New module-level constants** (`install`, placed after the `HARNESSES` dict):

```python
HB_FLOW_HOOK_MATCHER = "startup|clear"
HB_FLOW_HOOK_COMMAND = (
    "[ -d .hb ] && echo 'hashbuild: run /hb-flow to see where things left off.'; true"
)
```

- **Data model** — `HookUpdateResult` (new dataclass, mirrors `SettingsUpdateResult`):
  - `path_settings: Path`
  - `hook_added: bool = False`
  - `hook_removed: bool = False`
  - `updated_settings: dict[str, Any]` — the full settings dict, mutated in place
  - `__bool__`: `True` iff `hook_added or hook_removed` (mirrors `SettingsUpdateResult`'s
    "anything changed" semantics)
  - `flush()`: identical body to `SettingsUpdateResult.flush()` (die on empty dict,
    else write `json.dumps(..., indent=2) + "\n"`)

- **Interfaces** — `HookPatcher` (new class):
  - `__init__(self, path_settings: Path) -> None` — **new**. Claude-only; no
    `harness` parameter (see §1 Alternatives) — callers only ever construct it
    for `HARNESS_CLAUDE`.
  - `_read_settings(self) -> dict[str, Any]` — **new**, same body as
    `SettingsPatcher._read_settings` (return `{}` if file absent, else
    `json.loads(...)`).
  - `_find_matcher_group(self, data) -> dict | None` — **new**: scans
    `data.get("hooks", {}).get("SessionStart", [])` for a group whose
    `"matcher"` equals `HB_FLOW_HOOK_MATCHER`; returns the first match or `None`.
  - `_find_hook_entry(self, group) -> dict | None` — **new**: scans
    `group.get("hooks", [])` for an entry with `"type" == "command"` and
    `"command" == HB_FLOW_HOOK_COMMAND`; returns it or `None`.
  - `install(self) -> HookUpdateResult` — **new**: reads settings; if a
    matching matcher-group exists and already contains our hook entry, no-op
    (`hook_added=False`); if the group exists but lacks our entry, append our
    entry to that group's `"hooks"` list; if no matching group exists, append a
    brand-new `{"matcher": HB_FLOW_HOOK_MATCHER, "hooks": [<our entry>]}` group
    to `data["hooks"]["SessionStart"]` (creating `"hooks"`/`"SessionStart"` via
    `setdefault` as needed).
  - `uninstall(self) -> HookUpdateResult` — **new**: reads settings; if our
    entry is found inside a matcher-group, remove just that entry; if the
    group's `"hooks"` list becomes empty, remove the whole group; if
    `SessionStart` becomes empty, delete the key; if `hooks` becomes empty,
    delete that key too. Any unrelated matcher-group, hook entry, or event key
    is never inspected for removal — only ever located and pruned by exact
    identity match against `HB_FLOW_HOOK_COMMAND`.

- **Algorithm / rules** — idempotency and identity are both keyed on the exact
  string equality of `command == HB_FLOW_HOOK_COMMAND` (plus `type ==
  "command"`), never on list position/index. This is what makes `install()`
  safe to call twice (AC2) and `uninstall()` safe to run even after a user
  hand-edited the file, as long as they didn't retype our exact command.

- **Failure/degradation contract** — identical to `SettingsPatcher`: a missing
  `settings.json` is treated as `{}` (no error); `flush()` dies loudly only if
  `updated_settings` is empty (matching existing behavior, never hit in
  practice since `data` is always the full read-or-defaulted dict).

- **Conflict resolution** — n/a beyond the identity rule above; there is only
  ever one hb-flow hook entry by construction.

---

## 3. Integration / wiring

- `run_install` (`install:352-390`): immediately after the existing
  `if settings_path is not None:` permission block (which ends at `install:389`),
  add:

  ```python
  if harness is HARNESS_CLAUDE and settings_path is not None:
      hook_patcher = HookPatcher(settings_path)
      hook_result = hook_patcher.install()
      if not hook_result:
          info(f"  [skip] /hb-flow session-start hook already present in {settings_path}")
      else:
          info(f"\n  The following hook will be added to {settings_path}:")
          info(f"    SessionStart ({HB_FLOW_HOOK_MATCHER}): {HB_FLOW_HOOK_COMMAND}")
          if _confirm("  Apply? [Y/n] "):
              hook_result.flush()
              info(f"  [ok] patched {settings_path}")
          else:
              info("  [skip] skipped hook patch")
  ```

- `run_uninstall` (`install:392-423`): mirror block after the existing
  permission-removal block, calling `hook_patcher.uninstall()`, prompting with
  `"  Remove? [Y/n] "` (matching the existing uninstall wording), else
  identical shape.
- Both blocks reuse `_confirm` (`install:294-299`) verbatim — the exact
  confirm-before-write UX already used for permission patching (AC4), no
  deviation.
- No configuration, build wiring, entry points, or dependency manifests
  change. `HookPatcher` is self-contained within `install`; no new files are
  symlinked or installed.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `install` | **extend** — add `HB_FLOW_HOOK_MATCHER`/`HB_FLOW_HOOK_COMMAND` constants, `HookUpdateResult` dataclass, `HookPatcher` class, and one new confirm/flush block each in `run_install`/`run_uninstall`. Existing `SettingsPatcher`, `_check_symlink`, skill install/uninstall logic untouched. |
| `tests/test_install.py` | **new** — first test coverage for `install`; covers hook install/idempotency/uninstall/non-disturbance and the hook command's own gated behavior (§5). |

No dependency-manifest or lockfile changes (`pyproject.toml`/`uv.lock` unchanged;
`install` uses only stdlib).

---

## 5. Tests

New file `tests/test_install.py`, mirroring the subprocess-invocation style of
`tests/skills/scripts/hb_sdk/helpers.py::run` (spawn `sys.executable
<script> <args>`, assert on `returncode`/stdout/stderr) — but overriding the
`HOME` env var per-invocation (via `env={**os.environ, "HOME": str(home)}`
passed to `subprocess.run`) so `HARNESSES`' `Path.home()`-derived paths resolve
into a `tmp_path`-scoped fake home, and always passing `--harness claude` to
skip the interactive detect/select prompt. Each test pre-creates `home /
".claude"` so Claude is detected, and relies on `_confirm`'s existing
`EOFError → True` auto-confirm (no stdin piped) to apply writes
non-interactively.

- **Happy path — fresh install.** Empty `home`; run `install --harness claude`;
  assert `home/.claude/settings.json` contains a `hooks.SessionStart` entry
  with `matcher == "startup|clear"` and a hook whose `command ==
  HB_FLOW_HOOK_COMMAND`.
- **The motivating case — idempotency (AC2).** Run install twice; assert the
  second run's stdout contains `"already present"` and the resulting
  `hooks.SessionStart` list still has exactly one matcher-group with exactly
  one hook entry (no duplication).
- **Precedence/append into existing matching matcher-group.** Pre-seed
  `settings.json` with a `SessionStart` matcher-group for `"startup|clear"`
  containing one unrelated user hook (different `command`); run install;
  assert both hooks now coexist in that same group's `"hooks"` list (no new
  duplicate group created).
- **Uninstall removes cleanly (AC3).** Install then run `install --harness
  claude --uninstall`; assert the hb-flow hook entry is gone and (since it was
  the only entry) the `SessionStart` key and/or `hooks` key are pruned away
  entirely (not left as empty lists/dicts).
- **Non-disturbance of unrelated hooks (AC3).** Pre-seed `settings.json` with
  an unrelated `PreToolUse` hook and an unrelated `SessionStart` matcher-group
  using matcher `"startup"` only (not `"startup|clear"`); install then
  uninstall the hb-flow hook; assert both unrelated entries are byte-for-byte
  unchanged in the final file.
- **Confirm-before-write UX (AC4).** Assert install's stdout, before the
  write, prints a diff line naming the `SessionStart` matcher and the exact
  command about to be added — matching the existing permission-patch diff
  presentation style (`"The following ... will be added to ..."`).
- **Negative case — the hook command itself stays silent outside `.hb/`.**
  Directly execute `HB_FLOW_HOOK_COMMAND` via `subprocess.run(["bash", "-c",
  HB_FLOW_HOOK_COMMAND], cwd=<tmp dir without .hb/>)`; assert exit code `0` and
  empty stdout. Then re-run with `cwd=<tmp dir with an .hb/ dir>`; assert exit
  code `0` and stdout equals the reminder message. This directly proves the
  Design decision's gate, independent of the install/uninstall plumbing.
- **Non-regression.** No existing tests exist for `install` yet (§0), so there
  is nothing pre-existing to regress; the full `tests/skills/scripts/hb_sdk/`
  suite must still pass unchanged since this step never touches `hb-sdk`.

---

## 6. Verification (after implementation)

1. `uv run ruff check` and `uv run ruff format --check` are clean.
2. `uv run pytest` (via `make test`) is green, including the new
   `tests/test_install.py`.
3. Manual end-to-end smoke test against a scratch `HOME`:
   ```bash
   export SCRATCH=$(mktemp -d) && mkdir -p "$SCRATCH/.claude"
   HOME="$SCRATCH" ./install --harness claude
   cat "$SCRATCH/.claude/settings.json"   # confirm hooks.SessionStart entry present
   HOME="$SCRATCH" ./install --harness claude   # confirm idempotent ("already present")
   HOME="$SCRATCH" ./install --harness claude --uninstall
   cat "$SCRATCH/.claude/settings.json"   # confirm hook entry gone, permissions untouched
   ```
4. Per-AC checks: AC1 — step 3 of this sequence shows the hook entry with the
   right matcher/message; AC2 — the repeated install call in step 3 reports
   "already present" and produces no diff; AC3 — the non-disturbance test
   (§5) plus the final uninstall in step 3 leaving permissions intact; AC4 —
   the confirm-before-write UX test (§5) plus visual confirmation of the
   `Apply? [Y/n]` prompt appearing before the write in an interactive run.
5. Invariant check: `home/.claude/settings.json` remains valid JSON after every
   install/uninstall cycle (implicitly proven by every test reading it back via
   `json.loads`).
6. Scope check: only `install` and the new `tests/test_install.py` change; no
   file under `skills/` is touched, confirming `/hb-flow`'s own logic is
   untouched (per ticket's out-of-scope note and step-5's dependency on this
   step being install-only).

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| 1 | §2 (`HookPatcher`, constants), §3 (wiring) | Message gated per Design decision — fires as a session-start reminder only when `.hb/` exists in cwd, satisfying the ticket's intent (nudge hashbuild users) without global-settings spam |
| 2 | §2 `install()` idempotency (identity-by-command-string) | Tested directly (§5 "idempotency") |
| 3 | §2 `uninstall()` cleanup logic, §3 wiring | Tested directly (§5 "uninstall removes cleanly", "non-disturbance") |
| 4 | §3 (`_confirm` reused verbatim, no deviation) | Tested directly (§5 "confirm-before-write UX") |

---

## 8. Out of scope (per ticket)

- Hook support for the OpenCode harness — `HookPatcher` is Claude-only; no
  `HarnessKey.OpenCode` branch is added or stubbed.
- Any change to `/hb-flow`'s own behavior, prompting, or Action Registry.
- A separate hook script file — the hook body stays a single inline shell
  command (see §1 Alternatives).
