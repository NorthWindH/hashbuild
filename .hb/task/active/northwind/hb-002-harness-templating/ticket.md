# Background

**Prior state:** Skills are authored as static `.md` files in `skills/` with Claude Code-specific syntax baked in: `${CLAUDE_SKILL_DIR}` path references and `` !`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md` `` dynamic injection. The install script symlinks these source files directly into harness skill directories.

**The problem:** The syntax is Claude Code-only. OpenCode's skill runtime treats `${CLAUDE_SKILL_DIR}` as a literal string and passes `` !`cat ...` `` through to the LLM unchanged. Skills installed to OpenCode are broken. `allowed-tools` frontmatter (Claude Code permission scoping) has no equivalent in OpenCode and must be dropped for that harness.

**The motivating case:** `./install` targeting OpenCode installs source files verbatim, producing non-functional skills. All 10 skills are affected; reference files (e.g. `committing.md`) also contain `${CLAUDE_SKILL_DIR}` refs and need rendering.

**Chosen approach:** Treat source files as templates. At `./install` time, render harness-specific artifacts into `dist/`, then symlink the artifacts. `dist/` is gitignored and always rebuilt on install. Because rendering now happens at install time, `` !`cat ...` `` dynamic injection is no longer needed — file content is inlined by the renderer for all harnesses, removing the Claude Code-specific syntax from the output entirely.

# Acceptance Criteria

## A. Source template changes

1. `` !`cat ${CLAUDE_SKILL_DIR}/references/references-toc.md` `` occurrences in `skills/*.md` are replaced with a renderer-recognized include directive (e.g. a comment tag or dedicated syntax); the directive is the only change to source files in this task
2. All other source file content is unchanged

## B. Template rendering

3. A renderer (invoked by `./install`) produces artifacts in `dist/claude/` and `dist/opencode/` before any symlinking occurs
4. Include directives are resolved at render time for **all harnesses**: the target file's content is inlined into the artifact verbatim
5. Claude artifacts:
    1. Include directives are replaced with the inlined content (same observable result as the current `!`cat ...`` injection)
    2. `${CLAUDE_SKILL_DIR}` occurrences are passed through unchanged (Claude Code resolves them at runtime)
    3. `allowed-tools` frontmatter is preserved
6. OpenCode artifacts:
    1. Include directives are replaced with the inlined content
    2. All `${CLAUDE_SKILL_DIR}` occurrences are replaced with `${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}/skills/<skill-name>`, where `<skill-name>` is the stem of the source `.md` file
    3. The `allowed-tools` frontmatter line is removed (no equivalent in OpenCode)
    4. All other content is preserved verbatim

## C. Output layout

7. `dist/` is organized as:
    ```
    dist/
    ├── claude/
    │   └── skills/
    │       └── <skill-name>/
    │           ├── SKILL.md
    │           ├── references/     (rendered)
    │           └── scripts/        (unchanged; symlink or copy)
    └── opencode/
        └── skills/
            └── <skill-name>/
                ├── SKILL.md
                ├── references/     (rendered)
                └── scripts/        (unchanged; symlink or copy)
    ```
8. `dist/` is added to `.gitignore`

## D. Install / uninstall

9. `./install` generates `dist/` artifacts first, then symlinks `dist/<harness>/skills/<name>/` entries into the harness skill directories — replacing the current behavior of symlinking `skills/` source entries directly
10. `./install --uninstall` removes symlinks to `dist/` entries
11. Re-running `./install` is idempotent: artifacts are regenerated, existing correct symlinks are left in place, conflicting symlinks produce the same diagnostic they do today
12. `dist/` contents are always regenerated on `./install`, not cached across runs

## E. Constraints

13. The renderer uses Python stdlib only — no new pip dependencies
14. Existing tests pass
15. The renderer has at least one test asserting that a known `${CLAUDE_SKILL_DIR}` occurrence is absent from the OpenCode artifact for that skill, and present in the Claude artifact

# Out of scope

- Changes to skill or reference file content beyond replacing the `!`cat ...`` directives (AC 1)
- Changes to `hb-sdk`
- Adding new skills or reference files
- OpenCode command artifacts (`.opencode/commands/`) — skills only for this task
- Translating `allowed-tools` values to an OpenCode permission equivalent — the line is dropped, not translated
- Python version upgrade (3.10 stdlib is sufficient; upgrade only if a stdlib gap is found during implementation)
