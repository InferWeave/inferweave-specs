# AGENTS.md — Rules for AI Agents Contributing to InferWeave Specs

This repository is the canonical architecture/specification source for InferWeave.

## Before changing anything

Read:
1. `README.md`
2. `START_HERE.md`
3. `decisions/DECISIONS_REQUIRED.md`
4. `specs/00_INVARIANTS.md`
5. the relevant specification(s)
6. `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
7. `implementation/FEATURE_TASK_COVERAGE.md`
8. `OPEN_GATES.md` — what is *not* approved

## Evidence rules

**Measured basis.** Any figure a change relies on is measured by its author against the
pinned commit and reproduced in the change. Do not quote a number from another document
without reproducing it; a number copied twice is a number nobody has checked.

**Honest capability disclosure.** Where a control is specified but unstaffed, unexercised or
unmeasured, record that in `OPEN_GATES.md` in the same change. A control recorded as existing
but unstaffed invites reliance that is not warranted, and is worse than one recorded as
absent. State it as unsatisfied — not partially satisfied, not satisfied in spirit, not
pending confirmation.

**When the specification was the defect.** If an incident traces to specification text rather
than to an implementation error, say so explicitly: what the text caused, and what a future
implementer following it literally would reintroduce. A correction that reads as a
clarification teaches nobody.

**Proof status.** Every required test is `proven` or `owed`. `proven` means a test exists,
runs, and fails if the control is removed. Never record `owed` work as `proven`.

## Operational feedback is a specification obligation

These specifications are maintained continuously, not written once.

Each of the following produces a specification change in the same change set that introduced
it:

- a production incident whose root cause is behaviour these specifications do not describe;
- a new capability, surface or contract;
- a measured value that contradicts a stated assumption;
- an implementation choice made because a specification was silent.

Record the operational evidence — the observed failure, the measurement, the incident — inside
the change. A specification that cannot be traced to why it says what it says decays into
folklore, and the next reader cannot tell a deliberate constraint from an accident.

When an incident and a specification disagree, the incident is the fact. Fix the
specification.

## Authority order

1. resolved decisions;
2. invariants;
3. canonical target specs;
4. machine-readable contracts;
5. canonical implementation sequence/task graph;
6. task cards;
7. explanatory/source notes.

Do not allow a lower level to contradict a higher level.

## Clean-slate constraint

Do not preserve historical InferWeave implementation merely because it existed.

Historical sources may recover a capability; rewrite it into the current architecture.

## Required deployment architecture

- persistent services/nodes: Docker Engine + Docker Compose;
- Slurm allocation workers: Apptainer;
- no Podman/Kubernetes/bare-host production deployment without ADR.

## Required GPU safety

Never remove or weaken:
- GPU watchdog;
- bounded rescue;
- drain-before-rescue;
- automatic rollback triggers;
- preserved known-good rollback artifacts;
- restart-loop protection;
- quarantine/recovery;
- Slurm scheduler authority.

## How to propose a spec change

A change that adds/removes/changes behavior must update as needed:
- relevant `specs/*.md`;
- `decisions/` if architectural;
- `contracts/feature-registry.json`;
- `contracts/canonical-task-graph.json`;
- `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`;
- affected `tasks/*.md`;
- feature/spec coverage files;
- acceptance tests/matrix.

Run:

```text
python3 scripts/validate_specs.py
```

before opening a PR.

## Scope

Do not bundle unrelated architecture changes.

One PR should have one coherent purpose.

## Agent contribution workflow

1. state the problem and feature IDs;
2. inspect current canonical sources;
3. propose minimal spec changes;
4. update traceability;
5. run validation;
6. summarize compatibility/implementation-order impact;
7. open PR for independent review.

## Review independence

An agent that authors a material architecture change should not be the only final reviewer.

## Context discipline

This repository is intentionally large. Do not dump the whole repository into a model context.

Use `implementation/CONTEXT_50_100K_STRATEGY.md`.

## Do not

- implement production InferWeave code here;
- change resolved architecture silently;
- add a new deployment substrate without ADR;
- schedule Solana;
- weaken privacy or prompt durability;
- make gateway the normal inference byte path;
- bypass owner priority;
- replace stable GPU identity with ephemeral worker identity;
- remove exact model/runtime fingerprints;
- turn MCP into arbitrary shell/SQL;
- create unbounded retries/watchdog loops.
