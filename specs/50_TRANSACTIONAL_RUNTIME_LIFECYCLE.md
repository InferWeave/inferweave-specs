# 50 — Transactional Runtime Hot-Swap Lifecycle

## Relationship to existing state machines

[`state-machines/runtime.md`](../state-machines/runtime.md) already defines a
lifecycle of
`absent → starting → ready | degraded | draining → stopping → stopped | failed`.
[`specs/43_GPU_PLACEMENT_HOT_SWAP.md`](43_GPU_PLACEMENT_HOT_SWAP.md) defines GPU
placement hot-swap. This specification refines the runtime state machine into a
**transactional** lifecycle with explicit preparation, validation, and
unloading transitions, and reconciles the two so a hot swap is a single
transactional transition, not an independent set of ad-hoc steps.

## Transactional lifecycle

The canonical runtime lifecycle, in dependency order:

```
DISCOVERED
   │ resolve
   ▼
RESOLVING ──────────────┐ (resolution failed → FAILED)
   │ resolve ok
   ▼
PREPARING ──► DOWNLOADING ──► PREPARING   (weight/artifact acquisition, content-addressed)
   │ prepare ok
   ▼
RESERVING  (capacity/grant reservation under the rebalancer's authority)
   │ reserved
   ▼
STARTING
   │ started
   ▼
LOADING
   │ loaded
   ▼
WARMING
   │ warm
   ▼
VALIDATING  (probe that the runtime actually serves before READY)
   │ validated
   ▼
READY ◄──► BUSY / IDLE      (serving; the rebalancer may target it)
   │ drain
   ▼
DRAINING
   │ unload
   ▼
UNLOADING
   │ stopped
   ▼
STOPPED
```

Failure and cancellation edges: any of `RESOLVING`, `PREPARING`,
`DOWNLOADING`, `RESERVING`, `STARTING`, `LOADING`, `WARMING`, `VALIDATING`
may transition to `FAILED` (or, for cancellations, directly to `STOPPED`).
`DRAINING` and `UNLOADING` are terminal paths to `STOPPED`; a drain may be
interrupted back to `READY` only if the drain was cancelled before unload.

## Transactionality and the rebalancer

- `RESERVING` must be reconciled with the existing rebalancer's reservation
  model ([`specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md`](30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md)).
  A reservation is fenced and expires; a hot swap reuses the existing
  reservation authority and never creates a second scheduler.
- `READY ↔ BUSY / IDLE` transitions are the only states the rebalancer may
  target for placement/reclaim. A runtime in `VALIDATING` or `WARMING` is not
  yet schedulable.
- A hot swap is atomic with respect to the deployment when both versions fit: the old runtime is
  not removed from the routable set until the new one has passed `VALIDATING`.
- When both versions cannot fit on one node, the controller must choose either a controlled
  **drain-and-swap** with an explicit availability impact or a **cross-node** replacement that is
  healthy before route cutover. It must never promise unconditional zero downtime. A failed load,
  warm, validation or cutover rolls routing and reservation state back to the preserved known-good
  deployment; if rollback also fails, the device is quarantined under specs/36.

## Single-flight loading

Loads are coalesced only by `deployment_key`. Its exact digest input is the
`schemas/v1/deployments/deployment-identity.json` object: `schema_version`, `modality`, `model_id`,
`artifact_bindings`, `runtime_identity`, `effective_profile_digest`, `policy_digest`, and
`resource_contract_digest`, with no additional top-level fields. Rich profile, policy, runtime
configuration, and resource documents—including documents containing floating-point values—are
bound by their versioned SHA-256 digest fields. The identity therefore has a closed
string/digest-only value domain and no JSON-number canonicalization ambiguity. Encode it as RFC
8785 JSON Canonicalization Scheme UTF-8, hash the bytes
with SHA-256, and render `sha256:<lowercase-hex>`. `conformance/deployment-key-vectors.json` is the
cross-language known answer. Deployment ID, instances, assignment, placement reason, timestamps,
aliases, request IDs, and waiter IDs are excluded live data. `artifact_bindings` maps canonical semantic roles such as `weights` and `tokenizer` to digests;
JCS object-key ordering makes enumeration order irrelevant while a role change remains meaningful.
Receivers recompute `deployment_key` from `manifest` and reject a mismatch before lookup,
single-flight coalescing, reservation, or load; a caller-supplied key is never trusted as identity.
Each caller has an independent `waiter_id`; cancelling one
waiter detaches that waiter and does not cancel the shared load or other waiters. The manager may
cancel the underlying load only after the final waiter detaches, an authority revokes the fenced
reservation, or a classified fatal failure occurs. Late results from an older fencing epoch are
discarded.

## Runtime reservation contract

The rebalancer remains the sole reservation authority. The additive `contractVersion: 1` shape in
`schemas/v1/resources/reservation.json` carries an idempotency key, monotonic fencing epoch and a
safe-peak envelope covering weights, KV cache, activations, runtime workspace, auxiliary models,
temporary loading peak, CPU RAM, disk, GPU count and topology. Admission evaluates the whole safe
peak with headroom, never weights alone. Every byte is the `Quantity` from specs/46, including
explicit `basis`, `source`, and `confidence`; `unknown` and `unsupported` carry no bytes and cannot
be admitted as zero. `gpuSafePeak.bytes` must be at least the arithmetic sum of all six contributor
bytes plus `gpuHeadroom.bytes`. Admission may compare a new peak with current free bytes, or sum all
active holds plus the new peak against total allocatable capacity; it must not mix those two
conventions. The executable reference uses the latter convention. The result basis is
`estimated` with low confidence if any input is estimated or declared; only arithmetic over
measured/derived inputs is `derived`, and its confidence cannot exceed the weakest input or medium.
Initial `requestedBytes` and `effectiveBytes`
must cover `gpuSafePeak.bytes`. Retrying an idempotency key returns a prior grant only when the
immutable request identity—including payload digest, exact fencing epoch, owner, physical resource,
resource envelope and byte request—matches; otherwise it is a conflict. A fence matches the current
grant exactly: both older and unissued future epochs are rejected.
`payloadDigest` is the lowercase `sha256:<hex>` digest of that canonical immutable reservation
request and is required on every `contractVersion: 1` wire record; group and retry checks use the
wire value rather than an out-of-band caller assertion.

The canonical ledger formula is `observed physical allocation + effective unobserved holds + new
safe peak <= total allocatable budget`, evaluated per device for GPU bytes and per
`resourceDomainKey` for CPU RAM and disk. When an allocation becomes physically observable, the
authority shrinks its effective hold by the same amount before the next decision, so it is never
counted once as physical and again as reserved. The Python reference is fixture/conformance code
for initial grants (`effective == requested`), not a production allocator or a second scheduler;
production retains the existing controller/outbox reservation authority and reconciliation path.

`progressTimeoutMs` is selected by the sole reservation authority within the negotiated
`runtime_reservations/1` contract. The authority accepts only increasing `progressSequence` values
for observable work such as verified bytes, completed preparation steps or runtime load milestones,
records `lastProgressAuthorityTick`, and sets `leaseDeadlineAuthorityTick` to that monotonic local
observation plus the timeout. Producer `lastProgressAt` and `expiresAt` wall times are display-only:
progress also carries the grant's exact fencing epoch. An older or unissued future epoch, a
non-increasing authority observation tick, or progress observed at/after the current lease deadline
is rejected and cannot revive or extend the grant, even when reconciliation has not run yet.
clock skew cannot extend or shorten a lease. Per invariant 37, accepted progress can sustain an
arbitrarily long load; silence past the authority deadline expires it. Reconciliation after crash
or partition releases every GPU, CPU RAM, disk, topology, and auxiliary hold of the expired
reservation.

The physical de-duplication key is the stable resource identity (`resourceId`, falling back to
stable node/device identity), which excludes the advertising parent. A `parent_id` remains path
provenance. Capacity for the same physical GPU arriving through two parents is one physical
resource, never two schedulable copies. The existing rebalancer may issue distinct fenced
reservations for co-resident deployments only when their aggregate active GPU safe peaks fit the
device's total capacity. `resourceDomainKey` names the stable host capacity domain, so CPU RAM and
disk safe peaks are aggregated across reservations on distinct GPU keys as well as CPU-only work.
Each GPU grant has `gpuCount: 1`, exactly one `deviceIds` entry, and a
`physicalResourceKey = resourceDomainKey + "/" + deviceId`; a multi-GPU placement uses one grant
per device joined by the required nonempty `placementGroupId`. Shared host CPU RAM and disk peaks
are charged once for each `(resourceDomainKey, placementGroupId)` pair, so per-device rows in one
atomic placement do not multiply the same host peak while unrelated placements still aggregate.
The reservation authority issues the group ID and binds it to one domain, logical payload digest,
owner, exact fence, and shared host peak contract; reuse with a different claim is rejected.
Thus overlapping device sets cannot evade accounting through a caller-chosen aggregate key.
The same
logical demand learned through multiple parents coalesces to one grant; a different demand is never
aliased to it.

CPU-only embeddings, STT, and prediction use this same authority with `accelerator: cpu`,
`gpuCount: 0`, empty `deviceIds`, a stable host-capacity `physicalResourceKey`, and zero evidenced
GPU quantities. Their CPU RAM and disk safe peaks remain admitted and aggregated; no fake GPU
worker or GPU reservation is created. Legacy reservations without `contractVersion` retain the
specs/46 GPU-ledger shape.

## Transactional caches

Model, runtime and optimization artifacts use three distinct cache classes with the common
`schemas/v1/artifacts/cache-state.json` contract. `artifact_id` or a legacy custom `digest128`
lookup key is identity only; it is not cryptographic integrity evidence. New entries carry a
separate SHA-256 `content_digest`, stream multi-GB acquisition into bounded-memory staging storage,
verify the complete digest, then publish atomically. Partial or corrupt content is never visible as
published and is quarantined. Pins protect active, rollback and operator-required entries from
eviction. `offline_ready: true` means the entry and every declared dependency are already verified
locally; offline mode fails explicitly rather than silently fetching.

## Invariants

1. **Single allocation authority.** The lifecycle's `RESERVING`/`DRAINING`
   transitions only express intent to the existing rebalancer; no second
   scheduler is introduced.
2. **Availability-aware swap.** The outgoing runtime remains routable until an incoming runtime
   validates when capacity permits; constrained capacity uses explicit drain-and-swap or cross-node
   replacement and reports its availability impact.
3. **Validated-ready.** A runtime is never advertised `READY` without a
   successful `VALIDATING` probe.
4. **Terminal-state discipline.** `FAILED` and `STOPPED` are absorbing;
   `DRAINING`/`UNLOADING` cannot be interrupted back to `READY` once unload
   begins.

## Required tests

- state-machine-transitions: every allowed transition is enumerable and every
  forbidden transition is rejected by the machine model.
- availability-preserved: during a hot swap the routable set always contains at
  least the validated runtime when simultaneous or cross-node capacity exists; constrained
  drain-and-swap records the explicit gap and rolls back on failure.
- no-second-scheduler: `RESERVING` and `DRAINING` are expressed as events to the
  existing reservation authority, never as direct placement.
- single-flight: two waiters share one immutable-key load and cancelling either waiter cannot
  cancel the other.
- reservation-envelope: retry idempotency, stale-fence rejection, safe-peak accounting and
  progress-based expiry are executable.
- cache-transaction: each of the three cache classes rejects unverified publication, preserves
  pins, supports offline checks and streams acquisition with bounded memory.
