# Step 2 Plan — Short Lifecycle Column Headers in Status Table

The nine-column active-tasks table in `/hb-status` currently uses verbose headers
(`Skeleton`, `Ticketed`, `Planned`, `Executed`, `Review open`, `Reviewed`) that overflow
narrow terminals. This step abbreviates those six headers to single- or two-character
codes (`S`, `T`, `P`, `E`, `RO`, `R`) and appends a legend block immediately after the
table so readers can decode the codes without prior knowledge. The change is
output-altering but scope-bounded: only the six lifecycle column headers and the new
legend block change; all other columns (`Task`, `Ticket`, `Total`), all row values,
sub-lists, and other report sections are untouched. The externally observable effect:
`/hb-status` output narrows by ~30 characters of column-header width and gains a legend
six lines below the table.

Source ticket: `./ticket.md`. No prior steps in this task have shipped; this is the
first (and only) implementation step. The plan targets the code as it exists now.

---

## 0. Current-state facts (verified during planning)

**Files inspected:**

- `skills/references/status-template.md` — defines the Markdown table structure and
  column names rendered by `/hb-status`
- `skills/hb-status.md` — Step 4 hardcodes the same column names in its prose
  description of how to render the Active Tasks table

**Current table header (status-template.md:36–38):**

```
| Task                     | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total |
| ------------------------ | ------ | -------- | -------- | ------- | -------- | ----------- | -------- | ----- |
| `<author>/<task_folder>` | ✓/✗   | `<—/n>`  | `<—/n>`  | `<—/n>` | `<—/n>`  | `<—/n>`     | `<—/n>`  | `<n>` |
```

**Current prose in hb-status.md Step 4 (line 93):**

> "…one table with columns Task | Ticket | Skeleton | Ticketed | Planned | Executed | Review open | Reviewed | Total…"

**Blast radius:** Only `/hb-status` reads `status-template.md` and uses Step 4's prose.
No other skill or script references these column names. The hb-sdk `summarize` command
(which produces the JSON) uses the field names `steps_skeleton`, `steps_ticketed`, etc.
— these are internal JSON keys and are unaffected by display label changes. Confirmed:
no other file references the string "Skeleton" or "Review open" as column headers.

### 0.1 Impact (before → after)

| Element                    | Before        | After                             |
| -------------------------- | ------------- | --------------------------------- |
| Column header: Skeleton    | `Skeleton`    | `S`                               |
| Column header: Ticketed    | `Ticketed`    | `T`                               |
| Column header: Planned     | `Planned`     | `P`                               |
| Column header: Executed    | `Executed`    | `E`                               |
| Column header: Review open | `Review open` | `RO`                              |
| Column header: Reviewed    | `Reviewed`    | `R`                               |
| Legend block               | absent        | added immediately after the table |
| All other columns/rows     | unchanged     | unchanged                         |

Change type: **output-altering** (column display labels change; legend added).

### 0.2 Non-regression proof / risk

| At-risk element                     | Current behavior             | Guard                                             |
| ----------------------------------- | ---------------------------- | ------------------------------------------------- |
| Task column                         | Shows `author/task_folder`   | Not touched; only lifecycle-column headers change |
| Ticket column                       | Shows ✓/✗                    | Not touched                                       |
| Total column                        | Shows raw int                | Not touched                                       |
| Cell values (counts)                | `—` or `n`                   | Only header row changes, not data rows            |
| Needs review / Needs work sub-lists | Rendered below each task row | Not touched                                       |
| Archive section                     | Count + bullet list          | Not touched                                       |
| Next Action section                 | Decision-tree output         | Not touched                                       |

The change is limited to six header strings and the addition of a legend block after the
table. It cannot alter row data because row data is derived from JSON field values, not
from column header labels.

---

## 1. Design overview

Two files receive edits:

1. **`skills/references/status-template.md`** — replace the six long column headers
   with their abbreviations in the header row and separator row, then append a legend
   block immediately after the table (before `---`).

2. **`skills/hb-status.md`** — update the Step 4 prose column list to use the
   abbreviated names so the skill's instructions stay in sync with the template.

No new files, no new dependencies, no build wiring changes. The legend is static
Markdown text.

**Legend format** (to appear immediately before the table):

```
**Legend:** S = Skeleton · T = Ticketed · P = Planned · E = Executed · RO = Review Open · R = Reviewed
```

This is a single line rather than a six-item list to keep vertical space minimal.

**Alternatives considered and rejected:**

- _Tooltip-style HTML in Markdown_ — not universally rendered in terminals; rejected.
- _Footnote-style `[1]` references_ — harder to parse at a glance; adds complexity for
  no gain; rejected.
- _Separate legend section with heading_ — adds a heading to the report just for six
  abbreviations; disproportionate; rejected.

---

## 2. Column-header abbreviation mapping — specification

| Long header   | Abbreviated header | JSON field driving column value |
| ------------- | ------------------ | ------------------------------- |
| `Skeleton`    | `S`                | `steps_skeleton`                |
| `Ticketed`    | `T`                | `steps_ticketed`                |
| `Planned`     | `P`                | `steps_planned`                 |
| `Executed`    | `E`                | `steps_executed`                |
| `Review open` | `RO`               | `steps_review_open`             |
| `Reviewed`    | `R`                | `steps_reviewed`                |

The JSON field names are **unchanged** — only the display labels change.

**Legend line (exact text):**

```
**Legend:** S = Skeleton · T = Ticketed · P = Planned · E = Executed · RO = Review Open · R = Reviewed
```

No algorithm or logic change — this is a pure string substitution in a template and a
template-description string.

**Failure contract:** N/A — this is a static text change; there is no runtime logic to
fail.

---

## 3. Integration / wiring

- `skills/hb-status.md` Step 4 references the column names in prose; it must be updated
  to match the new abbreviated names so the skill's instructions and the template stay
  consistent. The update is to the description string only — no signature, no logic, no
  callers affected.
- No configuration, build wiring, entry points, scripts, or dependency manifests change.
- The hb-sdk `summarize` command is **untouched**; it outputs JSON field names, not
  column headers.

---

## 4. File-by-file changes

| File                                   | Change                                                                                                                |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `skills/references/status-template.md` | **edit** — replace six long column headers with abbreviations in header + separator rows; add legend line before table |
| `skills/hb-status.md`                  | **edit** — update Step 4 prose column-name list to use abbreviated names                                              |

No new files. No dependency manifests or lockfiles affected.

---

## 5. Tests

This project has no automated test suite for skill Markdown output. Verification is
manual (see §6). The changes are pure text substitutions with no logic branch, so the
risk profile is low; a careful visual diff is the appropriate check.

**Non-regression:** No existing tests reference these column header strings. The hb-sdk
`summarize` JSON field names are unchanged, so any downstream consumers of that JSON are
unaffected.

---

## 6. Verification (after implementation)

1. **Run `/hb-status`** in this repository and confirm the output renders without broken
   Markdown.

2. **Per-AC checks:**

   | AC         | Check                                                                                                       |
   | ---------- | ----------------------------------------------------------------------------------------------------------- |
   | AC 1.1–1.6 | Header row shows `S`, `T`, `P`, `E`, `RO`, `R` (not the long names)                                         |
   | AC 2       | A legend line appears immediately before the table, mapping each abbreviation to its full name |
   | AC 3       | `Task`, `Ticket`, `Total` columns and all row values are unchanged                                          |
   | AC 4       | Output renders as valid Markdown with no broken table rows or missing sections                              |

3. **Scope check:** only `skills/references/status-template.md` and `skills/hb-status.md`
   are modified. No other files change.

---

## 7. Acceptance-criteria traceability

| AC                                    | Satisfied by                                    | Note                |
| ------------------------------------- | ----------------------------------------------- | ------------------- |
| 1.1 `Skeleton` → `S`                  | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 1.2 `Ticketed` → `T`                  | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 1.3 `Planned` → `P`                   | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 1.4 `Executed` → `E`                  | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 1.5 `Review Open` → `RO`              | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 1.6 `Reviewed` → `R`                  | §2 mapping table; §4 edit to status-template.md | Header row change   |
| 2 Legend block before table           | §1 legend format; §4 edit to status-template.md | Single-line legend  |
| 3 All other columns/content unchanged | §0.2 non-regression table; §4 scope             | No row data touched |
| 4 Output renders correctly            | §6 verification step 1                          | Manual visual check |

---

## 8. Out of scope (per ticket)

- Changing any section of `/hb-status` output other than the lifecycle column headers
  and the new legend block.
- Responsive or dynamic width logic; static abbreviations only.
- Modifying hb-sdk `summarize` JSON field names or any script logic.
