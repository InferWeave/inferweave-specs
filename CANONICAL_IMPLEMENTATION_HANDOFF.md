# Canonical Implementation Handoff

Give this repository/spec bundle to AutoSpec/Pi and instruct it:

1. Read `AGENTS.md` and `START_HERE.md`.
2. Treat `contracts/canonical-task-graph.json` as the machine-readable execution DAG.
3. Start at `P0-T01`.
4. Load only the individual task card under `tasks/`.
5. Build context according to `implementation/CONTEXT_50_100K_STRATEGY.md`.
6. Do not begin a later phase until the current `implementation/PHASE_GATES.md` gate passes.
7. Use separate implementation and independent review sessions.
8. Never use historical InferWeave repository code as implementation context.
9. Do not implement Solana unless the owner explicitly reopens the deferred task.

## Main authoritative files

- `START_HERE.md`
- `decisions/DECISIONS_REQUIRED.md`
- `specs/00_INVARIANTS.md`
- `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
- `contracts/canonical-task-graph.json`
- `implementation/PHASE_GATES.md`
- `implementation/CONTEXT_50_100K_STRATEGY.md`
- `implementation/FEATURE_TASK_COVERAGE.md`
- `implementation/SPEC_TASK_COVERAGE.md`
- `pi/CANONICAL_TASK_EXECUTION.md`
- `pi/CONTEXT_PACK_CHECKLIST.md`

## Size strategy

Routine implementation: ~50–70K selected input context.

Cross-component integration: ~65–82K.

Independent reviews/gates: ~80–100K.

Do not compensate for uncertainty by loading the whole repository or all specifications.


## Deployment invariant
Use Docker Compose for persistent roles and Apptainer for Slurm workers.

## GPU watchdog
Do not mark the first GPU weave complete until watchdog detection, bounded rescue and automatic known-good rollback pass.
