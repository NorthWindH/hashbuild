# Folder/File Structure

- all files in `.hb` at top-level in project directory
- inside `.hb/`:
  - task folders in `task/`
  - inside `task/` folder:
    - active task folders in `active/`
    - archived task folders in `archive/`
    - for each task folder:
      - name pattern in [Task Name Format](#task-name-format) below
      - inside each task folder:
        - `.hb-task.json`: task file info
        - folder for each step: `<step-n>/`
        - steps are numbered in ascending order starting at `0`
        - examples: `step-0`, `step-1`, `step-2`, ..., `step-99999`

## Structure Examples

```
.hb/
└── task/
    ├── active/
    │   └── hasan/
    │       └── projslug-42-add-login-page/
    │           ├── .hb-task.json
    │           ├── step-0-scaffold-routes/
    │           ├── step-1-add-form/
    │           └── step-2-wire-auth/
    └── archive/
        └── hasan/
            └── projslug-17/
                ├── .hb-task.json
                ├── step-0-init-db/
                └── step-1-seed-data/
```

Mixed — some steps with `step_extra`, some without:

```
.hb/
└── task/
    ├── active/
    │   └── hasan/
    │       └── abc-55-refactor-api/
    │           ├── .hb-task.json
    │           ├── step-0/
    │           ├── step-1-extract-handler/
    │           └── step-2/
    └── archive/
```

Multi-author, multiple active tasks:

```
.hb/
└── task/
    ├── active/
    │   ├── hasan/
    │   │   ├── abc-100-fix-auth-token/
    │   │   │   ├── .hb-task.json
    │   │   │   ├── step-0-repro/
    │   │   │   └── step-1-patch-expiry/
    │   │   └── abc-101/
    │   │       ├── .hb-task.json
    │   │       └── step-0/
    │   └── northwind/
    │       └── abc-200-update-schema/
    │           ├── .hb-task.json
    │           ├── step-0-audit-tables/
    │           ├── step-1-migrate/
    │           └── step-2-backfill/
    └── archive/
        └── hasan/
            └── abc-99-initial-setup/
                ├── .hb-task.json
                ├── step-0-bootstrap/
                └── step-1-config/
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
