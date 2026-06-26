> **Subflow — interactive ticket creation.** Shared by `hb-task-create` and
> `hb-task-step-add`. Contains no side effects (no commit, no SDK calls, no user
> notification beyond the prompt itself).

**Caller contract.** Before injecting this subflow, the calling skill must have resolved:

- `$TARGET_PATH` — absolute path to the folder where `ticket.md` will be written
- `$TICKET_SUPPLIED` — set to `true` if `--ticket <path>` was passed; otherwise unset or `false`
- `$NO_INTERACTIVE` — set to `true` if `--no-interactive` was passed; otherwise unset or `false`

#### A. Guard clause

- If `$TICKET_SUPPLIED` is `true`: skip this entire subflow (a ticket file was supplied; it takes precedence). Do nothing.
- If `$NO_INTERACTIVE` is `true`: skip this entire subflow (skeleton-only mode requested). Do nothing.
- Otherwise: continue to Section B.

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
