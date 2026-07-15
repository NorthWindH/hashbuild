# Background

`hb-sdk task create` currently only accepts the fully-qualified `author/hb-NNN-flavor` form. The task ticket for `northwind/hb-018-oneshot-tasks` requires a new prefix-based invocation form so oneshot (and other prefix-sequence-backed) tasks can be created without a hand-picked number, resolving against the prefix sequences built in step-0 (`prefix-sequences-sdk`).

This step wires `task create` to step-0's sequence-resolution primitive and adds the atomic-consume operation itself (deferred here from step-0, since `task create` is its only caller).

# Goal

Let `hb-sdk task create` accept `author/prefix` or bare `author` (with `--oneshot`) forms, atomically consuming an id from the resolved prefix sequence, with `--number`/`--flavor`/`--oneshot` overrides.

# Acceptance Criteria

1. `hb-sdk task create` accepts a new invocation form in addition to the existing fully-qualified `author/hb-NNN-flavor` form:
    1. `author/prefix` — resolves `prefix` against that author's sequences (falling back to a `repo`-scope sequence of the same name if no author-scope match exists), consumes the next id from it, and increments the sequence. No number or flavor may be embedded in this form.
    2. `author` alone (no `/prefix`) — allowed **only** when `--oneshot` is also passed; resolves to that author's default `oneshot` sequence.
2. Consuming the next id from a resolved sequence is atomic:
    1. concurrent `task create` invocations against the same sequence never hand out a duplicate id (verified via a concurrency test: N parallel `task create` calls against the same sequence yield N distinct task numbers)
    2. this builds on step-0's resolve primitive; the increment-and-return is implemented here since `task create` is the only caller.
3. `--number <n>`: supplies the task number explicitly instead of consuming one from the resolved sequence.
    1. Errors if the positional argument already embedded a number (i.e. the fully-qualified `author/hb-NNN-flavor` form was used).
    2. If omitted (and the prefix form was used), the SDK consumes the next id from the resolved prefix sequence; errors if the sequence doesn't exist.
4. `--flavor <slug>`: supplies the flavor slug explicitly.
    1. Errors if the positional argument already embedded a flavor (i.e. the fully-qualified form was used).
5. `--oneshot`: marks this as a oneshot-mode task creation at the SDK level.
    1. Defaults the resolved prefix to `oneshot` when no explicit prefix was given in the positional argument.
    2. This step only wires the SDK-level flag/resolution behavior — triggering the oneshot guided subflow at the skill level is step-4's concern, not this step's.
6. Existing fully-qualified `author/hb-NNN-flavor` invocations behave exactly as before (non-regression).
7. Tests cover: `author/prefix` resolution (author-scope and repo-scope fallback), bare `author` + `--oneshot`, `--number` override with each error case, `--flavor` override with its error case, `--oneshot` prefix defaulting, and the concurrency case in AC 2.1. Existing SDK test suites pass unchanged.

# Out of scope

- Defining/resolving/listing/dropping/updating prefix sequences themselves — step-0.
- The `hb-prefix-*` CLI skills — step-3.
- Triggering or implementing the oneshot guided subflow itself — steps 4 and 5.
