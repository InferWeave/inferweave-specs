# InferWeave Protocol changelog

This file records the InferWeave Protocol release history and compatibility-relevant changes.
Version numbers are semantic and match the `VERSION` file. See `specs/45_PROTOCOL_V1.md` for the
versioning rules and the protocol change workflow.

## 1.1.0 — GPU memory accounting (in progress)

**Compatibility classification: minor, backwards-compatible, with one specification
correction.** Adds new capability-gated surfaces; no existing enum value or endpoint changes, and
older peers keep working unchanged (`specs/46_GPU_MEMORY_INTELLIGENCE.md` §10). The correction:
spec 45's memory fields had no unit and listed `reserved` beside physical categories; they are
now bytes and `reserved` is logical (spec 46 §11). A 1.0.0 producer that used another unit or
counted physical memory in `reserved` was following ambiguous text and must be corrected.

- `specs/46_GPU_MEMORY_INTELLIGENCE.md` and decision record
  `decisions/2026-10-07-gpu-memory-accounting.md` (feature `IW-GPUMEM-001`, tasks
  `P5-T30`–`P5-T32`, all `owed`).
- Capability family `iw.gpu-memory/1`, `iw.rebalance-decisions/1`,
  `iw.placement-simulation/1`, `iw.card-coresidency/1`, paired with the new `features` names
  `gpu_memory`, `rebalance_decisions`, `placement_simulation`, `card_coresidency`
  (`contracts/protocol-v1/gpu-memory-capabilities.json`).
- Schemas: `quantity`, `pressure`, `reservation`, `gpu-memory-report`, `gpu-memory-gpu`,
  `gpu-memory-runtime`, `gpu-memory-allocation`, `gpu-memory-anomaly`, `gpu-memory-fleet`,
  `gpu-memory-postmortem`, `rebalance-decision`, `placement-simulation-request`,
  `placement-simulation-response` (`schemas/v1/resources/`) and `gpu-memory-event`
  (`schemas/v1/events/`); frozen event vocabulary `contracts/protocol-v1/gpu-memory-events.json`.
- Four canonical contract fixtures under `contracts/gpu-memory/` (shared byte-for-byte with the
  reference implementation), their generator `tools/gen_gpu_memory_fixtures.py`, and valid and
  invalid conformance fixtures.
- Correction (not a clarification): spec 45 memory fields are bytes and `reserved` is logical;
  spec 46 §11 records what the old text allowed and maps the fields onto the new model.
- Contract fixtures are re-checked by regenerating them (`validate_specs.py`); `intended` is a
  string enum `yes`/`no`/`unknown`; ids are printable ASCII; allocation ids never carry pids.
- Review follow-ups: cursors pin their snapshot (`cursorTtlSecs`, `410 Gone`), `peers` repeat on
  every page and `reservations` ride the first, `nodeCount` is required with `nextCursor`;
  `origin.relayAgeMs` accumulates per hop and counts against `staleAfterSecs`; `origin.attachedBy`
  names an unowned node's attaching gateway; foreign-process allocations are always primary and
  unmovable; node and gateway ids refuse `/`.
- Conformance: new optional profile `IW-GPU-MEMORY` with scenario `gpu_memory_accounting`;
  `IW-FULL` is unchanged.
- The stale "only common and errors are published" sentence of spec 45
  is corrected.

## 1.0.0 — initial protocol (in progress)

The first Protocol v1 wire contract. Formalizes the scheduler-neutral vocabulary of
`specs/44_CORE_PROTOCOL.md` into a versioned, machine-readable, language-neutral contract:

- protocol versioning and feature negotiation
- three planes (data, control, observability)
- stable identity model and request/trace identity
- canonical objects and JSON Schemas under `schemas/v1/`
- events, state machines, canonical enums, and error taxonomy
- aliases, routing, affinity, jobs, streaming, and async jobs
- conformance levels and compatibility matrix

The full canonical-protocol artifact set is delivered: 30 JSON Schemas under `schemas/v1/`
(common, errors, topology, model, resources, runtime, requests, events, jobs, artifacts); frozen
canonical vocabularies under `contracts/protocol-v1/` (error taxonomy, lifecycle reasons,
workload classes, device types, provenance sources, model lifecycle events) reconciled by a
test guard; the OpenAPI definition `openapi/inferweave-v1.yaml`; conformance profiles, fixtures,
and the `conformance/runner.py` harness; the compatibility matrix and release manifest; and the
cross-repo `protocol-ci` workflow. `VERSION` remains `1.0.0`.

Status: specification and artifacts complete, BLOCKED for production. Production conformance by
a running component and independent multi-node verification remain `owed` by canonical tasks
`P5-T24`–`P5-T29` (feature `IW-PROTO-002`).
