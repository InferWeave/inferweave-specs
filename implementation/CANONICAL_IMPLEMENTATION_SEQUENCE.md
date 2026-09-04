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

### P1-T07 — Prompt ledger metadata and encrypted payload storage
**Context:** `C75`
**Depends on:** P0-T05, P0-T11
**Features:** IW-PROMPT-001
**Read:** specs/22_PROMPT_LEDGER.md, specs/34_PROMPT_STORE_TIERING.md

**Outcome:** Persist every submitted prompt idempotently with encrypted content, metadata, lineage and access-audit primitives.

**Required tests:**
- accepted/rejected/cancelled prompt storage
- idempotency
- content excluded from logs
- authorized read audit

### P1-T08 — Prompt ingest API and submission ordering
**Context:** `C65`
**Depends on:** P1-T07, P0-T06
**Features:** IW-PROMPT-001
**Read:** specs/22_PROMPT_LEDGER.md, specs/02_PROTOCOL_AND_API.md

**Outcome:** Client/proxy obtains prompt_id/hash before routing and executions/rejections reference it.

**Required tests:**
- storage unavailable behavior
- retry/outbox fixture
- no route without durable submission

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
**Read:** specs/08_CONNECTIVITY_DATA_PLANE.md

**Outcome:** Fallback order is direct → site/regional relay → gateway relay last resort with byte accounting/circuit breakers.

**Required tests:**
- forced NAT failure
- fallback ordering
- gateway relay bandwidth circuit breaker

### P1-T19 — Canonical 503/429 backpressure and bounded retries
**Context:** `C65`
**Depends on:** P1-T12, P1-T18
**Features:** IW-BP-001
**Read:** specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/04_CAPACITY_ADMISSION_SEATS.md

**Outcome:** Infrastructure/capacity returns 503; user/FairShare policy returns 429; retry candidate/time budgets are bounded.

**Required tests:**
- status mapping
- retry metadata
- no unbounded queue/retry loop

### P1-T20 — Per-request performance/resource telemetry
**Context:** `C75`
**Depends on:** P1-T05, P1-T10, P1-T12
**Features:** IW-OBS-001, IW-TEL-001
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** Persist request attempt facts linked prompt→route→deployment→GPU with TTFT/prefill/decode/cache/resource/power outcome.

**Required tests:**
- correlation completeness
- cancel/preemption facts
- no prompt body in metrics

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
**Read:** specs/10_DASHBOARD_PORTAL.md

**Outcome:** Display live nodes, GPUs, models, seats/context/KV, requests, route state and freshness.

**Required tests:**
- UI E2E with deterministic fixtures
- stale telemetry visible
- no misleading pooled VRAM totals

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
**Read:** specs/00_INVARIANTS.md, specs/06_BACKPRESSURE_RETURN_TO_SENDER.md, specs/09_OBSERVABILITY_RECEIPTS.md, specs/16_SECURITY_PRIVACY_TRUST.md

**Outcome:** Multi-hour mixed workload validates cancellation, node loss, stale telemetry, prompt durability and direct-path invariants.

**Required tests:**
- soak
- node crash
- gateway restart
- Postgres hiccup
- review requirement matrix

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
**Read:** specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md

**Outcome:** Persist raw samples and dimensioned rollups by exact GPU/runtime/model/context/concurrency/settings fingerprint.

**Required tests:**
- partition/rollup correctness
- no universal TPS aggregation
- retention test

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
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Versioned adapters record dataset/task/scorer versions and quality results without conflating performance.

**Required tests:**
- deterministic fixture scorer
- dataset revision persistence
- failure classification

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
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Produce workload-specific recommendations with measured_exact/equivalent/observed/predicted confidence and reproducible evidence.

**Required tests:**
- predicted never labeled measured
- exact evidence reconstruction
- confidence downgrade

### P2-T08 — Pareto frontier and next-experiment selection
**Context:** `C75`
**Depends on:** P2-T07
**Features:** IW-REC-002
**Read:** specs/24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md

**Outcome:** Maintain multi-objective Pareto frontier and select high-value uncertain benchmark experiments.

**Required tests:**
- domination tests
- missing evidence priority
- no single-score hidden override

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
**Read:** specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md

**Outcome:** Persist append-oriented resource/allocation/deployment/health lifecycle events with correlation IDs.

**Required tests:**
- state transition history
- append/idempotency
- query timeline

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
**Read:** specs/09_OBSERVABILITY_RECEIPTS.md, specs/18_SOLANA_DEV_ACCOUNTING.md

**Outcome:** Record verified useful-work facts independent of any blockchain; no prompt bodies in receipts.

**Required tests:**
- reconciliation
- duplicate prevention
- content-free records

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

### P3-T22 — Phase-3 operational/security review
**Context:** `C100`
**Depends on:** P3-T21, P3-T19, P3-T20, P3-T18A
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
