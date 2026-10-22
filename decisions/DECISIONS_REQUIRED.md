# InferWeave Architecture Decisions

Pi and implementation agents MUST treat resolved decisions as binding.

## D-001 Backend language — RESOLVED
All production backend, control-plane, routing, node, relay, local-proxy, telemetry and benchmark services use **Rust** unless a future ADR explicitly changes this.

**Amended 2026-09-22 — conformant site gateways.** A *site gateway* may be
implemented in another language provided it passes the language-neutral
conformance suite in `specs/42_SITE_GATEWAY_CONFORMANCE.md`. New services remain
Rust. The `metabolomics-us/inferweave-gateway` Go site gateway is such a gateway
and stays Go.

Why: spec 42 defines a language-neutral contract precisely so that "Rust and Go
gateway implementations are interchangeable and chainable". Read absolutely,
this decision contradicted spec 42 on its own terms — a language-neutral
conformance contract only earns its complexity if a non-Rust gateway is expected
to exist.

Python is allowed for offline/model-ecosystem evaluation tooling only when necessary.

## D-002 Web stack — RESOLVED
All browser-facing surfaces use **Next.js + TypeScript**:
- public dashboard;
- authenticated portal;
- GPU/benchmark/contribution explorer;
- CI/build history;
- Workbench;
- operator/admin UI.

**Narrow existing-system exception, amended 2026-10-12.** The existing
`metabolomics-us/inferweave-gateway` Go site gateway may extend its current light-theme embedded
operator UI for the runtime-family views required by the universal-runtime migration. This is an
operator surface of the D-001 conformant production site gateway, not authority to create another
general browser application or to use Go templates for new InferWeave web products. New dashboard,
portal, explorer, Workbench and standalone administration surfaces remain Next.js + TypeScript.

**Alias administration extension, amended 2026-10-12.** The same existing embedded Go
operator UI may implement spec 54 alias administration, candidate/routing explanations, simulation,
federation alias views and existing model/GPU crosslinks. Rust remains the only alias persistence,
resolution and admission authority. This exception does not authorize a standalone Go web product
or Go scheduling, discovery or backend integrations. See
`decisions/2026-10-12-dynamic-alias-authority.md`.

**Model-intelligence extension, amended 2026-10-12.** The same existing embedded
operator UI may add spec 58 analytics within existing pages and optional shared
system/light/dark parity while preserving current workflows and default styling.
Rust remains the metric, accounting, evaluation, capacity and recommendation
owner; Go adapts authorized reads and TypeScript presents them. No replacement
or second frontend, standalone Go browser product, or production gate approval
is implied. See `decisions/2026-10-12-model-intelligence-ui-cohesion.md`.

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
Every inference prompt/request payload is offered to the shared encrypted prompt
ledger, including requests later accepted, rejected, failed, cancelled,
capacity-blocked, policy-blocked or preempted. Ordinary gateway admission is not
conditional on storage acknowledgement: it uses the bounded asynchronous
recording contract in
`decisions/2026-09-28-buffered-gateway-recording.md`. Explicit durable-ingest
callers remain fail-closed and receive proof of committed submission.

Requirements:
- exact submitted content retained for records accepted by a durable sink;
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

**Scope, amended 2026-09-22.** "Existing repository contents" means the
**archived** `InferWeave/inferweave-*` prototypes this decision was resolved
alongside: `inferweave-chain`, `-client`, `-dashboard`, `-deploy`, `-docs`,
`-node`, `-protocol` and `-workbench`.

It does **not** cover production systems, which migrate under their own
specifications rather than being discarded:

- the `metabolomics-us/inferweave-gateway` Go site gateway (see D-001);
- the `metabolomics-us/inferweave-slurm` scheduler plant (see D-010);
- this monorepo, `InferWeave/inferweave`, itself.

Why: read without a scope, this decision contradicted spec 42 (a conformance
contract for a gateway that would not exist), D-010 (Slurm support for a plant
that would be discarded), and ADR 0002 in the monorepo ("the Go gateway is
kept as the site gateway, not retired"). All three assume the production
systems persist.

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
Recorded prompt bytes are accessed through a backend-independent PromptStore
abstraction so large deployments can tier encrypted content into object
storage. Gateway buffering and admission semantics are defined by D-006;
explicit durable-ingest callers still require committed storage.


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

## D-007 Token-free proof enrollment — RESOLVED

Node enrollment uses proof of protocol possession and model execution rather than an
operator-issued bootstrap token. The gateway issues a renewable role credential automatically
once proof succeeds; there is no operator approval step.

A challenge grants eligibility to exactly the signed role, model, artifact, runtime,
quantization, feature set, context class and measured resource claim challenged.

Rationale: a shared bootstrap token makes the token the credential, so every holder is
equivalent regardless of capability. Proof binds the credential to measured capability, and
makes a published context ceiling something a node proves rather than asserts.

Source: design recovered from the archived `InferWeave/inferweave-node` repository and
rewritten into this architecture under the clean-slate constraint. Adopted by owner direction
on 2026-09-03.

## D-024 Dispatcher is a first-class federated role — RESOLVED
A **dispatcher** is a new role: the component that turns demand into running capacity —
acquiring resources, fetching and staging model artifacts, and loading them. It is not a
router and never selects the node a request runs on.

- A gateway may have **zero, one or many** dispatchers, each with different capabilities
  (workstation GPUs, Slurm allocations, large multi-GPU nodes, different storage and runtimes).
- Dispatchers advertise **summarised** provisioning capability through gateway federation; the
  federation does not require a global dispatcher and must work with none.
- A dispatcher is **never in the successful inference data path**. It is consulted when a model is
  not READY anywhere, and is out of the picture once it is.
- Provisioning is deduplicated federation-wide: concurrent requests for the same model at the same
  placement attach to one logical operation rather than starting several.

This is distinct from, and complementary to, the inter-gateway capacity grants in
`specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md`: spec 41 **negotiates** capacity between gateways; a
dispatcher is what **realises** it.

Adopted by owner direction on 2026-09-22.

## D-025 Federation transport: HTTP/2 over established, multiplexed connections — RESOLVED
Gateway-to-gateway and relay-to-gateway traffic uses **HTTP/2 over TLS** by default.

- Connections are **established once and held**. Requests are multiplexed as streams over the
  standing connection; a request never opens its own connection.
- **No connection per request, and no connection per model.** One warm connection per peer is the
  target, with a small configurable ceiling rather than a brittle one-socket invariant.
- On failure: degrade, re-resolve, reconnect with bounded exponential backoff and jitter — and
  prefer reusing a live connection over establishing a new one.
- **HTTP/3 / QUIC is not the default.** It may be benchmarked behind a transport abstraction and
  adopted by a later decision on measured evidence. The QUIC reference in
  `specs/08_CONNECTIVITY_DATA_PLANE.md` concerns NAT-traversal rendezvous, not federation transport.

**Why this is an operational requirement, not a preference.** The site's IT operators flagged
InferWeave's connection behaviour. Connection churn is visible to the institution's network —
firewall and connection-tracking state, TLS handshake volume, ephemeral port pressure — in a way
per-request latency is not. Reuse is therefore required behaviour, and a regression in connection
count is a defect even when latency is unaffected.

Evidence it is achievable here: the relay (`crates/iw-relay-http`, merged in InferWeave/inferweave#524)
already measures 60 requests multiplexed over roughly one connection
(`tests/h2c.rs::http2_multiplexes_many_requests_over_one_connection`).

Adopted by owner direction on 2026-09-22.

## Scoped D-001/D-002 clarification — observability, 2026-10-20

The [observability capacity ADR](2026-10-20-observability-capacity.md) permits
bounded persistence of the existing Go site's own edge observations while Rust
retains global metric/warehouse/capacity authority. New public GPU profiles use
the existing Next.js application; existing embedded Go operator analytics retain
the prior exception. Deployment authorization is conditional on proof, not a
claim that production or hardware gates passed.
