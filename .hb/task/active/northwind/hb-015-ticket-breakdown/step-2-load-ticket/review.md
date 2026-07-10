# Step 2 Review

## Status

| ID              | Resolution |
| --------------- | ---------- |
| STEP-2-REVIEW-1 | ✅ Addressed — restored `Read`/`WebFetch` (needed by file/web Load sources); left `Bash(find *)` dropped, unused |
| STEP-2-REVIEW-2 |            |

---

## Notes

### STEP-2-REVIEW-1: Dropped broad `Read`/`WebFetch`/`Bash(find *)` allowed-tools — verify Load ticket sources still work — ADDRESSED

- **file(s):** `skills/hb-ticket-discuss.md` (`allowed-tools` frontmatter, around `TODO REVIEW` marker)
- The step removed the broad `Read`, `WebFetch`, and `Bash(find *)` entries from `allowed-tools`, replacing them with a comment: overly broad permissions aren't needed and the user can grant them as required. Confirm this doesn't silently break the file/Jira/web Load ticket sources added in this step (e.g. reading a local ticket file, or fetching a web-sourced ticket) now that the broad grants are gone.
- **source:** `TODO REVIEW` in commit `5592dd78ea71f91c56796a5cbc7a02a4c4d17963` — delete comment from source file after addressing

**Resolution:** Re-checked `skills/references/load-ticket-subflow.md` against the trimmed grant list:

| tool dropped | needed by Load ticket? | evidence |
|---|---|---|
| `Read` | yes — §B file source resolves an arbitrary user-given path/glob (e.g. `drafts/*.md`), not confined to `/tmp` | §B.1–2; only `Read(//tmp/*)`/`Read(//private/tmp/*)` remained, which can't cover a project-relative path |
| `WebFetch` | yes — §D's own capability check names it explicitly: "confirm a URL-fetching tool (`WebFetch`) is available in this session" | §D.1 |
| `Bash(find *)` | no — no subflow step in `hb-ticket-discuss.md`/`load-ticket-subflow.md` invokes shell `find`; glob resolution in §B is tool-agnostic | grepped `load-ticket-subflow.md`, `ticket-loop-subflow.md`, `hb-ticket-discuss.md` for `find`/`Bash` — no hits |

Restored `Read` and `WebFetch` to `allowed-tools` (matching the plain-`Read` grants already used by sibling skills `hb-status`, `hb-task-plan`, `hb-task-step-plan` for the same class of arbitrary-file-read need). Left `Bash(find *)` dropped — no evidence it's used by this step's subflows, and re-adding it isn't backed by anything more than the deleted comment's original inclusion. Without `Read`/`WebFetch` pre-approved, every file/web Load would still technically work but would hit a permission prompt on first use of each tool per session — not a silent break, but unnecessary friction for a capability the subflow assumes is already available. No build/tests in this repo (markdown-only skill definitions); verified by re-reading the subflow contract only.

---

### STEP-2-REVIEW-2: Drop `Read`/`WebFetch` from `allowed-tools` — bracketed re-request overriding STEP-2-REVIEW-1

- **file(s):** `skills/hb-ticket-discuss.md` (`allowed-tools` frontmatter, `Read`/`WebFetch` lines bracketed by the `TODO REVIEW` range)
- Reviewer re-opens the concern STEP-2-REVIEW-1 addressed by restoring `Read`/`WebFetch`: these are overly broad permissions and should be dropped — the agent harness should not be allowed to read or web-fetch *any* resource without an explicit per-use prompt. The comment explicitly notes that any tool not listed in `allowed-tools` is still available but will simply prompt the user on first use, so dropping them here will not block the Load ticket action's file/web sources — it only removes the blanket pre-approval.
- **source:** `TODO REVIEW` in commit `c449b95d9f103e8ae58f1823bc7b652dd657bdb4` — delete comment from source file after addressing

---

<!-- README-1:

Example of a filled-in review item (for reference only — do not edit):

### STEP-10-REVIEW-99: Short title of concern

- **file(s):** `path/to/file.py` (symbol or function name the concern touches)
- The concern or suggestion in the reviewer's terms: the smell, duplication, missing case, or proposed alternative.

-->

<!-- README-2:

Review note ids are NOT REQUIRED; they will be filled in by /hb-task-step-review-address

For example, if you defined a review item as follows:

### main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

Then /hb-task-step-review-address will normalize it as follows:

### STEP-7-REVIREW-13: main.py looks bad

- the file `path/to/main.py` looks ugly; fix it

-->
