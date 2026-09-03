# Canonical Pi Task Execution Protocol

## Input

The orchestrator selects exactly one task from `contracts/canonical-task-graph.json`.

It constructs a context pack using that task's:
- ID;
- dependencies;
- features;
- context class;
- specs;
- current relevant source/tests.

## Session sequence

### 1. PLAN
Produce:
- requirement interpretation;
- current-code impact;
- exact files/interfaces;
- test plan;
- risks;
- no implementation yet if planning role is separate.

For simple C50/C55 tasks, implementer may create a short internal plan before work.

### 2. IMPLEMENT
Implement only the task outcome.

Do not:
- pull in later-phase work;
- redesign unrelated contracts;
- preserve historical InferWeave behavior;
- bypass tests to make progress.

### 3. TEST
Run focused tests first, then required integration/property/failure tests.

Attach concise evidence:
- command;
- result;
- important metrics;
- failure reproduction if unresolved.

### 4. INDEPENDENT REVIEW
Reviewer gets:
- task card;
- relevant specs/contracts;
- diff;
- tests/evidence;
- only necessary surrounding source.

Reviewer checks:
- correctness;
- requirement coverage;
- security/privacy;
- failure behavior;
- observability;
- unnecessary scope;
- test quality.

### 5. REPAIR
Repairs become a bounded follow-up session if substantial.

### 6. COMPLETE
Completion record includes:
- task ID;
- feature IDs;
- files changed;
- tests;
- review result;
- ADR/spec/contract updates;
- known follow-ups.

## Parallelism

Safe parallel work must:
- have all dependencies satisfied;
- not mutate the same canonical schema/public interface;
- use separate worktrees;
- merge through CI and independent review.

Contract-owner tasks serialize dependent implementation until merged.

## Phase gates

When a gate task begins, stop starting new tasks in the next phase until gate defects are resolved.
