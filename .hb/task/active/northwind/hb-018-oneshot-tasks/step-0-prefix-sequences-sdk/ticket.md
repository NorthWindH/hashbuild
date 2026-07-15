# Background

`northwind/hb-018-oneshot-tasks` needs SDK-managed, collision-safe numbering so oneshot tasks don't require a hand-picked `hb-NNN` number. This step builds the underlying primitive everything else in the task depends on: named "prefix sequences" that the SDK tracks and hands out integer ids from, atomically, safe under concurrent authors committing simultaneously.

- **Chosen approach** (from the task ticket): the SDK tracks named prefix sequences, each scoped to either one author or the whole repo. Every author automatically gets a default per-author sequence (prefix `oneshot`). Users can also define additional named sequences beyond the default.
- Rejected alternatives (random slug, timestamp, single global counter, author-stuttering prefix) are recorded in the task ticket's Background — this step does not need to re-litigate them, only implement the chosen design.

This step covers the SDK-level engine only — no CLI-facing skills yet (those are step-3) and no `task create` integration yet (step-2). Atomically **consuming** the next id from a sequence is only ever exercised through `task create` (step-2), so the atomic-consume implementation and its concurrency test are left to that step; this step only defines, resolves, lists, drops, and updates sequences.

# Goal

Give the SDK a way to define, resolve, list, drop, and update named prefix sequences, enforcing the collision rules between author- and repo-scoped sequences. Atomic id consumption is implemented in step-2, against these sequences.

# Acceptance Criteria

1. The SDK supports creating a named prefix sequence with:
    1. a prefix string
    2. a scope of either `author` (isolated to one author) or `repo` (shared across all authors)
    3. an explicit starting next-value (defaulting to `0` when not given)
2. The SDK supports resolving a named sequence by scope + name (or by author + prefix), returning its current next-value — this is the read path step-2's atomic consume will build on.
3. Every author automatically has a default sequence with prefix `oneshot`, scoped to that author, with no explicit setup required — resolving `<author>`'s `oneshot` sequence succeeds even if it was never explicitly created.
4. Collision rules are enforced when creating a new named sequence:
    1. **author-scope**: rejected if the same author already has another sequence (any scope) with the same prefix, or if a `repo`-scope sequence exists with that prefix.
    2. **repo-scope**: rejected if any other sequence, at either scope and for any author, already uses that prefix.
    3. each rejection surfaces a clear, actionable error identifying the conflicting sequence.
5. The SDK supports listing existing sequences with their scope, owning author (if any), prefix, and next-value — this is the primitive `hb-prefix-list` (step-3) will call.
    1. Listing accepts optional filters — `scope` (`author`/`repo`), `author` (implies `scope=author`; errors if combined with `scope=repo`), and `prefix` (exact match) — applied server-side so step-3's skill can hand these through verbatim rather than re-filtering client-side.
    2. Listing accepts an optional `long`/detail flag: when unset, entries carry only their name; when set, entries also carry scope, owning author, prefix, and next-value — this backs `hb-prefix-list`'s `--long` flag.
6. The SDK supports dropping and updating (next-value only) an existing sequence by scope + name — these are the primitives `hb-prefix-drop`/`hb-prefix-update` (step-3) will call.
7. Tests cover: fresh sequence creation, the default per-author `oneshot` sequence, each collision-rejection case in AC 4, drop/update round-trips, and each listing filter/detail combination in AC 5.1–5.2. Existing SDK test suites pass unchanged.

# Out of scope

- Atomically consuming/incrementing the next id from a sequence, and its concurrency test — step-2, since `task create` is the only caller.
- Any `hb-prefix-*` skill (thin CLI wrappers) — step-3.
- `hb-sdk task create`'s new prefix-based invocation form and `--oneshot`/`--number`/`--flavor` flags — step-2.
- The oneshot guided subflow itself — steps 4 and 5.
- Renaming or rescoping a prefix after creation (explicitly out of scope in the task ticket).
