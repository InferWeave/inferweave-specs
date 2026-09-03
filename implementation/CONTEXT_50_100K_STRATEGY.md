# Canonical Context Strategy — 50K to 100K

This project is optimized for agents with a practical context envelope of **50K–100K tokens**.

The objective is not to fill the context window. The objective is to give the model enough exact local truth while preserving reasoning/edit/test/repair capacity.

## Context classes

### C50 — bounded implementation
Target total supplied context: **45K–55K**.

Use for:
- one crate/module;
- schemas;
- CLI commands;
- isolated storage/API features.

Suggested pack:
- 5–8K stable system/invariants/task;
- 5–10K target specs/contracts;
- 20–28K source/tests;
- 3–5K current errors/logs;
- leave substantial generation/reasoning headroom.

### C55/C60/C65/C70 — normal implementation
Target supplied context: **50K–70K**.

Use for most tasks.

Never include the entire repository. Supply:
- stable Pi implementation prompt;
- invariants;
- the exact canonical task card;
- 1–4 target specifications;
- exact current interfaces/types;
- 5–15 relevant source/test files;
- focused failing test output;
- recent decisions only if directly relevant.

### C75/C80/C85 — cross-component integration
Target supplied context: **65K–82K**.

Use for:
- gateway↔node↔proxy changes;
- installer + service integration;
- Slurm/site/cache;
- recommendation engine;
- Workbench boundaries.

Before using this class, generate a compact repository/symbol map and include interfaces instead of unrelated implementation.

### C90/C95/C100 — review, E2E, architecture verification
Target supplied context: **80K–100K maximum**.

Use for:
- phase gates;
- independent review;
- multi-component E2E;
- spec conformance;
- architecture/security review.

These tasks should primarily inspect/test/review. If they discover substantial implementation work, create smaller repair tasks instead of editing the entire system in one 100K session.

## Output headroom rule

For a nominal 100K model context, prefer **≤70K input** for implementation sessions so there is room for:
- reasoning;
- generated patches;
- tool outputs;
- compiler/test failures;
- one or two repair iterations.

For review tasks, up to ~85–90K input can be acceptable when expected output/patch volume is small.

## Stable prefix

Keep these stable and first whenever possible:
1. `pi/PI_IMPLEMENTATION_SYSTEM_PROMPT.md`
2. `specs/00_INVARIANTS.md`
3. current task card
4. canonical domain contracts required by the task

This increases prefix-cache reuse.

## Context inclusion priority

1. Exact current source/API definitions.
2. Exact failing tests/errors.
3. Target spec sections.
4. Direct dependencies/callers.
5. Recent relevant ADRs.
6. Historical explanation only if necessary.

## Never include by default

- all 35 specs;
- full Git history;
- previous implementation attempts;
- generated dependency trees;
- giant build logs;
- unrelated dashboard/backend code;
- historical InferWeave repos;
- Solana specs during active implementation.

## Context refresh

At task start:
- read current interfaces from repository;
- do not rely on interface copies from a previous task prompt.

At repair:
- replace old logs with latest failing output.

At phase review:
- use summaries/manifests plus selectively opened files, not a raw whole-repo dump.

## Splitting rule

Split a task if any two are true:
- >15 relevant source files must be modified;
- >3 architectural crates/services need new public APIs;
- task requires >4 major specifications;
- test matrix cannot be stated as one coherent outcome;
- expected patch is >2,000–3,000 LOC;
- model repeatedly loses requirement details.

## Merge rule

A task is not complete until:
- focused tests pass;
- required integration/failure/property tests pass;
- feature/requirement IDs are referenced in commit/PR metadata;
- docs/contracts are updated when behavior changed;
- no adjacent future feature was opportunistically implemented.

## Recommended agent separation

For each substantial task:
- planner/spec interpreter: independent session/model when useful;
- implementer: 50–80K targeted context;
- test/reviewer: independent 70–100K targeted context;
- phase gate: independent architecture/spec verification.

The same session should not be both primary implementer and final independent reviewer.
