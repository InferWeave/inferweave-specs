# 46 — GPU memory accounting, reservations, pressure, decision records and simulation

## Status

**SPECIFICATION ONLY — BLOCKED for production use.** This document defines the `iw.gpu-memory`
capability family of InferWeave Protocol 1.1.0. No deployed component emits or consumes it.
Every required test is recorded `owed` by canonical tasks `P5-T30`–`P5-T32` (feature
`IW-GPUMEM-001`). NVIDIA and AMD hardware validation are owed (`OPEN_GATES.md`). The design
decisions are recorded in `decisions/2026-10-07-gpu-memory-accounting.md`.

## Relationship to specs 45 and 44

This is a minor, additive Protocol v1 release (1.0.0 → 1.1.0). It adds new capability-gated
surfaces and changes no existing field, enum value or endpoint. Its GPU memory model is a strict
superset of the spec 45 "GPU memory model" (`schemas/v1/resources/memory.json`); §11 maps every
spec 45 field onto it. Where the two disagree on a surface this document defines, this document
is authoritative.

## Goal

Let InferWeave know where every byte of GPU memory goes, explain why memory is reserved, and say
how much can safely be reused, so that the **existing** rebalancer can use that capacity without
endangering primary workloads, and so that any consumer can render the result without
recomputing it.

## Non-goals

- A second scheduler or rebalancer. The rebalancer that owns a node is the only authority that
  computes `safeSchedulable`, pressure and eligibility for it; every other gateway relays and
  displays (§3.2, §4).
- Changing topology v2 (spec 40). Its decoders are strict, so no GPU-memory field is ever added
  to it (§10).
- Moving live GPU memory. A move is always start-replacement, advertise, withdraw, drain, unload.
- Treating aggregate fleet memory as one shared allocation. Free memory on independent GPUs is
  not additive.

## Design rules

1. **Bytes, unsigned integers, everywhere.** Every size is bytes, at most 2^53 − 1 so a
   JavaScript consumer reads it exactly.
2. **Unknown is never zero.** Every byte count is a `Quantity` with an explicit `basis` (§2.1).
   An absent quantity means *not reported*.
3. **camelCase JSON** on these surfaces, matching the link and HTTP wire family they ride. §11
   maps them onto the snake_case spec 45 objects.
4. **The node measures; the owning rebalancer composes.** A node reports physical memory,
   attribution and node-local logical reserves. The gateway whose rebalancer owns the node adds
   its placement reservations and computes `safeSchedulable`, `pressure` and `eligibility`.
5. **A new major is a new capability string.** Within a major, fields are only added. Readers
   ignore unknown fields **and** keep unknown enum values verbatim, reading them through the
   fallback each enum documents.
6. **Field names and enum values are case-sensitive.** A key that differs only in case
   (`ResourceId`) is not the field: a consumer whose decoder matches keys case-insensitively
   (Go `encoding/json`) MUST refuse or ignore case variants rather than bind them.
7. **Logical is never physical.** Reservations and the placement-class view are separate
   dimensions and are never added into a physical total.

## Schemas and forward compatibility

The JSON Schemas of this document validate a **producer at exactly Protocol 1.1.0**: their enums
are closed, as spec 45 requires ("reject malformed enums"). A **reader** never uses schema
rejection to drop a document from a newer producer: it ignores unknown fields, keeps an unknown
enum value verbatim and reads it through the fallback documented for that enum (basis → unknown;
placement class → primary; authority → grants nothing; pressure and allocation states →
unknown; anything else → shown verbatim and not acted on). A later minor release adds values to
the schemas; it never removes or re-purposes one.

## 1. Capabilities and features

A capability is negotiated exactly like the existing `iw.<name>/<major>` link capabilities: each
side offers a list on registration and a capability is in force only when **both** lists name it.
A side that names a capability promises to act on it. The Protocol v1 snake_case `features`
object (`schemas/v1/common/features.json`, spec 45 "Feature negotiation") carries the same
family for peers that discover through it. The pairing is frozen data in
`contracts/protocol-v1/gpu-memory-capabilities.json`:

| Feature (`features`) | Level | Capability (`iw.*`) | Meaning when in force |
|---|---|---|---|
| `gpu_memory` | `1` | `iw.gpu-memory/1` | The child sends `gpuMemory` (an `iw.gpu-memory.report/1`) on node telemetry and the heartbeat status, and the parent accepts it. A gateway serves the fleet snapshot (§4). |
| `rebalance_decisions` | `1` | `iw.rebalance-decisions/1` | The gateway serves the event feed (§7) with a cursor. |
| `placement_simulation` | `1` | `iw.placement-simulation/1` | The gateway answers read-only placement simulations from its real rebalancer evaluation (§9). |
| `card_coresidency` | `1` | `iw.card-coresidency/1` | The node accepts more than one assignment for the same GPU and runs the engines side by side. A gateway MUST NOT send a second assignment for a GPU unless this is in force. This is a precondition for packing an opportunistic runtime beside another. |

The existing spec 45 feature `gpu_memory_breakdown` is independent: it advertises the flat
spec 45 `memory` object on Protocol v1 surfaces, while `gpu_memory` advertises this family. A peer
may advertise either or both; neither implies the other.

Plain-string runtime capabilities (`"system_one"`, `"diffusion"`) are a separate family and are
unchanged.

## 2. Common types

### 2.1 Quantity — bytes with provenance

`schemas/v1/resources/quantity.json`. Fields: `bytes`, `basis`, `source`, `confidence`,
`observedAt` (only when it differs from the enclosing GPU's), `note` (at most 128 characters,
operator-facing, never prompts, request contents or secrets).

| `basis` | Meaning | `bytes` |
|---|---|---|
| `measured` | Read directly from a driver or runtime counter for exactly this thing. | required |
| `derived` | Arithmetic over measured values only. | required |
| `estimated` | Uses a model, registry, sizer or constant. | required |
| `declared` | An operator, config or adapter declaration. | required |
| `unknown` | It should exist but could not be read this time. | forbidden |
| `unsupported` | This producer or runtime can never provide it. | forbidden |

- A reader that meets a `basis` it does not know reads the quantity as `unknown` and uses no
  number from it, but keeps the value verbatim when it relays.
- `source` is an open vocabulary: `nvml`, `nvidia-smi`, `nvidia-smi-compute-apps`, `rocm-smi`,
  `amd-smi`, `drm-fdinfo`, `sysfs`, `llama.cpp-props`, `llama.cpp-slots`, `llama.cpp-metrics`,
  `vllm-metrics`, `comfyui-system-stats`, `torch-allocator`, `systemone-metrics`, `iw-ledger`,
  `iw-sizer`, `iw-registry`, `iw-resource-profile`, `config`. An unknown source is shown verbatim
  and graded like `estimated`.
- `confidence` (`high` | `medium` | `low`) defaults by basis: high for measured, medium for
  derived, low otherwise.
- An arithmetic result is `estimated` if any input is estimated, otherwise `derived`; policy
  constants count as exact inputs. An estimate is never presented as measured.

### 2.2 Identity, origin and de-duplication

- `origin`: `gatewayId` (the gateway whose rebalancer is authoritative for the node; empty until
  one composes the report), `nodeId` (a stable id, never an address), `via` (the reporting path,
  appended by each relay).
- A GPU's global `resourceId` is `gpu:<mintingGatewayId|standalone>/<nodeId>/<deviceKey>`.
  `deviceKey` is the vendor UUID when known (AMD: `unique_id`), else the PCI bus id, else
  `idx<N>` with `deviceKeyStable: false`. A MIG instance is `<uuid>-mig-<N>`. Gateway and node
  ids contain no `/`; the device key is everything after the second `/`. `nodeId` equals the
  report's `origin.nodeId`.
- **Who mints it.** A node reports `gpu:standalone/<nodeId>/<deviceKey>`. The **first gateway
  that attaches the node** (receives its report directly) replaces `standalone` with its own
  gateway id — in the GPU and in every reference to it (`placementGroup.gpus`, `perGpu`,
  `allocations`, `anomalies`) — and every gateway downstream preserves the id unchanged. A node
  attached to no gateway keeps `standalone`.
- **De-duplication keys.** One physical GPU can still arrive under two minted ids (a node
  attached directly to a viewer gateway and to its authority). Consumers de-duplicate by
  `resourceId` first and then by `(nodeId, deviceKey)`; node ids are stable identities (spec 45)
  and unique in a federation.
- `deviceId` equals the heartbeat `devices[].id`; `topologyGpuId` equals topology v2
  `configuration.gpus[].gpuId`. Both are carried so a consumer joins without a lookup table.
- **Path check.** `via` is self-reported, so a consumer checks it against what it knows itself.
  For a node in a fleet snapshot the consumer pulled from gateway `R`: the snapshot's
  `gatewayId` MUST equal `R`, `via` MUST be non-empty with `via[0] == origin.gatewayId` and
  `via[last] == R`, and no hop may repeat. A node failing any rule is unusable (an empty or forged
  `via` never wins). A node with `via == [R]` and `origin.gatewayId == R` is **authoritative**;
  any other passing node is **relayed**.
- When one GPU arrives by several paths, a consumer keeps the authoritative copy, otherwise the
  relayed copy with the shortest `via`. It **never** sums copies.
- A relayed node is **stale** — every GPU read as `telemetry.status: stale`, its capacity
  unknown — when the snapshot that carried it lists, for any hop of its `via`, a peer whose
  `status` is not `fresh` or whose `receivedAgeMs` exceeds `gpuMemory.staleAfterSecs`, or when the
  consumer's own receipt of that snapshot is older than `staleAfterSecs`.
- Freshness is judged by the consumer's receipt time and the producer's `sequence` and
  `producerEpoch`, never by comparing producer clocks.

### 2.3 Ownership and authority

Report-level `ownership`: `manager` (`slurm` | `standalone` | `remote-gateway` | `kubernetes` |
`unknown`), `allocationId` (the Slurm job id when known), `allocationState` (`active` |
`draining` | `preempting` | `expiring` | `revoked` | `ended` | `unknown`), `allocationEndsAt`,
`actionAuthority` (`origin-gateway` | `none`: who may pack, move or evict here).

Per-GPU `authority`: `owned` (inside InferWeave's allocation, or a host given to it),
`shared-policy` (a shared allocation with an explicit sharing policy), `not-owned` (visible to the
driver but another job's or user's), `unknown`. An absent or unknown authority grants nothing.
**Only `owned` and `shared-policy` GPUs may have `safeSchedulable` above zero**: unused memory on
a GPU allocated to another Slurm job is not InferWeave's. On a `not-owned` GPU `safeSchedulable`
is `{basis: declared, bytes: 0}` — an evidence-based zero, which is allowed.

**Eligibility.** `eligibility.opportunistic` may be true only when `actionAuthority` is
`origin-gateway`, `allocationState` is `active`, the GPU's `authority` is `owned` or
`shared-policy`, and its telemetry is `fresh`. `actionAuthority: none`, any other or absent
allocation state (`draining`, `expiring`, `preempting`, `revoked`, `ended`, `unknown`), and any
other authority force it false.

### 2.4 Placement class

`placementClass`: `primary` | `normal` | `opportunistic`. Absent means `normal` (today's
behaviour). A value a reader does not know is treated as `primary`: never evicted, never packed
against.

## 3. Node report — `iw.gpu-memory.report/1`

`schemas/v1/resources/gpu-memory-report.json`.

### 3.1 Carriers

Sent only while `iw.gpu-memory/1` is in force for the registration:

- as the optional `gpuMemory` member of node telemetry (`POST /v1/node/telemetry`);
- as the optional `gpuMemory` member of the heartbeat status (node control and the held link).

Both members are optional and additive. A receiver that cannot decode the member treats it as
absent and **never** refuses the telemetry or the heartbeat carrying it. A report that must fit a
carrier's size cap sets `truncated: true` and drops slot items first, then allocations, and never
`gpus[].physical`.

### 3.2 GPU

`schemas/v1/resources/gpu-memory-gpu.json`. Per GPU: identity (§2.2), `vendor`, `name`, `driver`,
`authority`, `telemetry` (`status` `fresh` | `stale` | `unavailable`, `observedAt`, `ageMs`,
`sources`), then:

- `physical`: `total`, `used`, `free`, all three required.
- `categories`: mutually exclusive physical categories — `weights`, `kvCache` (includes all slot
  KV; slot KV is never a category of its own), `prefixCache`, `runtimeAllocator`,
  `runtimeOverhead`, `executionGraphs`, `workspace`, `other` (processes that are not
  InferWeave's). A category the producer cannot split stays absent, never zero. A logical
  reservation name is refused inside `categories`.
- `attributed`: the sum of the allocations' physical bytes on this GPU.
- `unattributed`: `physical.used − attributed`. **Required whenever `physical.used` carries a
  number**, so memory nobody explains stays visible.
- `byClass` (`primary`, `normal`, `opportunistic`): a classification of physical usage, never
  added to a total. Opportunistic usage is a classification of allocations, not memory on top.
- `logical`: `kvGrowthReserve`, `slotReserve`, `runtimeGrowthReserve`, `safetyHeadroom`,
  `placementReservations` (unfulfilled reservations only; gateway-composed),
  `measurementUncertainty`. Never part of any physical total.
- `safetyHeadroom` defaults to `policy.safetyMarginPercent × physical.total`; an operator
  override is reported as `basis: declared`, `source: config`, with the override named in `note`.
- `nodeSafeSchedulable`: the node's view, `free − Σ logical` (except placement reservations),
  clamped at zero.
- `safeSchedulable`, `pressure`, `eligibility`: gateway-composed, absent in a raw node report.

**Accounting invariants**, per GPU, over known numbers only:

- (a) `physical.used + physical.free ≈ physical.total`;
- (b) `attributed + unattributed ≈ physical.used`.

`≈` means within the accounting tolerance: the **checking gateway's own**
`gpuMemory.accountingTolerancePercent` (default 2) of `physical.total`. A report's
`policy.accountingTolerancePercent` only explains the node's own figures; the node being judged
never sets the tolerance it is judged by. A GPU whose total, used or free is unknown is not reconciled at all: arithmetic
over an unknown reading would invent a mismatch or hide one. Each failed check is an
`AccountingAnomaly` (§3.6), and unattributed memory above the tolerance on a GPU that is not
`not-owned` is one too (`unattributed-over-tolerance`). Unattributed memory on a `not-owned` GPU
is another job's and is expected.

**Composing `safeSchedulable`.**
`max(0, physical.free − Σ logical{kvGrowthReserve, slotReserve, runtimeGrowthReserve,
safetyHeadroom, placementReservations, measurementUncertainty})`.

1. A reservation whose runtime's allocation is visible in `allocations` is reconciled and no
   longer counted in `placementReservations`: it is never subtracted twice.
2. If `physical.free` is unknown or the telemetry is not `fresh`, `safeSchedulable` is
   `{basis: unknown}` and `eligibility.opportunistic` is false.
3. `safeSchedulable` never exceeds `physical.free`. A value above it is refused.

### 3.3 Runtime

`schemas/v1/resources/gpu-memory-runtime.json`. `runtimeInstanceId`, `deployment`, `modelId`,
`adapter`, `placementClass`, `evictable`, `migrationSupported`, node-local `pids` (never
forwarded past the composing gateway), `placementGroup` (`gpus`, `topology` `single` | `tensor` |
`pipeline` | `layer-split` | `replica` | `unknown`, `tensorParallel`, `pipelineParallel`,
`shardMovable`), `perGpu` shares, `total`, `kvPool`, `slots`, `adapterResources`,
`lastActivityAt`, `activeRequests`.

The placement group is the unit the rebalancer evaluates and moves. Moving one shard on its own
is forbidden unless `shardMovable` is true.

**Preallocated KV pools.** llama.cpp allocates its whole KV pool at load; vLLM allocates
`gpu_memory_utilization × total` and carves it into blocks. For such a runtime
(`adapterResources.dynamicGrowth: preallocated`) KV growth raises **pool occupancy**
(`kvPool.usageRatio`), not physical usage, so `kvGrowthReserve` is absent or a declared zero and
the pool is already inside `categories.kvCache`. Physical-growth risk comes from
allocator-backed runtimes (`dynamicGrowth: allocator`), which carry
`runtimeGrowthReserve = workspacePeak − current workspace`. A vLLM primary sizes its pool from
free memory at start, so packing beside it is refused unless a `primary-restart` reservation
(§5) holds its restart footprint.

### 3.4 Slots

`slots.support`: `per-slot-measured` | `per-slot-estimated` | `runtime-total` | `unsupported`.
Under `runtime-total` and `unsupported` no slot items exist and the runtime-level figure is shown:
per-slot attribution is never fabricated. A slot carries `slotId`, `state` (`active` | `idle` |
`reserved` | `unknown`), context tokens, `kvCache`, logical `kvGrowth`, request age, last
activity and tokens per second — never prompts, request ids or caller identity.

### 3.5 Allocation

`schemas/v1/resources/gpu-memory-allocation.json`. One attributable physical allocation:
`allocationId` (stable for its GPU and process while it lives), `resourceId`,
`runtimeInstanceId` (absent for a foreign process), `modelId`, `category` (`runtime-total`, a
split category, or `foreign-process`), `physical`, `reservation`, `placementClass`, `evictable`,
`intended` (pinned to this GPU; absent is not reported and `null` is reported unknown), and at
most eight `meta` string pairs (never arguments, environment or secrets). Per-process totals
read in MiB convert to bytes with `basis: measured` and are rounded against placement.

### 3.6 Accounting anomaly

`schemas/v1/resources/gpu-memory-anomaly.json`. `anomalyId`, `resourceId`, `kind`,
`measuredBytes` (a magnitude; for `negative-derived` the size of the negative result),
`toleranceBytes`, `firstSeenAt`, `lastSeenAt`, `consecutive`, `detail`. Kinds:
`physical-sum-mismatch` (invariant a), `attribution-sum-mismatch` (invariant b),
`unattributed-over-tolerance`, `negative-derived`, `reservation-stale`, `slot-sum-exceeds-pool`,
`per-process-exceeds-card`.

### 3.7 Bounds

Per report: at most 64 GPUs, 64 runtimes, 256 allocations, 64 slots per runtime, 32 current
anomalies, 16 entries in `origin.via`, `telemetry.sources`, `pressure.reasons` and
`eligibility.reasons`, 8 `meta` pairs; ids at most 128 UTF-8 bytes with no control (Cc) or format
(Cf) characters; `note` and `reason` at most 128 characters, anomaly `detail` at most 512;
percentages at most 100; every integer at most 2^53 − 1. A serialized report is at most 1 MiB
(and is cut to fit a smaller carrier, `truncated: true`).

Per fleet snapshot: at most 1024 nodes, 1024 reservations and 64 peers, and at most 32 MiB
serialized. A consumer refuses a body over the byte cap **before** decoding it, so a decoder can
bound its allocation up front.

## 4. Fleet snapshot — `iw.gpu-memory.fleet/1`

`schemas/v1/resources/gpu-memory-fleet.json`. Served by a gateway that negotiated
`iw.gpu-memory/1` upward, beside its topology export and under the same authentication and
masking rules. The reference implementation serves it at `GET /iw/v1/gpu-memory` (beside
`GET /iw/v1/topology`); the Protocol v1 OpenAPI names the same document `GET /gpu-memory` under
its `/inferweave/v1` server.

Fields: `schema`, `gatewayId`, `producerEpoch`, `sequence`, `generatedAt` (this gateway's clock;
consumers stamp receipt time), `authority` (`rebalancer`, `mode` `off` | `observe` | `shadow` |
`on`), `nodes` (reports whose GPUs now carry the composed fields), `reservations` (this gateway's
ledger, §5) and `peers` (`gatewayId`, `status` `fresh` | `stale` | `unreachable` |
`unsupported`, `receivedAgeMs`, `capabilities`).

A consumer that is not the authority — a parent gateway, the operational console — merges peer
snapshots with directly attached nodes' reports, de-duplicates by `resourceId` (§2.2), and shows
a directly attached node's `nodeSafeSchedulable` labelled as a node estimate with no rebalancer
authority. When it sums a fleet it sums physical categories, logical reservations and
`safeSchedulable` as separate dimensions, never adds logical or `byClass` into physical, and
never treats free memory on independent GPUs as additive.

## 5. Reservations

`schemas/v1/resources/reservation.json`. `reservationId` (decision id plus GPU, stable),
`decisionId`, `owner` (`gatewayId`, `component`), `kind` (`placement` | `primary-restart` |
`kv-growth` | `runtime-growth` | `restore`), `resourceId`, `placementGroupId` (shared by every
GPU of a multi-GPU placement), `modelId`, `placementClass`, `requestedBytes`, `effectiveBytes`,
`createdAt`, `expiresAt` (default: the load deadline), `state` (`pending` | `loading` |
`reconciled` | `released` | `expired` | `cancelled`), `reason`.

Lifecycle (race-safe admission):

1. **Plan** against `safeSchedulable`.
2. **Reserve** in the same pass that dispatches the decision.
3. **Validate** at dispatch against the latest report; if it is stale, or its `sequence` has not
   advanced past the one planned against, the decision is withheld.
4. **Start** the runtime.
5. **Reconcile**: when the runtime's physical allocation appears, `effectiveBytes` becomes
   `max(0, requestedBytes − physical)` and the state `reconciled`.
6. **Release** on success after warm-up, on failure or expiry, or when the node is gone.

Two decisions never consume the same advertised capacity: within one gateway the rebalancer pass
is single-threaded; across gateway hosts the existing single-actor lease applies; across a
federation a gateway never reserves capacity it does not own (`actionAuthority`). After a restart
the ledger is rebuilt empty and the first pass does not pack. A reservation is never sent as a
physical allocation and never released into another job's allocation.

## 6. Pressure

`schemas/v1/resources/pressure.json`. `state` (`comfortable` | `constrained` | `pressure` |
`critical` | `unknown`), `since`, `previous`, `headroom`, `kvPoolOccupancy`, `reasons`,
`forecast`.

States are evaluated on **free-after-growth** = `physical.free − kvGrowthReserve −
runtimeGrowthReserve`, as a multiple of `safetyHeadroom` — not as a fraction of total, because a
vLLM primary that preallocates 90 % of a card is not at risk with 6 % free; it only has no room to
pack.

| State | Free-after-growth |
|---|---|
| comfortable | ≥ 2.0 × safety headroom |
| constrained | ≥ 1.0 × |
| pressure | ≥ 0.5 × |
| critical | < 0.5 ×, or any OOM on the GPU in the last 10 minutes |

Leaving a state requires `consecutive` (default 3) evaluations beyond `hysteresisFactor`
(default 0.25 ×). Stale telemetry is `unknown`. `kvPoolOccupancy` reports admission pressure and
feeds queue-pressure and scale-up logic, not physical eviction. A `forecast` (`method`,
`horizonSecs`, `samples`, `growthBytesPerMin`, `timeToPressureSecs`, `confidence`) is present only
when the sample count reaches `minSamples`; it informs pre-emptive action and never overrides a
hard safety constraint.

## 7. Events, decision records and OOM postmortems

### 7.1 Event feed

`schemas/v1/events/gpu-memory-event.json`, served with a cursor while `iw.rebalance-decisions/1`
is in force (`GET /iw/v1/gpu-memory/events?after=<cursor>&limit=`). Envelope: `eventId` (unique;
the idempotency key), `cursor` (`<producerEpoch>:<sequence>`; an epoch change means resynchronize
from a snapshot), `type`, `occurredAt`, `gatewayId`, `origin`, `correlationId` (the decision id
where one exists), `resourceIds`, `runtimeInstanceId`, `modelId`, `payload`. Consumers process
events idempotently by `eventId`. `correlationId` is the decision id where one exists, otherwise
the id of the episode (for an accounting anomaly, its `anomalyId`).

The frozen event vocabulary (`contracts/protocol-v1/gpu-memory-events.json`):

- GPU memory: `gpu.memory.updated`, `gpu.memory.pressure_changed`,
  `gpu.memory.accounting_anomaly`, `gpu.memory.oom`, `gpu.memory.postmortem`. Snapshots are
  pulled, so `gpu.memory.updated` is reserved for push transports and is not emitted on the pull
  feed.
- Runtime: `runtime.opportunistic_placed`, `runtime.eviction_started`, `runtime.evicted`,
  `runtime.restore_started`, `runtime.restored`, `runtime.migration_started`,
  `runtime.migrated`.
- Rebalance: `rebalance.decision`, `rebalance.started`, `rebalance.completed`,
  `rebalance.failed`.

Model residency transitions keep the spec 45 lifecycle events and reasons (`memory_pressure`
among them); the `rebalance.*` types wrap existing rebalancer decisions and add no second
decision path.

### 7.2 Decision record

`schemas/v1/resources/rebalance-decision.json`, the payload of `rebalance.decision`:
`decisionId`, `action` (`pack` | `move` | `evict` | `consolidate` | `restore` | `scale_up` |
`scale_down` | `place` | `repack` | `rebalance` | `renew` | `hold` | `give_back` | `suspend`),
`existingKind` (the decision variant actually carried out), `mode` (`observe` | `shadow` | `on`;
shadow decisions are recorded and never executed), `trigger`, `pressureState`, node, runtime and
model ids, `placementClass`, `source`, `destination`, `resourceSnapshot` (a reference plus key
numbers, not a copy), at most 16 `candidates` with named score `terms` and a `rejectedBecause`
reason, `selected`, `reason`, `estimatedCost`, `expected`, and `outcome`. Memory is never claimed
recovered before it is measured: a `succeeded` outcome carries a measured, signed
`physicalDeltaBytes`.

### 7.3 OOM postmortem

`schemas/v1/resources/gpu-memory-postmortem.json`, the payload of `gpu.memory.postmortem`: the
last pre-failure `gpu`, `runtimes` and `allocations` for the GPU, `ownership`, `pressure`,
`recentGrowth` (the last five minutes), at most ten `recentDecisions` from the last 30 minutes,
and `runtimeError` (exit
status, signal, matched OOM signature, and at most 2 KiB of the engine's stderr scrubbed by the
secret filters). The node keeps a ring of its last 12 reports, so a postmortem never depends on
the failed runtime still answering. OOM sources: an engine exit with a known OOM signature (CUDA
`out of memory`, `hipErrorOutOfMemory`, a ggml allocation failure) and the spec 36 `GPU_OOM`
watchdog signal.

## 8. Configuration

Implementations add configuration only under a new top-level `gpuMemory` key and under
per-model placement settings:

```jsonc
"gpuMemory": {
  "mode": "observe",            // off | observe | shadow | on ; absent = off = today's behaviour
  "safetyMarginPercent": 5, "accountingTolerancePercent": 2, "staleAfterSecs": 30,
  "pressure": { "comfortableFactor": 2.0, "constrainedFactor": 1.0, "pressureFactor": 0.5,
                "hysteresisFactor": 0.25, "consecutive": 3, "prediction": false, "minSamples": 24 },
  "opportunistic": { "mode": "off", "nodes": [], "minResidencySecs": 600, "cooldownSecs": 300,
                     "restoreHeadroomPercent": 15, "maxConcurrent": 1, "maxActionsPerHour": 6 }
}
```

Per model: `placementClass`, `evictable`, `migrationAllowed`, `minResidencySecs`,
`cooldownSecs`, `expectedVramBytes`, `growthReserveBytes`. Defaults are conservative and the first
deployment observes without changing placement.

**Version-skew rule.** A configuration key added to an object that older readers decode strictly
makes those readers refuse the whole configuration. New keys therefore go only under the new
`gpuMemory` object or onto objects older readers decode permissively, never into an existing
strictly decoded object.

## 9. Placement simulation

`schemas/v1/resources/placement-simulation-request.json` and
`placement-simulation-response.json` (`POST /iw/v1/gpu-memory/simulate`, while
`iw.placement-simulation/1` is in force). A simulation is answered by the **same function** the
rebalancer calls, on a cloned input with reservation disabled: it never reserves memory, starts a
runtime or changes the fleet (`mode: read-only`, `reservationsMade: 0`). A gateway that is not a
rebalancer authority refuses it with `FEATURE_UNSUPPORTED`. A consumer forwards the request to the
authoritative gateway and only renders the answer; it never computes scores.

## 10. Mixed versions

| Producer → consumer | Behaviour |
|---|---|
| new node → older gateway | The capability is not offered back, so no `gpuMemory` is sent; if it were, both carriers ignore unknown members. Safe. |
| older node → new gateway | No `gpuMemory`; the consumer shows "not reported" and the rebalancer keeps today's capacity rules. Safe. |
| new child gateway → older parent | The parent never asks for the fleet snapshot. Topology v2 is unchanged. Safe. |
| configuration with `gpuMemory` → older gateway | Ignored. Safe. |
| a key added inside a strictly decoded configuration object → older gateway | **Refused.** Forbidden by §8. |
| a GPU-memory member inside topology v2 → any deployed gateway | **Refused** (strict decoders). Forbidden: topology v2 is never a carrier. |
| a new enum value → a 1.1.0 reader | Kept verbatim and read through the documented fallback. |
| two assignments for one GPU → a node without `iw.card-coresidency/1` | Never sent. |

## 11. Mapping from the spec 45 memory model

The spec 45 memory fields (`schemas/v1/resources/memory.json`) are bytes. They map onto this
model as follows; a consumer of `memory.json` derives each value from the right-hand side and
keeps it unknown when every source on the right is unknown or absent.

| spec 45 `memory` field | `iw.gpu-memory` source | Note |
|---|---|---|
| `total` | `physical.total` | |
| `free` | `physical.free` | raw free, not safe schedulable |
| `weights` | `categories.weights` | |
| `kv_cache` | `categories.kvCache` | includes all slot KV and preallocated pools |
| `runtime_cache` | `categories.runtimeAllocator` (+ `categories.prefixCache` when the producer does not split it) | |
| `active_requests` | (no physical category) `categories.workspace` for activations; per-slot KV in `runtimes[].slots.items[].kvCache` | active-request KV is inside `kv_cache`, never counted twice |
| `reserved` | Σ `logical.*` | logical: never part of a physical total |
| `other_models` | `allocations[]` grouped by `modelId`; `byClass` | a classification, not memory on top |
| `system` | `categories.runtimeOverhead` + `categories.other` | |
| `unaccounted` | `unattributed` | |
| (none) | `physical.used`, `attributed`, `nodeSafeSchedulable`, `safeSchedulable` | new in 1.1.0 |

The §7 event envelope is camelCase; it maps onto the spec 45 envelope as `event_id` ↔ `eventId`,
`event_type` ↔ `type`, `timestamp` ↔ `occurredAt`, `correlation_id` ↔ `correlationId`,
`source_id` ↔ `gatewayId`, and `sequence` ↔ the sequence part of `cursor`.

**This section corrects spec 45.** Spec 45 1.0.0 gave the memory fields no unit and listed
`reserved` beside physical categories. A literal implementer could report MiB (as the reference
implementation's topology projection does) or GB (spec 40, spec 44 use other units), and could put
physically held memory in `reserved` and sum it into a physical total. Protocol 1.1.0 fixes both:
the fields are bytes — the unit of the published `memory.json` fixture, of the reference
implementation's heartbeat `devices[].vramBytes`, and of the operational gateway's
`gpu_memory_*_bytes` series — and `reserved` is logical. A 1.0.0 producer that used another unit
or put physical memory in `reserved` is non-conforming from 1.1.0 and must be corrected.

## 12. Contract fixtures

`contracts/gpu-memory/` holds four fleet snapshots, generated with exact byte arithmetic by
`tools/gen_gpu_memory_fixtures.py`, which checks invariants (a) and (b) on every GPU before
writing:

1. `01-b200-primary-whisper-pack` — the product requirement's worked example (a 96 GiB card
   with 80 GiB physically allocated, 16 GiB raw free, 6 GiB safely schedulable): a llama.cpp
   primary, an opportunistic whisper runtime, a foreign process, one pending pack reservation.
   The example's single "6 GiB KV growth reservation" is split per §3.3: the llama.cpp pool is
   preallocated (`kvGrowthReserve` 0), whisper's allocator growth is a 2 GiB
   `runtimeGrowthReserve`, and a 4 GiB pending pack is a `placementReservations` entry. Its
   safety headroom is a 4 GiB operator override of the 5 % default. Notes in the fixtures that
   cite "spec §N" refer to sections of that product requirement, not to `specs/N`.
2. `02-a100x4-vllm-tp4-slurm` — vLLM tensor-parallel 4 across four 80 GiB cards inside a Slurm
   allocation; `constrained` with no growth exposure.
3. `03-r9700x2-rocm-layer-split-no-slots` — two AMD R9700, ROCm, a llama.cpp layer split, per-slot
   memory `unsupported`, as served by the workstation gateway that attached the node and minted
   its GPU ids (`via: ["gw_beast"]`). A relay re-serving it appends itself to `via` and serves it
   under its own `gatewayId`.
4. `04-stale-anomaly-draining-notowned` — a stale GPU (used and free unknown), a GPU with 22 GiB
   unattributed (exactly one `unattributed-over-tolerance` anomaly), a draining Slurm allocation,
   and a GPU owned by another job.

The files are canonical bytes — keys sorted, 2-space indent, UTF-8, one trailing newline — and are
shared byte-for-byte with the reference implementation and the gateway consumer. A producer in
any language reproduces them by sorting object keys; struct field order is not part of the
contract. `scripts/validate_specs.py` rejects a non-canonical copy.

## Conformance

`conformance/runner.py` validates the four contract fixtures as fleet snapshots and the
`fixtures/valid/` objects of this spec, and requires each `fixtures/invalid/` object to fail:
a byte count beside `basis: unknown`, a logical reservation inside `categories` and inside
`physical`, a GPU with known usage and no `unattributed`, schedulable capacity on a `not-owned`
GPU, slot items under `runtime-total` support, a control character in an id, a measured quantity
without bytes, and a decision recorded `succeeded` without a measured outcome or with an
estimated one. The conformance scenario is `gpu_memory_accounting`
(`conformance/manifest.yaml`). It belongs to its own optional profile `IW-GPU-MEMORY`, not to
`IW-FULL`: the family is capability-gated, and a minor release does not widen an existing
profile.

## Open gates and evidence

Every required test of `P5-T30`–`P5-T32` is `owed`. A schema, fixture or unit test does not close
a gate. Owed and not approved: a node producer measured on NVIDIA hardware and on AMD hardware,
gateway composition and the fleet snapshot, the event feed, OOM postmortems from a real OOM,
placement simulation, and any change to placement. See `OPEN_GATES.md`.

## Task traceability

Feature `IW-GPUMEM-001` maps to canonical tasks `P5-T30`, `P5-T31`, `P5-T32`. See
`contracts/feature-registry.json`, `contracts/canonical-task-graph.json` and `implementation/`.
