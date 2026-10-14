# InferWeave Federated Model Provisioning — Phase 0 Audit & Gap Matrix

Status: **Autonomous bounded admission (Item 6) delivered & merged** (`inferweave/inferweave` PR #919, branch `feat/provisioning-autonomous`). This closes the admission gap: under an `autonomous` owner policy with explicit bounds, a reservation that fits is auto-approved on reserve (no operator action), and one that doesn't fit defers to the operator queue (fail closed, never auto-refused). Prior milestones: Item 5 (operator API + persisted owner-policy store, PR #916) gave the owner the management half of Phase 2's approval flow (owner-gated `/iw/v1/provision/operator/...` API + durable policy store); Phase 2 (approval-required activation) merged as PR #881 (merge `6a227e09`); Phase 1 (observe-only slice) merged as PR #863 (merge `75a6ee94`). Items 1-5 + autonomous mode done; the GUI (WS H) remains later-phase.
Date: 2026-10-12
Author: pi agent (in-session, mission pipeline unavailable due to orchestration store lock).
Scope: `inferweave/inferweave`, `inferweave/inferweave-specs`, `metabolomics-us/inferweave-gateway`.

This document is the Phase 0 deliverable of the *InferWeave Federated Model
Provisioning — Master Specification*: an inventory of existing components,
a verified gap matrix with source references, and the ownership boundaries for
the parallel workstreams. Every claim below was verified against the current
source tree, not assumed.

---

## 0. Method

- Read the master specification (§1–§17).
- Mapped each spec requirement to existing modules in the three repositories
  (`grep` + read of the relevant module doc-comments and type surfaces).
- Recorded **Present / Partial / Missing** with the concrete source reference.
- A claim of "present" requires the source to actually implement the behavior;
  a module whose doc-comment promises a later task is marked Partial at best.

---

## 1. What already exists (reusable building blocks)

These are the components the spec §2/§13 says to **reuse, not rebuild**. They
are real and tested.

| Spec need (§) | Existing implementation | Source |
|---|---|---|
| Registry / model & runtime identity | Immutable deployment manifest + fingerprint; aliases resolve to fingerprints | `crates/iw-core/src/deployment.rs` |
| Content-addressed artifacts | Digest-addressed cache, quarantine on digest mismatch, bounded/evictable | `crates/iw-core/src/artifact_cache.rs` |
| VRAM / resource accounting | Per-GPU + per-deployment VRAM ledger (weights counted once, KV reserves, free = vram−weights−KV) | `crates/iw-core/src/capacity.rs`, `capacity_frontier.rs`, `resource_profile.rs` |
| Scheduler-neutral allocation lifecycle | `ResourceRequest`/`Allocation` state machine (`Pending→Active→Released/Failed`) | `crates/iw-core/src/scheduler.rs` |
| Slurm adapter | Allocation-scoped worker identity, rediscovery (not re-mint), requeue handling, GPU-slot ownership | `crates/iw-core/src/slurm_worker.rs` |
| Rebalancer / autoscaler | Fleet autoscaler: rebalance-before-request, min hold, suspension, audit lines, demand ranking | `crates/iw-core/src/autoscaler.rs`, `demand.rs` |
| GPU swap policy + executor | Per-model swap policy, availability floor, GPU claim phases | `crates/iw-core/src/gpu_swap_policy.rs`, `gpu_claim.rs`, `swap_executor.rs` |
| Multi-parent routing | Federation provenance (`origin`/`reporting`/`path`), loop prevention, reconciliation | `crates/iw-core/src/federation.rs`, `docs/federation.md` |
| Capability negotiation | Versioned `iw.<name>/<major>` negotiation, exact-match, additive, fail-closed | `crates/iw-core/src/fed_capabilities.rs` |
| Runtime hot reload | Engine container lifecycle, measured runtime tuning | `crates/iw-core/src/engine_container.rs`, `deployment.rs` (P1-T06C) |
| Route preview / dry-run analog | Non-committing placement preview: eligibility, hard-constraint reasons, headroom, fallback | `crates/iw-core/src/route_preview.rs` |
| Admission | Context/modality/license/deny admission; non-admissible outcomes; seat model | `crates/iw-core/src/context_admission.rs`, `docs/scheduling.md` |
| Node advertisement | Standardized served-model advert (model, ctx ceiling, slots, vram) | `crates/iw-core/src/node_advert.rs` |
| Protocol types | Versioned schema, strong IDs, error envelope, reason-code vocabulary | `crates/iw-protocol/src/{lib,ids,version,error}.rs` |
| Gateway (metabolomics-us) | Registry (who serves), catalog (what we advertise), proxy, pool (desired-state), acquire (Slurm borrow), lifecycle | `inferweave-gateway/internal/{registry,catalog,proxy,pool,acquire,lifecycle}` |
| Gateway placement sizer | Demand→resource-shape (worker-based concurrency) | `inferweave-gateway/internal/placement/placement.go` |
| State plane | Envelope, journal, reasons, redaction, states | `inferweave-gateway/internal/stateplane/` |

---

## 2. Verified gap matrix

Legend: **Present** = implemented + tested in source. **Partial** = concept/module
exists but the federated-provisioning behavior is absent. **Missing** = no source.

### 2.1 Opt-in and policy (§4)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Disabled by default; no silent opt-in | **Missing** | No `disabled/advertise_only/approval_required/autonomous` mode enum anywhere. |
| Policy-filtered capacity signals | **Partial** | Advert/capacity exist; no per-provider policy filter, no per-parent allowlist, no local reserve, no quota object. |
| Approval-required mode | **Partial** | Federation has operator *enrollment* approval (`EnrollmentStatus::PendingApproval`, `Registry::approve`) but that is peer identity, not deployment approval. |
| Autonomous bounded admission | **Delivered (Item 6)** | Auto-approval on reserve under an `autonomous` policy with explicit `maxConcurrent`/`maxTotalVram`/`perParentQuota` bounds; out-of-bounds defers to the operator queue (fail closed). See the Item 6 status section. |
| Remote cannot change opt-in/policy | **Missing** | No opt-in concept, hence no such guard (must be added with the feature). |
| Local clients outrank upstream | **Missing** | No upstream-vs-local priority model exists. |

### 2.2 Desired-state declaration (§5)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Declarative `ModelDeployment` CRD | **Partial** | Gateway `pool.Desired` is a per-tier target (`internal/pool/pool.go`), not a federated multi-provider deployment object. No `apiVersion/kind ModelDeployment`. |
| generations / optimistic concurrency / dry-run | **Missing** | No generation or OCC on a deployment object. |
| Reconcile + status subresource | **Partial** | `pool.Manager.Reconcile` exists (owner-side only). |
| Separate owner policy from requester prefs | **Missing** | No policy-vs-preference split. |

### 2.3 Protocol extension (§6)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Versioned `provisioning` capability | **Missing** | `fed_capabilities.rs` has `admission-report`, `demand`, `link-meta`, `scaling-status` — no `iw.provisioning/*`. |
| Feature flags for approvals/leases/revocation | **Missing** | No such flags. |
| `provision.*` message family | **Delivered** | `crates/iw-protocol/src/provision.rs` (`7f8cdf0b`): envelope, feature flags, state machine, tagged message family. Transport adapter `crates/iw-gateway/src/provision_transport.rs` (`43cdb0c2`): canonical JSON decode/encode, envelope validation, feature-negotiation gating, idempotency dedup, dispatch (capabilities/request/offer/reserve/activate/revoke/heartbeat) to the controller. No socket/HTTP wiring yet. |
| Envelope (id, idempotency key, actor, provenance, expiry, trace) | **Partial** | `envelope.rs` + relay frames exist; no provisioning-specific envelope, no idempotency-key dedup for provisioning, no hop/rate/payload limits for provisioning. |
| Fail closed on unknown versions | **Partial** | `fed_capabilities` drops malformed entries; the provisioning capability itself is absent. |

### 2.4 Admission / reservation / state machine (§7)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Full provisioning state machine (`DESIRED→…→READY`, `REVOKED/EXPIRED/FAILED→RELEASED`) | **Delivered** | `crates/iw-protocol/src/provision.rs` (`ProvisionState::transition`, tested) + `crates/iw-gateway/src/provision_controller.rs` (owner-side ledger driving it). `scheduler::Allocation` covers scheduler lifecycle only. |
| Atomic, scoped, expiring, auditable, idempotent reservation | **Partial** | `gpu_claim.rs` / `capacity_frontier` reserve per-seat; not federated, no single-use token, no fencing epoch, no lease TTL. |
| Single-use token + fencing epoch | **Missing** | `actuator_lease.rs` (gateway) is a different mechanism. |
| Approval binds request+digest+budget+policy-rev+lease | **Missing** | No binding object. |
| Multi-GPU placement-group commit only when all ranks available | **Missing** | Distributed placement is described in specs but no all-ranks commit gate. |
| Routable only after health/readiness | **Partial** | Node advert + engine health exist; no provisioning-commit gate. |
| Retry with backoff + jitter | **Partial** | `backpressure.rs`, autoscaler retries; not a provisioning handshake. |

### 2.5 Placement / scheduling (§8)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Extend existing scheduler/rebalancer | **Partial** | Strong foundation (`autoscaler`, `scheduler`, `swap_executor`, `capacity_frontier`); no federated placement-group arbitration across parents. |
| Consider weights/KV/overhead/scratch/fragmentation/margin | **Present** | `capacity_frontier.rs` counts weights/KV/free; resource profile measures runtime overhead. |
| GPU arch/topology/MIG, CPU/RAM/disk/network | **Partial** | `nvidia_eval.rs`, `gpu_detect.rs`, `resource_profile` cover GPU; network/disk quotas absent. |
| Per-parent quotas + owner priorities | **Missing** | No per-parent quota ledger. |
| Advertisements are snapshots, not reservations | **Present** | `node_advert.rs` + freshness TTL; advert is not a reservation. |
| Stable physical-resource identity, origin-aware dedup, loop prevention | **Present** | `identity.rs`, `slurm_worker.rs` (stable GPU identity), `federation.rs` (loop prevention). |
| No global lock (serialize per owner) | **Missing** | No owner-side serialized reservation ledger for provisioning. |
| Demand-driven w/ hysteresis, cooldown, min residency | **Present** | `autoscaler.rs` invariants (min hold, suspension, hysteresis via utilisation sample). |

### 2.6 Slurm lifecycle (§9)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Only actual allocations provisionable | **Partial** | `slurm_worker.rs` binds to granted allocations; no provisioning concept. |
| Observe resize/preempt/termination/device loss/end-time | **Partial** | Slurm drain, requeue, rediscovery exist; no provisioning unready-on-partial-loss wiring. |
| On losing one GPU from a group: unready, deregister, unload invalid group, release, report | **Missing** | No partial-placement-group invalidation. |
| Respect partition policy / allocation ownership | **Present** | `slurm_worker.rs`, `slurm_drain.rs`. |

### 2.7 Security & supply chain (§10)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Mutual peer auth, scoped identity, least privilege | **Present** | `identity.rs`, `privilege.rs`, `credential.rs`, `enrollment.rs` (scoped delegation). |
| Approved runtime families + content-addressed artifacts, digest + optional signature | **Present** | `engine_container.rs`, `artifact_cache.rs`, `signature.rs`, deployment manifest. |
| Prevent unsafe deserialization / remote code load | **Partial** | Unsafe code forbidden (`[workspace.lints.rust] unsafe_code = forbid`); no explicit provisioning sandbox policy. |
| Sandbox runtimes (device/fs/net/secret/proc) | **Partial** | `fsperm.rs`; not a full provisioning sandbox contract. |
| Bounded concurrent downloads, checksum, cancel, dedup, cache quotas | **Present** | `artifact_cache.rs`. |
| Audit actor/policy/decision/artifact/transitions/cleanup | **Partial** | `audit.rs`, autoscaler audit lines; no provisioning audit records. |
| Disconnection: retain local serving; leases expire w/ grace | **Missing** | No provisioning lease/grace. |
| Revoked lease not renewable by old controller; fencing on failover | **Delivered (controller)** | `provision_controller.rs`: single-use token consumed once + monotonic fencing epoch; a revoked/released reservation is never reactivated (terminal→`RELEASED`, absorbing). No cross-process failover fencing yet (transport workstream). |
| Emergency stop | **Partial** | `context_admission.rs` mentions emergency; not a provisioning emergency-stop policy. |
| Never rely on remote for safe cleanup | **Missing** | No provisioning cleanup ownership statement. |

### 2.8 GUI (§11)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Fleet view | **Present** | gateway web console. |
| Provision wizard (registry/digest/runtime/profile/replicas/priority/constraints) | **Missing** | No provisioning wizard. |
| Placement preview (candidates, VRAM est., cold-start, reject reasons, dry-run caveats) | **Partial** | Gateway `placement`/`capacityplan` size; no federated candidate preview. |
| Owner settings (opt-in, allowlists, caps, reserve, quotas, preemption, emergency stop) | **Missing** | No settings surface. |
| Approval queue (exact proposal, resource impact, TTL, approve/reject) | **API present; GUI missing** | Operator API exposes the pending-approval queue (`GET /iw/v1/provision/operator/approvals`) and approve/reject; a GUI consuming it is later-phase (WS H). |
| Live deployment lifecycle | **Partial** | Gateway lifecycle/stateplane; not the provisioning states. |
| Federation topology | **Partial** | Topology exists (`topology.rs`, gateway `link`); no provisioning provenance display. |
| Audit/history | **Partial** | `audit.rs`; no provisioning audit UI. |
| No duplicated scheduling logic in GUI | **Present** | `placement/placement.go` explicitly removes dual-brain placement (#174); gateway is client, not scheduler. |

### 2.9 Persistence / reliability / observability (§12)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Persist desired state / generations / policy / approvals / reservations / audit | **Partial** | `iw-storage` (SQLite), gateway `stateplane` journal; no provisioning records. |
| Restart reconciliation, at-least-once w/ idempotent handlers, monotonic fencing | **Partial** | `autoscaler` restart-survives claims; no provisioning at-least-once/fencing. |
| Metrics (pending, admission, approval latency, contention, VRAM, cold-start, failure, lease expiry, rebalance, placement quality) | **Partial** | Autoscale/capacity/worker metrics exist; no provisioning metrics. |
| End-to-end tracing without disclosing inventories | **Partial** | `trace`/telemetry exist; no provisioning correlation. |

### 2.10 Specs repo (§13/§17)

| Requirement | Status | Evidence / gap |
|---|---|---|
| Canonical wire format / schemas / state machines / authz model / threat model / conformance fixtures / migration notes for provisioning | **Missing** | Specs repo has `federation.md`, `scheduling.md`, `security.md`; no provisioning spec. |
| SDK update from canonical schemas | **Partial** | `schema-gen` + `schemas/json-schema` exist; would extend for provisioning. |
| Backward compat for non-provisioning peers | **Present** (by design) | `fed_capabilities` additive negotiation; must be preserved. |

---

## 3. Ownership boundaries (workstream → repos/areas)

Consistent with §13/§14; non-overlapping file areas.

| WS | Deliverable | Primary locations |
|---|---|---|
| A | Audit & architecture | This doc; dependency map in `inferweave-specs/docs`. |
| B | Protocol | `crates/iw-protocol/src/`, `crates/iw-core/src/fed_capabilities.rs`, `inferweave-specs/docs/federation.md`, `schemas/json-schema/`. |
| C | Security | `crates/iw-core/src/{identity,privilege,credential,enrollment,audit}.rs`, `inferweave-specs/docs/security.md`. |
| D | Resource ledger | `crates/iw-core/src/{capacity,capacity_frontier,gpu_claim,actuator_lease}.rs`, new `reservation.rs`/`lease.rs`. |
| E | Controller | `crates/iw-gateway/src/` (new `provisioning.rs`), desired-state API. |
| F | Placement | `crates/iw-core/src/{autoscaler,scheduler,swap_executor,capacity_frontier}.rs`. |
| G | Slurm/runtime | `crates/iw-core/src/slurm_worker.rs`, `crates/iw-node/src/`, `engine_container.rs`. |
| H | GUI | `inferweave-gateway/web/src/`, `internal/` (thin API client only). |
| I | Testing/ops | `crates/conformance/`, `inferweave-specs/conformance/`, gateway `acceptance/`. |

---

## 4. Phase-1 (observe-only) recommended slice

Smallest disabled-by-default increment that satisfies the invariants and
acceptance criteria for Phase 1:

1. Add `ProvisioningMode` enum (`disabled` default) + owner policy object
   (allowlists, quotas, local reserve, preemption, emergency stop) —
   **WS C**; policy is local and remote-immutable.
2. Add `iw.provisioning/1` capability negotiation + feature flags —
   **WS B**; unknown versions fail closed.
3. Privacy-filtered `provision.capacity` advertisement (advertise-only never
   downloads/loads) — **WS A/B/D**.
4. Dry-run planner reusing `route_preview` primitives for federated
   candidate eligibility/rejection reasons — **WS F**.
5. GUI inventory + owner-policy controls — **WS H**.

Phase 1 must pass: non-opted-in peers unchanged and non-provisionable;
advertise-only never downloads/loads; disabled default; no GUI scheduling
logic. Each later phase gates on the previous (approval → autonomous →
hardening) per §15.

### Status (2026-10-10)

Delivered and committed (branch `feat/federated-provisioning-phase1`, on
`inferweave/inferweave`): items **1**, **2** and **3**.

- `crates/iw-core/src/provisioning.rs` (`af0abef0`) — `ProvisioningMode`
  (`Disabled` default) + `OwnerPolicy` + side-effect-free
  `permits(policy, parent, action)` gate. Enforces: disabled by default (no
  silent opt-in), remote cannot change policy, observe-only never
  downloads/loads, fail closed (emergency stop beats all; empty allowlist
  authorizes nobody). 10 tests.
- `crates/iw-core/src/fed_capabilities.rs` (`af0abef0`) — `iw.provisioning/1`
  capability token wired into the existing versioned negotiation (in force
  only when both sides name it).
- `crates/iw-core/src/provision_capacity.rs` (`1698a4d1`) — the
  privacy-filtered observe-only signal `iw.provisioning.capacity/1`:
  topology-free (no node/GPU/placement identity), coarse per-model offers, one
  aggregated `available_vram` `Quantity`, `from_adverts()` aggregator (unknown
  VRAM never summed as zero), and structural `validate()` (a disabled owner
  must not advertise). 10 tests.
- `crates/iw-core/src/provision_planner.rs` (`9b1d1726`) — the federated
  dry-run planner: which offering owner could serve a request, reusing
  `route_preview::ReasonCode`'s closed rejection vocabulary. Pure and
  eligibility-only (never placement, never reserves), keyed by the opaque
  `offerer` token (GUI stays a thin client with no solver). Hard rules: model
  is exact with a qualifier boundary; context ceiling never widened;
  below-minimum slots is a hard mismatch; a disabled owner is never planned
  onto; a stale signal is refused before any match. 11 tests.
- `crates/iw-protocol/src/provision.rs` (`7f8cdf0b`) — the `provision.*`
  protocol message family and wire schemas (WS B, master spec §6):
  `ProvisionFeature` flags (approvals/leases/revocation), the §7
  `ProvisionState` state machine with a tested transition table (terminal →
  `RELEASED`, absorbing; never reactivated — fencing), the `ProvisionEnvelope`
  (schema version, id, idempotency key, actor, bounded provenance, expiry,
  trace), and the tagged `ProvisionMessage` family
  (capabilities/request/offer/reserve/approval/activate/revoke/heartbeat).
  Fail-closed: incompatible major version refused; unknown kinds/features
  refused at deserialization; `requires_feature()` gates message use by
  negotiated flags. Self-contained (no `iw-core` dependency), disabled by
  default (in force only when `iw.provisioning/1` is negotiated). 16 tests.
- `crates/iw-gateway/src/provision_controller.rs` (`5e336b65`) — the
  owner-side controller core (WS E, master spec §7): an in-memory reservation
  ledger that drives a provision through `ProvisionState`, and the single
  place the owner's policy is applied to a remote parent. Disabled by default
  and gated end to end — a default `OwnerPolicy` is `Disabled` with an empty
  allowlist; every remote action is checked with `provisioning::permits`; and
  in Phase 1 the gate refuses `Action::Activate` in every mode, so a
  reservation can be booked by an allowlisted parent but can never be
  activated (nothing downloads or loads). Invariants enforced: `on_request`
  (gate → dry-run planner vs advertised capacity → offer), `on_reserve`
  (binds to a real offer key, single-use token, fencing epoch, expiring
  lease), `activate` (token consumed once, fencing epoch checked;
  `Reserved→Activating→Ready` when a later workstream enables it),
  `tick(now)` (clock-free lease expiry), `revoke`/`preempt` (terminal →
  `RELEASED`; preempt lets a local client outrank a non-live upstream
  reservation). Every state change returns a `ReservationEvent` for the audit
  log. Pure and clock-free. 10 tests.

**WS C wire transport adapter delivered** (`43cdb0c2`):
`crates/iw-gateway/src/provision_transport.rs` bridges raw `provision.*`
bytes to the controller — canonical JSON decode/encode with envelope
validation and a 1 MiB body cap; feature-negotiation gating
(`requires_feature`, a message needing an unnegotiated feature is refused,
never silently dropped); bounded idempotency dedup by key (replay is a no-op
ack); and dispatch (capabilities negotiate+reply, request→offer,
reserve→reserve-confirmation, activate/revoke→controller, heartbeat
no-op). `Controller::on_reserve` now takes the wire `ProvisionReserve`
body and binds to an `OfferRecord` store by offer id (`in_reply_to`),
never taking model/slots/offer_key from the requester; stale offers are
not bindable. Disabled by default: a default `OwnerPolicy` refuses every
message via the controller gate. 8 transport tests, 10 controller tests.

**WS D durable reservation/lease persistence delivered** (`35feffa5`):
`crates/iw-gateway/src/provision_store.rs` persists the controller's
ledger as a whole [`ControllerSnapshot`] (reservations, offers, capacity,
`next_fencing_epoch`) atomically — write-temp + `fsync` + rename, the same
`actuator_lease` discipline. `Controller::snapshot()/restore()` rebuild the
ledger without ever overriding the owner policy (local config,
remote-immutable); restore refuses incompatible format markers (fail
closed). The fencing epoch is now a durable monotonic counter, so a
restored controller never reissues a revoked epoch. 7 store tests.

**Parent-side provisioning client core delivered** (`1d048168`):
`crates/iw-gateway/src/provision_client.rs` drives the parent's half of
`provision.*` — request (correlating on the immutable `request_digest`),
on_offer (refuses mismatch/stale offers), reserve, on_reserve_confirmation
(records the owner-minted single-use token + fencing epoch), and
activate()/revoke() (formulate the messages; activation still subject to
the owner's Phase 1 observe-only gate). Pure and clock-free. 7 client
tests.

**Provisioning HTTP transport wiring delivered** (`9d89e1ab`):
`crates/iw-gateway/src/provision_http.rs` turns a `provision.*` request
body into a `provision.*` response body over the gateway's HTTP surface —
`handle_provision_request` bridges one body to the controller via the
transport (decode/feature-gate/dedup/dispatch, mapping outcomes to HTTP
statuses incl. idempotent-ack on replay), and `ProvisionHttpClient` drives
the parent side (request → offer → reserve → confirmation → `Reserved`).
The full parent↔owner round-trip is exercised in one test. Disabled by
default: a handler on a default `OwnerPolicy` refuses every request.

**Live-server registration delivered** (`70f16215`): `POST /iw/v1/provision`
is registered on the live `Gateway` (a `provision: Mutex<Option<
ProvisionTransport>>` field, `None` by default so the endpoint is absent and
nothing is served — disabled by default; `with_provision_transport` builder
mirrors the `peer_deny` convention). The handler reads the sender's origin
token from the query (like `/iw/v1/admission`) and feeds the body to
`handle_provision_request`. E2E tests against a real HTTP client and live
gateway prove: endpoint absent (404) without a transport; negotiate→
request→offer over the wire (200); a parent outside the allowlist refused
(403) on request, fail closed.

Item 5 (operator API + persisted owner-policy store) delivered in PR #916; autonomous bounded admission delivered in PR #919 — see the Item 6 status section below. Remaining (later workstream): the GUI that calls the operator API (WS H).

### Status — Phase 2: approval-required activation (2026-10-11)

Implemented on `feat/provisioning-phase2` and merged via PR #881 (merge
commit `6a227e09`), the approval-required slice that closes the observe-only
gap: a parent can now bring an approved reservation live. The gate stays stateless (policy-level); the approval is a
per-reservation controller concern.

- `crates/iw-core/src/provisioning.rs` — `ApprovalRequired + Action::Activate`
  now returns `Allowed` at the policy level (the mode *does* permit
  activation); `Disabled`/`AdvertiseOnly`/`Autonomous` remain refused (fail
  closed). `Refusal::ApprovalRequired` is retained, now emitted by the
  controller when a specific reservation is not yet `Approved`.
- `crates/iw-gateway/src/provision_controller.rs` — new `Controller::approve`
  (`Reserved → Approved`, grants budget, binds request digest + policy
  revision + fencing epoch, returns a `provision.approval::Approved` message)
  and `Controller::reject` (`Reserved → Revoked → Released`, returns
  `provision.approval::Rejected`). These are local operator actions and are
  **not** gated by `permits` (the owner authorizes its own reservation; the
  gate still governs the parent's later `activate`). `request_digest` is
  threaded request → offer → reservation so the approval binds to the
  original request; `approved_budget_vram_bytes` and `policy_revision` are
  recorded on the reservation. `activate()` now requires `state == Approved`
  (per-reservation approval gate) before `Approved → Activating → Ready`;
  observe-only activation is still refused by the gate. Snapshot format
  bumped to `iw.provisioning.controller/2` (restore refuses the old marker,
  fail closed).
- `crates/iw-gateway/src/provision_client.rs` — new `AttemptState::Approved`
  and `on_approval()`: the parent records the granted budget/policy revision
  and may activate from `Reserved` or `Approved`; a `Rejected` approval ends
  the attempt (`ClientError::Rejected`).
- `crates/iw-gateway/src/provision_http.rs` — inbound `provision.approval`
  routed to the client; full approve → activate HTTP round-trip test.
- The transport's inbound refusal of `Approval` stays correct: approval is an
  owner → parent (outbound) message, never inbound to the owner.

Tests: controller approve→activate and reject flows, transport
approval-required activation, HTTP round-trip, client approval/rejection;
updated gate and `may_activate` tests. Full `iw-gateway` lib (315) and
`gateway_e2e` (29) suites green; clippy clean on the changed modules.

Item 5 (operator API + persisted owner-policy store) delivered in PR #916; autonomous bounded admission delivered in PR #919 — see the Item 6 status section below. Remaining (later workstream): the GUI that calls the operator API (WS H).

---

## 5. Open questions for the spec

- Does `provision.capacity` reuse `node_advert`/`capacity_frontier` shapes or
  define new ones? (Recommend reuse + additive fields.)
- Where does the provisioning controller live in the current gateway
  (`crates/iw-gateway/src/`) vs the Go gateway? The Rust `iw-gateway` is the
  natural home; the Go gateway is a relay/UI per §13.
- Lease/approval persistence: reuse `iw-storage` (SQLite) patterns. **Resolved (Item 5, PR #916):** the owner policy is persisted to its own `provisioning-policy.json` in the existing `ProvisionStore` directory using the same atomic write-then-rename discipline as the ledger snapshot — consistent with the existing store pattern, no SQLite dependency, and it keeps the ledger snapshot policy-free (a restored ledger never overrides the operator's configured policy).

---

## 6. Status — Item 5: operator API + persisted owner-policy store (2026-10-12)

Implemented on `feat/provisioning-item5` and merged via PR #916 (commit
`bcfc9473`). This is the owner's management half of the Phase 2 approval
flow, which previously had `approve()`/`reject()` reachable only
programmatically. Item 5 delivers the owner-facing gateway API and makes the
owner policy durable.

- `crates/iw-gateway/src/provision_operator.rs` (new) — a pure, clock-free,
  testable operator handler plus route parsing. Actions: get/set policy,
  list pending approvals, approve/reject a reservation, and a status view
  (policy + capacity + ledger counts). The handler never bypasses the gate:
  it drives the same `Controller` the transport drives, and approve/reject
  move a reservation through the same state machine a remote `activate`
  would have to pass. No model is ever downloaded or loaded here.
- `crates/iw-gateway/src/provision_controller.rs` — `Controller::set_policy`
  (an *owner operator* action, **not** gated by `permits` — the operator is
  configuring its own opt-in mode/allowlist/emergency stop) and `pending()`
  (the `Reserved` approval-queue view).
- `crates/iw-gateway/src/provision_store.rs` — persist the `OwnerPolicy` to
  its own `provisioning-policy.json` with the same atomic write-then-rename
  discipline as the ledger snapshot. Policy is stored **separately** from the
  ledger, so a restored ledger never overrides the operator's configured
  policy; a corrupt policy file is refused (fail closed), never silently
  replaced by defaults.
- `crates/iw-gateway/src/server.rs` — register `/iw/v1/provision/operator/...`
  gated on the **owner**: admin secret (`x-inferweave-admin`) OR loopback
  (`same_host`), mirroring `occupancy_shows_devices`. A parent's `origin=`
  token is explicitly *not* sufficient (fail-closed), so a remote parent
  cannot touch policy or approve its own reservation. Attach a `ProvisionStore`
  via `Gateway::with_provision_store` to persist policy and operator
  decisions across a restart (without one, the API works but is volatile).

Security model: operator endpoints are owner-only and distinct from the
parent-facing `/iw/v1/provision` channel. The approval/rejection message an
operator action produces is surfaced in the API response body for the
operator tooling to relay to the parent over the inter-gateway channel
(approval remains an outbound owner→parent message; the transport's inbound
refusal of `Approval` stays correct).

Tests: operator handler unit tests (policy get/set + persist, approvals list,
approve/reject, status, route parsing), store policy round-trip + malformed-
file refusal, and gateway e2e operator endpoints (policy read/persist, status,
empty approvals, owner gating). Full `iw-gateway` lib (361) and `gateway_e2e`
suites green; clippy clean on the changed modules. Remaining later-phase work:
the GUI that calls this API (WS H).

---

## 7. Status — Item 6: autonomous bounded admission (2026-10-13)

Implemented on `feat/provisioning-autonomous` and merged via PR #919. This
closes the admission gap identified in the §2 gap matrix (autonomous bounded
admission was previously **Missing**). Under an `autonomous` owner policy with
explicit bounds, the controller auto-approves a reservation on reserve when it
fits; when it does not (or the bounds are absent), the reservation stays
`Reserved` and waits in the operator approval queue — fail closed, never
auto-refused.

- `crates/iw-core/src/provisioning.rs` — `(Autonomous, Action::Activate)` now
  returns `Allowed` at the policy level (the gate stays stateless);
  `Refusal::AutonomousUnavailable` is removed. `OwnerPolicy` gains the
  bounded-admission fields `max_concurrent: Option<u32>`,
  `max_total_vram: Option<u64>`, and `per_parent_quota:
  BTreeMap<String, PerParentQuota>` (all serde camelCase, `#[serde(default)]`,
  fail-closed: absent → `None`/empty). New `PerParentQuota` struct with
  `max_concurrent` and `max_total_vram` caps.
- `crates/iw-gateway/src/provision_controller.rs` — the requester's named
  budget (`ProvisionRequest.budget_vram_bytes`) is carried through the offer
  (`OfferRecord.budget_vram_bytes`, additive `#[serde(default)]`) to the
  reservation (`approved_budget_vram_bytes`). `on_reserve` now returns
  `(Reservation, ProvisionMessage, Option<ProvisionMessage>)` and, when the
  policy is `Autonomous` and `fits_autonomous_bounds` passes, reuses the
  existing `approve()` machinery to auto-approve (`Reserved → Approved`,
  `policy_revision = 0`) and returns the approval as the third tuple element.
  `fits_autonomous_bounds` is fail-closed: no requester budget or *no bounds
  configured at all* → defer; it counts live (Approved/Activating/Ready)
  reservations against `max_concurrent`, the sum of granted budgets against
  `max_total_vram`, and each parent's quota. Snapshot format stays
  `iw.provisioning.controller/2` (no `Reservation`/`OfferRecord` layout break).
- `crates/iw-gateway/src/provision_transport.rs` — the `Reserve` dispatch
  appends the auto-approval to `outbound` when present, so the parent receives
  both the reserve confirmation and the auto-approval in one reply. No
  parent-side client change was needed (`on_approval` already handles
  `Approved`; `activate()` works from `Reserved` or `Approved`).
- No new operator endpoints: auto-approved reservations flow to `Approved` and
  appear in the existing status/approvals views; bounded-out reservations wait
  in the operator queue exactly as in approval-required mode.

Fail-closed decisions: autonomous admission is only permitted under an
*explicit* bound set (empty bounds defer everything); a reservation over any
cap, or with no requester-named budget, defers rather than auto-refuses; a
policy-revision counter is deferred to a hardening phase (`policy_revision = 0`
for auto-approval, matching the operator path's initial value). Non-goals in
this slice: local reserve, preemption, per-parent VRAM caps distinct from
quota, cross-process failover fencing, and the GUI.

Tests: gate (`Autonomous + Activate → Allowed`), `OwnerPolicy`/`PerParentQuota`
serde + fail-closed defaults, controller auto-approve/defer matrix (within
bounds, over concurrent cap, over VRAM cap, over per-parent quota, no budget,
empty bounds, bounded-out waits for operator approval), transport relay
(autonomous reserve → `reserve` + `approval` outbound; approval-required →
`reserve` only), an HTTP round-trip that drives request-with-budget → offer →
reserve → auto-approval → activate with no operator action, and a gateway e2e
that PUTs an autonomous bounded policy and verifies it persists across a
restart. Full `iw-gateway` lib (379) and `gateway_e2e` (33) suites green;
clippy clean on the changed modules. Remaining later-phase work: the GUI that
calls the operator API (WS H), then hardening per §15.
