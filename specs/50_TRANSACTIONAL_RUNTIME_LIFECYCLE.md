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
`requestIdentity` is the exact non-self-referential digest input: `schema_version`, `deployment_key`,
`owner_component`, `owner_gateway_id`, `kind`, `physical_resource_key`, `resource_domain_key`, `placement_group_id`, and the
base-10 string `requested_bytes_decimal` (bounded to 9007199254740991), with no additional fields. It contains only strings.
Encode it as RFC 8785 JCS UTF-8 and set `payloadDigest` to lowercase
`sha256:<hex>` over those bytes. `payloadDigest`, idempotency key, fence, authority outputs,
progress, lease, and timestamps are excluded. Receivers recompute the digest; group and retry
checks never trust an out-of-band caller assertion. Before admission, every duplicated identity field must equal its top-level reservation/admission value. Separate owner fields avoid delimiter collisions.

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
The reservation authority issues the group ID and binds it to one domain, immutable deployment key,
owner, reservation kind, exact fence, and shared host peak contract; reuse with a different claim
is rejected.
Thus overlapping device sets cannot evade accounting through a caller-chosen aggregate key.
The same
logical demand learned through multiple parents coalesces to one grant; a different demand is never
aliased to it.

CPU-only embeddings, STT, and prediction use this same authority with `accelerator: cpu`,
`gpuCount: 0`, empty `deviceIds`, a stable host-capacity `physicalResourceKey`, and zero evidenced
GPU quantities. Their CPU RAM and disk safe peaks remain admitted and aggregated; no fake GPU
worker or GPU reservation is created. Legacy reservations without `contractVersion` retain the
specs/46 GPU-ledger shape.

## Managed pinned-profile increment (2026-10-27)

IW-RT-003/B-T03 and IW-BOOT-001/IW-BOOT-004/P0-T03 also cover the existing Rust
owner's bounded managed-profile path. This increment reuses the adaptive controller,
its persisted instances, fenced owner lease, operation outbox and existing router admission.
It introduces neither another allocator nor a separate runtime owner. It does **not**
claim implementation or qualification of the full `runtime_reservations/1` contract,
immutable deployment-key single-flight waiter semantics, or every lifecycle stage above.
Its request ID is a retry identity for one explicit placement, not a deployment key.

### Internal owner control and durable retries

Authenticated owner control uses bearer authorization on
`POST /internal/orchestrator/control` and `GET /internal/orchestrator/snapshot`.
The action discriminator is snake case on the wire:

```json
{"action":"ensure_profile","request_id":"run-example","model_id":"canonical-model","profile_digest":"sha256:<64 lowercase hex digits>","worker_ids":["worker-a","worker-b"]}
```

`EnsureProfile` binds the configured model version, exact raw-file profile digest and
explicit unique worker set to the request ID. Worker order does not change retry identity.
The owner validates placement and records either its instance identity or an error through
its existing state/outbox path; the client does not reserve or assign workers itself.
An accepted queue submission returns HTTP 202 with `accepted: true` and `request_id`.
This acknowledges queueing only. Invalid authorization, malformed control, unapproved
profile bindings or conflicts fail explicitly; asynchronous semantic failure appears in
the durable record. Neither 202 nor a helper process starting establishes READY.

`CancelProfile` uses `{"action":"cancel_profile","request_id":"run-example"}`.
Cancellation is durable even before ensure, during loading/warming, or after readiness.
A cancelled identity cannot be replayed to create another runtime; late load/warm results
cannot revive it. Repeating the same ensure resolves to its existing snapshot record; changing the
model/version, profile or worker set under that ID is a conflict. The ledger retains at
most 1024 distinct ensure/cancel identities, including cancel-before-ensure tombstones.
It does not evict old identities to accept new work: saturation fails closed and requires
owner intervention. This bounded retained history is not indefinite deduplication after
an operator deliberately replaces the controller state.

Snapshot `profile_requests` is an object keyed by request ID. Each record contains
`intent` (`request_id`, `model_id`, `model_version`, `profile_digest`, `worker_ids`),
nullable `instance_id`, nullable `error`, `created_at_ms`, and `cancelled`.
A cancel-before-ensure tombstone has null intent and instance identity. Existing
`instances` and `workers` remain arrays; instance states include `staging`, `loading`,
`warming`, `ready`, `active`, `draining`, `evicting`, `failed`, and worker `assignment`
is an instance ID or null. These implementation states are a projection of the lifecycle,
not additional canonical transactional states. Owner-confirmed release requires the
cancelled record and removal of its instance after unload acknowledgement; former worker
assignments must no longer reference that instance. Reassignment to a later instance is
not evidence that the old instance remains loaded. A tombstone confirms no instance was
created for that identity. Control loss cannot be converted into a claim of release.

### Bounded request-scoped snapshot projection

Foreground clients use the same authenticated endpoint with
`GET /internal/orchestrator/snapshot?request_id=<URL-form-encoded ID>`. Authenticate
before query validation. The query is at most 1024 bytes and contains exactly one
`request_id`: empty values, duplicate/unknown parameters, malformed percent encoding
or a decoded ID outside the owner's nonempty ASCII-graphic, 256-byte limit return
HTTP 400 with `error.code: invalid_request_query`. An unknown valid ID is not an error.
No query preserves the legacy full diagnostic snapshot.

The projection reads one existing snapshot under its lock. It retains original
`mode`, `version` and `updated_at_ms` when present; it does not mint freshness or a
new revision. `profile_requests` contains only the selected record, or `{}` for an
unknown ID. The projected record retains its five-field intent, `instance_id`,
`cancelled` and nullable `error`; it omits `created_at_ms`. A nonnull backend error is
replaced with the bounded marker `profile request failed`, never copied as raw text.
Fields absent in the underlying record remain absent so clients fail closed.
`instances` contains only the record's selected instance, with `id`, `model_id`,
`model_version`, `state`. `workers` contains only the intent's workers, with `id` and
`assignment`; a later reassignment is preserved rather than hidden. Tombstones have
no intent workers or selected instance. An unknown ID returns empty request, instance
and worker collections plus any original snapshot metadata. This bounds client reads
independently of the retained retry ledger without weakening its 1024-identity limit
or returning a complete history for each poll. It adds no public scheduling authority.

### Authoritative profile and inference identity

Owner `profile_files` and `profile_digests` maps have identical canonical-model keys.
The owner reads bounded regular profile files without following symlinks, checks the
SHA-256 of their exact bytes, parses `RuntimeProfile`, and requires explicit `servedModel`.
The model must exist in the configured catalogue. Profile binding changes or removal
against persisted owner state fail restart; a changed binding requires a new model identity.
Concrete serving `Engine::Sglang` uses wire name `sglang` and the LLM family; profile
launch engine vocabulary in `schemas/v1/requests/node-assignment.json` includes it. This
does not change the runtime-family adapter type enum or prove live SGLang kernels.
Engine/backend metadata is derived from this verified profile, not guessed from a display
label, accelerator vendor or runtime name.

The public canonical model ID and backend HTTP `servedModel` are distinct. For an
otherwise admission-eligible route, route identity
binds profile digest, engine/backend and backend model name. Each admitted lease retains
its selected instance and backend model name: direct HTTP inference rewrites the request
model from that pinned lease, not a later mutable catalogue lookup. Canonical model identity
remains the control/admission/accounting identity. A profile or backend-name update cannot
retarget an already admitted request. This is an identity boundary, not evidence that a
Go/public gateway or every relay path already preserves the binding.

### Default managed-profile quarantine

Profile loading and helper warm/health success establish diagnostic lifecycle state only.
Until genuine qualification is integrated, the owner excludes managed-profile models,
aliases, instances and activation candidates from the ordinary router projection (including
the shadow catalogue), and suppresses
ordinary demand-driven automatic placement for those models. An explicit `EnsureProfile`
may exercise the laboratory lifecycle and diagnostic snapshot, including `ready`/`active`,
but that state does not make the instance ordinarily discoverable, schedulable or routable.
Legacy routes without managed profile bindings retain their existing behavior.

There is no `qualified: true` configuration escape hatch or readiness-based promotion.
Qualification must traverse the genuine authorization/admission and exact-deployment proof
path before ordinary discovery/admission can use the profile. The direct lease-pinned
model rewrite described above preserves identity for an otherwise eligible admitted route;
it is not a bypass for a quarantined managed profile. Real qualification integration and
its negative cases remain **owed**. A fake HTTP backend or a helper Warm acknowledgement
cannot authorize ordinary serving or close this gate.

### Node helper and device materialization

The existing helper's operator-owned `profile_models[canonical_model_id]` binds
`profile_file`, `profile_sha256`, version `fingerprint`, `source_dir`, checksum-bearing
`artifacts`, and allowed `mount_roots`. Requests must match that fingerprint, profile
digest and explicit backend model name. Artifacts remain verified before launch; parsed
profile launch content is not authority to bypass approved roots or device assignments.
Stage/load/warm/inspect/drain/unload reuse the existing helper journal and fences.

The helper persists immutable preparation identity before either Stage or Load, including
when cached artifacts skip Stage. Deterministic pre-launch failure may release only after
confirmed absence; an actual unresolved load intent retains its holds. Successful unload
retains an immutable terminal record and known container ID so a lost acknowledgement can
be replayed across owner epochs only after rechecking ID and name absence. A replacement
container is never removed or reported absent by name alone, and terminal instance IDs
cannot be staged or loaded again. The helper bounds these distinct identities at 4096:
new unseen identities fail closed at saturation while existing retries and drains remain
usable. Records are not silently evicted to make room; authorized reconciliation or a new
controlled state epoch is required. Tests must cover cached-artifact first-Load failure,
loaded and stage-only cross-epoch unload, uncertain-load refusal, replacement refusal,
terminal non-resurrection and saturation with existing cleanup preserved.

`nodes[node_id].gpu_runtime_ids` maps stable discovered logical GPU IDs to fixed kernel
physical UUIDs. ROCm masks use validated nonzero physical UUIDs, never PCI discovery IDs
or transient ordinals. Missing or duplicate mappings fail closed. Materialized instance
identity records the selected binding and ordered physical IDs; launch/adoption/inspection
must reconcile that identity against local hardware rather than trust ambient masks.

The typed `gpuBinding: paiton_native_tp2_v1` is restricted to AMD, exactly two GPUs,
`vllm`/`rocm`, and
`ghcr.io/eliovp/paiton-vllm-plugin@sha256:328be15c6f1bc3ec99b1b7a436c4a38eeb82ec36d0589b7bbef38f0e465e11cf`.
Raw profile `PAITON_FN_GPU_MASK` is rejected. Native selectors are materialized only
after exclusive whole-host proof: under the existing logical/physical locks, the complete
local DRM/kernel physical GPU set must equal the assigned two mapped UUIDs. The typed
strategy, ordered IDs and effective candidate environment become immutable helper instance
identity before Docker starts, with full inventory rechecked for launch, adoption,
inspection, warm and unload. Only the local default Docker Unix socket is eligible.
This helper journal/device fence does not prove exact issued-grant authority under
`runtime_reservations/1`, and container launch does not establish runtime quality.

### Acceptance and proof boundary

Required tests cover durable retry/conflict/saturation and restart binding; cancellation
before ensure and across late load/warm acknowledgements; exact profile/helper/artifact
identity; ordered physical mappings and exclusive native binding; lease-pinned inference
model rewrite; and the foreground CLI contract in spec28. Hardware execution and a live
owner → real helper/container → genuinely qualified admitted inference → cancellation/restart demonstration
are **owed**, as recorded in OPEN_GATES. No profile, engine vocabulary addition or local
fake-container test opens production routing, qualification or reservation gates.

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
