# InferWeave Specs

`InferWeave/inferweave-specs` is the canonical specification, architecture-decision, implementation-order and agent-collaboration repository for the clean-slate InferWeave platform.

It intentionally contains **specifications and implementation guidance, not the production InferWeave source code**.

The production implementation is expected to live in:

```text
InferWeave/inferweave
```

## What InferWeave is

InferWeave is a distributed heterogeneous GPU inference fabric with:
- direct-first client ↔ GPU-node data paths;
- gateway/control-plane routing and admission;
- stable GPU identity and lifetime performance history;
- Docker-based persistent deployments;
- Apptainer-based Slurm ephemeral workers;
- full GPU/runtime/model telemetry;
- bounded encrypted prompt recording that cannot block gateway admission, plus an explicit durable-ingest API;
- model qualification and workload-specific recommendation;
- owner-first GPU priority and FairShare;
- GPU watchdogs, rescue and automatic rollback;
- site connectors, artifact caches and edge relays;
- Next.js dashboard/portal/Workbench;
- AI-first install/init CLI;
- MCP diagnostics and operations;
- RAG/LSP/tools/images;
- multi-region/federation scale.

## Clean-slate rule

Historical InferWeave code does not constrain the implementation.

Old code can be consulted only when recovering a deliberately preserved capability. It is not a migration target.

## Start here

Humans and agents should read in this order:

1. `AGENTS.md`
2. `START_HERE.md`
3. `decisions/DECISIONS_REQUIRED.md`
4. `specs/00_INVARIANTS.md`
5. `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`
6. `contracts/canonical-task-graph.json`
7. the selected task under `tasks/`

## Canonical implementation model

The active roadmap is split into bounded tasks optimized for approximately **50K–100K context**.

Routine implementation should usually load 50K–70K of selected context, not the entire repository.

See:
- `implementation/CONTEXT_50_100K_STRATEGY.md`
- `implementation/PHASE_GATES.md`
- `pi/CANONICAL_TASK_EXECUTION.md`

## Deployment rule

Persistent roles:

```text
Docker Engine + Docker Compose
```

Slurm allocation workers:

```text
Apptainer
```

See `specs/37_CONTAINER_DEPLOYMENT_STANDARD.md`.

## GPU rescue

GPU watchdog/rescue is required in the first working GPU weave.

See `specs/36_GPU_WATCHDOG_RESCUE.md`.

The watchdog detects resets, illegal-memory faults, OOM below admitted envelopes, backend restart loops, correctness corruption and profile drift; drains first; uses bounded recovery; automatically rolls back known-bad profiles; and quarantines after repeated failure.

## Contributing

This repository is designed for both human and AI-agent contributions.

Read:
- `CONTRIBUTING.md`
- `AGENTS.md`
- `agents/README.md`

Every material change must preserve feature/task/spec traceability.

## Repository layout

```text
specs/           canonical product/architecture specifications
decisions/       binding decisions and ADR template
implementation/  canonical implementation sequence, context policy and gates
tasks/           one bounded task card per canonical task
contracts/       machine-readable registries/task graph/examples
pi/              Pi/agent execution instructions
agents/          contributor role guides
docs/            operator/AI bootstrap documents
scripts/         spec-repository validation
.github/         contribution templates
```

## Solana

Solana/settlement work is intentionally deferred until the deployed GPU weave is stable and explicitly reopened.

## License

Released under the [MIT License](LICENSE).
