# Canonical Phase Gates

No task from the next phase should merge before the current phase gate passes, except isolated research spikes that produce no production dependency.

## Gate 0 — Bootstrap foundation
Must prove:
- clean monorepo builds;
- schemas generate reproducibly;
- `inferweave doctor/probe --json` works read-only;
- `init plan` is explicit;
- dev stack boots idempotently;
- secret/redaction policy passes;
- persistent roles have Docker Compose plans and Slurm role has Apptainer-only plan.

Gate task: `P0-T12`.

## Gate 1 — Working direct GPU weave
Must prove:
- every submitted prompt durable;
- two heterogeneous GPU nodes;
- full fingerprints/live telemetry;
- dynamic seat/context/KV admission;
- hard filtering + best-fit + sticky sessions;
- direct proxy↔node stream;
- relay fallback;
- 503/429 semantics;
- request telemetry correlation;
- GPU watchdog detects resets/OOM/restart loops and bounded rescue/profile rollback passes;
- live dashboard;
- gateway sees no normal response payload bytes.

Gate tasks: `P1-T24`, `P1-T25`.

## Gate 2 — Benchmark-driven private alpha
Must prove:
- reproducible benchmark warehouse;
- Pi/AutoSpec real-workflow quality benchmark;
- evidence-based recommendations/Pareto frontier;
- requalification;
- owner always wins;
- FairShare anti-gaming;
- thin AutoSpec integration;
- resumable benchmark DAG;
- 10K churn simulation.

Gate task: `P2-T22`.

## Gate 3 — Deployable HPC/Slurm platform
Must prove:
- persistent site connector;
- content-addressed cache;
- Slurm allocation worker;
- stable GPU history across reservations;
- gateway deployment assignments;
- deadline drain/preemption;
- AI-first init gateway/node/edge/site;
- MCP diagnostics/actions with scopes;
- watchdog CLI/dashboard/MCP rescue is authorized/audited;
- prompt tiering;
- health quarantine/recovery;
- site/Slurm production E2E.

Gate task: `P3-T22`.

## Gate 4 — Workbench and capability platform
Must prove:
- durable jobs/artifacts;
- Workbench persistence/fork/files;
- tool/RAG/LSP capability boundaries;
- CI/Pi review history;
- image generation direct data path;
- deterministic annotation QA.

Gate task: `P4-T14`.

## Gate 5 — Federated production readiness
Must prove:
- multi-gateway HA;
- regional sharding/relays;
- federation no-cycle/dedup;
- verification bands;
- large scale simulation;
- security/privacy review;
- long soak;
- complete requirement/acceptance evidence.

Gate tasks: `P5-T09`, `P5-T10`.

## Deferred gate
Solana/settlement has no active gate and must not be scheduled unless explicitly reopened.
