# START HERE — InferWeave Clean-Slate Implementation

This ZIP contains the complete canonical specification and implementation order.

## Authoritative precedence

1. `AGENTS.md`
2. `decisions/DECISIONS_REQUIRED.md`
2. `specs/00_INVARIANTS.md`
3. target `specs/*.md`
4. canonical contracts/schema
5. `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
6. current task card
7. current monorepo code

Historical repositories are not authoritative.

## First implementation task

Start with:

```text
P0-T01 — Bootstrap clean Rust/Next.js monorepo
```

Then continue according to:

```text
implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md
```

Machine-readable DAG:

```text
contracts/canonical-task-graph.json
```

## Context size

Use:

```text
implementation/CONTEXT_50_100K_STRATEGY.md
```

Do **not** load the entire ZIP into every implementation session.

Routine implementation should usually receive ~50K–70K of selected context, leaving headroom for reasoning, code, tool output and repair.

## Gate discipline

Use:

```text
implementation/PHASE_GATES.md
```

Do not move to the next phase because code "mostly works." Pass the gate.

## Pi orchestration

Use:

```text
pi/PI_IMPLEMENTATION_SYSTEM_PROMPT.md
pi/CANONICAL_TASK_EXECUTION.md
pi/TASK_TEMPLATE.md
```

Each task should have independent review before completion where practical.

## Solana

Solana is deferred. Do not implement it during the active roadmap.


## Deployment
Persistent roles are Docker Compose. Slurm workers are Apptainer.

## GPU watchdog
`specs/36_GPU_WATCHDOG_RESCUE.md` is mandatory and enters during Phase 1.
