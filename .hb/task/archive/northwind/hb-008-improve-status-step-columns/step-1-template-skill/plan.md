# Step 1 Plan — Template and Skill Update

Step 0 shipped a new `hb-sdk summarize` JSON shape (six lifecycle-count fields, two name-list fields, `archive.recent`) that the `hb-status` skill and its status template have not yet consumed. Today `/hb-status` attempts to read `steps_pending_execution` (now absent) and renders a two-column count table and a `Last archived` row (now wrong). This step updates the two presentation-layer files — `skills/references/status-template.md` and `skills/hb-status/SKILL.md` — so the skill renders the nine-column lifecycle table, zero-as-dash, per-task Needs review / Needs work sublists, and the archive recent list, and keeps the embedded JSON schema and render instructions in sync. Behavior change only; no SDK changes, no other skills touched. Once landed, `/hb-status` will produce the full lifecycle view defined in the task ticket.

Source ticket: `./ticket.md`. Builds on the **shipped** step 0 (`skills/scripts/hb-sdk`) which replaced `steps_pending_execution` / `steps_with_ticket` / `last_archived` with the new fields; this plan targets the skill files as they exist **now** (pre-step-1).

---

## 0. Current-state facts (verified during planning)

**`skills/hb-status.md` — JSON schema (step 2, confirmed at lines 43–64):**
```
"steps": [
  { "name": str, "has_ticket": bool, "has_plan": bool, "has_execution": bool }
],
"steps_pending_execution": int,
"next_pending_step": str | null
```
and:
```
"archive": {
  "count": int,
  "last_archived": str | null
}
```
Both `steps_pending_execution` and `last_archived` are now absent from the live SDK output (confirmed in step-0 execution AC 7 check); `steps_with_ticket` is also absent and was never in `SKILL.md`.

**`skills/hb-status.md` — step 4 render instructions (confirmed at lines 74–79):**
```
- **Active Tasks**: one table with columns Task, Steps pending execution, Total steps
- **Archive**: fill `count` and `last_archived`; omit the "Last archived" row when `last_archived` is null
```
References stale column names and stale archive field.

**`skills/references/status-template.md` — Active Tasks table (confirmed at lines 26–34):**
Columns: `Task | Ticket | Steps pending execution | Steps with ticket | Total steps`.
Comment block above defines `steps_pending_execution` and `steps_with_ticket`.

**`skills/references/status-template.md` — Archive section (confirmed at lines 39–49):**
Two-row table with `Archived tasks` and `Last archived`; comment says "most recent modification time".

**`skills/references/status-template.md` — decision tree (confirmed at lines 55–71):**
No bare field-name references in the decision tree body itself; the comment block above the Active Tasks table is where old field names appear as column definitions.

**Live SDK output (from step-0 execution smoke and today's `/hb-status` run — confirmed):**
New active-task fields: `steps_skeleton`, `steps_ticketed`, `steps_planned`, `steps_executed`, `steps_review_open`, `steps_reviewed` (int); `steps_needs_review`, `steps_needs_work` (array of str); each step object has `has_review: bool` and `status: str`. Archive: `{ count: int, recent: [{ author, task_id, task_folder }] }`.

### 0.1 Impact (before → after)

| Artifact | Before | After |
|---|---|---|
| Active Tasks table | 5 columns; old field names | 9 columns; zero-as-dash; + Needs review/work sublists |
| Archive section | 2-row table with `Last archived` | Count row + `recent` bulleted list; omit when `recent` is empty |
| SKILL.md JSON schema | 4 step fields; `steps_pending_execution`; `archive.last_archived` | 6 step fields + `status`; 6 count fields + 2 list fields; `archive.recent` |
| SKILL.md step 4 instructions | Old column names; old archive field | New column names; zero-as-dash rule; sublist rule; new archive render |
| Decision tree | Field-name references in column comment | Updated to new field names |

Change type: output-altering for `hb-status` rendered reports; additive+removing for SKILL.md schema (no logic changes).

### 0.2 Non-regression proof / risk

The two files edited are instruction/template files — no executable code is touched. The only risk is introducing an inconsistency between `SKILL.md` schema and the actual SDK output, which would cause a future `/hb-status` run to misread the JSON. This is prevented by: (a) the new schema in SKILL.md is derived directly from step-0's execution summary (confirmed output shape) and (b) today's live `hb-sdk summarize` call (already run in the `/hb-status` output at session start) gives ground truth to check against.

No existing callers of these files beyond Claude running `/hb-status`.

---

## 1. Design overview

Two files receive targeted edits; changes are ordered by file to avoid context-switching:

1. **`skills/references/status-template.md`** — replace Active Tasks table + comment, replace Archive section, update decision tree comment
2. **`skills/hb-status.md`** — replace JSON schema block, replace step 4 render instructions

**Zero-as-dash rule:** count cells in the Active Tasks table show `—` when the count is zero. The `Total steps` column is exempt (always shows the raw integer, including `0`, to distinguish "no steps yet" from "all reviewed"). This rule lives in the template comment and the SKILL.md render instructions.

**Sublist rendering:** below each task row, two indented lists are rendered using standard Markdown list syntax inside the table row's following block. The template shows them as example bullets; the SKILL.md render instruction says to omit each list when the corresponding array is empty.

**Archive recent list:** the archive key changes from a two-column table to a count-only row plus a bulleted list. Omit the section entirely when `archive.recent` is empty (not when `count` is 0 — both conditions are equivalent since `count` equals `recent.length`, but the ticket says "omit when `archive.recent` is empty", which is the cleaner guard).

**Alternatives considered and rejected:**
- Keeping a two-column table and adding columns for each lifecycle stage: rejected — the ticket specifies replacing the table with the nine-column format.
- Nesting sublists inside table cells: rejected — Markdown tables don't support multi-line cells portably; separate indented blocks below the row are idiomatic.
- Keeping `Last archived` row alongside `recent` list: rejected — ticket AC 6 explicitly removes it.

---

## 2. File specifications

### 2.1 `skills/references/status-template.md`

**Active Tasks table and comment (replaces lines 26–34):**

```markdown
<!--
  One row per active task, in filesystem order (author → task_id).
  "Ticket" shows ✓ if the task has ticket.md, ✗ otherwise (task-level has_ticket).
  Count columns (Skeleton/Ticketed/Planned/Executed/Review open/Reviewed) show — when zero.
  "Total" always shows the raw integer.
  Below each task row, two indented lists are rendered (each omitted when the
  corresponding array is empty):
    - Needs review — step folder names from steps_needs_review
    - Needs work   — step folder names from steps_needs_work
-->

| Task                     | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total |
| ------------------------ | ------ | -------- | -------- | ------- | -------- | ----------- | -------- | ----- |
| `<author>/<task_folder>` | ✓/✗   | `<—/n>`  | `<—/n>`  | `<—/n>` | `<—/n>`  | `<—/n>`     | `<—/n>`  | `<n>` |

  - **Needs review:** `<step-folder>`, …
  - **Needs work:** `<step-folder>`, …
```

**Archive section (replaces lines 39–49):**

```markdown
|                |           |
| -------------- | --------- |
| Archived tasks | `<count>` |

- `<author>/<task_folder>`

<!--
  Recent: up to 5 most-recently-archived entries from archive.recent, each as
  author/task_folder. Omit the section entirely when archive.recent is empty.
-->
```

**Decision tree (lines 55–71) — update comment only:**
Replace the two references to old field names in the column-definition comment above the Active Tasks table (already handled in §2.1 above). The decision tree body itself uses plain English conditions ("a step with ticket.md but no plan.md") — no field names appear there and no logic changes are required (ticket AC 9 says "beyond field name updates").

### 2.2 `skills/hb-status.md`

**JSON schema block (replaces the ` ``` ` fenced block in step 2, currently lines 43–64):**

```json
{
  "initialized": bool,
  "active_tasks": [
    {
      "author": str,
      "task_id": str,
      "task_folder": str,
      "task_path": str,
      "has_ticket": bool,
      "total_steps": int,
      "steps": [
        {
          "name": str,
          "has_ticket": bool,
          "has_plan": bool,
          "has_execution": bool,
          "has_review": bool,
          "status": str
        }
      ],
      "steps_skeleton": int,
      "steps_ticketed": int,
      "steps_planned": int,
      "steps_executed": int,
      "steps_review_open": int,
      "steps_reviewed": int,
      "steps_needs_review": [str],
      "steps_needs_work": [str],
      "next_pending_step": str | null
    }
  ],
  "archive": {
    "count": int,
    "recent": [
      { "author": str, "task_id": str, "task_folder": str }
    ]
  }
}
```

**Step 4 render instructions (replaces the three Active Tasks / Archive bullets, currently lines 74–79):**

```markdown
- **Active Tasks**: one table with columns Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total — one row per entry in `active_tasks` using `author/task_folder`; show `—` for any count column that is zero (Total column always shows the raw integer); below each row render two indented lists (each omitted when the corresponding array is empty): **Needs review** (names from `steps_needs_review`) and **Needs work** (names from `steps_needs_work`); omit the section entirely when `active_tasks` is empty
- **Archive**: render a count-only row (`Archived tasks | <count>`) then a bulleted list of `author/task_folder` from `archive.recent` (up to 5 entries); omit the section entirely when `archive.recent` is empty
```

---

## 3. Integration / wiring

Both files are instruction/template files consumed only by Claude executing `/hb-status`. No call sites in executable code. No build wiring, dependency manifests, or lockfiles affected. All other hb-\* skills reference `status-template.md` indirectly (as a template example) but do not parse it programmatically; changing column names does not break them.

Note: `skills/hb-status.md` is the canonical project-level source; the installed copy at `~/.claude/skills/hb-status/SKILL.md` is a deploy artifact and is not modified by this step.

The step-4 render bullet currently also references `last_archived` null-check — that bullet is replaced entirely, removing the reference.

---

## 4. File-by-file changes

| File | Change |
|---|---|
| `skills/references/status-template.md` | **edit** — replace Active Tasks table + comment block; replace Archive section; column-definition comment updated (decision tree body unchanged) |
| `skills/hb-status.md` | **edit** — replace JSON schema fenced block (step 2); replace Active Tasks and Archive bullets in step 4 render instructions |

No other files change. No dependency manifests or lockfiles.

---

## 5. Tests

No automated test suite covers instruction/template files — they are consumed at runtime by Claude. Verification is behavioral (§6). The SDK test suite (`tests/skills/scripts/test_hb-sdk.py`) is unchanged; its 129 tests remain the regression guard for the data layer. No new tests are introduced or required for this step.

---

## 6. Verification (after implementation)

1. **Scope check:** `git diff --name-only` shows exactly two files — `skills/references/status-template.md` and `skills/hb-status.md`. Nothing else.

2. **Schema correctness:** confirm the new JSON schema in SKILL.md exactly matches the live SDK output:
   ```bash
   skills/scripts/hb-sdk summarize | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   t = d['active_tasks'][0]
   for f in ['steps_skeleton','steps_ticketed','steps_planned','steps_executed','steps_review_open','steps_reviewed']:
       assert f in t, f'missing: {f}'
   for f in ['steps_needs_review','steps_needs_work']:
       assert f in t and isinstance(t[f], list), f'missing/wrong: {f}'
   assert 'steps_pending_execution' not in t, 'stale field present'
   assert 'recent' in d['archive'] and isinstance(d['archive']['recent'], list), 'archive.recent missing'
   assert 'last_archived' not in d['archive'], 'stale last_archived present'
   print('schema OK')
   "
   ```

3. **AC B1–B4 — Active Tasks table:** confirm status-template.md shows the nine-column header and that the comment instructs zero-as-dash and the two sublists.
   - Open `skills/references/status-template.md` and verify the header row contains exactly: Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total.
   - Verify the comment above says "show — when zero" and names `steps_needs_review` / `steps_needs_work`.
   - Verify old columns (`Steps pending execution`, `Steps with ticket`) are absent.

4. **AC C.3 — Archive section:** confirm the Archive section in status-template.md has no `Last archived` row and includes a bulleted list placeholder for `author/task_folder`.

5. **AC D.1 — schema:** `skills/hb-status.md` fenced block contains `steps_skeleton` through `steps_reviewed`, `steps_needs_review`, `steps_needs_work`, `has_review`, `status`, and `archive.recent`; does not contain `steps_pending_execution`, `steps_with_ticket`, or `last_archived`.

6. **AC D.1 render instructions:** step 4 bullet in `skills/hb-status.md` names the nine columns and mentions the `—` rule and the two sublists. The Archive bullet references `archive.recent` and not `last_archived`.

7. **AC D.2 — decision tree field names:** neither `status-template.md` nor `hb-status.md` contains the strings `steps_pending_execution` or `steps_with_ticket` anywhere.
   ```bash
   grep -rn "steps_pending_execution\|steps_with_ticket" skills/hb-status.md skills/references/status-template.md
   # expect: no output
   ```

---

## 7. Acceptance-criteria traceability

| AC | Satisfied by | Note |
|---|---|---|
| B1 — nine-column table header | §2.1, §6.3 | Exact column names in template |
| B2 — zero-as-dash | §2.1 comment + §2.2 render, §6.3 | Total column exempted |
| B3 — old columns removed | §2.1, §6.3 | Steps pending execution, Steps with ticket absent |
| B4 — Needs review/work sublists | §2.1, §2.2 render, §6.3 | Omit when empty |
| C.3 — archive.recent list | §2.1, §6.4 | Omit section when recent is empty |
| C.3 — Last archived row removed | §2.1, §6.4 | Replaced by recent list |
| D.1 — schema updated (remove old) | §2.2, §6.5 | steps_pending_execution, steps_with_ticket, last_archived absent from hb-status.md |
| D.1 — schema updated (add new) | §2.2, §6.5 | Six count fields, two list fields, status, archive.recent |
| D.1 — render instructions updated | §2.2, §6.6 | New column names, dash rule, sublists, archive.recent |
| D.2 — decision tree field names | §2.1, §6.7 | Strings absent from hb-status.md and status-template.md |

---

## 8. Out of scope (per ticket)

- SDK changes (`skills/scripts/hb-sdk`, `tests/`) — shipped in step 0
- Changes to any skill other than `hb-status/SKILL.md`
- Decision tree logic changes — field name updates only; conditions and recommended actions unchanged
- Review file structure or authoring conventions
