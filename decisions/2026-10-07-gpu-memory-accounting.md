# GPU memory accounting on capability-gated surfaces — 2026-10-07

**Status:** Proposed  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-07  
**Authorizes:** Nothing until accepted. On acceptance: the Protocol 1.1.0 wire contract of
`specs/46_GPU_MEMORY_INTELLIGENCE.md` and observe-only implementations of it (wire types,
validation, accounting reconciliation). It does **not** authorize deployment, any change to
placement, eviction or scaling, or any action on a Slurm allocation.  
**Relationship:** Extends `specs/45_PROTOCOL_V1.md` (minor release 1.1.0); supersedes no record.
Every spec 45 enum and endpoint stands unchanged. One spec 45 defect is corrected: its memory
fields gain a unit (bytes) and `reserved` is declared logical (spec 46 §11 states what the old
text allowed a literal implementer to do).

## Measured basis

- Fixture arithmetic: `python3 -I tools/gen_gpu_memory_fixtures.py <dir>` regenerates the four
  `contracts/gpu-memory/` files byte-for-byte and asserts, on every GPU, `used + free = total`
  within 2 % and `attributed + unattributed = used` exactly. Reproduced for this record.
- Strict decoding of topology v2 and of several configuration objects: established by reading
  the reference implementation at InferWeave/inferweave `b2b63c2`
  (`crates/iw-core/src/topology_v2.rs`, `topology_configuration.rs`: `deny_unknown_fields` on the
  graph, vertex, edge and configuration types). The implementation PR that follows this record
  pins it with a test that a GPU-memory member inside a topology v2 vertex is refused.
- Units: spec 45's memory fields carried no unit. Bytes are used by the published `memory.json`
  fixture, the reference implementation's heartbeat `DeviceReport.vram_bytes`
  (`crates/iw-core/src/control_connection.rs`, InferWeave/inferweave `b2b63c2`) and the operational
  gateway's `gpu_memory_*_bytes` series (metabolomics-us/inferweave-gateway
  `cmd/gateway/gpu_accounting.go`, `9fe254c`); the reference implementation's topology projection
  uses MiB (`CardMemory`). No other figure is relied on.

## Context

The fleet needs per-GPU accounting of where VRAM goes, what is reserved and what can safely be
reused, across NVIDIA and AMD, Slurm and standalone hosts, and nested gateways. Spec 45 has a flat
memory object with no units, no provenance, and a `reserved` field that mixes a logical
reservation into what reads as physical memory. The deployed gateways decode topology v2 strictly,
so any new member there is refused by every deployed parser.

## Options

1. Extend topology v2 and the spec 45 `memory` object in place.
2. A new capability-gated family (`iw.gpu-memory/1` and three siblings) on optional members of
   node telemetry and the heartbeat status plus new endpoints, with a mapping table onto spec 45.
3. A separate, gateway-specific API owned by the operational console.

## Decision

Option 2:

- **Capability-gated surfaces, never topology v2.** GPU memory travels only as the optional
  `gpuMemory` member of node telemetry and the heartbeat status (while `iw.gpu-memory/1` is in
  force) and as the `iw.gpu-memory.fleet/1` snapshot. Option 1 is refused by every deployed
  strict decoder; option 3 creates a second, incompatible definition and a second calculation.
- **Bytes, unsigned, at most 2^53 − 1.**
- **`Quantity` with an explicit `basis`.** Unknown is never zero: a number is present exactly
  when the basis says one exists.
- **camelCase JSON** on these surfaces, matching the link and HTTP family they ride; spec 46 §11
  maps them onto the snake_case spec 45 objects (`memory.json` fields, the event envelope:
  `event_id` ↔ `eventId`, `event_type` ↔ `type`, `correlation_id` ↔ `correlationId`, `timestamp`
  ↔ `occurredAt`).
- **Schemas validate producers at exactly 1.1.0 (closed enums); readers never drop a document on
  schema rejection** and read unknown values through documented fallbacks.
- **The `iw.<name>/<major>` capability grammar is published** together with the snake_case
  `features` names it pairs with (`contracts/protocol-v1/gpu-memory-capabilities.json`), so the
  two negotiation vocabularies no longer drift.
- **The node measures and the owning rebalancer composes**; every other gateway relays and
  displays.
- **Unknown enum values are kept verbatim** and read through a documented fallback (basis →
  unknown, placement class → primary, authority → grants nothing).
- **Canonical contract bytes**: the shared fixtures are written with sorted keys so every
  language reproduces them without depending on struct field order.

## Consequences

- Positive: older peers keep working unchanged; every byte is explainable; a consumer never has
  to recompute placement capacity.
- Negative: two negotiation vocabularies coexist (snake_case features and `iw.*` capabilities),
  bridged by frozen data; producers must carry basis/source on every number.
- Operational: nothing changes until a node producer and gateway composition ship and are
  enabled (`gpuMemory.mode`, default off).
- Migration: none; spec 45 consumers keep `memory.json` and may derive it from the new model.

## Requirements affected

- `IW-GPUMEM-001` (new)
- `IW-PROTO-002` (minor release 1.1.0)

## Rollback/revisit trigger

Revisit if a deployed decoder of the heartbeat status or node telemetry is found to refuse an
unknown member (the carriers would then need a new capability-gated message instead), or if
hardware validation shows a required category cannot be expressed with `basis`.
