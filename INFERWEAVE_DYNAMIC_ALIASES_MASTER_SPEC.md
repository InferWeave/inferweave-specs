# InferWeave Dynamic Model Aliases — Master Implementation Specification

**Version:** 1.0  
**Date:** 2026-10-12  
**Status:** Implementation handoff  
**Repositories:** `inferweave/inferweave-specs` (contracts), `inferweave/inferweave` (engine), `metabolomics-us/inferweave-gateway` (Go admin UI/edge relay)

> **Repository-verification note:** Live access to the three repository trees was unavailable during preparation. All agents MUST inventory the checked-out source first; paths and API examples below are proposed contracts rather than claims of existing implementation. Reuse existing components, contracts and migrations whenever compatible.

## 0. Mission / copy-paste execution prompt

Implement this specification end-to-end, using a supervising Codex agent and parallel Pi implementation agents where supported. First audit all three repositories, identify implemented functionality and drift, preserve working behavior, and publish an evidence-backed gap matrix. Track the canonical specification and contract changes in `inferweave/inferweave-specs`. Implement all domain logic in `inferweave/inferweave`; implement only administration, presentation, typed protocol consumption and transparent edge relay in `metabolomics-us/inferweave-gateway`. Do not introduce duplicate alias resolution, model inventories, schedulers, model-selection heuristics or transport-specific backend integrations in Go. Reuse current scheduler, rebalancer, federation, VRAM, runtime, metrics, admission and authentication subsystems. Write deterministic unit, property, conformance, integration, UI and end-to-end tests; execute them; fix failures; collect screenshots and traces; publish reproducible verification. Coordinate worktrees and shared contract changes, review, merge, remove worktrees, and clean build artifacts when finished. Where implementation differs from this proposal because of existing code, record the rationale, preserve semantics and update the canonical specification.

## 1. Goals

1. Give clients stable intent-oriented names that outlive individual checkpoints, runtimes and deployments.
2. Resolve aliases dynamically against *actual* current schedulable capacity, capabilities, policy and runtime state.
3. Support exact immutable model IDs, operator-managed aliases and capability-derived aliases with explicit, unambiguous precedence.
4. Allow clients including Pi, AIMS, Augur and OpenAI-compatible consumers to specify hard requirements and soft preferences without hardcoding the best model.
5. Integrate aliases with the existing Tern/router, admission and scheduling, per-GPU resource accounting, hot-loading, model rebalancer, federation and runtime families.
6. Advertise compact and truthful alias capability envelopes upstream while avoiding duplication of underlying GPUs/capacity.
7. Explain *why* a request selected a model, rejected others, queued, provisioned, failed over or could not be served.
8. Provide a polished alias administration and observability UI in the metabolomics Go gateway; **never** route using UI-side heuristics.
9. Introduce incrementally, preserving existing exact-model requests and existing protocol consumers.

### Non-goals

- No second router, solver, provisioning engine or scheduler in Go.
- No direct Go integration with Slurm, Kubernetes, Docker, worker registries or GPU discovery; these are InferWeave protocol producers/consumers behind Rust.
- No automatic relaxation of a required modality, context size, privacy level, tool-calling fidelity or data-residency constraint.
- No silent migration of a partially streamed response to another model.
- No unsolicited upstream control of downstream resources; federation remains downstream-owner controlled and opt-in.
- No new tunnels, credential forwarding, remote-code execution, or unbounded retry loops.
- No wholesale rewrite of existing InferWeave.

## 2. Ownership and system boundaries

| Concern | Canonical owner | Go gateway responsibility |
|---|---|---|
| Versioned types, behavior, compatibility and conformance | `inferweave/inferweave-specs` | Generated or shared typed client |
| Model/catalog discovery, runtime-class metadata | `inferweave/inferweave` | Read-only views and edit flows where authorized |
| Alias CRUD, validation, evaluation, versions, publication | `inferweave/inferweave` | Forms, preview, diff, approvals, audit viewer |
| Capability matching, ranking, fallback | `inferweave/inferweave` | Display authoritative evaluations/explanations |
| Capacity, admission, queueing, session affinity | `inferweave/inferweave` | Utilization/status visualizations |
| Demand, autoscaling, provisioning, VRAM placement | `inferweave/inferweave` | Desired-state controls and state timelines |
| Federation, demand/offer/lease accounting, trust | `inferweave/inferweave` | Topology, owner policy and provenance views |
| Request execution/streaming/cancellation | `inferweave/inferweave` | Lossless authorized upstream proxy/relay |
| Authentication at public edge, Cognito/OIDC integration | Existing edge integration plus canonical InferWeave authorization | Authenticate caller and forward trusted identity claims using validated mechanism |
| Audit source, metrics, event history | Canonical protocol events/core state | Display and optional non-authoritative analytics materialization |

**Single source of truth:** Rust owns persisted alias desired state, published versions and effective state. Go may cache read-only protocol snapshots for display, clearly labeled by age/revision, but cannot turn those into authoritative routing decisions.

## 3. Discovery-first implementation requirements

Before changing code, publish `docs/alias-implementation-gap-matrix.md` with:

- Existing protocol schema/versioning, catalog endpoints and capabilities.
- Existing exact model aliases, model ID parser and resolution precedence.
- Worker/runtime registries, health status, readiness and lifecycle generations.
- Tern or equivalent router, rankers, admission seats, queueing, retries and session affinity.
- Rebalancer, scheduler, VRAM accounting, warm pools, hot-loaded model lifecycle.
- Federation advertisement, offer, lease, loop protection, ownership and multi-parent de-duplication.
- Go gateway routing/proxy middleware, API clients, administration pages, stores, auth, telemetry.
- Existing tests and backward-compatibility behavior.
- Per requirement: `implemented`, `partial`, `missing`, `duplicated`, `conflicting`; exact files/symbols, baseline tests and planned changes.

Write characterization tests around current public behavior before refactoring. Consolidate existing duplicate mechanisms rather than extending them twice. Do not claim functionality implemented until source and tests confirm it.

## 4. Canonical domain model

### 4.1 Terms

- **Concrete model ID**: exact immutable/qualified identity for a checkpoint or published model artifact, including revision where needed; requests with exact IDs never silently substitute.
- **Deployment/RuntimeInstance**: a specific READY, healthy serving placement of a model, with runtime class, generation, reachable endpoint and currently admitted capacity.
- **Managed alias**: operator-defined stable name and revisioned policy/selection rule.
- **Dynamic alias**: named query of capabilities/constraints evaluated against the live model/instance catalog, optionally with pinned allowed families.
- **Alias envelope**: conservative downstream-advertised set of available capabilities and qualified capacity, not a promise of every capability combination.
- **Alias resolution**: side-effect-free eligibility/ranking analysis based on a particular catalog revision, subject to revalidation at admission.
- **Admission**: authoritative reservation of a concrete instance/seat/resources/lease by the owning gateway, potentially followed by provisioning.

### 4.2 Proposed Alias object (versioned contract)

```json
{
  "api_version": "inferweave/v1",
  "kind": "ModelAlias",
  "id": "coding-fast",
  "revision": 12,
  "status": "ACTIVE",
  "description": "Low-latency code generation with verified tool use",
  "visibility": "TENANT",
  "owner_scope": "tenant/example",
  "selection": {
    "type": "DYNAMIC",
    "families_allow": ["qwen", "deepseek"],
    "model_ids_allow": [],
    "model_ids_deny": [],
    "required": {
      "runtime_classes": ["chat"],
      "modalities": ["text"],
      "features": {"tool_calling": "verified"},
      "min_context_tokens": 32768
    },
    "preferred": {
      "latency": 0.4,
      "quality": 0.3,
      "availability": 0.2,
      "cost_efficiency": 0.1
    }
  },
  "execution": {
    "allow_cold_start": false,
    "allow_federation": true,
    "fallback_policy": "COMPATIBLE_ONLY",
    "max_admission_attempts": 3,
    "queue_deadline_ms": 15000
  },
  "metadata": {"tags": ["coding", "interactive"]}
}
```

Schema validates stable case-normalized IDs, allowed chars/lengths, tenant namespace, ownership, RBAC, limits, weight normalization, references and schema version. Sensitive tenant policy never leaks in upstream advertisements. Alias revisions are monotonic, immutable once published, and track actor, timestamp, reason, hash, approval and rollback source.

### 4.3 Candidate/model capabilities

Structured machine-readable fields, not scraped names:

- Model identity: ID, family, checkpoint/revision, variant/quantization, origin/trust, license/allowed tenants.
- Runtime class: `chat`, `completions`, `embeddings`, `rerank`, `speech_to_text`, `text_to_speech`, `prediction`, `system_one`, and extensible types registered in the runtime protocol.
- Input/output modalities: text, image, audio, video where truly implemented; output content types.
- Features: tools/function calling, JSON/schema-constrained output, streaming, logprobs, structured predictions, multilingual, FIM/coding, reasoning and tool-concurrency support where verified.
- Numeric limits: max total context, input/output tokens, image count/size, audio duration, batch size, embeddings dimension, prediction classes or scoring features as relevant.
- Compatibility/fidelity: per feature `native`, `translated`, `emulated` or `unsupported`; confidence `advertised`, `probed`, `verified`, `degraded`, `disabled` with verification timestamp, protocol/build version and provenance.
- Deployment: current READY generation, health, capacity/seats, queue, warm/cold state, startup ETA confidence, cache locality, topology, per-GPU memory weights/cache/KV usage/free memory, cost/throughput/latency if measured.
- Policy: tenant allowed, data residency/trust boundary, privacy, authorized origin, network reachability, upstream/federation sharing permissions, preemptibility.

`UNKNOWN` never means `VERIFIED`; stale/unverified hard-constraint evidence is conservatively ineligible unless the requesting policy explicitly permits the specified confidence.

## 5. Name resolution and safety semantics

1. **Explicit exact model** (`model_id` or canonical qualified exact identifier) resolves *only* that model revision. No substitution.
2. **Explicit alias reference** (`alias_id` or reserved `alias:` syntax) evaluates that alias only.
3. **Legacy unqualified `model` strings** preserve pre-existing behavior: exact named model first, then managed alias, then recognized dynamic alias. Reject conflicting ambiguous namespace collisions at alias creation; migration warnings for legacy conflicts.
4. Resolve alias indirection only if intentionally allowed in schema; detect cycles, set depth <= 4, return reason `ALIAS_CYCLE` or `ALIAS_DEPTH_EXCEEDED`. Prefer flattened eligibility at publication and prohibit recursive runtime resolution chains.
5. Request overrides may strengthen hard requirements, never weaken alias-owner policy, tenancy, license, federation and privacy rules. Requests may relax *their own* soft preferences explicitly.
6. A context minimum is hard. A smaller context model may be chosen only with an explicit, authorized relaxation by the client and clear response trace; default is fail/queue/provision.
7. A concrete model may have many deployment variants. Never conflate checkpoint ID with a single running instance.
8. Unknown alias produces actionable `ALIAS_NOT_FOUND`, not silent nearest-name matching.

## 6. Matching, ranking and dispatch algorithm

**Hot path must reuse the existing core router/admission state.** Conceptual stages:

1. Parse and authenticate requested name and required capabilities; normalize request metadata.
2. Resolve tenant-visible alias definition at a consistent revision; construct an immutable `ResolutionContext`.
3. Retrieve inventory snapshot plus federated eligible offers; prevent duplicate capacity advertisements from appearing as separate physical supply.
4. Hard-filter instances by runtime class, modality, verified feature fidelity, context, tool/output request needs, tenant policies, data residency/trust, routing reachability, READY/healthy/current lifecycle generation, sharing/local priority and cancellation state.
5. Classify candidates as `ready`, `busy/queueable`, `cold_start_possible`, `provisionable`, or `ineligible` with stable reason codes. **Do not count an unloadable model as READY capacity.**
6. Rank *eligible* candidates using requested weighted preferences, measured quality for workload where statistically defensible, expected latency including queue and cold starts, throughput, resource/cost efficiency, cache locality, reliability, current load, topology and session affinity.
7. Apply smallest-sufficient-resource bias within quality/capability thresholds; do not sacrifice user hard constraints or quality target for compactness.
8. Atomically request admission from selected owner using catalog revision, instance generation, idempotency key, deadline and scoped lease. Revalidate readiness and capacity at admission. Retry next eligible candidate if a *pre-stream* admission race occurs, within a strict attempt/time budget.
9. If none READY, use existing queue/rebalancer/provisioning flow only when alias and owner policies allow it. Communicate reason, estimated startup only when grounded, and optional alternatives; never create speculative jobs in a preview request.
10. Preserve sticky session/affinity when valid; migration only when compatible and explicitly allowed. For stateful requests that cannot safely migrate, fail clearly.
11. Once response bytes are streamed, never replay on a new backend unless the protocol explicitly supports resume with proven semantics. For tool calls, writes or nondeterministic operations, require idempotency-specific protection.
12. Release leases on completion, cancellation and timeout; record causal tracing and final resource accounting.

### 6.1 Ranking contract

- A versioned, deterministic `routing_policy_version` identifies scoring code and weights.
- Hard filters take precedence over scores; no high score can bypass policy.
- Scores normalized per candidate set, with explained contributions and missing-metric treatment.
- Use confidence/sample size/freshness when computing quality/latency; low-sample estimates cannot dominate proven alternatives without explicit exploration policy.
- Tie-breaking deterministic by stable ID or policy-defined preference; small bounded exploration only if separately enabled and safe.
- No cross-tenant training or telemetry leakage in explanations.
- Duplicate requests must not double-admit, even when retried over several parent gateways.

### 6.2 Fallback reason taxonomy

At minimum: `ALIAS_NOT_FOUND`, `ALIAS_DISABLED`, `ALIAS_CYCLE`, `INVALID_CAPABILITY`, `FEATURE_UNVERIFIED`, `CONTEXT_TOO_SMALL`, `MODALITY_UNSUPPORTED`, `POLICY_DENIED`, `TENANT_DENIED`, `TRUST_DENIED`, `RESIDENCY_DENIED`, `NO_READY_INSTANCE`, `NO_ADMISSION_CAPACITY`, `QUEUE_DEADLINE`, `PROVISIONING_UNAVAILABLE`, `COLD_START_DISALLOWED`, `STALE_ADVERTISEMENT`, `FEDERATION_UNAVAILABLE`, `LEASE_CONFLICT`, `MODEL_DRAINING`, `MODEL_PREEMPTED`, `INSTANCE_GENERATION_STALE`, `BACKEND_UNHEALTHY`, `BACKEND_UNREACHABLE`, `UPSTREAM_RATE_LIMITED`, `RETRY_BUDGET_EXHAUSTED`, `PARTIAL_STREAM_FAILURE`, `CLIENT_CANCELLED`.

Return machine-readable error code, human-safe explanation, retryable flag, optional `retry_after_ms`, correlation ID, and policy-safe compatible alternative summary. Do not leak forbidden model identities.

## 7. Federation and upstream alias advertisement

- Only downstream-owner authorized `opt-in` resources may be advertised; upstream demand is a request, not command to provision.
- Upstream advertisements contain aggregate **conservative capability envelopes** (alias IDs/version, supported runtime/modalities/features/limits, capacity class, ready/warm/provisionable distinction, health, expiry/sequence, provenance/trust, owner policy identifier), not a combinatorial enumeration of variants.
- Aggregate claims must preserve feature co-occurrence: never advertise vision+tools+128K as jointly available if those features exist only on different concrete variants. Represent a bounded set of *valid capability profiles* or conservative intersection/envelopes with qualification.
- Distinguish **advertised availability**, **accepted offer**, **reservation**, and **READY serveable endpoint**; only latter can be immediately routed.
- Shared physical capacity advertised to multiple parents is deduplicated by stable owner/resource-group identity and reserved atomically by owner. Advertisements do not confer allocation entitlement.
- Use signed/authenticated parent links, sequence numbers, TTLs, tombstones, provenance path vectors and max-hop protection. Never route cycles or count one model multiple times.
- Local authenticated clients outrank upstream federation demand; owner can cap, revoke, deny, preempt permitted federated leases. Preemption immediately invalidates lost placements, notifies upstream and may trigger compatible lower-resource repacking using remaining GPUs.
- Demand may flow downstream, offers/capability publication upstream according to owner control; no tunnels, unsolicited remote installation or arbitrary execution.
- When an alias is unavailable locally, eligible federated candidate routes may be explored within trust/policy and deadline; one consistent core admission/ownership path decides.
- UI exposes advertised vs actual ready, owner, reservation, expiry, shared-capacity de-duplication and local-vs-upstream priority.

## 8. Runtime, rebalance, provisioning and GPU awareness

- The alias resolver consumes versioned `RuntimeInstance` facts from the existing universal runtime framework; it never hardcodes an inference engine.
- Support hot-loaded models: receiving an alias request can trigger existing authorized demand/placement flow only if profile, runtime family, model artifacts, node eligibility, memory and owner policy permit.
- On VRAM pressure, consult the existing rebalancer for feasible packing and small/warm model placement. Do not implement an alias-specific rebalancer.
- Account separately for immutable weights, quantization-specific footprint, temporary startup overhead, KV cache, runtime overhead, shared caches, fragmented/reserved VRAM, colocated models and free headroom.
- Multi-GPU model placements are atomic placement groups; losing a required GPU invalidates the instance and requires deregistration, even if other GPUs remain available for smaller compatible models.
- Slurm/node ETA and offer confidence come from canonical provider events, not Go calculations.
- Introduce demand hysteresis, cooldowns, minimal residence times and load/unload cost safeguards to prevent oscillation.
- Alias health reflects candidate set: `READY`, `DEGRADED`, `QUEUE_ONLY`, `PROVISIONABLE`, `UNAVAILABLE`, `DISABLED` with separately stated cause and revision.

## 9. API and protocol contract (proposed; reconcile with current routes)

Prefer current `/inferweave/v1` convention. Preserve existing OpenAI-compatible routes. All management writes use RBAC, audit, idempotency and optimistic concurrency (`If-Match` revision or equivalent). Administrative writes are executed by Rust, never written into a parallel Go database.

| Method | Route | Purpose |
|---|---|---|
| GET | `/inferweave/v1/aliases` | Filter, sort, paginate alias definitions/status |
| POST | `/inferweave/v1/aliases` | Validate/create draft, idempotently |
| GET | `/inferweave/v1/aliases/{id}` | Definition, published revision, effective state |
| PATCH | `/inferweave/v1/aliases/{id}` | Revise draft with revision match |
| POST | `/inferweave/v1/aliases/{id}/validate` | Semantic/lint validation and compatibility hints |
| POST | `/inferweave/v1/aliases/{id}/publish` | Atomic publish approved revision |
| POST | `/inferweave/v1/aliases/{id}/rollback` | Publish a revision copied from prior version |
| POST | `/inferweave/v1/aliases/resolve` | Side-effect-free resolution preview |
| POST | `/inferweave/v1/aliases/simulate` | Side-effect-free counterfactual / dry-run |
| GET | `/inferweave/v1/aliases/{id}/history` | Audit, revisions and change diff |
| GET | `/inferweave/v1/catalog/models` | Concrete model and deployment capability catalog |
| GET | `/inferweave/v1/requests/{id}/routing` | Per-request routing/fallback explanation |
| GET | `/inferweave/v1/events` | Resumable typed snapshots/deltas/event stream |
| GET | `/inferweave/v1/federation/alias-advertisements` | Authorized provenance and envelopes |

### 9.1 Example resolve request

```json
{
  "alias_id": "coding-fast",
  "request_context": {
    "tenant": "example",
    "runtime_class": "chat",
    "required": {"min_context_tokens": 65536, "tool_calling": "verified"},
    "preferred": {"latency": 0.6, "quality": 0.4},
    "allow_federation": true,
    "allow_cold_start": false,
    "deadline_ms": 12000
  },
  "include_explanations": true
}
```

### 9.2 Example resolution response

```json
{
  "resolution_id": "res_01",
  "alias_id": "coding-fast",
  "alias_revision": 12,
  "catalog_revision": "cat_2049",
  "routing_policy_version": "policy_3",
  "evaluated_at": "2026-10-12T20:00:00Z",
  "expires_at": "2026-10-12T20:00:02Z",
  "status": "READY",
  "selected": {"model_id": "qwen/example-revision", "instance_id": "rt_42", "owner_gateway_id": "gw_a", "state": "READY"},
  "candidates": [
    {"model_id": "qwen/example-revision", "instance_id": "rt_42", "eligibility": "ELIGIBLE", "score": 0.91, "factors": {"latency": 0.85, "quality": 0.94, "capacity": 0.96}, "route_kind": "LOCAL"},
    {"model_id": "deepseek/example-revision", "instance_id": "rt_81", "eligibility": "EXCLUDED", "reasons": ["CONTEXT_TOO_SMALL"], "route_kind": "FEDERATED"}
  ],
  "admission_reserved": false,
  "warnings": ["PREVIEW_ONLY_REVALIDATE_ON_DISPATCH"]
}
```

All IDs in examples are illustrative. `resolve`/`simulate` are **read-only**, never allocate GPUs, load/unload models, or reserve admission. Actual execution returns request ID and (where policy permits) resolved model, alias ID/revision, route provenance and routing-policy version via response metadata/headers/events. Never promise an instance from a preview will still be available at dispatch.

### 9.3 OpenAI compatibility

- `/v1/models` exposes permitted stable alias identities as model choices **in addition** to concrete models, with optional InferWeave extension metadata. Keep normal OpenAI response shape for legacy clients.
- `model:"coding-fast"` invokes an unambiguous published alias; `model:"canonical/exact-id@revision"` stays exact.
- Preserve chat/completions, responses where supported, tool-call JSON, SSE stream chunk sequence, audio/multimodal payloads and content types without alteration.
- Forward useful `x-inferweave-request-id`, `x-inferweave-alias`, `x-inferweave-alias-revision`, `x-inferweave-resolved-model` and diagnostic link only if authorized; no headers that expose protected tenant/candidate details.
- Preserve cancellation, caller deadlines, backpressure, request IDs, idempotency and error status codes through Go relay.

### 9.4 Snapshot/event protocol

- Versioned full snapshot on first subscription/reconnect, then monotonic sequence-numbered deltas; cursor/resume, heartbeat, event deduplication, gap detection and snapshot resync.
- Events: `alias.created`, `alias.published`, `alias.disabled`, `alias.state_changed`, `alias.resolved`, `request.candidate_excluded`, `request.admission_failed`, `request.routed`, `request.fallback`, `request.completed`, `deployment.ready`, `deployment.draining`, `deployment.lost`, `offer.updated`, `offer.revoked`, `lease.preempted`, `capacity.changed`.
- Retention, sampling, cardinality caps and redaction policies prevent telemetry from becoming the hot-path bottleneck.

## 10. Go administration UI — product requirements

Build on existing gateway layout/navigation, components, auth, color tokens and dashboards. Fast, responsive, accessible and visually consistent; support desktop and tablet. Always show *observed authoritative* state and snapshot age, never invented freshness or locally inferred capacity.

### 10.1 Navigation and screen inventory

**A. Models > Aliases — primary new page**

- Header: `Aliases`, search, filters (runtime class, owner, enabled, status, federated/local, family), `Create alias`, refresh/auto-refresh and snapshot age.
- Compact overview tiles: total aliases; ready; degraded; queue-only; unavailable; most-used; 24h fallback percentage. Counts derive from core API.
- Data table: alias + intent, runtime class, requirements chips, top selected concrete model, healthy candidates/total candidates, status/reason, local/federated availability, current routed requests, p50/p95 observed latency with sample size, revision, last edited, actions.
- Each row expands to a **candidate tree**: alias → qualified model variants → READY runtime instances → node/gateway/topology, with exclusion reasons and policy provenance.
- Row actions: inspect, preview, edit, revision history, duplicate draft, disable with confirmation and permissions.

**B. Alias detail / editor**

- Tabs: `Overview`, `Candidates`, `Routing`, `Performance`, `Federation`, `Configuration`, `History`.
- Primary summary: alias intent, effective status, last-resolved time, published revision, owner, health, policy and exact constraints.
- Visual drag/reorder or sensible form controls for allowed families, pinned/denied models, required modalities/tools/context/runtime, tenancy/trust/privacy and allowed federation.
- Weighted preference sliders with normalization; clear separation **Required (hard)** vs **Preferred (soft)**.
- Queue/cold-start/compatible-only fallback/timeout settings with validated ranges.
- `Validate`, `Preview candidate set`, `Simulate`, `Save draft`, `Review changes`, `Publish` controls, permissions and safeguards. No hidden side effects from preview.
- Side-by-side diff and impact estimate before publication: additions/removals, newly excluded candidates, changes in health, estimated effect and unknowns.
- Status safety indicator for impossible/empty aliases; publish block or explicit protected override as defined by owner policy.
- Conflict/optimistic-lock error presents an actionable diff rather than overwriting concurrent edits.

**C. Routing Explorer**

- Request lookup by correlation/request ID, alias, model, tenant (subject to authorization), gateway, node, outcome and time.
- Timeline: resolve → hard exclusions → score candidates → admission → queue/provision (if any) → selected path → streaming → done/error/preemption.
- Side-by-side candidate comparison showing scored contributions, verified capability confidence, context/feature constraints, warm/ready, seats/queue, locality, route and reason exclusions.
- Actual routed path with federation hops vs data path; no conflation of control-plane topology and traffic relay.
- For every fallback, show trigger, candidates skipped, timeout/retry counts and whether response had started.
- `Explain this decision` as an evidence-based UI panel based on the routing trace; no UI re-scoring.

**D. Alias Simulation / “What Should I Use?”**

- Workload intent presets: coding fast/best, reasoning, long-context, vision, chat, embedding, transcription, TTS, prediction and System One where supported; presets *populate structured constraints*, not hidden hardcoded rankings.
- Inputs for required context, tools, modality, latency target, priority, tenant/trust, warm-only and federation permission.
- Output: eligible aliases and concrete candidates with confidence/verification, trade-offs, reasons, capacity and provenance.
- `Compare` 2–4 candidates, quality evidence/sample sizes, throughput, p50/p95, cost-equivalent where separately supported, and cold-start uncertainty.
- A read-only `Copy request example` with explicit alias and requirements; never dispatch a real inference during a simulation unless user takes a separately labeled `Send test request` action.

**E. Federation & Sharing — alias tab/subview**

- Per parent/downstream advertisement: offered alias envelope, valid capability profiles, available vs reserved vs READY, owner policy, freshness/lease TTL, trust and route provenance.
- Clear markers of duplicated shared capacity, priority of local users, owner-controlled sharing/preemption and expiring offers.
- Reasoned diagnostics: why a remote alias is unavailable, stale, blocked or not eligible for upstream use.
- Authorization-gated configuration for federation sharing policy through core APIs only.

**F. Model catalog + GPU/Capacity cross-links**

- Distinguish `Alias` from `Concrete model` and `Runtime instance` everywhere.
- From alias candidate click, open existing model/runtime/GPU detail to inspect placement groups, weights, caches, KV, slots, reserved/free memory, warmness and rebalancer decisions.
- Capacity panel differentiates READY, queued, provisioning, unavailable and draining; connects demand pressure to model loading without implying UI commands made scheduling choices.

### 10.2 Minimum UI layout sketch

```text
Models / Aliases                                              [Create Alias]
[Search aliases...] [Runtime ▾] [State ▾] [Owner ▾] [Refresh]
[Ready 18] [Degraded 3] [Queue-only 2] [Unavailable 1]
┌──────────────────┬───────────┬─────────┬──────────┬─────────┐
│ Alias            │ Required  │ Status  │ Selected │ p95     │
├──────────────────┼───────────┼─────────┼──────────┼─────────┤
│ coding-fast      │ tools 32k │ READY   │ qwen/... │ 1.1s    │
│ coding-best      │ tools 64k │ QUEUED  │ —        │ —       │
│ qwen-vision      │ image 32k │ READY   │ qwen/... │ 2.7s    │
└──────────────────┴───────────┴─────────┴──────────┴─────────┘

Alias: coding-fast  [Overview] [Candidates] [Routing] [Config] [History]
Required: tools=verified / text / context>=32k  | Preferred: latency 40%
Alias → model A (eligible, score .91) → gw A → node 7 [READY, 2 slots]
      → model B (excluded: context too short)
      → model C (eligible, score .77) → remote gw B [READY, 1 slot]
[Preview] [Validate] [Edit draft] [Publish revision]
```

Sketch values are mock data, not target or observed deployment metrics.

### 10.3 UI state and interaction rules

- Loading skeleton, empty, no-permission, offline/stale, partial-data, failed API, tombstoned/disabled and confirmation states designed explicitly.
- Accessible contrast, keyboard/ARIA, responsive table-to-card behavior, tooltips with stable reason codes and human explanations, no color-only signals.
- Avoid refresh storms: SSE/event invalidation plus throttled live updates, resumable cursors, backoff and user-visible stale badge.
- Paginate/filter server-side; virtualize large tables; do not ship unbounded metrics cardinality to browser.
- Permissions: viewer (read), operator (simulate/draft depending on role), administrator (publish/rollback/sharing); enforcement is Rust-side even if UI hides buttons.
- Visual QA screenshots for alias index/detail/editor, empty/failed/stale states, routing explorer, federation and mobile/tablet.

## 11. Persistence, migrations and backward compatibility

- Single authoritative Rust persistence for definitions, immutable published revisions, optimistic revision numbers, tombstones/disable status and audit trail; use existing store where available.
- No second Go alias DB. Go read caches may be ephemeral and invalidated by sequence/generation.
- Migration: inventory current hardcoded aliases (including Go-side definitions), translate to canonical managed aliases while preserving names/behavior; run shadow resolution and compare results before moving traffic.
- Preserve existing `/v1/models` and exact inference traffic. Roll out behind `alias_engine_v1` and read-only UI flag. Introduce alias publishing only after parity tests.
- Support expand/migrate/contract schema revisions, mixed-version gateway compatibility, unknown-field tolerance where safe and explicit incompatibility errors.
- Rollback means publish a new revision based on a previous revision; never rewrite audit history.
- Preserve externally visible request IDs, tenancy, auth, headers and observability contracts.

## 12. Security and abuse resistance

- Enforce alias CRUD and resolve authorization in Rust per tenant, owner and role; edge auth is additional, not sufficient.
- Never expose hidden candidates, proprietary models, forbidden gateways, internal addresses, cross-tenant quality data or reservation secrets in catalog/resolve/explain.
- Bound alias expression complexity, depth, candidate set, filter costs, dry-run rate, API pagination, session occupancy, queue deadlines and attempt counts.
- SSRF protection: router endpoints derive only from authenticated registered runtime instances; never from untrusted alias fields.
- Signed/trusted federation snapshots and lease ownership; protect against stale/replayed offers and conflicting revisions.
- Protect prompt/content privacy in telemetry: metadata by default, redact payloads, restrict trace retention and tenant-scoped audit access.
- Publication requires validation, authorization, audit reason, optimistic-lock control and optional approval workflow aligned with existing admin policies.

## 13. Metrics, traces and SLOs

- `alias_resolution_total{alias,status,reason}` (bounded labels; IDs hashed or capped where appropriate)
- `alias_resolution_duration_seconds` p50/p95/p99
- `alias_candidate_filter_total{reason}`
- `alias_admission_attempts_total{outcome}`
- `alias_route_selected_total{runtime_class,route_kind}`
- `alias_fallback_total{reason,stage}`
- `alias_queue_wait_seconds`; `alias_cold_start_seconds`
- `alias_active_requests`, `alias_eligible_instances`, `alias_ready_seats`
- `alias_federation_offers{state}`, `alias_stale_advertisements_total`, `alias_lease_conflicts_total`
- `alias_revision_published_total`, `alias_resolution_cache_hits_total`, `alias_resolution_stale_rejects_total`

Every request produces trace/correlation linkage across gateway → owner → instance including alias ID/revision, catalog generation, policy version, hard-filter outcomes, scoring contributions, admission attempt and fallback history (redacted for tenant visibility). Define p95 overhead baseline before activation and require no material hot-path regression; gate rollout on measured parity/latency rather than invented numeric targets.

## 14. Cache and consistency

- Compile immutable alias definitions keyed by alias revision; dynamic candidate lists may be short-lived cached by `{alias revision, catalog revision, tenant/policy scope, requirement fingerprint}`.
- Cache only eligibility/ranking hints, never capacity entitlement. Admission always revalidates at owner.
- Negative cache uses very short TTL and invalidation on ready/health/capacity/deployment/offer changes; avoid long-lived unavailability after model startup.
- Event sequence gaps force snapshot recovery; record stale state and stop advertising unverified READY supply.
- Federation envelopes expire; tombstones and owner generation prevent resurrection of dead instances.
- Resolution preview includes `evaluated_at`, `expires_at` and `admission_reserved=false`.

## 15. Acceptance tests — mandatory

### Unit/property

1. Exact IDs never silently substitute; legacy name precedence stable; alias namespace collisions validated.
2. Context/tool/modality/privacy/residency/trust requirements are strict; no soft score overrides.
3. All capability fidelity/confidence states, missing metrics, stale and degraded instances handled conservatively.
4. Alias cycles/depth bounded; deterministic scoring and stable ties; weight normalization correct.
5. Candidate set updates with event revisions; cache invalidation and negative cache expiry reliable.
6. Disabled, draining, preempted, stale generation and unhealthy instances excluded.
7. All errors emit machine-readable reason and retryability; no prohibited candidate disclosure.

### Integration/conformance

8. OpenAI `/v1/models` and requests work for aliases and exact IDs; SSE/tool/multimodal/cancellation intact.
9. Busy top candidate falls back to compatible READY runner without stampede; atomic admission and retry budgets work.
10. Context-hard constraint causes safe failure even if an otherwise highly ranked candidate is available.
11. All READY instances disappear → explicit QUEUE_ONLY/PROVISIONABLE/UNAVAILABLE, never a fake ready route.
12. New high-demand alias triggers policy-authorized provisioning through existing runtime profiles/rebalancer; reaches READY and routes.
13. Warm/cold cycles, model unloading, cancellation, preemption and GPU loss deregister without stale routing.
14. Multi-GPU model loses one GPU → entire placement invalidates and remaining GPUs may be offered for other feasible workloads.
15. Upstream with several parents does not double-count owner capacity; reservation leases are exclusive/idempotent.
16. Federation declines or local-priority preempts upstream demand; immediate propagation and safe fallback.
17. Cyclic/malformed/expired advertisements cannot route; no tunnels, no unsolicited provisioning.
18. Streaming fails mid-output → explicit partial failure, no invisible replay.
19. Full snapshot → event resume → dropped cursor → snapshot recovery, no duplicate counters or stale resurrection.
20. Cross-tenant and unauthorized requests never expose private candidate lists or protected metadata.
21. Go relay preserves status, bytes, headers, streams, cancellation, timeouts and correlation IDs under load.
22. Go alias management pages use only core APIs; code search confirms zero Go-side model-selection engine or shadow alias persistence.
23. Mixed-version old/new gateways preserve existing exact-model behavior and reject unsupported new schema safely.

### End-to-end UI

24. Create draft → validate → preview → review diff → publish → live resolve → inspect routing trace → rollback.
25. Compare two aliases, see excluded candidates with explanations and navigate to concrete model/GPU view.
26. Federation offer appears/ages/expires, de-duplication visible; local priority and preemption reasons visible.
27. Offline, stale stream, permission denied, conflicting edits, empty lists, loading and pagination behave correctly.
28. Responsive desktop/tablet, keyboard navigation and accessibility checks; visual screenshot baselines reviewed.
29. Production-like load simulates model saturation, queueing, provision/rebalance, repeated failures and gradual recovery without loops or admission stampedes.

## 16. Parallel workstreams and dependencies

| Lane | Repository | Deliverables | Dependencies |
|---|---|---|---|
| 0 — Audit + contract | specs and both repos | Gap matrix, baseline tests, immutable terminology, API schemas, reason codes, fixtures | First; shared blocking contract |
| 1 — Domain persistence | Rust | Alias CRUD, revisions, validation, auth, audit | Lane 0 |
| 2 — Core resolver | Rust | Capability matching, ranking, caching, explain, preview | 0, initial 1 |
| 3 — Router integration | Rust | Admission, fallback, streaming-safe trace, affinity | 2 |
| 4 — Runtime/federation | Rust | READY facts, envelopes, owner leases, hot loading/rebalancer integration | 0; coordinate with 2/3 |
| 5 — Go API integration | Go | Typed client, transparent relay, snapshot/event subscription, auth controls | Contract from 0; core API mocks |
| 6 — Go alias UI | Go | Index, detail, editor, publish, history, responsive states | 5; mocked contracts until core ready |
| 7 — Go routing/federation UI | Go | Explain, simulation, candidate visualization, fleet crosslinks | 5; test fixtures |
| 8 — Test/QA/security | All | Golden contract fixtures, conformance, integration, Playwright, load/security, migration | Continuous, final full-system gate |

### Supervising agent instructions

- One contract owner reviews schema changes. Agents work on isolated branches/worktrees and open small PRs with traceable acceptance IDs.
- No concurrent modification of shared core routing or shared generated clients without explicit coordination.
- Before implementing a new helper/module, search for existing same-purpose code and refactor/reuse it; actively remove duplicate implementation once parity is proved.
- Record exact ownership boundaries in PR review; reject Go-side routing or independent model inventory.
- Use available Pi agents with Qwen/DeepSeek slots for implementation and Codex as supervisor/reviewer; support capability-driven fallback to other available suitable hosted local models when slots are unavailable. No long-hanging builds/tests; per-job deadlines, heartbeats, log updates, retries and visible progress.
- Run focused tests before full suite; use shared build cache and bounded Rust target directories; remove worktrees/build artifacts after merges according to repo safeguards.
- Contract and characterization tests must merge before behavior switches; then Rust routes; then Go wiring; then flag enablement.
- Update specs based on source audit; never silently claim pre-existing functionality or overwrite independent concurrent work.

## 17. Rollout and gates

**Phase A — Audit/contracts:** Snapshot all current behavior, map drift, publish schemas and fixtures. Gate: baseline test suite and gap matrix approved.

**Phase B — Rust shadow resolver:** Management APIs, dynamic matching, explain outputs, side-effect-free preview; existing routing remains authoritative. Gate: golden tests and measured parity.

**Phase C — Admission/federation integration:** Enable exact-safe alias dispatch for internal test tenants and a handful of aliases; capture deterministic traces. Gate: preemption, admission, concurrency and failure scenarios pass.

**Phase D — Go UI/relay:** Introduce pages and editor backed by typed Rust APIs; no duplicate engine. Gate: user journeys and streaming-compat tests pass.

**Phase E — Controlled production rollout:** Canary alias traffic by authorized tenant or policy, track routing correctness and p95 overhead, gradual enablement; immediate feature-flag rollback to existing exact behavior. Gate: accepted SLO/error/correctness targets measured against baseline.

**Phase F — Cleanup:** Remove redundant Go alias logic and obsolete compatibility shims only after proof of parity, references updated, migrations safe and rollback window expired. Publish implementation inventory, screenshots, load reports and final traceable acceptance matrix.

## 18. Definition of done

- Every managed/dynamic alias and exact-model request uses a single authoritative Rust routing/admission path.
- Go provides a complete alias creation/administration experience, candidate visualization and causal routing explanation **without owning selection logic**.
- Runtime classes, verified features and context/privacy constraints govern eligibility correctly.
- Federation remains strictly opt-in, owner-authoritative, loop-free and non-double-counting.
- Rebalancer/provisioning/VRAM/runtime changes are integrated with existing code, not forked.
- Contracts, migrations, rollback, telemetry, security and all relevant acceptance scenarios have automated evidence.
- Existing client protocol functionality continues working; duplication is removed with characterization proof.
- Source gap matrix links each requirement to actual implementation files/PRs/tests; no unverified “done” checkboxes.

## 19. Concrete launch aliases (configuration examples, not hardcoded engine rules)

| Alias | Intent | Illustrative hard constraints | Default bias |
|---|---|---|---|
| `coding-fast` | Responsive agent coding | text, verified tools, defined context floor | latency and admission readiness |
| `coding-best` | High-quality complex code | text, verified tools, higher context | measured quality and reliability |
| `reasoning-best` | Complex planning | reasoning-capable verified profile | measured quality |
| `long-context` | Large-document tasks | explicit context floor | sufficient context and memory efficiency |
| `qwen-vision` | Qwen-family vision | image input verified + family allow | warm/readiness and performance |
| `chat-fast` | Interactive conversation | chat/text | latency and efficiency |
| `embedding` | Semantic vectorization | embeddings runtime + dimensional compatibility | throughput/efficiency |
| `transcription` | Speech-to-text | STT runtime + specified audio limits | latency/accuracy |
| `tts` | Speech synthesis | TTS runtime + required output format | latency/quality |
| `prediction` | Structured prediction | prediction runtime + required schema | correctness/latency |
| `laya-auto` | System One routing | System One runtime and required structured feature fidelity | latency and reliability |

Do not claim a specific alias is currently READY, or map it to specific deployed checkpoints, until verified against live catalog and tenant policy. Operators define floors/weights and publish through the same canonical API. **Names represent intent, not guaranteed vendor/model deployments.**

---

### Copy-paste final supervisor command

> Execute `INFERWEAVE_DYNAMIC_ALIASES_MASTER_SPEC.md` in `inferweave/inferweave-specs`, `inferweave/inferweave`, and `metabolomics-us/inferweave-gateway`. Audit first and generate the source-backed gap matrix; then run parallel contract/core/UI/test lanes with Codex supervision and available Pi workers using Qwen/DeepSeek capacity. Preserve existing behavior, reuse/refactor already implemented services, enforce one Rust routing/alias authority and a UI-only Go administrative boundary, implement and run all relevant acceptance tests, inspect UI screenshots and routing traces, resolve failures, merge reviewed changes and cleanup worktrees/builds. Provide a final report mapping every requirement to PRs, tests and observed proof, with remaining blockers clearly marked. Do not mark complete solely because code compiled.
