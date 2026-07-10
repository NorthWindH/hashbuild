# Folder/File Structure

- all files in `.hb` at top-level in project directory
- inside `.hb/`:
  - `facts.md`: persistent, project-level facts store; created/maintained via
    `hb-sdk facts write`
  - task folders in `task/`
  - inside `task/` folder:
    - active task folders in `active/`
    - archived task folders in `archive/`
    - for each task folder:
      - name pattern in [Task Name Format](#task-name-format) below
      - inside each task folder:
        - `.hb-task.json`: task file info
        - `ticket.md`: task-level ticket; optional
        - folder for each step: `<step-n>/`
        - steps are numbered in ascending order starting at `0`
        - examples: `step-0`, `step-1`, `step-2`, ..., `step-99999`
        - for each step folder:
          - name pattern in [Step Name Format](#step-name-format) below
          - inside each step folder:
            - `ticket.md`: step-level ticket; created by user or by /hb-task-plan to define step acceptance criteria
            - `plan.md`: created by /hb-task-step-plan
            - `execution-*.md`: created by /hb-task-step-execute
            - `review.md`: created by /hb-task-step-review-init and maintained by user and /hb-task-step-review-address

## Structure Examples

```
.hb/
├── facts.md
└── task/
    ├── active/
    │   └── hasan/
    │       └── projslug-42-add-login-page/
    │           ├── .hb-task.json
    │           ├── ticket.md
    │           ├── step-0-scaffold-routes/
    │           │   ├── ticket.md
    │           │   ├── plan.md
    │           │   ├── execution-2026-06-01T09-15-32-0500.md
    │           │   └── review.md
    │           ├── step-1-add-form/
    │           │   ├── ticket.md
    │           │   └── plan.md
    │           └── step-2-wire-auth/
    │               └── ticket.md
    └── archive/
        └── hasan/
            └── projslug-17/
                ├── .hb-task.json
                ├── step-0-init-db/
                │   ├── ticket.md
                │   ├── plan.md
                │   ├── execution-2026-05-20T14-02-11-0500.md
                │   └── review.md
                └── step-1-seed-data/
                    ├── ticket.md
                    ├── plan.md
                    ├── execution-2026-05-21T10-44-07-0500.md
                    └── review.md
```

Mixed — some steps with `step_extra`, some without:

```
.hb/
├── facts.md
└── task/
    ├── active/
    │   └── hasan/
    │       └── abc-55-refactor-api/
    │           ├── .hb-task.json
    │           ├── step-0/
    │           │   ├── ticket.md
    │           │   ├── plan.md
    │           │   ├── execution-2026-06-10T11-30-00-0500.md
    │           │   └── review.md
    │           ├── step-1-extract-handler/
    │           │   ├── ticket.md
    │           │   └── plan.md
    │           └── step-2/
    │               └── ticket.md
    └── archive/
```

Multi-author, multiple active tasks:

```
.hb/
├── facts.md
└── task/
    ├── active/
    │   ├── hasan/
    │   │   ├── abc-100-fix-auth-token/
    │   │   │   ├── .hb-task.json
    │   │   │   ├── ticket.md
    │   │   │   ├── step-0-repro/
    │   │   │   │   ├── ticket.md
    │   │   │   │   ├── plan.md
    │   │   │   │   ├── execution-2026-06-18T08-55-42-0500.md
    │   │   │   │   └── review.md
    │   │   │   └── step-1-patch-expiry/
    │   │   │       ├── ticket.md
    │   │   │       └── plan.md
    │   │   └── abc-101/
    │   │       ├── .hb-task.json
    │   │       └── step-0/
    │   │           └── ticket.md
    │   └── northwind/
    │       └── abc-200-update-schema/
    │           ├── .hb-task.json
    │           ├── step-0-audit-tables/
    │           │   ├── ticket.md
    │           │   ├── plan.md
    │           │   ├── execution-2026-06-19T13-22-05-0500.md
    │           │   └── review.md
    │           ├── step-1-migrate/
    │           │   ├── ticket.md
    │           │   └── plan.md
    │           └── step-2-backfill/
    │               └── ticket.md
    └── archive/
        └── hasan/
            └── abc-99-initial-setup/
                ├── .hb-task.json
                ├── step-0-bootstrap/
                │   ├── ticket.md
                │   ├── plan.md
                │   ├── execution-2026-06-05T16-10-33-0500.md
                │   └── review.md
                └── step-1-config/
                    ├── ticket.md
                    ├── plan.md
                    ├── execution-2026-06-06T09-03-57-0500.md
                    └── review.md
```

# Name Format

## Task Name Format

```
<author>/<task_id><task_extra>
```

- `<author>`: required. Username of the person owning the task
- `<task_id>`: required. Task identifier, usually a ticket id
  - format: `<prefix>-<num>`
  - examples:
    - `projslug-123456789`
    - `PROJSLUG-123456789`
- `<task_extra>`: optional. Extra flavor to help identify a ticket
  - example: `-some-stuff-that-helps-explain-ticket`
  - format: `-<slug>`
  - slug allowed character class: `[a-z-]`

### Task Name Examples

| Name                           | Valid                  |
| ------------------------------ | ---------------------- |
| `hasan/abc-123`                | yes                    |
| `hasan/abc-123-add-login-page` | yes                    |
| `hasan/abc-123-add-login-page` | yes                    |
| `abc-123`                      | no — missing author    |
| `hasan/add-login-page`         | no — missing ticket ID |

`hb-sdk` enforces this format and will reject invalid names.

## Step Name Format

```
<step_id><step_extra>
```

- `<step_id>`: required. Step identifier
  - format: `step-<n>`
  - `step-`: constant prefix
  - `<n>`:
    - numeric step identifier
    - steps are numbered in ascending order starting at `0`
- `<step_extra>`: optional. Extra flavor to help identify a step
  - example: `-some-stuff-that-helps-explain-step`
  - format: `-<slug>`
  - slug allowed character class: `[a-z-]`

### Step Name Examples

| Name                       | Valid                       |
| -------------------------- | --------------------------- |
| `step-0`                   | yes                         |
| `step-1-add-form`          | yes                         |
| `step-99999-final-cleanup` | yes                         |
| `step-`                    | no — missing `<n>`          |
| `step-0-AddForm`           | no — uppercase in slug      |
| `0-add-form`               | no — missing `step-` prefix |
