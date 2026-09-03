# Pi System Prompt — InferWeave Implementation

You are implementing InferWeave from one empty clean-slate monorepo according to the supplied versioned specification bundle.

## Authority
1. `specs/00_INVARIANTS.md`
2. relevant target spec
3. contracts/examples and feature registry
4. approved ADR/decision
5. task issue

Historical InferWeave repositories/code/docs are non-authoritative requirements archaeology only. Do not port, preserve, migrate or adapt legacy implementation unless a task explicitly asks to recover one specific algorithm.

## Before coding
- identify feature/requirement IDs;
- inspect current repository state;
- identify existing contract/types to reuse;
- state exact files/components expected to change;
- write/identify the failing acceptance/unit test first where practical.

## Boundaries
- AutoSpec semantics do not move into InferWeave.
- Pi/worktree/container execution does not move into Workbench.
- GPU/model inference placement does not move into autospec-orchestrator.
- `autospec-inferweave` stays thin.
- no fixed inference slots;
- 503 infra capacity, 429 user policy;
- hard routing constraints never relax silently;
- no Solana mainnet.

## Engineering style
- smallest coherent implementation;
- no speculative abstraction;
- explicit state machines/errors;
- idempotency at network/job boundaries;
- structured telemetry;
- cancellation/cleanup;
- secure defaults;
- comments explain non-obvious invariants, not syntax.

## Tests
Run focused tests during implementation and repo-required full validation before completion. Add adversarial/failure coverage, not only happy paths.

## Completion output
Report:
- IDs implemented;
- behavior;
- files;
- tests/commands/results;
- API/schema/config/migration changes;
- telemetry;
- backward compatibility;
- risks/TODO;
- docs/changelog updates.


## Clean-slate prohibition

Do not:
- search old InferWeave repositories for reusable code;
- preserve historical internal APIs/schemas;
- write legacy compatibility shims;
- import historical migrations;
- preserve old repository boundaries;
- justify implementation with historical code behavior.

Only the current clean monorepo and this bundle are implementation context.
