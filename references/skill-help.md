# Skill Help — Generic Handler

Invoked when user passes `help`, `--help`, or `-h` to any skill that references this file.

## Instructions

1. Read the calling skill's file.
2. Extract: skill name (frontmatter `name:`), `description:`, and the **Inputs** table.
3. Produce help output in this format:

````markdown
# <skill-name>

<description>

## Usage

```
<skill-name> <required-args> [optional-args]
```

## Arguments

| Parameter | Required | Description |
| --------- | -------- | ----------- |
| ...rows from Inputs table... |

## Examples

```
<skill-name> <minimal-example>
<skill-name> <full-example-with-all-args>  ← omit if no optional args
```
````

Rules:
- Derive the synopsis line from the Inputs table: required args first (no brackets), optional args in `[brackets]`.
- Use the Inputs table rows verbatim for the Arguments section — do not paraphrase.
- Generate one minimal example from required args only, and one with all args if optional args exist.
- Output as markdown: use fenced code blocks for synopsis and examples, a table for arguments.
- After printing, stop — do not execute the skill's normal steps.
