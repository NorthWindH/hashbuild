# Task Name Format

```
<author>/<task-id><task-extra>
```

- `<author>`: required. Username of the person owning the task
- `<task-id>`: required. Task identifier, usually a ticket id
  - format: `<prefix>-<num>`
  - examples:
    - `projslug-123456789`
    - `PROJSLUG-123456789`
- `<task-extra>`: optional. Extra flavor to help identify a ticket
  - format: `-some-stuff-that-helps-explain-ticket`
  - allowed character class: `[a-z-]`

## Examples

| Name                           | Valid                  |
| ------------------------------ | ---------------------- |
| `hasan/abc-123`                | yes                    |
| `hasan/abc-123-add-login-page` | yes                    |
| `hasan/abc-123-add-login-page` | yes                    |
| `abc-123`                      | no — missing author    |
| `hasan/add-login-page`         | no — missing ticket ID |

`hb-sdk` enforces this format and will reject invalid names.
