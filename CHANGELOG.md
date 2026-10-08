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
- Round-4 follow-ups: a relayed node without `relayAgeMs` is stale; every GPU of a node shares one
  minting prefix and `attachedBy` must equal it; an unanchored unowned node carries no runtimes
  or allocations; unknown, foreign and pre-restart cursors get `410`; pinned snapshots are
  bounded (`pinShareSecs`, `maxPinnedSnapshots`); reservation cross-checks wait for all pages.
- Round-5 follow-ups: pins are never evicted while live (`maxPinnedSnapshots` defaults to
  ⌈`cursorTtlSecs`/`pinShareSecs`⌉ = 12; a new first page gets `503` + `Retry-After` at the cap);
  a config-free relay-age floor (the sender's own `receivedAgeMs` for the adjacent hop; below it is
  forged and stale); anomalies must name the report's own GPUs; phantom nodes carry no
  allocations or anomalies; a relay re-serves one copy of a node whole.
- Round-6 follow-ups: every response carries `servedAgeMs` (added to the data's age; a paginated
  response without it is stale; age is per page, see round 7); pins
  release at age ≥ `cursorTtlSecs`, the default cap is ⌈TTL/share⌉ + 1 = 13, and one-page
  responses create no pin; the relay-age floor allows 1 s of rounding.
- Round-7 follow-ups: age is computed per page (that page's receipt age plus that page's
  `servedAgeMs`); a continuation page fetched with a cursor and lacking `servedAgeMs` is stale;
  producers put `nodeCount` on every page of a multi-page snapshot.
- Round-8 follow-ups: a truncated report's lists are partial (aggregates stay authoritative; the
  remaining allocations may only fall short of `attributed`); page assembly is all or nothing
  (reference: `FleetAssembler`); a response served from a pin MUST carry `servedAgeMs`.
  A repeated key refuses the object at any depth (unknown and `meta` keys included);
  `relayAgeMs` exists only on relayed nodes.
- Round-9 follow-ups: truncated reports count what they dropped (`allocationsDropped`,
  `runtimesDropped`, `anomaliesDropped`); an unexplained attribution gap is refused and an
  explained one is shown as unverified; a truncated report under half its carrier cap is suspect;
  duplicate nodes within one page are malformed; Go needs a token pre-scan for repeated keys.
- Conformance: new optional profile `IW-GPU-MEMORY` with scenario `gpu_memory_accounting`;
  `IW-FULL` is unchanged.
- The stale "only common and errors are published" sentence of spec 45
  is corrected.

### Node join: hardware-only registration and tokenless enrollment (added to 1.1.0, unreleased)

**Compatibility classification: minor, backwards-compatible.** `v1.1.0` is still `owed` in
`conformance/release-manifest.yaml`, so this lands in 1.1.0 rather than a new version.

- `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` and decision record
  `decisions/2026-10-08-open-proof-enrollment-and-hardware-registration.md` (feature
  `IW-NODEHW-001`, tasks `P5-T33`, `P5-T34`, both `owed`).
- `POST /v1/node/register` gains one optional member `hardware` (versioned object, stored
  verbatim, informational only; refused with `400 bad_request` when not an object, without an
  integer `version`, or over 65536 compact bytes).
- A registration with empty `models`, `endpoint` and `deployment` is valid: recorded, never
  routable, never dialled.
- The register response gains an always-present `assignments: []`.
- Tokenless enrollment (`/v1/node/key`, `/challenge`, `/proof`) is specified on the wire, with the
  exact signed transcript and known answers; open registration at the lowest trust tier is
  permitted and its tension with identity scarcity is recorded.
- Tokenless proof enrollment grants only the role `node`; other roles are refused with
  `400 bad_request` at `/v1/node/challenge`. Caps on pending challenges and keys are permitted
  implementation limits (a `429` is allowed).
- A credential earned only by tokenless proof may register hardware-only and heartbeat, but a
  non-empty endpoint or any models is `403 forbidden`, and a proof never replaces an
  operator-issued credential (`403`); only operator-issued enrollment makes a node routable.
- Hardening (spec 47 sections 6.2 to 6.9) from independent security review of both gateways:
  operator enrollment replaces a proof-only credential and evicts its registration, hardware and
  links; proof-only and hardware-only nodes hold no link; tokenless challenge and proof are
  refused (`403`) for known ids, at both steps; unauthenticated state is bounded (`429`); request
  bodies are size-capped before parsing; hardware is cleared when omitted and dropped with its
  registration; hardware-only heartbeats add no capacity; proof-only credentials SHOULD persist
  fail-closed for rollback. This supersedes "first issued wins" for the proof-only case.
- Schemas `requests/node-hardware.json`, `requests/node-hardware-report.json`; fixtures; vectors
  `conformance/node-join-vectors.json`; reference model `conformance/node_join.py`; manifest
  scenarios `node_enrollment`, `hardware_registration`.
- Specification gap recorded, not a correction: the repository never defined the `/v1/node/*`
  bodies, so no earlier text is changed.


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
