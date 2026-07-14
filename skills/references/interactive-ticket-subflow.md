> **Subflow — interactive ticket creation.** Shared by `hb-task-create`,
> `hb-task-step-add`, and `hb-ticket-discuss`'s `describe-ticket-subflow.md`/
> `load-ticket-subflow.md`. Contains no side effects (no commit, no SDK calls,
> no user notification beyond the prompt itself).

**Caller contract.** Before injecting this subflow, the calling skill must have resolved:

- `$TICKET_SUPPLIED` — set to `true` if `--ticket <path>` was passed; otherwise unset or `false`
- `$NO_INTERACTIVE` — set to `true` if `--no-interactive` was passed; otherwise unset or `false`

#### A. Guard clause

- If `$TICKET_SUPPLIED` is `true`: skip this entire subflow (a ticket file was supplied; it takes precedence). Do nothing.
- If `$NO_INTERACTIVE` is `true`: skip this entire subflow (skeleton-only mode requested). Do nothing.
- Otherwise: continue to Section A.1.

#### A.1 Resolve target path

Resolve `$TARGET_PATH` — the directory `ticket.md` will be written to — with this precedence:

1. **Harness-declared session scratch dir.** If the current operating context/instructions document a session-specific scratch or temporary directory (any convention — for example, some harnesses surface this as in-session "Scratchpad Directory" guidance), use it.
2. **Hand-rolled fallback.** Otherwise, run `mktemp -d /tmp/hb-ticket.XXXXXXXX` and use the directory it creates.

`mktemp -d` failing (e.g. `/tmp` unwritable) is a hard environment failure outside this subflow's control — surface the error verbatim rather than silently retrying or picking an unvalidated path.

Continue to Section B.

#### B. Prompt step

Ask the user:

> "Please describe what this ticket should cover. You can share content in any form: freeform prose, a bullet list, a structured draft, or a fully-formed Background / Acceptance Criteria / Out of scope."

Capture the user's response as `$USER_INPUT`. Do not restate or summarize the input yet; proceed to Section C.

#### C. Transform step

Read `${CLAUDE_SKILL_DIR}/references/ticket-template.md` before applying any transform rules. Use it as the authoritative structural reference for heading names, section order, list format, and prose guidance when shaping the output.

Apply these rules to convert `$USER_INPUT` into the standard three-section `ticket.md` structure.

**Rule 1 — Near-perfect match (transcribe):**

If `$USER_INPUT` already contains recognizable Background and Acceptance Criteria sections (exact or near-exact heading names, in any order):

- Transcribe verbatim.
- Apply only minimal conforming adjustments: normalize heading levels to `#`, capitalize section names (`Background`, `Acceptance Criteria`, `Out of scope`), and normalize list markers to `- ` or `1. ` as appropriate.
- Do not paraphrase or restructure.

**Rule 2 — Freeform (derive):**

If `$USER_INPUT` is prose, bullets, or a partial draft that does not match Rule 1:

| Section                 | Derived from                                                                                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `# Background`          | The "why": motivation, context, and the problem being solved. Narrative prose, 1–3 sentences.                                                          |
| `# Acceptance Criteria` | Discrete checkable conditions. Numbered list. Extract explicit requirements; infer additional criteria only when clearly implied by the user's intent. |
| `# Out of scope`        | Explicit exclusions stated by the user. **Omit this section entirely if the user stated no exclusions and none are inferred from the content.**        |

**Ambiguity rule:** When content could belong in either Background or Acceptance Criteria, prefer Background for narrative/context statements and Acceptance Criteria for conditions that can be verified true or false.

#### D. Write step

Before writing, if `$TARGET_PATH/ticket.md` already exists, delete it.

Write the derived content to `$TARGET_PATH/ticket.md` using this structure:

```
# Background

<background text>

---

# Acceptance Criteria

<numbered list>

---

# Out of scope         ← omit this section and the preceding --- if none

<bullet list>
```

**Return value:** `$TARGET_PATH` — the directory resolved in Section A.1 — so the caller can build `$TARGET_PATH/ticket.md` for its own use (e.g. a `--ticket` argument, or a read-back per `ticket-loop-subflow.md`'s ticket entry model).
