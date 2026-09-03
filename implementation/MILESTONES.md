# Milestones

## M0 — Clean monorepo alive
The single Rust/Next.js monorepo builds/tests/lints and generated Rust/TypeScript contracts pass drift checks.

## M1 — One direct real request
Gateway authenticates/routes, client/local proxy connects directly to one node, prompt is persisted, response streams without gateway byte proxying.

## M2 — Correct two-node routing
Two heterogeneous nodes advertise exact fingerprints and detailed GPU telemetry. Model/context routing and session affinity work.

## M3 — Safe overload + owner priority
Dynamic context/KV capacity, leases, 503/429 semantics, cancellation and owner GPU reclaim/preemption work.

## M4 — Prompt + telemetry observability
Every accepted request links prompt → route → deployment → GPU → performance/resource/power facts. Next.js dashboard shows live GPU/model/capacity/request history.

## M5 — Global benchmark private alpha
Qualified profiles and global benchmark warehouse compare exact runtime/model/GPU configurations and contribution facts. FairShare/API keys/AutoSpec integration pass soak.

## M6 — Ephemeral Slurm capacity
A known Slurm host/GPU can connect under an allocation, rediscover its stable identity, receive a gateway deployment assignment, serve/benchmark, drain at reservation end, disconnect, and later reconnect under a new allocation while preserving performance history.

## M7 — Workbench/data plane maturity
Full Next.js Workbench, durable jobs/artifacts, direct/relay reliability and local proxy optimization.

## M8 — Capability network
RAG/LSP/MCP/vision/image work through same deployment/telemetry/prompt-ledger model.

## M9 — Regional/federated network
Multiple gateways/regions and sharded presence/telemetry operate at scale.

## Deferred — Development settlement experiments
Not a milestone until the working deployed GPU weave exists and the owner explicitly reopens Solana/ASPEC work.
