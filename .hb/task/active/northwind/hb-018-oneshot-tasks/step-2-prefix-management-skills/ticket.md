# Background

`northwind/hb-018-oneshot-tasks` requires the prefix-sequence functionality built in step-0 (`prefix-sequences-sdk`) to be exposed to users as thin-wrapper `hb-*` skills, following the same convention as other `hb-*` skills: each skill parses its own args and hands execution off to a corresponding `hb-sdk prefix` subcommand.

# Goal

Add four skills — `hb-prefix-create`, `hb-prefix-list`, `hb-prefix-drop`, `hb-prefix-update` — that expose step-0's SDK-level prefix-sequence operations (create, list, drop, update) as CLI-facing commands.

# Acceptance Criteria

1. `hb-prefix-create <scope> <name>`:
    1. `scope` is `author` or `repo`.
    2. When `scope` is `author`, `name` must be of the form `author/prefix` (`prefix` following the standard prefix-name rules).
    3. When `scope` is `repo`, `name` must be just `prefix` (same prefix-name rules, no author segment).
    4. `--next-value <n>`: sets the initial next value to hand out; defaults to `0` when omitted.
    5. Creation is handed off to `hb-sdk`, which enforces the collision rules (step-0 AC 4).
2. `hb-prefix-list`:
    1. Prints prefix names only by default.
    2. `--long`: also prints each prefix's attributes (e.g. next value). Passed through verbatim to `hb-sdk`'s listing detail flag (step-0 AC 5.2) — the skill does not compute this locally.
    3. `--scope <author|repo>`: filters to prefixes of the given scope. Passed through verbatim to `hb-sdk`'s listing filter (step-0 AC 5.1).
    4. `--author <name>`: filters to prefixes belonging to the given author; implies `scope=author`; errors if combined with `--scope repo`. Passed through verbatim (step-0 AC 5.1).
    5. `--prefix <name>`: filters to one exact prefix. Passed through verbatim (step-0 AC 5.1).
3. `hb-prefix-drop <scope> <name>`: drops an existing prefix; takes the same positional args as `hb-prefix-create`.
4. `hb-prefix-update <scope> <name>`: updates an existing prefix; takes the same positional args as `hb-prefix-create`, plus `--next-value <n>` to set the next value.
5. Each skill is a thin wrapper: it parses/validates its own args and reshapes them as needed, then hands execution off to `hb-sdk prefix <subcommand>` (built in step-0) for the actual logic — no sequence/collision logic duplicated in the skill layer.
6. Tests or examples demonstrate each skill invocation form (including each error/filter case above) round-tripping correctly through to the `hb-sdk prefix` subcommand.

# Out of scope

- Implementing the underlying sequence create/list/drop/update/collision logic — step-0.
- `hb-sdk task create`'s prefix-based invocation form — step-1.
- Renaming or rescoping a prefix after creation (explicitly out of scope in the task ticket; `hb-prefix-update` only adjusts `--next-value`).
