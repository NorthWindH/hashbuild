# Background

The `hb-status` skill currently reads `status-template.md`, gathers JSON from `hb-sdk summarize`, and renders the markdown report itself. Moving the rendering logic into `hb-sdk` centralizes it — the skill becomes a thin passthrough and the template file may be retired.

---

# Acceptance Criteria

1. `hb-sdk summarize` accepts a `--format <value>` flag with two valid values: `json` and `md`.
2. When `--format` is omitted, behavior is identical to today (JSON output) — no callers break.
3. `hb-sdk summarize --format json` produces the same JSON output as the current default.
4. `hb-sdk summarize --format md` produces a rendered markdown status report equivalent to what the `hb-status` skill produces today, covering the same sections (Initialization, Active Tasks with legend and task details, Archive, Next Action).
5. The `hb-status.md` skill is updated to invoke `hb-sdk summarize --format md` and write its stdout directly to the user — no internal template reading or rendering.
6. `skills/references/status-template.md` is deleted if it is no longer referenced by any skill file after the skill update.

---

# Out of scope

- Changes to the JSON schema emitted by `hb-sdk summarize`.
- Changes to any other `hb-sdk` subcommands or flags.
- Styling or content changes to the rendered markdown beyond matching current output.
