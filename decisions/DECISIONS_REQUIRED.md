# InferWeave Architecture Decisions

Pi and implementation agents MUST treat resolved decisions as binding.

## D-001 Backend language — RESOLVED
All production backend, control-plane, routing, node, relay, local-proxy, telemetry and benchmark services use **Rust** unless a future ADR explicitly changes this.

Python is allowed for offline/model-ecosystem evaluation tooling only when necessary.

## D-002 Web stack — RESOLVED
All browser-facing surfaces use **Next.js + TypeScript**:
- public dashboard;
- authenticated portal;
- GPU/benchmark/contribution explorer;
- CI/build history;
- Workbench;
- operator/admin UI.

## D-003 Owner priority — RESOLVED
The physical owner/provider of a GPU always has priority over shared/network workloads on that GPU.

When owner demand appears:
- stop new shared admissions;
- reclaim borrowed owner-reserved capacity;
- gracefully drain interruptible shared sessions when possible;
- preempt interruptible work when needed to restore owner service;
- record reclaim/preemption telemetry.

Public workload hints cannot impersonate owner priority.

## D-004 Solana timing — RESOLVED
Do not implement Solana integration until there is a working deployed GPU weave with:
- direct-first routing;
- prompt persistence;
- full GPU telemetry;
- stable deployment qualification;
- global benchmark/contribution storage;
- real routing/admission/FairShare stability.

After that milestone, Solana remains a separate explicit future decision.

## D-005 Direct-first data plane — RESOLVED
Inference traffic is routed as directly as possible.

Normal path:
1. client/local proxy ↔ selected node directly;
2. nearest regional relay if direct traversal fails;
3. gateway relay only as last-resort compatibility/emergency fallback.

The gateway is the control authority, not the normal inference-byte proxy.

## D-006 Shared prompt ledger — RESOLVED
Every **submitted** inference prompt/request payload is durably stored in a shared database, including requests later accepted, rejected, failed, cancelled, capacity-blocked, policy-blocked or preempted.

Requirements:
- exact submitted content retained;
- encrypted at rest;
- idempotent durable ingest;
- linked to tenant/user/API key/session/request/route/deployment/node/GPU;
- strict read authorization;
- every privileged prompt-content read audited;
- prompt bodies excluded from public snapshots, metrics labels and contribution receipts.

Direct routing must not require response bytes to pass through the gateway.

## D-007 Global GPU telemetry/benchmarks — RESOLVED
Every GPU in the cluster publishes a complete hardware/software/runtime/model/configuration fingerprint plus live telemetry where supported.

This includes:
- hardware, VRAM, topology, PCIe/interconnect;
- driver/firmware;
- ROCm/CUDA/Vulkan;
- llama.cpp/vLLM/AITER/future runtime versions;
- container/image digest;
- model/tokenizer revision;
- quantization/precision/KV precision;
- context, attention, batching, TP/PP, MTP/speculative settings;
- benchmark dataset/suite versions;
- temperature, hotspot, power, clocks, utilization, VRAM, throttling, errors/resets;
- request-level TTFT, prefill, decode, aggregate throughput, cache behavior and energy/resource facts.

These feed global benchmarks and contribution accounting.

## D-008 Repository topology — RESOLVED
InferWeave is one **clean-slate monorepo**:

```text
InferWeave/inferweave
```

The monorepo owns:
- Rust gateway/control plane;
- Rust node agent;
- Rust relay/local proxy;
- routing/capacity/FairShare;
- prompt ledger;
- telemetry/benchmark warehouse;
- deployment/tuning services;
- jobs/artifacts;
- RAG/LSP/MCP/image capabilities;
- Next.js public dashboard/portal/Workbench;
- AutoSpec/Pi InferWeave client integration;
- schemas/generated bindings;
- integration/E2E/chaos tests.

Separate historical repositories are not architecture boundaries.

## D-009 Existing code — RESOLVED
All existing InferWeave repository contents are discarded as implementation constraints.

Agents MUST NOT:
- port historical code simply because it exists;
- preserve old internal APIs/schemas/database migrations;
- preserve old repo boundaries;
- build migration adapters for historical prototypes;
- retain deprecated slot scheduling;
- audit old repos for reusable implementation unless explicitly asked to recover one specific algorithm.

Historical conversations/specifications are requirements archaeology only.

The new monorepo starts from an empty implementation baseline.


## D-010 External Scheduler / Slurm — RESOLVED
InferWeave supports ephemeral scheduler-owned GPU resources through a generic scheduler adapter, with Slurm first.

Slurm workers:
- exist only inside active allocations;
- connect outbound to the gateway/control plane;
- register stable host/GPU identity plus temporary allocation/worker identity;
- rediscover current hardware/software/cache state every start;
- request desired deployment assignments from the gateway;
- serve/benchmark only until their reservation is reclaimed/expires;
- drain and disconnect cleanly.

Stable resource performance history survives across many allocations.

## D-011 Model Recommendation Engine — RESOLVED
Global benchmarking must produce workload-specific recommended model/runtime/deployment profiles for each hardware/resource class, using measured evidence, real Pi/AutoSpec workflow replay, exact fingerprints and explicit predicted-vs-measured confidence.


## D-012 Persistent site connector — RESOLVED
Slurm/HPC sites may run a persistent InferWeave site connector that survives ephemeral GPU allocations and owns stable cluster integration, scheduler mapping, site cache coordination, worker credential bootstrap and preferred site relay functionality.

## D-013 Zero-friction bootstrap — RESOLVED
A single Rust `inferweave` CLI is the canonical install/init/doctor/verify interface for gateway, node, edge, site connector, proxy, Slurm worker and development stacks. Normal setup is containerized, idempotent and AI-automation friendly with versioned `--json` output.

## D-014 MCP — RESOLVED
InferWeave provides authenticated read-first MCP servers for cluster and local diagnostics, benchmarks, routing, resources and scoped operations. MCP reuses canonical InferWeave APIs/types and never provides unrestricted shell/SQL/filesystem access.

## D-015 Artifact caching — RESOLVED
Model/runtime artifacts are immutable/content-addressed and use hierarchical host/site/regional/upstream caches. Gateway/control plane assigns artifacts but is not the normal model-byte path.

## D-016 Resource lifecycle intelligence — RESOLVED
Workload contracts, resource lifecycle events, degradation/quarantine, demand forecasting/pre-staging and resumable benchmark tasks are first-class control-plane capabilities.

## D-017 Prompt storage abstraction — RESOLVED
Every submitted prompt remains durably stored, but physical prompt bytes are accessed through a backend-independent PromptStore abstraction so large deployments can tier encrypted content into object storage.


## D-018 Container deployment substrate — RESOLVED
Persistent InferWeave roles use Docker Engine + Docker Compose. Slurm allocation workers use Apptainer. Production model/runtime services are not deployed as unmanaged bare-host processes. Adding Podman, Kubernetes or another production substrate requires a new ADR.

## D-019 GPU watchdog/rescue — RESOLVED
Every GPU-serving resource has bounded watchdog/rescue behavior. The node drains first, attempts least-destructive recovery, automatically rolls back known-bad profiles under defined triggers, preserves the previous image/model/environment/cache until rollback succeeds, and quarantines after bounded failed rescue. Slurm workers never seize host authority from Slurm.

## Still open

### D-020 Anonymous public playground
Enable `/play` in the first public release or later?

Current default: later, after authenticated deployment is stable.

### D-021 Node administration
Keep authoritative administration local-only or add secure remote administration later?

Current default: local-only authoritative node administration.

### D-022 API surfaces
Expose both `/v1` and `/api/v1` from day one?

Current default: yes.

### D-023 Authentication
Start with API keys and add OIDC before public multi-user launch?

Current default: yes.

Changing a resolved decision requires an ADR.

## D-006 Status of `autospec-inferweave` — OPEN

Invariant 27 states that `autospec-inferweave` remains a thin integration client/operator
surface. That is currently false.

The `InferWeave/inferweave-*` implementation repositories were archived on 2026-09-03, and
`autospec-inferweave` is now the only running inference stack. It holds the only working
implementations of the deployment context ceiling, capability persistence and reservation
liveness behaviours specified in `specs/03`, `specs/04` and `specs/00`.

Required decision: is `autospec-inferweave` a temporary bridge whose behaviours are rewritten
into the target architecture under the clean-slate constraint, or the transitional production
plane these specifications must describe?

Until this resolves, invariant 27 describes the target state, not the current one. No task may
cite invariant 27 as authority for removing a capability that is currently serving production
traffic.
