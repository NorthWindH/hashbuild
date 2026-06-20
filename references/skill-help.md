# Skill Help — Generic Handler

Invoked when user passes `help`, `--help`, or `-h` to any skill that references this file.

## Instructions

1. Read the calling skill's file.
2. Extract: skill name (frontmatter `name:`), `description:`, and the **Inputs** table.
3. Produce help output in this format:

```
Usage: <skill-name> <required-args> [optional-args]

<description>

Arguments:
  <arg-name>    <Required|Optional>   <description>
  ...

Examples:
  <skill-name> <minimal-example>
```

Rules:
- Derive the synopsis line from the Inputs table: required args first (no brackets), optional args in `[brackets]`.
- Use the Inputs table rows verbatim for the Arguments section — do not paraphrase.
- Generate one minimal example from required args only, and one with all args if optional args exist.
- Print plain text, no markdown rendering.
- After printing, stop — do not execute the skill's normal steps.
