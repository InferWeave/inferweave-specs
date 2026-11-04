# Canonical InferWeave Implementation Sequence

This file is the **single authoritative implementation order**.

Rules:
- Execute tasks in dependency order.
- Parallelize only dependency-complete tasks that do not modify the same public contract.
- Persistent production deployment uses Docker Compose; Slurm allocation workers use Apptainer.
- Respect `implementation/PHASE_GATES.md`.
- Use the declared 50–100K context class.
- Do not implement downstream features early.
- GPU watchdog/rescue is part of the first working GPU weave, not a later operations add-on.
- Solana remains deferred.

## Phase 0 — Foundation / Bootstrap

### P0-T01 — Bootstrap clean Rust/Next.js monorepo
**Context:** `C50`
**Depends on:** none
**Features:** IW-BOOT-001
**Read:** specs/00_INVARIANTS.md, specs/01_REPOSITORIES_AND_OWNERSHIP.md

**Outcome:** Rust workspace, apps/web, CI skeleton, docs/ADR/changelog layout compile from an empty repository.

**Required tests:**
- cargo fmt/check/test baseline
- Next.js lint/typecheck baseline

### P0-T01A — Machine-checked registry pattern and anti-vacuous guards
**Context:** `C65`
**Depends on:** P0-T01
**Features:** IW-EVID-002
**Read:** specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/00_INVARIANTS.md

**Outcome:** Shared vocabularies ship as frozen data plus a published document plus conformance tests that fail on disagreement, and every structural guard is executed against a deliberately broken copy of what it guards.

**Required tests:**
- document and frozen data reconciled cell by cell
- each guard rejects its known-bad input
- removing a guard fails the guard self-test
- new vocabulary value without a decision record fails

**Notes:** A guard that silently stops checking reports success indefinitely. scripts/validate_specs.py --self-test demonstrates the rule on this bundle.

### P0-T02 — Canonical protocol versioning, typed IDs and error envelope
**Context:** `C55`
**Depends on:** P0-T01
**Features:** IW-CORE-001
**Read:** specs/00_INVARIANTS.md, specs/02_PROTOCOL_AND_API.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md

**Outcome:** Create canonical protocol crate with strongly typed IDs, schema versions and normalized error types.

**Required tests:**
- unit serialization round trips
- schema compatibility fixture tests

### P0-T03 — Bootstrap CLI command framework and versioned JSON output
**Context:** `C55`
**Depends on:** P0-T01, P0-T02
**Features:** IW-BOOT-001, IW-BOOT-004
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Create `inferweave` CLI with stable commands, exit codes, JSON envelope and secret-redaction rules.

**Required tests:**
- CLI golden JSON tests
- exit-code tests
- secret redaction tests

### P0-T04 — Read-only doctor and host probe
**Context:** `C65`
**Depends on:** P0-T03
**Features:** IW-BOOT-004, IW-NODE-002, IW-TEL-001
**Read:** specs/20_NODE_AUTOCONFIG_DISCOVERY.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** `inferweave doctor/probe --json` reports OS/CPU/RAM/storage/network/container/GPU/runtime facts without mutation.

**Required tests:**
- fixture probes AMD/NVIDIA/no-GPU
- unsupported sensor representation
- read-only integration test

### P0-T05 — PostgreSQL development storage foundation
**Context:** `C60`
**Depends on:** P0-T01, P0-T02
**Features:** IW-PROMPT-001, IW-TEL-001
**Read:** specs/22_PROMPT_LEDGER.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/34_PROMPT_STORE_TIERING.md

**Outcome:** Create storage crate, migrations, transaction helpers and local PostgreSQL Compose profile.

**Required tests:**
- migration up/down in disposable DB
- transaction/idempotency tests

### P0-T06 — Canonical schemas and generated Rust/TypeScript bindings
**Context:** `C65`
**Depends on:** P0-T02
**Features:** IW-CORE-001
**Read:** specs/02_PROTOCOL_AND_API.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** Establish OpenAPI/JSON Schema source of truth and generated bindings with CI drift detection.

**Required tests:**
- generation reproducibility
- Rust/TS schema parity
- CI drift failure test

### P0-T06A — Conformance vectors and hostile vectors
**Context:** `C70`
**Depends on:** P0-T06
**Features:** IW-EVID-001
**Read:** specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/02_PROTOCOL_AND_API.md

**Outcome:** Hash-pinned conformance vectors with a digest manifest cover the message envelope, identity, discovery, error envelope, receipt chain, capability advertisement and context ceiling, each with hostile cases and expected refusals.

**Required tests:**
- Rust and TypeScript agree with the same vector, not the same prose
- manifest digest mismatch fails the build
- each hostile vector produces its expected refusal
- a vector set with no hostile case fails

**Notes:** Two implementations agreeing with a document is not evidence of agreement.

### P0-T07 — Container stack renderer and init plan
**Context:** `C70`
**Depends on:** P0-T03, P0-T04, P0-T05
**Features:** IW-BOOT-002, IW-BOOT-004
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** `inferweave init plan <role> --json` emits explicit containers, ports, volumes, device mappings, privilege changes and rollback plan.

**Required tests:**
- golden plans gateway/node/edge/site/proxy
- no silent firewall mutation
- GPU device selection test

### P0-T08 — Local development stack generator
**Context:** `C65`
**Depends on:** P0-T07
**Features:** IW-BOOT-002
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** `inferweave init dev` creates and verifies deterministic gateway/node/mock/web/Postgres development stack.

**Required tests:**
- Compose bring-up E2E
- idempotent second run
- teardown leaves persistent data as documented

### P0-T09 — Next.js shell and generated API client
**Context:** `C55`
**Depends on:** P0-T01, P0-T06
**Features:** IW-UI-001
**Read:** specs/10_DASHBOARD_PORTAL.md

**Outcome:** Create common Next.js application shell, generated API client and server/client auth-ready boundaries.

**Required tests:**
- typecheck
- component smoke tests
- generated client compile

### P0-T10 — Bootstrap CLI support bundle and config model
**Context:** `C55`
**Depends on:** P0-T03, P0-T04
**Features:** IW-BOOT-004
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Implement config discovery/export, status skeleton and redacted support-bundle format.

**Required tests:**
- redaction fixture
- bundle manifest test
- config permissions test

### P0-T11 — Foundation security and secrets policy
**Context:** `C70`
**Depends on:** P0-T03, P0-T05, P0-T07
**Features:** gate/review
**Read:** specs/16_SECURITY_PRIVACY_TRUST.md, specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Implement shared secret types/redaction, filesystem permissions, container privilege policy and bootstrap credential primitives.

**Required tests:**
- secret cannot serialize to logs
- permissions tests
- negative privilege configuration tests

### P0-T11A — Docker/Apptainer deployment substrate contract
**Context:** `C70`
**Depends on:** P0-T04, P0-T07, P0-T11
**Features:** IW-DEPLOY-001
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** Bootstrap/runtime abstraction supports Docker Compose for persistent roles and Apptainer for Slurm, with pinned container artifacts, GPU device scoping and no bare-host model server path.

**Required tests:**
- gateway/node role plan selects Docker Compose
- slurm role plan selects Apptainer
- Podman/bare-host production mode rejected
- GPU device scoping fixture
- pinned digest validation

**Notes:** This task defines deployment mechanics; it does not implement Slurm scheduling.

### P0-T12 — Phase-0 architecture and bootstrap review
**Context:** `C90`
**Depends on:** P0-T01, P0-T02, P0-T03, P0-T04, P0-T05, P0-T06, P0-T07, P0-T08, P0-T09, P0-T10, P0-T11, P0-T11A
**Features:** gate/review
**Read:** specs/00_INVARIANTS.md, specs/01_REPOSITORIES_AND_OWNERSHIP.md, specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Independent review verifies clean-slate boundaries, schema ownership, CLI safety and that Phase 1 can build without legacy assumptions.

**Required tests:**
- full workspace CI
- fresh-machine dev bootstrap acceptance

**Notes:** Review-only; do not add features.

## Phase 1 — Working Direct GPU Weave

### P1-T01 — Stable provider/node/GPU identity primitives
**Context:** `C65`
**Depends on:** P0-T12
**Features:** IW-NODE-001, IW-SLURM-002
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md

**Outcome:** Implement stable provider/cluster/host/GPU identities separate from worker/connection identities.

**Required tests:**
- same fingerprint resolves same identity
- hardware replacement creates new generation
- duplicate mapping property tests

### P1-T02 — One-time enrollment and node credentials
**Context:** `C70`
**Depends on:** P1-T01, P0-T11
**Features:** IW-BOOT-003, IW-NODE-001
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/16_SECURITY_PRIVACY_TRUST.md, specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Gateway issues one-time short-lived enrollment codes that exchange for scoped persistent node credentials.

**Required tests:**
- single-use/expiry tests
- replay rejection
- revocation test

### P1-T02A — Token-free proof enrollment
**Context:** `C75`
**Depends on:** P1-T02
**Features:** IW-NODE-004
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Nodes enrol by protocol-role proof and, per advertised model and context class, model-execution proof, receiving a renewable role credential with no operator token and no approval step.

**Required tests:**
- node enrols with no operator-issued token
- eligibility is granted only to the exact challenged claim
- unchallenged context class cannot be served
- a replayed or hostile proof is refused

**Notes:** A shared bootstrap token makes the token the credential; proof binds it to measured capability.

### P1-T03 — Outbound node control connection and heartbeat
**Context:** `C65`
**Depends on:** P1-T02
**Features:** IW-NODE-001, IW-DP-001
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Node maintains authenticated outbound control connection with registration, heartbeat and freshness expiration.

**Required tests:**
- disconnect/stale TTL test
- reconnect same identity
- gateway restart recovery

### P1-T04 — Full hardware/software/GPU discovery fingerprint
**Context:** `C70`
**Depends on:** P1-T01, P0-T04
**Features:** IW-NODE-002, IW-TEL-001
**Read:** specs/20_NODE_AUTOCONFIG_DISCOVERY.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md

**Outcome:** Node produces immutable hardware/software/runtime fingerprint including GPU UUIDs/topology/drivers/runtime/model-server capabilities.

**Required tests:**
- AMD/NVIDIA fixtures
- fingerprint stability
- material change causes new fingerprint

### P1-T05 — Live GPU/host telemetry collection
**Context:** `C65`
**Depends on:** P1-T04, P0-T05
**Features:** IW-TEL-001, IW-OBS-001
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** Collect temperature/power/clocks/utilization/VRAM/errors plus host CPU/RAM/storage/network where supported.

**Required tests:**
- sensor unsupported semantics
- sample ingestion
- bounded frequency/backpressure
- AC-OBS-04/08: measured CPU entitlement and per-GPU NVIDIA observe telemetry preserve unknown/unsupported; AMD proof remains separate

### P1-T06 — Immutable deployment manifest and node advertisement
**Context:** `C65`
**Depends on:** P1-T03, P1-T04, P0-T06
**Features:** IW-NODE-002
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/12_MODEL_TUNING_BENCHMARKS.md

**Outcome:** Define deployment fingerprint and advertise resident/available deployments with exact model/runtime/profile versions.

**Required tests:**
- fingerprint roundtrip
- mutable alias cannot change immutable fingerprint
- freshness tests

### P1-T06A — Publish a deployment context ceiling sized to the envelope
**Context:** `C75`
**Depends on:** P1-T06
**Features:** IW-DEPLOY-003, IW-CAP-002
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Deployment loads at the largest context its measured envelope safely permits and publishes that value as max_context_tokens in the immutable manifest and node advertisement.

**Required tests:**
- ceiling derived from envelope, not configuration
- published ceiling matches the loaded runtime window
- reduced window records its stated constraint

**Notes:** Context size is derived, never an operator constant.

### P1-T06B — Capability precedence: declared, measured, persisted
**Context:** `C75`
**Depends on:** P1-T06A
**Features:** IW-NODE-003
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md

**Outcome:** Capability claims resolve declared then measured then persisted, keyed by deployment fingerprint, so a model that is not currently loaded remains admissible and cold start cannot deadlock.

**Required tests:**
- unloaded model admissible from declared claim
- measured supersedes declared for the same fingerprint
- persisted claim survives restart
- new fingerprint falls back to declared

**Notes:** An autoloading runtime reports no window for an unloaded model.

### P1-T06C — Record measured runtime tuning per deployment
**Context:** `C70`
**Depends on:** P1-T06A
**Features:** IW-TUNE-002
**Read:** specs/39_INFERENCE_RUNTIME_TUNING.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md

**Outcome:** Each qualified deployment records measured prefill and decode at depth, KV cache type, backend, thread count, device memory headroom, and drafter acceptance, as measurements rather than configuration intent.

**Required tests:**
- throughput record without a depth is rejected
- drafter without a recorded acceptance rate is not qualified
- backend change produces a new deployment fingerprint
- MoE deployment with non-resident experts advertises as low-throughput

**Notes:** Thread count set to SMT threads rather than physical cores cost 19x on one host.

### P1-T07 — Prompt ledger metadata and encrypted payload storage
**Context:** `C75`
**Depends on:** P0-T05, P0-T11
**Features:** IW-PROMPT-001
**Read:** specs/22_PROMPT_LEDGER.md, specs/34_PROMPT_STORE_TIERING.md

**Outcome:** Record encrypted prompt events idempotently behind a bounded sink-neutral buffer while preserving durable-ingest access-audit primitives.

**Required tests:**
- accepted/rejected/cancelled prompt storage
- idempotency
- content excluded from logs
- authorized read audit
- bounded loss is visible and never blocks gateway admission

### P1-T08 — Prompt ingest API and submission ordering
**Context:** `C65`
**Depends on:** P1-T07, P0-T06
**Features:** IW-PROMPT-001
**Read:** specs/22_PROMPT_LEDGER.md, specs/02_PROTOCOL_AND_API.md

**Outcome:** Gateway derives prompt_id/hash before routing, offers the encrypted record without waiting for storage, and keeps the explicit durable-ingest API fail-closed.

**Required tests:**
- unavailable or blocked sink does not delay or refuse gateway admission
- bounded buffer overflow is measured and does not backpressure admission
- retry preserves stable event identity
- explicit durable ingest still fails without committed submission

### P1-T08A — Read-side ledger integrity
**Context:** `C75`
**Depends on:** P1-T08
**Features:** IW-OBS-003
**Read:** specs/22_PROMPT_LEDGER.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md

**Outcome:** Every read of an ordered record proves the whole record gapless rather than the returned page, with storage-engine premises asserted against the live engine.

**Required tests:**
- gap below the reader cursor is detected
- page-shaped check alone fails the suite
- engine rejects the write that would violate each premise
- no second journal implementation is introduced

**Notes:** A correct writer is not the same thing as a trustworthy reader.

### P1-T09 — Gateway registry and `/v1/models`
**Context:** `C60`
**Depends on:** P1-T03, P1-T06
**Features:** IW-CORE-001
**Read:** specs/02_PROTOCOL_AND_API.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md

**Outcome:** Gateway maintains fresh node/deployment catalog and exposes OpenAI-compatible model listing.

**Required tests:**
- stale node removed
- model alias/fingerprint test
- OpenAI response contract

### P1-T10 — OpenAI streaming ingress against deterministic backend
**Context:** `C70`
**Depends on:** P1-T08, P1-T09
**Features:** IW-CORE-001
**Read:** specs/02_PROTOCOL_AND_API.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md

**Outcome:** Implement streaming chat/completion ingress with request IDs, cancellation plumbing and deterministic mock backend.

**Required tests:**
- stream contract
- client disconnect
- malformed backend
- prompt correlation

### P1-T11 — Seat/session/context/KV capacity model
**Context:** `C75`
**Depends on:** P1-T06, P1-T10
**Features:** IW-CAP-001
**Read:** specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Model active sessions as unequal seats with context/KV/output reserve and shared model weight accounting.

**Required tests:**
- capacity never negative property
- shared weights counted once
- context growth update tests

### P1-T11A — Enforce the context ceiling as a hard admission bound
**Context:** `C75`
**Depends on:** P1-T11, P1-T06A
**Features:** IW-CAP-002
**Read:** specs/04_CAPACITY_ADMISSION_SEATS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md

**Outcome:** Admission refuses any request whose total or predicted peak context exceeds the deployment ceiling, before capacity arithmetic, returning a non-retryable 413 CONTEXT_WINDOW_EXCEEDED naming the actual ceiling.

**Required tests:**
- oversized request refused before prefill
- refusal names the real ceiling
- unknown ceiling is not admissible
- 413 non-retryable, distinct from transient 503

**Notes:** Free capacity never raises a ceiling.

### P1-T11B — Reservation liveness and stale reclamation
**Context:** `C75`
**Depends on:** P1-T11
**Features:** IW-CAP-003
**Read:** specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Reservations carry progress timestamps and are reclaimed on silence rather than duration, with idempotent release and recorded reclaim events.

**Required tests:**
- leaked reservation reclaimed after the silence bound
- long request making progress is never reclaimed
- release is idempotent
- reclaim events are recorded

**Notes:** Measuring duration instead of silence kills long legitimate requests.

### P1-T12 — Node authoritative admission and leases
**Context:** `C70`
**Depends on:** P1-T11, P1-T03
**Features:** IW-CAP-001, IW-BP-001
**Read:** specs/04_CAPACITY_ADMISSION_SEATS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md

**Outcome:** Gateway prediction is confirmed by authoritative node lease/admission with bounded expiration/cancellation.

**Required tests:**
- lease expiration
- double-admit race
- cancel releases resources
- prediction mismatch

### P1-T12A — Single-source queue observability
**Context:** `C75`
**Depends on:** P1-T12, P1-T11B
**Features:** IW-OBS-002
**Read:** specs/04_CAPACITY_ADMISSION_SEATS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/10_DASHBOARD_PORTAL.md

**Outcome:** Queue position and estimated wait are served from the structure that orders admission, so every waiter is visible to API and dashboard alike.

**Required tests:**
- waiting requests appear while they wait
- position ordering matches admission ordering
- absent estimate reported as absent, never zero
- rejection reason/scope counters survive queue-entry removal; effective limits and missing-metadata buckets explain saturation without exposing caller identities
- shared credential/default subdivisions remain intentional; distinct authenticated parents cannot collapse and subdivision fan-out cannot bypass parent limits

**Notes:** Recording only executing work reports an empty queue to waiting clients.

### P1-T12B — Node serviceability gate and shipped default policy
**Context:** `C75`
**Depends on:** P1-T12
**Features:** IW-BOOT-005
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** A node becomes schedulable only after a real request traverses its full authorization and admission path, and every fail-closed gate ships a working default policy with its installer.

**Required tests:**
- fresh install serves a real request end to end
- missing policy fails the install, not the first user
- liveness probe alone does not satisfy the gate

**Notes:** A fail-closed gate with no policy refuses everything while reporting healthy.

### P1-T13 — Routing hard constraints
**Context:** `C70`
**Depends on:** P1-T09, P1-T11
**Features:** IW-ROUTE-001
**Read:** specs/05_ROUTING_AFFINITY.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Filter candidates by exact model/capability/context/resource/privacy/license/policy constraints.

**Required tests:**
- hard constraints never relaxed property
- no eligible candidate semantics
- model mismatch

### P1-T13A — Context-size alias semantics
**Context:** `C50`
**Depends on:** P1-T13, P1-T09
**Features:** IW-ROUTE-004
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/05_ROUTING_AFFINITY.md

**Outcome:** Context-size aliases resolve as request-shaping hints against one deployment rather than as separate qualified deployments, and never widen a ceiling.

**Required tests:**
- alias family resolves to a single deployment
- alias below the ceiling is honoured as intent
- alias above the ceiling is refused, not downgraded

**Notes:** Separate deployments per size reintroduce the fixed tiers invariant 4 forbids.

### P1-T14 — Best-fit capacity placement
**Context:** `C70`
**Depends on:** P1-T13, P1-T12
**Features:** IW-ROUTE-002
**Read:** specs/05_ROUTING_AFFINITY.md, specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Choose lowest sufficient context/KV headroom after hard filtering to preserve large capacity.

**Required tests:**
- best-fit property tests
- tie handling
- capacity changes during lease

### P1-T15 — Sticky sessions and cache affinity
**Context:** `C65`
**Depends on:** P1-T14
**Features:** IW-ROUTE-003
**Read:** specs/05_ROUTING_AFFINITY.md

**Outcome:** Preserve long-lived session/model-instance affinity while respecting health/capacity/hard constraints.

**Required tests:**
- affinity retained
- affinity broken on hard failure
- no silent model substitution mid-stream

### P1-T16 — Route tickets and rendezvous protocol
**Context:** `C80`
**Depends on:** P1-T12, P1-T15, P0-T11
**Features:** IW-DP-003, IW-DP-002
**Read:** specs/08_CONNECTIVITY_DATA_PLANE.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Issue route-scoped short-lived connection tickets and exchange connectivity candidates without gateway stream proxying.

**Required tests:**
- ticket expiry/replay
- wrong node rejection
- rendezvous fallback fixture

### P1-T17 — Local proxy direct node streaming
**Context:** `C80`
**Depends on:** P1-T16, P1-T10
**Features:** IW-DP-003, IW-PROXY-001
**Read:** specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Local proxy connects directly to selected node, streams OpenAI response and propagates cancellation.

**Required tests:**
- gateway sees zero response payload
- direct success
- cancel propagation
- session affinity

### P1-T18 — Regional/gateway relay fallback
**Context:** `C75`
**Depends on:** P1-T17
**Features:** IW-DP-001, IW-DP-002
**Read:** specs/08_CONNECTIVITY_DATA_PLANE.md, specs/59_LINK_HTTP_JSON.md

**Outcome:** Fallback order is direct → site/regional relay → gateway relay last resort with byte accounting/circuit breakers. Negotiated exact-model Held Link HTTP JSON preserves target, status, MIME and bytes with terminal failure and no replay (spec59).

**Required tests:**
- forced NAT failure
- fallback ordering
- gateway relay bandwidth circuit breaker
- spec59 exact-registration/Link negotiation, HTTP byte fidelity and hostile response vectors; production mixed-version, cancellation/backpressure and no-replay proof owed
- spec63 (proposed, owed): typed-credential upstream binding, acceptor-appended path and hop limit, no transit by default, request-id idempotency, per-key bounds, revocation drain, invariant-11 direct-path preference

### P1-T19 — Canonical 503/429 backpressure and bounded retries
**Context:** `C65`
**Depends on:** P1-T12, P1-T18
**Features:** IW-BP-001
**Read:** specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/04_CAPACITY_ADMISSION_SEATS.md, contracts/backpressure-action-codes.json, contracts/backpressure-conformance-v1.json

**Outcome:** Bounded pre-dispatch admission-queue restrictions and user/FairShare policy return 429; missing or unusable infrastructure/model capacity returns 503; retry candidate/time budgets are bounded.

**Required tests:**
- status mapping
- retry metadata
- no unbounded queue/retry loop
- shared action vocabulary and conformance-vector reconciliation
- rejection of unknown/duplicate actions, condition drift, unbounded retry guidance, and unsafe replay state

### P1-T20 — Per-request performance/resource telemetry
**Context:** `C75`
**Depends on:** P1-T05, P1-T10, P1-T12
**Features:** IW-OBS-001, IW-TEL-001
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Persist request attempt facts linked prompt→route→deployment→GPU with TTFT/prefill/decode/cache/resource/power outcome.

**Required tests:**
- correlation completeness
- cancel/preemption facts
- no prompt body in metrics
- AC-STREAM-01..08: useful-output/prefill timeout separation, distinct failure codes, cross-hop correlation, bounded authenticated diagnostics and admission isolation (contracts/inference-stream-reliability.json)
- MI-01 separate transport/attempt/logical/task outcomes and denominators through retries, cancellation and missing data
- MI-03 SLO-qualified observed capacity bins reject sparse, mismatched and extrapolated load; unknown users remain unknown
- AC-OBS-01..05: idempotent event lineage, distinct attempts, timing provenance and read-only context offers never grant admission
- AC-REQOBS-01..06/08: terminal ingress/attempt/hop identity, immutable replay, HTTP200 stream failures, missing values and monotonic engine/proxy provenance remain bounded and content-free
- AC-REQOBS-09: bounded failure companion conserves status marginals and correlated timeout phases with exact-parent fingerprint, atomic three-resolution revision/seal/prune, persistent late-ingest fence and per-cell privacy evidence
- AC-PRIVATEOBS-01..06: private gateway-authenticated bounded durable ingest, operator snapshot reads, independent capture coverage and default-off paired generator/sealing gate (contracts/private-observability.json)

### P1-T20A — GPU/runtime watchdog detection and incident classification
**Context:** `C75`
**Depends on:** P1-T05, P1-T06, P1-T20
**Features:** IW-WATCH-001
**Read:** specs/31_RESOURCE_HEALTH_QUARANTINE.md, specs/36_GPU_WATCHDOG_RESCUE.md

**Outcome:** Node watchdog detects bounded GPU/backend/container/correctness incidents, drains uncertain resources and writes correlated lifecycle/telemetry events before further admission.

**Required tests:**
- GPU reset fixture removes route eligibility
- OOM-below-envelope incident
- backend hung/stuck request
- restart-loop counter
- unsupported sensor not treated as zero

### P1-T20B — Bounded rescue ladder and automatic profile rollback
**Context:** `C85`
**Depends on:** P1-T20A, P1-T12
**Features:** IW-WATCH-002
**Read:** specs/12_MODEL_TUNING_BENCHMARKS.md, specs/36_GPU_WATCHDOG_RESCUE.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** Watchdog performs least-destructive bounded rescue: request cleanup, backend restart, known-good profile rollback, Docker runtime recreation, optional policy-gated device recovery, then quarantine.

**Required tests:**
- soft restart success
- automatic rollback trigger matrix
- previous image/model/env/cache preserved until success
- Docker runtime recreate
- bounded retry ends quarantine
- no automatic host reboot default

### P1-T20C — Discovered device inventory and requalification on change
**Context:** `C75`
**Depends on:** P1-T20A, P1-T04
**Features:** IW-WATCH-004
**Read:** specs/26_RESOURCE_IDENTITY_REDISCOVERY.md, specs/36_GPU_WATCHDOG_RESCUE.md

**Outcome:** Expected device inventory is derived from discovery and versioned with the hardware fingerprint; a device count or identity change triggers a new host generation and requalification instead of a permanent degraded state.

**Required tests:**
- node with fewer cards requalifies rather than degrading permanently
- device change creates a new host generation
- context ceiling re-derived for the new generation
- no silent CPU fallback on missing devices

**Notes:** A hard-coded expected device count cannot survive a rebuild.

### P1-T21 — Live Next.js cluster/GPU/request dashboard
**Context:** `C75`
**Depends on:** P0-T09, P1-T09, P1-T20
**Features:** IW-UI-001
**Read:** specs/10_DASHBOARD_PORTAL.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md, openapi/model-intelligence.yaml

**Outcome:** Display live nodes, GPUs, models, seats/context/KV, requests, route state and freshness.

**Required tests:**
- UI E2E with deterministic fixtures
- stale telemetry visible
- no misleading pooled VRAM totals
- MI-06 existing routes/actions/permissions and pause/focus preferences survive desktop/tablet/mobile and theme checks
- MI-06 live/empty/error/unsupported provenance, accessible filters/exports and source/dist parity
- AC-OBS-03..05: stale/unowned capacity is unavailable; CPU entitlement, idle GPUs, per-card VRAM and shared-pool context offers remain separate

### P1-T21A — Machine-checked presentation policy
**Context:** `C65`
**Depends on:** P1-T21
**Features:** IW-UI-003
**Read:** specs/10_DASHBOARD_PORTAL.md

**Outcome:** A policy maps every route to required rendering variants — narrow, forced-colors, reduced-motion, wired or fixture, unsupported — names the single token source, and denies superseded components, enforced by the build.

**Required tests:**
- route absent from the policy fails the check
- each declared variant is exercised per route
- a colour outside the token source fails
- a denylisted component reappearing fails

**Notes:** Accessibility stated only in prose regresses at the first route added under deadline.

### P1-T22 — `init gateway` production container flow
**Context:** `C85`
**Depends on:** P0-T07, P1-T02, P1-T21
**Features:** IW-BOOT-002, IW-BOOT-003, IW-DEPLOY-001
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** Fresh host can initialize gateway/web/Postgres/MCP-placeholder/telemetry stack, bootstrap admin/enrollment and verify health.

**Required tests:**
- fresh VM/container E2E
- second init idempotent
- secret permissions

### P1-T23 — `init node` production container flow
**Context:** `C85`
**Depends on:** P0-T07, P1-T02, P1-T04, P1-T17
**Features:** IW-BOOT-002, IW-BOOT-003, IW-NODE-002, IW-DEPLOY-001
**Read:** specs/20_NODE_AUTOCONFIG_DISCOVERY.md, specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** Fresh GPU host probes, enrolls, generates device-safe container config, connects, smoke-tests and displays stable IDs.

**Required tests:**
- AMD real/simulated fixture
- NVIDIA fixture
- idempotent re-init
- wrong GPU exposure blocked

### P1-T24 — Two heterogeneous real-node vertical-slice E2E
**Context:** `C95`
**Depends on:** P1-T19, P1-T20, P1-T21, P1-T22, P1-T23, P1-T20B
**Features:** IW-CORE-001, IW-DP-003, IW-PROMPT-001
**Read:** specs/00_INVARIANTS.md, specs/02_PROTOCOL_AND_API.md, specs/04_CAPACITY_ADMISSION_SEATS.md, specs/05_ROUTING_AFFINITY.md, specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** A real client submits a prompt, gateway routes, proxy streams directly from one of two heterogeneous GPU nodes, telemetry/prompt facts persist.

**Required tests:**
- full E2E
- model mismatch
- context pressure
- direct path byte assertion

### P1-T25 — Phase-1 soak, failure injection and independent review
**Context:** `C100`
**Depends on:** P1-T24, P1-T20B
**Features:** gate/review
**Read:** specs/00_INVARIANTS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/09_OBSERVABILITY_RECEIPTS.md, specs/16_SECURITY_PRIVACY_TRUST.md, specs/22_PROMPT_LEDGER.md, decisions/2026-09-28-buffered-gateway-recording.md

**Outcome:** Multi-hour mixed workload validates cancellation, node loss, stale telemetry, bounded recorder loss, durable-ingest acknowledgement and direct-path invariants.

**Required tests:**
- soak
- node crash
- gateway restart
- Postgres hiccup
- review requirement matrix
- blocked recorder sink does not delay admission or change serving health
- buffer overflow exposes bounded loss and crash-loss uncertainty
- explicit durable ingest fails closed when storage is unavailable

**Notes:** Review-only plus defect fixes; no Phase 2 features.

## Phase 2 — Benchmark-Driven Private Alpha

### P2-T01 — Benchmark campaign/sample schemas and workload contracts
**Context:** `C75`
**Depends on:** P1-T25
**Features:** IW-BENCH-002, IW-WORK-001
**Read:** specs/12_MODEL_TUNING_BENCHMARKS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md

**Outcome:** Define versioned benchmark campaign/run/sample and workload scheduling contracts.

**Required tests:**
- schema roundtrip
- versioned suite identifiers
- duration/deadline validation

### P2-T02 — Node benchmark runner and profile capture
**Context:** `C80`
**Depends on:** P2-T01, P1-T06, P1-T20
**Features:** IW-TUNE-001
**Read:** specs/12_MODEL_TUNING_BENCHMARKS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** Run deterministic TTFT/prefill/decode/concurrency/context/cache/power benchmarks and persist exact launch profile.

**Required tests:**
- cold/warm/cache cases
- timeout/cleanup
- profile fingerprint

### P2-T03 — Global benchmark warehouse and rollups
**Context:** `C75`
**Depends on:** P2-T02
**Features:** IW-BENCH-002
**Read:** specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md, openapi/model-intelligence.yaml

**Outcome:** Persist raw samples and dimensioned rollups by exact GPU/runtime/model/context/concurrency/settings fingerprint.

**Required tests:**
- partition/rollup correctness
- no universal TPS aggregation
- retention test
- MI-05 additive nullable facts and bounded query/rollup coverage preserve unknown historical values
- MI-05 every analytics route rejects missing/invalid operator identity and tenant-header escalation; shared reports redact private data
- AC-OBS-06: bounded content-free new-family-only 90-day aggregate/7-day diagnostic retention preserves source and coverage without purging legacy records or shared backups
- AC-REQOBS-01/06..08: exact-dimension dataset-separated fixed-bin rollups preserve counts, ratios, coverage, replay/seal identity and new-family-only retention
- AC-REQOBS-09: bounded failure companion conserves status marginals and correlated timeout phases with exact-parent fingerprint, atomic three-resolution revision/seal/prune, persistent late-ingest fence and per-cell privacy evidence
- AC-PRIVATEOBS-01..06: private gateway-authenticated bounded durable ingest, operator snapshot reads, independent capture coverage and default-off paired generator/sealing gate (contracts/private-observability.json)

### P2-T04 — Model candidate registry and feasibility filter
**Context:** `C70`
**Depends on:** P2-T03
**Features:** IW-REC-001
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Register immutable model/runtime/deployment candidates and statically reject impossible hardware/policy combinations.

**Required tests:**
- VRAM/context feasibility
- runtime support
- license/policy filters

### P2-T05 — Quality evaluation adapters
**Context:** `C75`
**Depends on:** P2-T04
**Features:** IW-REC-001
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Versioned adapters record dataset/task/scorer versions and quality results without conflating performance.

**Required tests:**
- deterministic fixture scorer
- dataset revision persistence
- failure classification
- MI-04 versioned task-family evaluation retains direction, provenance, sample confidence and separate production feedback
- AC-MI-08 incomplete, failed, skipped and invalid-score cohorts never pass quality

### P2-T06 — Pi/AutoSpec real-workflow replay benchmark
**Context:** `C90`
**Depends on:** P2-T05
**Features:** IW-REC-003, IW-AUTOSPEC-001
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md, specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Replay representative planning/implementation/review/test/tool workflows and score task success/time/tokens/iterations/reviewer quality.

**Required tests:**
- deterministic repo fixture
- compile/test outcome capture
- independent reviewer record

### P2-T07 — Recommendation engine and evidence classes
**Context:** `C85`
**Depends on:** P2-T03, P2-T05, P2-T06
**Features:** IW-REC-001, IW-REC-002
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Produce workload-specific recommendations with measured_exact/equivalent/observed/predicted confidence and reproducible evidence.

**Required tests:**
- predicted never labeled measured
- exact evidence reconstruction
- confidence downgrade
- MI-04 recommendation-only default and evidence-gated shadow/canary/opt-in promotion/rollback reject skipped stages
- AC-MI-08 per-card reserve, exact physical GPU set and checked-memory arithmetic

### P2-T08 — Pareto frontier and next-experiment selection
**Context:** `C75`
**Depends on:** P2-T07
**Features:** IW-REC-002
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Maintain multi-objective Pareto frontier and select high-value uncertain benchmark experiments.

**Required tests:**
- domination tests
- missing evidence priority
- no single-score hidden override
- MI-04 Pareto filtering rejects unknown/unavailable owned hardware and compares equal task/workload/SLO evidence

### P2-T09 — Requalification and regression gates
**Context:** `C75`
**Depends on:** P2-T07, P1-T04
**Features:** IW-TUNE-001, IW-REC-002
**Read:** specs/12_MODEL_TUNING_BENCHMARKS.md, specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Material hardware/software/model/settings changes invalidate/downgrade evidence and trigger smoke/full requalification.

**Required tests:**
- driver change
- model hash change
- settings change
- stable exact match reuse

### P2-T10 — Resource lifecycle event log
**Context:** `C65`
**Depends on:** P2-T01, P1-T20
**Features:** IW-EVENT-001
**Read:** specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Persist append-oriented resource/allocation/deployment/health lifecycle events with correlation IDs.

**Required tests:**
- state transition history
- append/idempotency
- query timeline
- MI-01 time-weighted availability preserves unknown/no-demand intervals and links preemption/recovery to logical requests and GPU hours

### P2-T11 — Owner priority/reclaim/preemption
**Context:** `C80`
**Depends on:** P2-T01, P1-T12, P2-T10
**Features:** IW-QOS-002
**Read:** specs/07_FAIRSHARE_OWNER_PRIORITY.md, specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md

**Outcome:** Owner demand stops shared admissions and drains/preempts interruptible borrowed work until owner service is restored.

**Required tests:**
- owner always wins property
- non-owner cannot claim owner
- preemption telemetry

### P2-T12 — Hierarchical FairShare and anti-gaming
**Context:** `C85`
**Depends on:** P2-T11
**Features:** IW-QOS-001
**Read:** specs/07_FAIRSHARE_OWNER_PRIORITY.md

**Outcome:** Implement org/team/user/app/key/session hierarchy, minimums/weights/borrowing/wait fairness and stable-parent anti-fanout.

**Required tests:**
- fanout gaming test
- borrowing/reclaim
- starvation bound
- shadow simulation

### P2-T13 — API keys and routing preference policy
**Context:** `C70`
**Depends on:** P0-T11, P2-T12
**Features:** gate/review
**Read:** specs/02_PROTOCOL_AND_API.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Issue scoped API keys and persist hard/soft routing preferences with explicit fallback permissions.

**Required tests:**
- scope enforcement
- hard preference failure
- fallback disclosure

### P2-T14 — Route preview and explainability
**Context:** `C70`
**Depends on:** P2-T13, P1-T15, P2-T07
**Features:** IW-ROUTE-001, IW-REC-001
**Read:** specs/05_ROUTING_AFFINITY.md, specs/10_DASHBOARD_PORTAL.md

**Outcome:** Preview candidate eligibility/scores/recommendation/fallback reasons without consuming a serving lease.

**Required tests:**
- explanation reconstructs decision
- privacy-safe reason data
- no hidden hard relaxation

### P2-T15 — Thin AutoSpec/Pi client integration
**Context:** `C80`
**Depends on:** P2-T13, P1-T17, P2-T06
**Features:** IW-AUTOSPEC-001
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md

**Outcome:** Expose stable task/session/workload IDs, local-proxy routing, cancellation, workload hints and telemetry correlation to Pi/AutoSpec.

**Required tests:**
- session affinity
- cancel release
- workload class mapping
- prompt correlation

### P2-T16 — Internal deterministic contribution/usage ledger
**Context:** `C70`
**Depends on:** P1-T20, P2-T12
**Features:** IW-ECON-001
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/18_SOLANA_DEV_ACCOUNTING.md, specs/58_MODEL_INTELLIGENCE_UI_COHESION.md

**Outcome:** Record verified useful-work facts independent of any blockchain; no prompt bodies in receipts.

**Required tests:**
- reconciliation
- duplicate prevention
- content-free records
- MI-02 nested cache/reasoning usage, overlap, zero/missing fields and retries preserve exclusive/logical/billed/physical accounting
- MI-02 versioned fixed-point rates and unique GPU allocation conserve attribution; missing rates and zero successes remain unknown

### P2-T17 — Public-safe signed snapshot builder
**Context:** `C70`
**Depends on:** P2-T03, P2-T16
**Features:** gate/review
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/10_DASHBOARD_PORTAL.md

**Outcome:** Build freshness-aware signed aggregate network snapshots without private addresses/users/prompts.

**Required tests:**
- privacy fixture
- stale state
- signature verify

### P2-T18 — Next.js GPU/benchmark/recommendation explorer
**Context:** `C80`
**Depends on:** P2-T03, P2-T07, P2-T09
**Features:** IW-UI-002
**Read:** specs/10_DASHBOARD_PORTAL.md, specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Filter exact fingerprints, compare benchmark distributions/Pareto recommendations and show confidence/regressions.

**Required tests:**
- UI E2E
- measured/predicted labels
- dimension filters
- AC-OBS-07: public GPU profiles use existing Next.js apps/web with private-field redaction, sparse-cohort suppression and context/fingerprint provenance

### P2-T19 — Resumable benchmark DAG core
**Context:** `C75`
**Depends on:** P2-T02, P2-T08
**Features:** IW-BENCH-003
**Read:** specs/33_RESUMABLE_BENCHMARK_DAG.md

**Outcome:** Break campaigns into immutable leaseable leaves whose completed samples survive worker loss/preemption.

**Required tests:**
- lease expiry/reschedule
- completed leaf not rerun
- partial confidence

### P2-T20 — Cluster simulator protocol skeleton
**Context:** `C85`
**Depends on:** P1-T25, P2-T10
**Features:** IW-SIM-001
**Read:** specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** Synthetic nodes use real protocol to simulate identities/capacity/latency/churn with deterministic seeds.

**Required tests:**
- 1k join smoke
- reproducible seed
- stale lease invariant

### P2-T21 — 10k churn/chaos scenarios and invariant checks
**Context:** `C95`
**Depends on:** P2-T20, P2-T12, P2-T19
**Features:** IW-SIM-001
**Read:** specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** Exercise 10k ephemeral workers, mass expiry, duplicate identities, cache storms, failures and demand shifts.

**Required tests:**
- 10k scenario
- mass disconnect
- duplicate authoritative lease prevention
- bounded queues

### P2-T22 — Phase-2 private-alpha review and qualification
**Context:** `C100`
**Depends on:** P2-T07, P2-T12, P2-T15, P2-T18, P2-T19, P2-T21
**Features:** gate/review
**Read:** specs/12_MODEL_TUNING_BENCHMARKS.md, specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md, specs/07_FAIRSHARE_OWNER_PRIORITY.md

**Outcome:** Independent review verifies recommendations are evidence-based, owner/FairShare correct, AutoSpec works and simulator covers invariants.

**Required tests:**
- full private-alpha E2E
- benchmark reproducibility
- requirement coverage review

**Notes:** Review-only; fix defects before Phase 3.

## Phase 3 — Sites / Slurm / Operations

### P3-T01 — Persistent site connector identity and control channel
**Context:** `C75`
**Depends on:** P2-T22, P1-T03
**Features:** IW-SITE-001
**Read:** specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md

**Outcome:** Implement persistent non-GPU site connector with provider/cluster identity and resilient control connection.

**Required tests:**
- restart/reconnect
- multi-connector instance IDs
- zero-GPU site

### P3-T02 — Hierarchical content-addressed artifact cache
**Context:** `C85`
**Depends on:** P3-T01, P1-T06
**Features:** IW-CACHE-001
**Read:** specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md

**Outcome:** Implement immutable digest inventory, resumable fetch, verification, corruption quarantine and host/site/upstream lookup.

**Required tests:**
- partial resume
- hash mismatch
- eviction/disk pressure
- no gateway byte path by default

### P3-T03 — Gateway desired-deployment assignment negotiation
**Context:** `C80`
**Depends on:** P3-T02, P2-T07
**Features:** IW-SLURM-003
**Read:** specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md

**Outcome:** Worker offers resources/cache/lifetime; gateway assigns immutable deployment; worker estimates/accepts/rejects and reports warm readiness.

**Required tests:**
- short lifetime rejection
- cache-aware assignment
- failed warm rollback

### P3-T04 — Generic external scheduler adapter
**Context:** `C70`
**Depends on:** P3-T01
**Features:** IW-SCHED-001
**Read:** specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md

**Outcome:** Define scheduler-neutral allocation/resource lifecycle interface; Slurm-specific logic stays behind adapter.

**Required tests:**
- fake scheduler adapter
- allocation lifecycle contract
- no core Slurm types leak

### P3-T05 — Slurm allocation identity and worker registration
**Context:** `C85`
**Depends on:** P3-T04, P1-T01, P3-T01
**Features:** IW-SLURM-001, IW-SLURM-002
**Read:** specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md

**Outcome:** Allocation-scoped worker exposes only allocated GPUs and resolves stable host/GPU history plus temporary allocation/worker IDs.

**Required tests:**
- same GPU later same stable ID
- replacement GPU new generation
- array/requeue identity
- allocated-only GPU visibility

### P3-T06 — Slurm deadline/preemption drain
**Context:** `C75`
**Depends on:** P3-T05, P3-T03, P2-T01
**Features:** IW-SLURM-004
**Read:** specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md

**Outcome:** Reservation expiry/signals transition to DRAINING, stop admission, flush telemetry/results and disconnect cleanly.

**Required tests:**
- preemption signal
- normal expiry not fault
- deadline-aware no-new-session

### P3-T07 — Slurm opportunistic benchmark execution
**Context:** `C75`
**Depends on:** P3-T06, P2-T19, P2-T08
**Features:** IW-SLURM-005
**Read:** specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/33_RESUMABLE_BENCHMARK_DAG.md

**Outcome:** Spare allocation time executes recommended benchmark leaves that fit remaining safe lifetime.

**Required tests:**
- preempt/resume
- setup+case time budget
- completed leaves retained

### P3-T08 — Site relay and direct-connect integration
**Context:** `C80`
**Depends on:** P3-T01, P1-T18
**Features:** IW-DP-002, IW-SITE-001
**Read:** specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md, specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Site connector serves rendezvous/relay fallback before regional/gateway relay while preserving direct preference.

**Required tests:**
- HPC no-inbound fixture
- fallback order
- byte accounting

### P3-T09 — `init site` and Slurm discovery
**Context:** `C85`
**Depends on:** P0-T07, P3-T01, P3-T04
**Features:** IW-BOOT-002, IW-SITE-001, IW-DEPLOY-001
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md, specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** CLI detects Slurm/cluster/shared cache/network and installs persistent connector safely.

**Required tests:**
- Slurm fixture
- no-Slurm blocker
- idempotent init
- shared path permissions

### P3-T10 — `init slurm-worker` allocation-scoped flow
**Context:** `C80`
**Depends on:** P3-T05, P3-T06, P3-T09
**Features:** IW-SLURM-001, IW-BOOT-002, IW-DEPLOY-002
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** One command inside a Slurm allocation launches the worker/runtime under Apptainer, obtains short-lived credentials, registers only allocated GPUs, receives deployment, serves/benchmarks and drains without Docker.

**Required tests:**
- allocation E2E
- credential expiry
- requeue/restart

### P3-T11 — Edge node role and container init
**Context:** `C75`
**Depends on:** P1-T18, P3-T02, P0-T07
**Features:** IW-BOOT-002, IW-DEPLOY-001
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md, specs/37_CONTAINER_DEPLOYMENT_STANDARD.md

**Outcome:** `init edge` composes approved relay/cache/rendezvous/API-edge capabilities without requiring GPU.

**Required tests:**
- capability combinations
- no accidental GPU dependency
- idempotent init

### P3-T12 — PromptStore object-storage tiering
**Context:** `C75`
**Depends on:** P1-T07, P2-T22
**Features:** IW-PROMPT-002
**Read:** specs/34_PROMPT_STORE_TIERING.md

**Outcome:** Large encrypted prompt payloads can live in object storage while PostgreSQL retains authoritative metadata/locator/hash/audit.

**Required tests:**
- inline→object threshold
- object unavailable submission semantics
- authorized short-lived read

### P3-T13 — Resource health baseline and degradation detector
**Context:** `C80`
**Depends on:** P2-T03, P2-T10
**Features:** IW-HEALTH-001
**Read:** specs/31_RESOURCE_HEALTH_QUARANTINE.md

**Outcome:** Compare each GPU against own history and peer-class exact fingerprints using robust minimum-sample rules.

**Required tests:**
- single outlier ignored
- sustained regression detected
- unlike workload excluded

### P3-T14 — Quarantine, diagnostics and recovery canaries
**Context:** `C75`
**Depends on:** P3-T13, P2-T09
**Features:** IW-HEALTH-001
**Read:** specs/31_RESOURCE_HEALTH_QUARANTINE.md

**Outcome:** Implement HEALTHY→SUSPECT→DEGRADED→DIAGNOSTIC→QUARANTINED→RECOVERING state and bounded recovery qualification.

**Required tests:**
- quarantine no shared traffic
- canary recovery
- owner warning

### P3-T15 — Demand forecasting and explainable pre-staging
**Context:** `C75`
**Depends on:** P2-T07, P3-T02, P3-T03
**Features:** IW-FORECAST-001
**Read:** specs/32_DEMAND_FORECASTING_PRESTAGING.md

**Outcome:** Transparent seasonal/window demand forecasts drive artifact pre-stage/residency suggestions without overriding hard constraints.

**Required tests:**
- forecast reproducibility
- hard constraint precedence
- explanation record

### P3-T16 — Control-plane MCP read server
**Context:** `C80`
**Depends on:** P2-T14, P2-T18, P0-T11
**Features:** IW-MCP-001
**Read:** specs/29_MCP_SERVERS.md

**Outcome:** Expose typed authenticated read resources/tools for cluster, GPU, model, routes, benchmarks, capacity, health and history.

**Required tests:**
- scope enforcement
- stateless instance test
- schema discovery
- no generic shell

### P3-T17 — Local node/site diagnostic MCP
**Context:** `C75`
**Depends on:** P3-T16, P0-T04, P3-T01
**Features:** IW-MCP-002
**Read:** specs/29_MCP_SERVERS.md

**Outcome:** Local MCP exposes bounded host/GPU/runtime/cache/connectivity diagnostics backed by canonical probe APIs.

**Required tests:**
- local-only binding default
- secret redaction
- typed diagnostics

### P3-T18 — MCP controlled operations and audit
**Context:** `C75`
**Depends on:** P3-T16, P3-T17
**Features:** IW-MCP-001, IW-MCP-002
**Read:** specs/29_MCP_SERVERS.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Add scoped enrollment/reprobe/deployment/drain/benchmark actions with audit and no unrestricted host execution.

**Required tests:**
- unauthorized mutation
- audit trail
- prompt content scope

### P3-T18A — Watchdog operator rescue via CLI/dashboard/MCP
**Context:** `C80`
**Depends on:** P1-T20B, P3-T14, P3-T18
**Features:** IW-WATCH-003
**Read:** specs/10_DASHBOARD_PORTAL.md, specs/29_MCP_SERVERS.md, specs/36_GPU_WATCHDOG_RESCUE.md

**Outcome:** Authorized operators can inspect incident history, diagnose, request bounded rescue/rollback/recreate/quarantine and verify recovery through CLI, Next.js and typed MCP tools.

**Required tests:**
- read-only status scope
- destructive rescue authorization
- audit record
- quarantine UI
- MCP cannot expose arbitrary host control

### P3-T19 — AI copy/paste installer acceptance flow
**Context:** `C90`
**Depends on:** P1-T22, P1-T23, P3-T09, P3-T11, P3-T16, P3-T18A
**Features:** IW-BOOT-001, IW-BOOT-002, IW-BOOT-004
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/29_MCP_SERVERS.md

**Outcome:** A shell-capable AI can follow docs/AI_INSTALL_INFERWEAVE.md and complete gateway/node/site/edge setup using only structured CLI operations.

**Required tests:**
- clean VM scripted acceptance
- no secret in transcript
- blocking issue explanation

### P3-T20 — Update/backup/restore operational lifecycle
**Context:** `C80`
**Depends on:** P3-T19, P3-T12
**Features:** gate/review
**Read:** specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Implement signed update plan, DB compatibility check, backup/checkpoint, verification and supported rollback/restore.

**Required tests:**
- failed update rollback
- backup restore
- version skew detection

### P3-T21 — Production Slurm/site E2E and reconnect history
**Context:** `C95`
**Depends on:** P3-T07, P3-T08, P3-T10, P3-T14
**Features:** IW-SLURM-001, IW-SLURM-002, IW-SLURM-003, IW-SLURM-004, IW-SLURM-005
**Read:** specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md, specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md

**Outcome:** Same physical Slurm GPU appears across multiple reservations, reuses history/cache/recommendation, serves/benchmarks, drains and reconnects safely.

**Required tests:**
- multi-allocation E2E
- software change requalifies
- cache reuse
- preemption

### P3-T23 — Per-GPU claims, per-model dwell and availability floor in the autoscaler
**Context:** `C75`
**Depends on:** P3-T03, P1-T06C
**Features:** IW-SCHED-002
**Read:** specs/43_GPU_PLACEMENT_HOT_SWAP.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/05_ROUTING_AFFINITY.md, specs/00_INVARIANTS.md

**Outcome:** The autoscaler claims individual GPUs, rebalances one GPU per decision, holds each GPU for its model's dwell (configured, or max(300 s, 10 x measured p95 load)), never chooses a donor that would breach a model's healthy-instance floor or whose load cost is unmeasured, and persists loaded_at and swap intent on the claim.

**Required tests:**
- GPU inside dwell is never a donor and restart cannot shorten dwell
- derived dwell and per-model override
- model without measured load time is never a donor
- property: no decision sequence breaches an availability floor
- model at floor is freed only after another instance is healthy
- GpuDwell, AvailabilityFloor and UnmeasuredLoadCost holds carry their numbers
- existing autoscaler invariants still hold

### P3-T24 — Node GPU swap executor: drain, pinned load, rollback
**Context:** `C80`
**Depends on:** P3-T23, P3-T06, P3-T14
**Features:** IW-SCHED-002
**Read:** specs/43_GPU_PLACEMENT_HOT_SWAP.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/36_GPU_WATCHDOG_RESCUE.md, specs/31_RESOURCE_HEALTH_QUARANTINE.md, specs/39_INFERENCE_RUNTIME_TUNING.md

**Outcome:** A node executes a GPU swap from persisted intent: drain with a bounded per-model deadline and INSTANCE_DRAINED cancellation, unload, load with every runtime component pinned to the claimed GPU and verified from device memory accounting, warm through the real admission path, and roll back or quarantine on failure, with runtime on-demand loading and eviction disabled.

**Required tests:**
- request within drain deadline completes before unload
- request past drain deadline receives retryable 503 INSTANCE_DRAINED
- failed load rolls back to the previous deployment and records a start failure
- OOM on load is classified and not retried into the same placement
- executor killed during STARTING resumes from persisted intent
- weights, drafter and projector allocated on the claimed GPU
- request for an unloaded model is refused and evicts nothing

### P3-T25 — GPU hot-swap conformance and live-load swap evidence
**Context:** `C75`
**Depends on:** P3-T24
**Features:** IW-SCHED-002
**Read:** specs/43_GPU_PLACEMENT_HOT_SWAP.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/09_OBSERVABILITY_RECEIPTS.md

**Outcome:** A multi-GPU node under live load swaps a GPU to a second instance of another model while the donor model stays above its floor elsewhere, and the recorded decision and phase events show no sample where any model's healthy instances fell below its floor.

**Required tests:**
- live swap under load keeps every model at or above its floor at every sample
- every swap decision and phase event is recorded with swap ID
- measured load duration updates p95 used for derived dwell

### P3-T22 — Phase-3 operational/security review
**Context:** `C100`
**Depends on:** P3-T21, P3-T19, P3-T20, P3-T18A, P3-T25
**Features:** gate/review
**Read:** specs/16_SECURITY_PRIVACY_TRUST.md, specs/28_BOOTSTRAP_INIT_CLIENT.md, specs/29_MCP_SERVERS.md

**Outcome:** Independent review verifies enrollment, containers, MCP scopes, Slurm lifecycle, caches, prompt tiering and operational recovery.

**Required tests:**
- security negative tests
- fresh installs
- Slurm/site soak
- requirement review

**Notes:** Review-only.

## Phase 4 — Workbench / Tools / Capabilities

### P4-T01 — Durable async job/event/lease state machine
**Context:** `C75`
**Depends on:** P3-T22
**Features:** IW-JOB-001
**Read:** specs/15_ASYNC_JOBS_ARTIFACTS.md

**Outcome:** Implement restart-safe durable job lifecycle, idempotency, leases/fencing, cancellation and sequenced events.

**Required tests:**
- restart recovery
- duplicate submit
- lease fencing
- cancel

### P4-T02 — Artifact metadata/grants and direct transfer
**Context:** `C75`
**Depends on:** P4-T01, P3-T02
**Features:** IW-JOB-001
**Read:** specs/15_ASYNC_JOBS_ARTIFACTS.md, specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Manage checksummed artifacts and short-lived grants while keeping large bytes off gateway path.

**Required tests:**
- resumable transfer
- checksum failure
- grant expiry

### P4-T03 — Workbench session/history core
**Context:** `C80`
**Depends on:** P4-T01, P2-T15
**Features:** IW-WB-001
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md

**Outcome:** Next.js Workbench stores persistent conversations/session metadata and attaches/resumes without owning Pi execution.

**Required tests:**
- session persist/resume
- tenant isolation
- route metadata display

### P4-T04 — Workbench fork/split/files/rendering
**Context:** `C80`
**Depends on:** P4-T03, P4-T02
**Features:** IW-WB-001
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md

**Outcome:** Implement branch/fork, artifact/file views and safe Markdown/HTML/YAML/XML/JSON/code rendering/download.

**Required tests:**
- fork lineage
- unsafe HTML sandboxing
- large file behavior

### P4-T05 — Workbench coding/review and tool UX
**Context:** `C85`
**Depends on:** P4-T04, P3-T16
**Features:** IW-WB-001, IW-TOOL-001
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md, specs/29_MCP_SERVERS.md

**Outcome:** Display diffs/reviews/context/capacity and permission-aware MCP/tool catalog/invocation.

**Required tests:**
- permission prompts
- tool result provenance
- diff rendering

### P4-T06 — CI/build history and Pi review records
**Context:** `C80`
**Depends on:** P2-T15, P4-T03
**Features:** IW-CI-001
**Read:** specs/19_CI_CD_LIVING_SPECS.md

**Outcome:** Persist builds, current/history/logs/tests/coverage/artifacts/Pi reviews/requirement mappings/changelog/spec evolution.

**Required tests:**
- build ingestion
- history UI
- review provenance

### P4-T07 — Agentic RAG retrieval contracts and provenance
**Context:** `C85`
**Depends on:** P4-T01, P2-T15
**Features:** IW-RAG-001
**Read:** specs/13_RAG_TOOLS_LSP.md

**Outcome:** Implement versioned retrieval bundles across lexical/vector/symbol/files/git/docs with provenance/confidence/tenant isolation.

**Required tests:**
- tenant isolation
- provenance completeness
- deterministic context bundle

### P4-T08 — LSP/MCP/tool capability broker
**Context:** `C80`
**Depends on:** P4-T07, P3-T16
**Features:** IW-LSP-001, IW-TOOL-001
**Read:** specs/13_RAG_TOOLS_LSP.md

**Outcome:** Broker self-hosted LSP and typed tool capabilities separately from LLM serving; no arbitrary public shell.

**Required tests:**
- capability discovery
- permission isolation
- LSP lifecycle

### P4-T09 — Embeddings/rerank/vision deployment capabilities
**Context:** `C80`
**Depends on:** P1-T06, P4-T07
**Features:** gate/review
**Read:** specs/13_RAG_TOOLS_LSP.md, specs/02_PROTOCOL_AND_API.md

**Outcome:** Extend immutable deployment/capacity/routing model to embeddings, rerank and vision capabilities.

**Required tests:**
- capability routing
- model mismatch
- resource accounting

### P4-T10 — Image deployment manifests and compatible/native APIs
**Context:** `C85`
**Depends on:** P4-T01, P4-T09
**Features:** IW-IMG-001
**Read:** specs/14_IMAGE_GENERATION.md

**Outcome:** Implement immutable full image pipeline deployment, compatible images endpoint and durable native async job API.

**Required tests:**
- manifest pinning
- job restart
- policy/license routing

### P4-T11 — Image direct artifact data plane and resource accounting
**Context:** `C80`
**Depends on:** P4-T10, P4-T02
**Features:** IW-IMG-001
**Read:** specs/14_IMAGE_GENERATION.md, specs/15_ASYNC_JOBS_ARTIFACTS.md

**Outcome:** Input/output image bytes use direct/object/regional path; accounting uses pixels/steps/GPU time/energy.

**Required tests:**
- gateway bypass
- cancel
- artifact checksum/provenance

### P4-T12 — Deterministic technical annotation + vision QA
**Context:** `C85`
**Depends on:** P4-T11
**Features:** IW-IMG-002
**Read:** specs/14_IMAGE_GENERATION.md

**Outcome:** Two-stage generation→grounding/segmentation→deterministic annotation with exact labels/arrows and QA failure on low confidence.

**Required tests:**
- label spelling
- no clipping/overlap
- low-confidence fail
- seed provenance

### P4-T13 — Optional bounded public playground behind decision gate
**Context:** `C70`
**Depends on:** P4-T05, P4-T12
**Features:** IW-PUBLIC-001
**Read:** specs/10_DASHBOARD_PORTAL.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** If explicitly approved, implement anonymous text-only trial with tight quotas/circuit breakers/owner reserve and no tools/files/images.

**Required tests:**
- global circuit breaker
- abuse limits
- owner reserve

**Notes:** Decision-gated; skip unless D-018 is approved.

### P4-T14 — Phase-4 capability/UX review
**Context:** `C100`
**Depends on:** P4-T06, P4-T08, P4-T12
**Features:** gate/review
**Read:** specs/11_WORKBENCH_AUTOSPEC_PI.md, specs/13_RAG_TOOLS_LSP.md, specs/14_IMAGE_GENERATION.md, specs/19_CI_CD_LIVING_SPECS.md

**Outcome:** Independent review validates Workbench boundaries, jobs/artifacts, tools/RAG, image pipeline and CI living-spec behavior.

**Required tests:**
- E2E Workbench
- tool security
- image 72h mixed soak where hardware available
- spec verification

**Notes:** Review-only.

## Phase 5 — Regional / Federated Production

### P5-T01 — Multi-gateway stateless control services
**Context:** `C85`
**Depends on:** P4-T14
**Features:** IW-SCALE-001
**Read:** specs/17_SCALING_HA_REGIONS.md

**Outcome:** Remove single-instance assumptions from gateway/API/MCP and establish shared state/freshness semantics.

**Required tests:**
- two-gateway failover
- sticky control not required
- concurrent route decisions

### P5-T02 — Regional presence/sharded telemetry ingestion
**Context:** `C85`
**Depends on:** P5-T01, P2-T03
**Features:** IW-SCALE-001
**Read:** specs/17_SCALING_HA_REGIONS.md

**Outcome:** Shard presence/telemetry/snapshot ingestion by region with TTLs, compact deltas and aggregation.

**Required tests:**
- regional partition
- stale expiry
- aggregation correctness

### P5-T03 — Regional relay failover and routing locality
**Context:** `C80`
**Depends on:** P5-T02, P3-T08
**Features:** IW-SCALE-001, IW-DP-002
**Read:** specs/17_SCALING_HA_REGIONS.md, specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Select/health regional relays and fail over without making central gateway the data bottleneck.

**Required tests:**
- relay loss
- WAN locality
- byte ratio SLO

### P5-T04 — Federation/coordinator hierarchy
**Context:** `C85`
**Depends on:** P5-T02
**Features:** IW-FED-001
**Read:** specs/21_FEDERATION_ROLES.md

**Outcome:** Implement provider/intermediate coordinator/subscription gateway/relay hierarchy with no cycles/duplicate accounting.

**Required tests:**
- cycle rejection
- backup parent
- dedup lineage

### P5-T05 — Node/deployment challenge and verification bands
**Context:** `C80`
**Depends on:** P2-T09, P5-T04
**Features:** IW-VERIFY-001
**Read:** specs/16_SECURITY_PRIVACY_TRUST.md, specs/21_FEDERATION_ROLES.md

**Outcome:** Add challenge/verification/reliability bands so self-reported performance alone cannot establish trust.

**Required tests:**
- challenge failure quarantine
- verification expiry
- no prompt disclosure

### P5-T06 — Million-node public snapshot/query scale simulation
**Context:** `C95`
**Depends on:** P5-T02, P2-T21
**Features:** IW-SCALE-001, IW-SIM-001
**Read:** specs/17_SCALING_HA_REGIONS.md, specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** Simulate large sharded presence, faceted pagination/deltas and verify browser/control APIs remain bounded.

**Required tests:**
- 1M synthetic summary test
- pagination/delta correctness
- regional failure

### P5-T07 — Cross-region security/privacy review
**Context:** `C95`
**Depends on:** P5-T03, P5-T05
**Features:** gate/review
**Read:** specs/16_SECURITY_PRIVACY_TRUST.md, specs/17_SCALING_HA_REGIONS.md

**Outcome:** Review credentials, tenant isolation, public snapshots, relay trust and private-address/prompt leakage across regions.

**Required tests:**
- penetration-style negative suite
- privacy fixture
- credential rotation

### P5-T08 — Federated production soak and chaos
**Context:** `C100`
**Depends on:** P5-T04, P5-T06, P5-T07
**Features:** gate/review
**Read:** specs/17_SCALING_HA_REGIONS.md, specs/21_FEDERATION_ROLES.md, specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** Long-running regional/federated chaos validates routing, accounting, direct paths, owner priority and recovery.

**Required tests:**
- multi-region soak
- coordinator failure
- mass churn
- accounting reconciliation

### P5-T09 — Final requirements/spec conformance audit
**Context:** `C100`
**Depends on:** P5-T08
**Features:** gate/review
**Read:** specs/00_INVARIANTS.md

**Outcome:** Map every required feature and acceptance criterion to passing evidence, current docs and operational ownership.

**Required tests:**
- feature registry complete
- AC matrix complete
- no orphan required feature

**Notes:** Independent spec-verifier role.

### P5-T10 — Production-readiness release gate
**Context:** `C100`
**Depends on:** P5-T09
**Features:** gate/review
**Read:** specs/16_SECURITY_PRIVACY_TRUST.md, specs/19_CI_CD_LIVING_SPECS.md, specs/28_BOOTSTRAP_INIT_CLIENT.md

**Outcome:** Produce signed release manifest, deployment docs, backups/rollback, known limitations and go/no-go evidence.

**Required tests:**
- clean install
- upgrade rollback
- disaster restore
- release manifest

## Phase deferred — Deferred

### D-T01 — Optional development settlement adapter
**Context:** `C70`
**Depends on:** P5-T10
**Features:** IW-ECON-002
**Read:** specs/18_SOLANA_DEV_ACCOUNTING.md

**Outcome:** Only after explicit owner reactivation: implement replaceable local/devnet settlement adapter without making inference depend on it.

**Required tests:**
- settlement unavailable inference continues
- no mainnet config

**Notes:** Do not schedule until explicitly reopened.

### P2-T23 — Topology graph model and local gateway export
**Context:** `C80`
**Depends on:** P0-T06, P1-T04, P1-T05
**Features:** IW-TOPO-001, IW-TOPO-002
**Read:** specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** A gateway emits a typed vertex/edge graph of the nodes, child gateways and GPUs it directly knows, keyed on stable resource IDs, with every vertex carrying a complete/partial/unknown horizon and its own snapshot_at and version.

**Required tests:**
- unknown-horizon vertices are not counted as empty
- vertices key on stable IDs, not addresses
- export validates against contracts/topology-graph.example.json
- guard suite runs against a deliberately broken fixture

### P2-T24 — Per-viewer topology redaction
**Context:** `C75`
**Depends on:** P2-T23
**Features:** IW-TOPO-004
**Read:** specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Topology export is rendered per viewer: unauthorized vertices remain present with kind, edges and horizon intact, and their address, hostname and operator identity replaced by a stable per-session opaque handle.

**Required tests:**
- redacted export contains no private address
- redacted export has the same vertex count as the unredacted one
- opaque handles are stable within a session and uncorrelatable across viewers

### P5-T11 — Federated topology composition
**Context:** `C85`
**Depends on:** P2-T23, P5-T04
**Features:** IW-TOPO-003
**Read:** specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/21_FEDERATION_ROLES.md

**Outcome:** Local exports compose into a network view that deduplicates one service reached by several discovery paths, marks cycles without traversing them, resolves conflicting vertices by version rather than arrival order, and carries per-subtree staleness instead of one network-wide timestamp.

**Required tests:**
- two discovery paths to one provider compose to one vertex
- composition over a cyclic graph terminates and marks the cycle
- conflicting exports resolve by version, not arrival order
- composed graph exposes no single network-wide timestamp

### P5-T12 — Topology scale aggregation
**Context:** `C80`
**Depends on:** P5-T11
**Features:** IW-TOPO-005
**Read:** specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/21_FEDERATION_ROLES.md

**Outcome:** Above a configured fan-out a coordinator emits a typed aggregate vertex carrying counts and summed capacity for its subtree, inheriting that subtree's horizon so an aggregate over unknown vertices is never reported complete.

**Required tests:**
- an aggregate over a subtree containing unknown is not complete
- aggregate vertices are distinguishable from leaves by type
- fan-out threshold is honoured

### P5-T13 — Whole-network topology visualization surface
**Context:** `C80`
**Depends on:** P5-T11
**Features:** IW-TOPO-006
**Read:** specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/10_DASHBOARD_PORTAL.md

**Outcome:** Dashboard and CLI render the composed graph from the published contract, showing completeness and staleness rather than hiding them, and never presenting an aggregate or an unknown-horizon vertex as a known leaf.

**Required tests:**
- unknown and complete vertices render distinguishably
- totals are shown with the uncertainty they were computed over
- renderer consumes only the published contract

### P5-T14 — Inter-gateway capacity request protocol
**Context:** `C85`
**Depends on:** P5-T04, P1-T12
**Features:** IW-GRANT-001
**Read:** specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** A gateway can ask a peer for capacity on the control plane without holding the triggering client request: negotiation runs on its own clock, a peer answers or refuses immediately with a spec 06 reason code, and no peer offers capacity it has already granted elsewhere.

**Required tests:**
- client request is not held beyond the spec 06 admission budget while a peer is asked
- a peer with outstanding grants does not offer the same capacity twice
- refusal is immediate and carries a reason code

### P5-T15 — Standby slot grants and lifecycle
**Context:** `C85`
**Depends on:** P5-T14, P1-T11B
**Features:** IW-GRANT-002
**Read:** specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md, specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Granted standby slots are held against the granting site's measured envelope, expire on time since last progress, are revocable with notice under local owner priority, and return to the granting site's envelope on expiry or revocation.

**Required tests:**
- standby offered never exceeds the measured envelope
- expiry is evaluated on time since last progress, not elapsed time
- revocation honours the stated notice and returns slots to the envelope
- routing to an expired grant is rejected

### P5-T16 — Capacity request loop and amplification control
**Context:** `C75`
**Depends on:** P5-T14
**Features:** IW-GRANT-003
**Read:** specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md, specs/21_FEDERATION_ROLES.md

**Outcome:** Capacity requests carry a path vector and hop budget and are bounded by a configured fan-out breadth, so one shortage cannot broadcast across a mesh and a malformed path causes refusal rather than an unbounded walk.

**Required tests:**
- a request whose path already contains the receiver is refused
- a request at hop budget zero is answered or refused, never forwarded
- fan-out never exceeds the configured breadth
- a malformed path vector causes refusal, not traversal

### P5-T17 — Capacity grant receipts and forecast signals
**Context:** `C80`
**Depends on:** P5-T15
**Features:** IW-GRANT-004
**Read:** specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md, specs/09_OBSERVABILITY_RECEIPTS.md, specs/32_DEMAND_FORECASTING_PRESTAGING.md

**Outcome:** Every grant, refusal, revocation and expiry is a receipt carrying path vector, hop budget, envelope offered and accounting lineage, and held/revoked grants feed pre-staging so a site meeting demand by borrowing is visible rather than hidden.

**Required tests:**
- each grant, refusal, revocation and expiry emits a receipt
- receipts carry lineage so one served request bills exactly once
- repeated revocation surfaces as an under-provisioning signal

### P5-T18 — Core protocol data model: canonical identity, artifacts, capabilities, resources, provenance
**Context:** `C80`
**Depends on:** P4-T14
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/02_PROTOCOL_AND_API.md, specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md, specs/16_SECURITY_PRIVACY_TRUST.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md

**Outcome:** Nodes, runtimes and gateways advertise a canonical model identity, artifact identity, capabilities with extensible properties, resource requirements with topology, serving profiles, runtime engine metadata and provenance, where unknown metadata stays explicitly unknown and never forces a missing field into a guessed value.

**Required tests:**
- serialization/deserialization of the full advertisement
- missing optional metadata yields unknown, not rejection
- unknown capability IDs and model types are preserved and forwarded
- capability properties are capability-specific and extensible
- artifact quantization/precision values are preserved without assuming one framework
- topology-sensitive resource requirements distinguish 1x80GB from 4x24GB

### P5-T19 — Core protocol capacity and lifecycle events
**Context:** `C80`
**Depends on:** P5-T18, P3-T23
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/04_CAPACITY_ADMISSION_SEATS.md, specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md, specs/31_RESOURCE_HEALTH_QUARANTINE.md

**Outcome:** Runtimes and deployments advertise timestamped slot/capacity, residency, cold-start, pending capacity and capacity confidence, and emit generic lifecycle, eviction, recovery, scale, rebalance and node-loss events with standard reason codes mapped from infrastructure without exposing the scheduler as a required abstraction.

**Required tests:**
- capacity advertisements are timestamped and change independently of model identity
- model residency distinguishes a free slot on a loaded model from a required download
- lifecycle and eviction events carry standard reason codes with scheduler mapping
- recovery event sequence lets upstream compute recovery time without guessing
- pending capacity never fabricates an ETA when the scheduler cannot provide one
- health probes are classified and do not count as user demand

### P5-T20 — Core protocol metric system and benchmark interchange
**Context:** `C75`
**Depends on:** P5-T18, P2-T04
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md, specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md, specs/09_OBSERVABILITY_RECEIPTS.md

**Outcome:** Performance, quality, reliability and resource-usage telemetry is transported as extensible metric definitions and structured samples with provenance, windows, distributions and counters, and benchmark results use a standard interchange format attributable to the actual artifact and runtime.

**Required tests:**
- metrics use the extensible metric schema, not hard-coded global fields
- metric samples carry source type, producer and confidence
- percentiles (P50/P90/P95/P99) and counters with reset semantics are representable
- benchmark results are attributable to the actual artifact and runtime
- quality evidence transports metrics without a universal intelligence score
- self-reported and observed values coexist without overwriting each other

### P5-T21 — Core protocol federation provenance and reconciliation
**Context:** `C80`
**Depends on:** P5-T19, P5-T04, P5-T14
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/21_FEDERATION_ROLES.md, specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Federated advertisements retain origin gateway/node, trust level and freshness, preserve independent remote deployments instead of collapsing by model_id, mark disconnected capacity stale rather than live, and reconcile on reconnect without duplicate runtime identity or duplicate event replay.

**Required tests:**
- remote deployment provenance and origin are preserved through aggregation
- two gateways advertising the same model_id keep independent deployments, capacity, health and performance
- a remote gateway advertising only model/capabilities/slots participates without artifact or hardware
- disconnected capacity becomes stale/unavailable and is not advertised live
- reconnect reconciles state without duplicate runtime identities or duplicate events
- trust is never auto-promoted by passing through a trusted gateway

### P5-T22 — Core protocol routing, fallback and error semantics
**Context:** `C80`
**Depends on:** P5-T20, P5-T21, P1-T13
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/05_ROUTING_AFFINITY.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/02_PROTOCOL_AND_API.md

**Outcome:** Schedulers and gateways match capability contracts and hard requirements, evaluate resource compatibility, cold-start and reliability signals, resolve aliases and advisory fallbacks, and return structured errors with retryability, while preserving existing OpenAI-compatible behavior and request classification.

**Required tests:**
- hard requirements determine eligibility and preferences only rank
- topology-sensitive resource compatibility is enforced (2x24GB not 1x48GB)
- aliases and fallbacks are advisory and never bind permanently to one deployment
- structured routing reasons and error taxonomy/retryability are transmitted
- request class (user/system/health_probe/benchmark/warmup/internal) is preserved
- older gateways advertising only model/endpoint/slots keep functioning

### P5-T23 — Core protocol conformance and scheduler-agnostic tests
**Context:** `C90`
**Depends on:** P5-T22
**Features:** IW-PROTO-001
**Read:** specs/44_CORE_PROTOCOL.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/42_SITE_GATEWAY_CONFORMANCE.md

**Outcome:** A language-neutral conformance suite proves the generic protocol surfaces Slurm-backed, Docker, manual-worker and remote-gateway runtimes identically, with no upstream logic requiring scheduler fields, and covers the protocol, federation, health-probe, event-recovery and resource-compatibility test scenarios of the core protocol.

**Required tests:**
- Slurm-backed, Docker, manual worker and remote gateway appear through the same generic protocol
- no upstream logic requires Slurm fields
- 100 health probes and 0 user requests yield user demand 0
- capacity 8 to eviction 0 to load to 4 to 8 produces correct events and snapshots
- unknown future types, metrics and events flow through the federation safely
- conformance vectors pass against the frozen protocol vocabulary


### P5-T24 — Protocol v1: versioned wire contract, planes, identity, registration, heartbeat, negotiation
**Context:** `C80`
**Depends on:** P5-T18, P5-T19
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/44_CORE_PROTOCOL.md, specs/02_PROTOCOL_AND_API.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Formalize the scheduler-neutral core protocol vocabulary into a versioned, feature-negotiated wire contract with protocol versioning, stable identity, request/trace identity, registration, heartbeats, and time semantics, without assuming a scheduler, runtime, or deployment substrate.

**Required tests:**
- protocol version envelope serializes and negotiates minimum_compatible_version
- peers tolerate and preserve unknown features
- stable identity never equals physical address
- registration supports initial, re-registration, reconnect, metadata and capability change, and graceful unregister
- heartbeat distinguishes temporarily unreachable, stale, removed, and terminated
- timestamps are UTC ISO-8601 with skew detection

### P5-T25 — Protocol v1: canonical JSON Schemas under schemas/v1
**Context:** `C80`
**Depends on:** P5-T24
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/44_CORE_PROTOCOL.md

**Outcome:** Publish authoritative JSON Schemas for common, topology, model, resources, runtime, requests, events, errors, jobs, and artifacts that use stable IDs, reject malformed enums, document required vs optional fields, preserve forward compatibility, support extensions, and never collapse false/0/null/unknown/not_reported/unsupported.

**Required tests:**
- common schemas validate against fixtures
- malformed enums are rejected and unknown enum values are preserved where allowed
- unknown fields are preserved and forwarded
- extension namespace is ignored by core readers
- unknown-vs-zero-vs-false semantics are preserved by schemas

### P5-T26 — Protocol v1: state machines and canonical enums
**Context:** `C75`
**Depends on:** P5-T24
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/44_CORE_PROTOCOL.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md

**Outcome:** Publish explicit state machines (model residency, runtime, node, allocation, job) and frozen canonical enums (error taxonomy, lifecycle reasons, workload classes, device types, provenance sources) reconciled by test as machine-readable data.

**Required tests:**
- state machines reject invalid transitions and identify terminal states
- error taxonomy frozen data matches published tables
- lifecycle reasons and workload classes reconcile
- device types and provenance sources reconcile
- removing a vocabulary entry fails a guard test

### P5-T27 — Protocol v1: OpenAPI and transport-independent surfaces
**Context:** `C75`
**Depends on:** P5-T25
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/02_PROTOCOL_AND_API.md, specs/44_CORE_PROTOCOL.md

**Outcome:** Publish the OpenAPI definition for control, observability, and data-plane HTTP surfaces (discovery, topology, models, aliases, capacity, health, events, jobs, routing explanation) while keeping object semantics transport-independent and preserving OpenAI-compatible endpoints.

**Required tests:**
- OpenAPI examples conform to the JSON Schemas
- discovery endpoints return protocol version and features
- routing explanation surface exposes candidates, selected route, fallbacks, retries
- OpenAI-compatible endpoints are preserved
- compression is supported for large topology/event responses

### P5-T28 — Protocol v1: conformance suite and fixtures
**Context:** `C90`
**Depends on:** P5-T25, P5-T26, P5-T27
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/42_SITE_GATEWAY_CONFORMANCE.md

**Outcome:** Publish conformance profiles, a language-neutral conformance suite, and valid/invalid/federation fixtures covering schema validation, protocol discovery, feature negotiation, registration, heartbeat, topology, events, retries, errors, aliases, federation, capability advertisement, snapshot consistency, and backwards compatibility.

**Required tests:**
- conformance profiles are declared in manifest.yaml
- valid fixtures pass and invalid fixtures fail schema validation
- federation fixtures preserve provenance and reject paths containing a gateway itself
- snapshot consistency holds across a snapshot plus deltas
- backwards-compatibility vectors pass against the frozen protocol vocabulary

### P5-T29 — Protocol v1: compatibility matrix, changelog, release artifacts, cross-repo CI
**Context:** `C75`
**Depends on:** P5-T28
**Features:** IW-PROTO-002
**Read:** specs/45_PROTOCOL_V1.md, specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md, specs/19_CI_CD_LIVING_SPECS.md

**Outcome:** Publish the machine-readable compatibility matrix, maintain VERSION and the protocol changelog, define the protocol change workflow and cross-repository compatibility CI that fails on protocol-visible drift, and define published immutable release artifacts per protocol version.

**Required tests:**
- compatibility matrix reconciles with published protocol versions
- changelog records each change's compatibility classification
- protocol change workflow is documented
- cross-repo CI guard rejects protocol-visible drift
- release artifact manifest is reproducible for a protocol version

### P5-T30 — GPU memory: accounting wire contract, node report and reconciliation
**Context:** `C80`
**Depends on:** P5-T24, P5-T25
**Features:** IW-GPUMEM-001
**Read:** specs/46_GPU_MEMORY_INTELLIGENCE.md, specs/45_PROTOCOL_V1.md

**Outcome:** Publish and implement the iw.gpu-memory/1 node report: byte quantities with an explicit basis, per-GPU physical, attributed and unattributed memory, runtimes, slots, allocations, ownership and authority, carried only as optional members of node telemetry and the heartbeat status, with accounting reconciliation that emits anomalies and never treats unknown as zero.

**Required tests:**
- every contract fixture round-trips byte-stable through the reference implementation types
- a quantity carrying bytes beside basis unknown or unsupported is refused
- used plus free and attributed plus unattributed reconcile within the configured tolerance, otherwise an anomaly is emitted
- unattributed memory is present whenever physical used is known
- an older node's telemetry and heartbeat parse unchanged and a malformed report never refuses the carrier
- topology v2 carries no GPU-memory member
- NVIDIA and AMD producers report physical memory measured on real hardware
- AC-OBS-08: unchanged memory report in NVIDIA observe mode requires real pinned hardware reconciliation; no AMD qualification is inferred

### P5-T31 — GPU memory: gateway composition, reservations, pressure and fleet snapshot
**Context:** `C85`
**Depends on:** P5-T30
**Features:** IW-GPUMEM-001
**Read:** specs/46_GPU_MEMORY_INTELLIGENCE.md, specs/04_CAPACITY_ADMISSION_SEATS.md, specs/43_GPU_PLACEMENT_HOT_SWAP.md

**Outcome:** Compose safeSchedulable, pressure and eligibility only in the gateway whose rebalancer owns the node, keep a race-safe reservation ledger reconciled against measured allocations, and serve the iw.gpu-memory.fleet/1 snapshot that federated consumers de-duplicate by resource id without recomputing it.

**Required tests:**
- a reservation already visible as a physical allocation is not subtracted twice
- two decisions in one pass cannot reserve the same bytes
- a not-owned or stale GPU has no schedulable capacity
- pressure states follow free-after-growth with hysteresis
- a resource relayed by two paths is counted once
- a gateway that is not the authority never composes safeSchedulable
- AC-OBS-03..05: typed owner capacity expires by monotonic age and epoch; duplicate/replayed snapshots and shared pools cannot multiply capacity

### P5-T32 — GPU memory: decision records, lifecycle events, OOM postmortem and placement simulation
**Context:** `C85`
**Depends on:** P5-T31
**Features:** IW-GPUMEM-001
**Read:** specs/46_GPU_MEMORY_INTELLIGENCE.md, specs/36_GPU_WATCHDOG_RESCUE.md, specs/35_CLUSTER_SIMULATOR_CHAOS.md

**Outcome:** Record every meaningful rebalancer decision with candidates, scores and measured outcomes on a cursor-based idempotent event feed, preserve the last pre-failure state of a GPU in an OOM postmortem, and answer read-only placement simulations from the real rebalancer evaluation.

**Required tests:**
- an event replayed with the same eventId is recorded once
- a decision outcome is never succeeded before a measured delta exists
- a postmortem reconstructs the OOM without the failed runtime answering
- a simulation leaves the ledger, the router and every allocation unchanged
- a gateway without rebalancer authority refuses a simulation
- AC-OBS-09: telemetry and simulation grant no Nibbler serving or placement authority before runtime qualification and applicable safety proofs

### P5-T33 — Node join: hardware-only registration, assignments and tokenless enrollment in the Rust gateway
**Context:** `C80`
**Depends on:** P5-T24, P5-T25
**Features:** IW-NODEHW-001
**Read:** specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/45_PROTOCOL_V1.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md

**Outcome:** Implement the specs/47 node-join contract in the Rust gateway (InferWeave/inferweave): the optional versioned hardware member stored verbatim, hardware-only registration that is recorded but never routable or dialled, the always-present empty assignments array, and tokenless enrollment whose proof credential is accepted by register, replaying conformance/node-join-vectors.json.

**Required tests:**
- every register vector in conformance/node-join-vectors.json passes over HTTP against a running gateway
- hardware that is not an object, lacks an integer version or exceeds 65536 compact bytes is refused with 400 bad_request and admits nothing
- unknown members of hardware are stored verbatim and shown only on the operator surface
- a hardware-only node heartbeats, is listed with its hardware, is absent from /v1/models and its endpoint is never dialled
- an older node registering without hardware is unchanged and its response carries assignments []
- the enrollment known answers verify, and a proof credential earned over /v1/node/proof is accepted by /v1/node/register
- a proof with a non-canonical signature or a small-order key is refused and the multi-byte hex input does not poison the proof store

### P5-T34 — Node join: hardware-only registration, assignments and tokenless enrollment in the Go gateway
**Context:** `C80`
**Depends on:** P5-T24, P5-T25
**Features:** IW-NODEHW-001
**Read:** specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/45_PROTOCOL_V1.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md

**Outcome:** Implement the specs/47 node-join contract in the in-house Go gateway (metabolomics-us/inferweave-gateway): the optional versioned hardware member stored verbatim, hardware-only registration that is recorded but never routable or dialled, the always-present empty assignments array, and the three tokenless enrollment endpoints with the exact signed transcript, replaying conformance/node-join-vectors.json.

**Required tests:**
- every register vector in conformance/node-join-vectors.json passes over HTTP against a running gateway
- hardware that is not an object, lacks an integer version or exceeds 65536 compact bytes is refused with 400 bad_request and admits nothing
- unknown members of hardware are stored verbatim and shown only on the operator surface
- a hardware-only node heartbeats, is listed with its hardware, is absent from /v1/models and its endpoint is never dialled
- an older node registering without hardware is unchanged and its response carries assignments []
- the enrollment known answers verify with the gateway's own verifier, and a proof credential is accepted by /v1/node/register
- a nonce above 2^53 round-trips as an unsigned 64-bit integer and the verifier refuses non-canonical signatures and small-order keys

## Phase B — Runtime families (protocol)

### P5-T35 — Dynamic nodes: capability-gated assignments, facts, status and gateway provisioning
**Context:** `C85`
**Depends on:** P5-T33
**Features:** IW-DYNNODE-001
**Read:** specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md, specs/39_INFERENCE_RUNTIME_TUNING.md, specs/43_GPU_PLACEMENT_HOT_SWAP.md

**Outcome:** Implement the specs/64 contract in the Rust gateway and node (InferWeave/inferweave): a node started with --model dynamic registers hardware-only with its dynamic facts and offers iw.dynamic-node/1; a gateway with desired models answers its register and every heartbeat with serve, measure and stop assignments chosen from measured runtime profiles with every card of an engine on one node; the node fetches pinned artifacts, launches the assigned profile, probes it, re-registers as a routable node and reports provisioning status; a measurement becomes a draft profile the next plan may select.

**Required tests:**
- a dynamic node's register is hardware-only, carries the dynamic facts and the capability offer, and files no telemetry while idle
- assignments on the register and heartbeat responses are acted on only while iw.dynamic-node/1 is in force, and provisioning rides the beat only then
- malformed dynamic facts are refused with 400 bad_request before anything is minted
- a serve assignment fetches artifacts with size and SHA-256 verified and a cut HTTP download resumed, launches the profile pinned to the assigned cards, probes it and reports serving with the engine endpoint and the derived dep_ id
- a profile without decode evidence at 90 percent of the context floor at the serving slot count is never assigned to serve, and a required quality suite excludes unscored profiles
- a measure assignment runs every matrix cell, reports one evidence row per cell, stops the engine, and the gateway drafts a profile the next plan selects
- a failed placement is recorded and, for the permanent failure reasons (launch_failed, probe_failed, measure_failed), not retried on the same node until the gateway restarts (the transient reasons, disk_full and runtime_unavailable among them, expire after 600 seconds), a refusal is never recorded as a failure but backs the same placement off for 60 seconds doubling to 600 and is shown on the operator view, and a serving engine that stops answering is released after three beats
- a model removed from the configuration is stopped explicitly, a restarted gateway adopts a serving engine instead of stopping it (one active status per node and model) and stops an engine beyond the model's replicas, a held assignment its node never reports is dropped after 300 seconds as a transient failure, and a stale node releases its placement
- every card of one assignment is on one node, profiles are ordered by quality tier, measured decode at the floor, name and version (never by group size), and the deployment id is the one derived from the entry's payload (the known answers of specs/64 section 5 rule 6 reproduce), differs between profiles and is refused by a node when it does not match
- facts, status and matrix bounds hold as sent: a facts member over 64 KiB or past a schema bound is refused 400 with a message of at most 200 characters, a report is read for at most 64 entries, and a measure whose depth is below 10 x (maxTokens + 16), whose artifacts collide on disk or whose sizes overflow 64 bits is refused

### P5-T36 — InferWeave Storage Phase 1: signed grants, store daemon, S3 front end, digest index and multi-source stager
**Context:** `C85`
**Depends on:** P5-T33
**Features:** IW-STORE-001
**Read:** specs/65_INFERWEAVE_STORAGE.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/20_NODE_AUTOCONFIG_DISCOVERY.md, specs/40_NETWORK_TOPOLOGY_GRAPH.md, specs/45_PROTOCOL_V1.md

**Outcome:** Implement the specs/65 Phase 1 contract in the Rust gateway, the iw-store daemon and the staging client (InferWeave/inferweave): a store registers hardware-only under role store and capability iw.store/1, serves sha256-pinned blobs read-only over a native range API authenticated by a short-lived signed iwg1 grant and over an optional read-only S3 front end, never writes under its blob directory, refuses to start on an exposed bind, and advertises verified digests that the gateway indexes; a gateway issues grants only to enrolled nodes for catalogued digests in their scope and quarantines a store that served bytes not matching a pin; a node stages a blob from several holders in ranges, verifies size and SHA-256 before the file is visible and falls back to the origin.

**Required tests:**
- the iwg1 token reproduces the signed-transcript known answers, is verified in the specified order returning the first failure, caps lifetime and length, rejects duplicate and unknown keys and non-canonical encodings, and never panics on garbage or oversize input
- a store trusts only the issuer keys its home gateways return in grantIssuerKeys plus operator extras, applies a changed set without restart, and rejects an untrusted issuer before the signature is evaluated
- the native data plane answers only the status codes of specs/65 section 5.4 in the specified order, serves 206 ranges that match Content-Range, rejects multi-range, suffix and unranged requests under a range grant, authenticates before it reveals whether a digest exists, and resolves blobs by digest only without following a symlink out of the blob directory
- the daemon never creates, opens for write, truncates, renames or removes anything under its blob directory, refuses a state directory or index inside the blob directory or on a shared filesystem unless overridden, holds one exclusive lock per state directory and names every temp file uniquely
- a store refuses to start on a wildcard bind, on a non-loopback bind without an allow-list, and on a public bind without the explicit flags, closes a peer outside the allow-list before reading any byte, and never takes the peer address from a header
- failed authentication is charged to (address, identity) only after a grant verified against a trusted issuer and otherwise to the address, garbage never locks a victim identity, lockout doubles to its cap and answers 429 with Retry-After, the lockout table is bounded, and the global request ceiling and per-IP connection cap answer 503
- the S3 front end has no anonymous access, verifies AWS Signature Version 4 in header and presigned form, answers every write verb 403 read-only without reading the body, lists and pages only keys inside the access key's bucket and prefix scope, emits the sha256 as ETag, serves byte-exact ranges, and refuses a keys file readable by group or other
- a gateway sends the store messages and the grantIssuerKeys and topology store fields only to a peer that negotiated iw.store/1, accepts advertisements from an enrolled store only (full, delta and paged, with need_full on an epoch gap), indexes a digest as held only when complete, ages entries out after three refresh intervals and drops a store on a leave notice only if the caller owns the store id
- a gateway issues a grant only to a node currently enrolled with a fresh registration, only for a catalogued digest in the node's scope, with node_id taken from the authenticated link, never signs a grant for a holder behind a child gateway, rate-limits requests per node, and grants a non-public digest by range for at most 60 seconds
- topology store pages carry at most 1000 digests each and one hop, a parent ingests them only from an enrolled gateway whose registration negotiated iw.store/1 and keeps only catalogued digests, a gateway peer that did not negotiate receives the pre-storage document unchanged, and remote entries expire after 900 seconds
- a store reported with an attributable digest_mismatch by the configured number of distinct enrolled nodes is quarantined, excluded from holders, grants and topology until an operator clear, a store cannot report itself, and an unattributable mismatch never quarantines
- the stager fetches ranges from several holders, resumes from its .part files after a restart or a dead source, discards a 206 whose Content-Range does not match, reports a source that served bytes failing the pin, never makes the file visible before size and SHA-256 equal the pin, treats ENOSPC as fatal, and falls back to the origin when no source completes or the fabric is unavailable

### P5-T37 — InferWeave Storage Phase 2: ingest leases, replication, TLS, federated grants and per-range hashes
**Context:** `C85`
**Depends on:** P5-T36
**Features:** IW-STORE-002
**Read:** specs/65_INFERWEAVE_STORAGE.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md, specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md

**Outcome:** Implement the specs/65 Phase 2 contract after its open items are decided: a TLS listener and per-listener blob scope so a non-private bind may serve gated blobs, a gateway-forwarded grant request across federation, per-range hashes in the catalog, ingest leases with an epoch and a no-replace publish so exactly one writer exists per file, replication with repair, quota and eviction, an optional write path that publishes only a blob matching its pin, and a rendezvous so a store listens on no inbound port.

**Required tests:**
- a store listener serves TLS with a configured certificate, and a gated-scope blob is served only on a TLS or private listener while a publicly bound plain listener serves public-scope blobs only
- a parent gateway forwards a node's grant request to the child gateway that owns the store, the child signs the grant, and a store never accepts a grant signed by a gateway it does not trust
- a catalog with per-range hashes lets the stager attribute a corrupt range to one source and retry that range alone
- an ingest lease is granted to at most one store per digest with a monotonically increasing epoch, a take-over after expiry writes a different temp name than the old writer, publication uses a no-replace rename and never replaces a file being read, and publishing an existing digest is idempotent
- a store missing a catalogued digest replicates it from holders, a failed periodic verify deletes the blob and re-replicates it, and eviction never removes the only complete copy or a blob under a lease
- a write to the S3 front end succeeds only for a key granted write and only for an object whose SHA-256 and size equal the pin, publishes by atomic rename after verification and deletes the part file otherwise
- a store reachable only through a rendezvous accepts no inbound connection, and the grant and signature checks are unchanged

### P5-T38 — Managed persistent node onboarding, qualification and durable reconciliation
**Context:** `C85`
**Depends on:** P5-T35, P1-T23, P1-T20B, P3-T25
**Features:** IW-DYNNODE-002
**Read:** specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md, specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md, specs/20_NODE_AUTOCONFIG_DISCOVERY.md, specs/26_RESOURCE_IDENTITY_REDISCOVERY.md, specs/36_GPU_WATCHDOG_RESCUE.md, specs/39_INFERENCE_RUNTIME_TUNING.md, specs/43_GPU_PLACEMENT_HOT_SWAP.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md

**Outcome:** Implement iw.node-reconcile/1 in the Rust monorepo: a persistent Compose owner automatically reconciles stable mixed-GPU inventory, honest telemetry, one instance per deployment per node, durable assignment execution, bounded watchdog recovery and policy-scoped qualification. Reuse existing HTTP registration/heartbeat, assignment and provisioning schemas without weakening legacy behavior. Nibbler clean-install, real process signals, host reboot, gateway restart and full authorization/admission-path evidence must pass before managed serving is claimed ready.

**Required tests:**
- ONB-01: clean installation and idempotent rerun use persistent Linux Compose without Apptainer; real owner-to-sibling host-loopback connectivity is proven before GPU qualification
- ONB-02: mixed Pascal/Turing inventory retains per-card stable identities across reordering and reboot, and the pinned compatible runtime executes on every qualified card
- ONB-03: unnegotiated or unenrolled peers cannot provision; idle hardware and control status never advertise serving offers
- ONB-04: automatic policy-scoped qualification runs verified artifacts through real authorization, admission, correctness, context and cancellation/reuse checks before readiness
- ONB-05: throughput drafts, missing or expired evidence, fingerprint drift, absent attestation, stale status, unhealthy watchdog or quarantine cannot publish through adoption or settle; permits enforce exact identity, scope, expiry and atomic request budgets
- ONB-06: distinct deployments use disjoint homogeneous groups; a second assignment for an identical deployment is refused before executor translation and never becomes an implicit span
- ONB-07: elective stop/replacement drains before unload and preserves healthy-instance floors; severe faults immediately withdraw unsafe capacity and expose any floor deficit
- ONB-08: bounded rescue preserves actual known-good artifacts, never invents a rollback target, and persists exhausted attempts and quarantine across node and gateway restart
- ONB-09: real subprocess SIGTERM, SIGINT and graceful owner drop preserve attested containers and durable claims for adoption; explicit retirement withdraws, drains and unloads; host reboot preserves identity and avoids duplicate engines
- ONB-10: gateway restart reconciles durable holdings and qualification evidence after a fresh report, invalidates prior permits and requires a fresh full-path probe before publication
- ONB-11: managed link-only inference and cancellation work through reconnect without duplicated placement or exposed unauthenticated engine ports
- ONB-12: exact-commit and digest-pinned Nibbler installation/restart/recovery evidence, independent review and required checks pass before normal merge; offline contract tests never substitute for runtime or hardware proof

### P5-T39 — Site attestation: the Rust gateway attests the grant it enforces to a paid runtime that may join any gateway
**Context:** `C85`
**Depends on:** P5-T35, P5-T33
**Features:** IW-SITEATT-001
**Read:** specs/67_SITE_ATTESTATION.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md, specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md, decisions/2026-11-01-gateway-served-site-attestation.md

**Outcome:** Implement `iw.site-attestation/1` in the Rust gateway and node (InferWeave/inferweave). The gateway loads a private paid-grant policy and enforces each grant with default-deny before admission; it puts the capability in force only with a valid loaded policy; it answers a node's heartbeat `siteAttestation` request with a short-lived attestation bound to the instance, the gateway and the grant digest, or a closed-set refusal. The node registers without its paid model, requests and verifies an attestation against its trusted gateways, advertises the model only while it holds an acceptable one, refreshes it before expiry with the link held, and withdraws it on expiry or refusal. It works against any gateway and for any number of scheduled or restarted instances.

**Required tests:**
- the capability is listed only with a loaded, valid paid-grant policy, and an invalid policy is absent
- every refusal code is produced by exactly its condition, in the stated order, and a refusal is never an empty success
- an attestation is issued only to an enrolled, fresh registration; a key-only identity gets `not_enrolled`
- two instances with different node ids are each attested for one grant, and a copy of one is refused by the other, by another gateway id and by another grant digest
- the gateway refuses a request for the model from any subject other than the grant's before admission
- the site does not advertise the paid model before an attestation, withdraws it at expiry and on refusal, and re-requests before expiry with the link held
- the site never falls back to an older attestation or a file while the capability is in force
- `any` is accepted only when configured explicitly
### B-T01 — Runtime families and typed capabilities
**Context:** `C75`
**Depends on:** none
**Features:** IW-RT-001
**Read:** specs/00_INVARIANTS.md, specs/48_RUNTIME_FAMILIES_AND_CAPABILITIES.md

**Outcome:** Define the canonical runtime-family registry, typed capability descriptor, isolated twelve-method adapter contract and additive feature negotiation. Unknown family ids fail admission; no capability is inferred from a model name.

**Required tests:**
- typed-capability round-trip (e.g. `embeddings`)
- name-derived-rejection
- registry-closure (unknown family id fails admission)
- adapter lifecycle completeness and process/container isolation
- mixed-version peer compatibility without family inference

### B-T02 — Native `/inferweave/v1` control-plane and inference endpoints
**Context:** `C75`
**Depends on:** B-T01
**Features:** IW-RT-002
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md, specs/49_NATIVE_CONTROL_PLANE_ENDPOINTS.md

**Outcome:** Extend `openapi/inferweave-v1.yaml` with native runtime-family endpoints, publish standalone deployment and family-request JSON Schemas reconciled against the full inline constraints, and define independently negotiated bounded native Link request plus exact HTTP response proof bound to the current authenticated registration and Link incarnation without arbitrary URI, proxy behavior or body-derived status.

**Required tests:**
- openapi-validation
- family-routing (e.g. `POST /rerank` only for `reranking`)
- parity (native endpoints honour admission/fairshare like `/v1/chat/completions`)
- standalone/OpenAPI schema parity
- node-register hardware-only conditional-schema parity and de-duplicated capability intersection; registration/Link-incarnation Hello/ack negotiation and re-registration/credential/socket revocation vectors
- negotiated native link family/endpoint whitelist and hostile URI/content/size fixtures
- native Link response proof vectors for exact 201/4xx/5xx status, bounded canonical headers, exact UTF-8 body bytes/digest, success code extensions, missing proof and request-only peers
- family model minLength 1 and JSON integer spelling parity (1, 1.0, 1e0)

### B-T03 — Transactional runtime hot-swap lifecycle
**Context:** `C75`
**Depends on:** B-T01
**Features:** IW-RT-003
**Read:** specs/00_INVARIANTS.md, specs/50_TRANSACTIONAL_RUNTIME_LIFECYCLE.md

**Outcome:** Define the transactional lifecycle, immutable-key single-flight loading, waiter-independent cancellation, full safe-peak fenced reservations, three transactional cache classes and constrained-memory rollback under the existing rebalancer authority.

**Required tests:**
- state-machine-transitions
- availability-preserved
- no-second-scheduler
- single-flight waiter independence
- safe-peak reservation, fencing, physical de-duplication and progress-based expiry
- cache integrity, atomic publication, pins, offline behavior and streamed acquisition
- constrained-memory swap impact and rollback

### B-T04 — Typed inference pipelines
**Context:** `C75`
**Depends on:** B-T01, B-T02
**Features:** IW-RT-004
**Read:** specs/00_INVARIANTS.md, specs/51_PIPELINES_AND_DURABLE_JOBS.md

**Outcome:** Define the typed inference pipeline contract (acyclic DAG of runtime-family stages) and its wire schema, with `POST /pipelines/execute`. Define the canonical `rag` pipeline as a composition of `embeddings`/`reranking` and `llm` stages that respects per-stage admission and capacity — no separate ad-hoc RAG path.

**Required tests:**
- dag-acyclicity
- stage-family-resolution
- rag-composition

### B-T05 — Durable inference jobs
**Context:** `C75`
**Depends on:** B-T02, B-T04
**Features:** IW-RT-005
**Read:** specs/00_INVARIANTS.md, specs/52_DURABLE_INFERENCE_JOBS.md

**Outcome:** Extend the durable inference job contract with result-by-reference, resume, family-aware no-bypass controls and additive compatibility for legacy jobs without family or with completed.

**Required tests:**
- job-lifecycle
- restart-resume
- no-bypass
- legacy job read compatibility and canonical succeeded emission

### B-T06 — Runtime-family conformance and traceability
**Context:** `C75`
**Depends on:** B-T01, B-T02, B-T03, B-T04, B-T05
**Features:** IW-RT-006
**Read:** specs/00_INVARIANTS.md, specs/53_RUNTIME_FAMILY_CONFORMANCE.md

**Outcome:** Add executable runtime-family advertisement and positive/negative request vectors, honest offline labeling, optional live HTTP replay and complete feature/task traceability.

**Required tests:**
- conformance-runs
- executable negative fixtures and optional live HTTP replay
- registry-traceable
- self-test-green

## Dynamic aliases — protocol before implementation

### A-T01 — Contracts and compatibility
**Context:** `C80`
**Depends on:** none
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md

**Outcome:** Canonical schemas, frozen vocabularies, compatibility fixtures and independently reviewed alias authority boundaries.

**Required tests:**
- artifact schema and vocabulary guard rejects deliberate drift
- legacy level-1 fixture unchanged and validates
- spec57 inference transcript/fingerprint, claim schema and hostile vectors agree; offline proof only

### A-T02 — Rust alias persistence and authorization
**Context:** `C80`
**Depends on:** A-T01
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md

**Outcome:** Durable tenant-scoped drafts, immutable publication, optimistic concurrency, idempotency and audit/rollback under Rust authorization.

**Required tests:**
- concurrent CAS and idempotency survive restart
- cross-tenant CRUD and forged identity rejected
- publish and rollback append immutable history
- independently reviewed request-bound Ed25519 edge delegation, Rust-owned identity grants and cross-language replay vectors
- personal-key current tenant infer grant; separate inference purpose and shared nonce ledger; no raw tenant/header authority

### A-T03 — Rust alias preview and deterministic matching
**Context:** `C80`
**Depends on:** A-T01, A-T02
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md

**Outcome:** Instance-level hard filtering and deterministic ranking reuse current router facts with read-only preview and bounded redacted explanations.

**Required tests:**
- hard constraints and evidence confidence cannot be bypassed by scores
- preview leaves demand, leases and allocations unchanged
- stable ties and snapshot/cache invalidation

### A-T04 — Rust admission and stream integration
**Context:** `C80`
**Depends on:** A-T03
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md

**Outcome:** Aliases and exact requests use the existing owner admission path with generation revalidation, bounded retries and stream-safe cancellation.

**Required tests:**
- exact identity and legacy precedence preserved
- admission races are atomic and retry budgets bounded
- partial stream never replays and cancellation releases leases
- shared operation/idempotency claim prevents two-parent double admission; reservation acquisition crash reconciles before takeover
- fenced DISPATCHED intent precedes bytes/direct permit; ambiguous and partial streams never auto-replay
- purpose-bound owner permit, exact node audience and negotiated Link capability; direct/proxy unsupported until qualified
- durably synced node INTENT before central ConsumeDispatch and SPENT before backend; duplicate/timeout/lost acknowledgement never starts
- one claim fence across permit IDs/transports/restarts; runtime instance/generation pinned through backend start
- protected Link executable bytes and asynchronous consume request/ack preserve exact bindings; heartbeat/cancellation continue during waits and post-fsync expiry/cancellation prevents start

### A-T05 — Runtime and federation alias integration
**Context:** `C80`
**Depends on:** A-T01, A-T03, A-T04
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md, specs/56_RUNTIME_INSTANCE_OBSERVATIONS.md

**Outcome:** Consume existing lifecycle, GPU placement and owner federation authority with conservative profiles and exclusive reservations.

**Required tests:**
- multi-GPU loss invalidates entire placement
- shared supply and retry leases deduplicate across parents
- stale cyclic offers and unauthorized provisioning rejected
- owner preemption and policy-authorized provisioning exercised
- generation, TTL, sequence, epoch and tombstone hostile report vectors
- authenticated node report ingestion and mixed-version UNKNOWN fallback
- generation-bound verifier and owner policy references cannot grant capability or capacity
- multi-GPU group loss and source reconnect prevent stale READY resurrection
- claim-bound owner/node reservation fencing and one-use direct permits; holder expiry never reclaims progressing GPU work
- purpose-bound owner permit, exact node audience and negotiated Link capability; direct/proxy unsupported until qualified
- durably synced node INTENT before central ConsumeDispatch and SPENT before backend; duplicate/timeout/lost acknowledgement never starts
- one claim fence across permit IDs/transports/restarts; runtime instance/generation pinned through backend start
- protected Link executable bytes and asynchronous consume request/ack preserve exact bindings; heartbeat/cancellation continue during waits and post-fsync expiry/cancellation prevents start

### A-T06 — Go typed alias client and transparent relay
**Context:** `C80`
**Depends on:** A-T01, A-T02, A-T04
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md

**Outcome:** Go consumes Rust alias contracts with validated identity and lossless compatible relay; no local alias authority.

**Required tests:**
- schema parity and mixed-version negotiation
- status bytes headers SSE cancellation and trusted identity survive relay
- code audit finds no new Go alias resolver or database
- Go signs distinct inference proof binding every accepted semantic header; no caller credential forwarding; operation identity survives retry

### A-T07 — Go alias administration and observability
**Context:** `C80`
**Depends on:** A-T06, A-T03, A-T05
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md

**Outcome:** Existing operator UI provides alias drafts, preview, publication, history, routing, simulation and federation views backed by Rust APIs.

**Required tests:**
- create preview publish trace rollback journey
- permission stale offline conflict empty and pagination states
- default-off/read-only/full UI modes, current Rust grant projection, and no dependence on stale Go operator groups
- desktop tablet keyboard accessibility and screenshots

### A-T08 — Alias migration load and measured rollout
**Context:** `C80`
**Depends on:** A-T02, A-T03, A-T04, A-T05, A-T06, A-T07
**Features:** IW-ALIAS-001
**Read:** specs/00_INVARIANTS.md, specs/45_PROTOCOL_V1.md, specs/54_DYNAMIC_MODEL_ALIASES.md, specs/57_ALIAS_EXECUTION_IDENTITY_AND_CLAIMS.md

**Outcome:** Run all master acceptance scenarios, characterize migration, shadow compare, canary and verify rollback before removing duplicate behavior.

**Required tests:**
- all 29 acceptance IDs have reproducible evidence
- measured baseline and canary overhead under saturation/failure
- legacy exact traffic and feature-flag rollback preserved
- actual HTTP PostgreSQL owner/node crash and concurrent-parent tests prove spec57 before activation
