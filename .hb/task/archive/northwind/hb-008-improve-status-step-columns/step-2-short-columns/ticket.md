# Background

The nine-column lifecycle table in `/hb-status` output overflows on narrow terminals because column headers like "Skeleton", "Ticketed", "Planned", "Executed", "Review Open", "Reviewed" are long. Abbreviating them and adding a legend keeps the table compact without losing meaning.

---

# Acceptance Criteria

1. The lifecycle columns in the status table use these abbreviated headers:
    1. `Skeleton` → `S`
    2. `Ticketed` → `T`
    3. `Planned` → `P`
    4. `Executed` → `E`
    5. `Review Open` → `RO`
    6. `Reviewed` → `R`
2. A legend block appears immediately after the table, mapping each abbreviation to its full name:
    - `S` = Skeleton Steps
    - `T` = Ticketed Steps
    - `P` = Planned Steps
    - `E` = Executed Steps
    - `RO` = Review Open Steps
    - `R` = Reviewed Steps
3. All other columns and table content are unchanged.
4. The status output still renders correctly (no broken Markdown, no missing rows).

---

# Out of scope

- Changing any other section of `/hb-status` output beyond the column headers and the new legend.
- Responsive or dynamic width logic; this step only introduces static abbreviations.
