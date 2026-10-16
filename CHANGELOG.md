# InferWeave Protocol changelog

This file records the InferWeave Protocol release history and compatibility-relevant changes.
Version numbers are semantic and match the `VERSION` file. See `specs/45_PROTOCOL_V1.md` for the
versioning rules and the protocol change workflow.

## 1.1.0 — GPU memory accounting (in progress)

- Spec 61: a held `selection.precision_table_version` now **binds classification**, not only validation (a candidate
  advertising another table version, or none, is classified by its token under the pinned table, whatever its
  route; the pinned class is what `preferred.precision` ranks and `unmet.observed` reports). New frozen `unmet`
  requirement token `precision_table_version` (after `min_precision_class`), produced only when a stored revision's
  pin names a table the resolving producer does not hold; such candidates are `EXCLUDED` with the existing
  `PRECISION_UNVERIFIED`. Additive vocabulary: a consumer that closes the `unmet_requirement` enum must add it. With
  no pin, behaviour is unchanged. Rust implementation in an open pull request; see `OPEN_GATES.md`.

- Spec 63: closed, bounded schemas and conformance vectors for the `upstream` role frames (`IW-DP-002`; proof owed,
  see `OPEN_GATES.md`): `link-upstream-hello.json`, `link-upstream-hello-ack.json` (`kind: upstream_ack`),
  `link-upstream-catalog.json`, `link-upstream-catalog-request.json`, `link-upstream-refused.json`,
  `meta.traffic_class` on the closed `link-http-request.json`, an `api_key` Hello accepted by `link-hello.json`,
  `contracts/protocol-v1/link-upstream.json` and `conformance/link-upstream-vectors.json`. Additive: no existing
  frame changes shape; nothing opens a production gate.

- Spec 65 (InferWeave Storage, proposed and implemented in part on an unmerged branch of the reference
  implementation) added with decision record `decisions/2026-10-16-inferweave-storage.md` (features
  `IW-STORE-001` and `IW-STORE-002`, tasks `P5-T36` and `P5-T37`, both `owed`): the `store` role and the
  additive capability `iw.store/1`, the signed `iwg1` read grant, the native `/v1/blob` data plane and a
  read-only S3 front end, network exposure and abuse controls, the single-writer rule for shared filesystems,
  the digest index with an optional capability-gated topology `store` field and `grantIssuerKeys`, the
  multi-source stager and store quarantine. Older peers are unaffected. Nothing opens a production gate; see
  `OPEN_GATES.md` (TLS, grant forwarding across federation, per-range hashes and ingest leases unsatisfied).

- Spec 56 amended after the Rust producer and ingester (`IW-ALIAS-001`; proof still owed, see `OPEN_GATES.md`): the
  report may ride the node heartbeat; duplicate JSON members are refused; additive, diagnostic-only heartbeat
  answer member `runtimeObservations.resync` (an old peer ignores it) with a paced producer epoch rotation; the
  producer rotates its epoch before the owner's fence budget; durable producer epoch and sequence ceiling;
  UNLOADED tombstones; same-epoch re-registration keeps fences. Nothing opens a production gate.

- Spec 63 (link `upstream` role, proposed and implemented in part, default off) amended after the Rust
  implementation (`IW-DP-002`; see `OPEN_GATES.md`): optional request-`meta` member `traffic_class` (spec 59,
  `link-request-meta.json`; an old receiver ignores it), the `refused` frame carried by the `upstream` role,
  closed catalog entries with `max_context_tokens`, `records_prompt_content` assertion semantics, fresh request
  id per dispatch, token-budget semantics, relay circuit breaker, drain wait. Nothing opens a production gate.

- Additive, optional System One CPU capacity wire (`IW-NODEHW-001`, `IW-DP-001`; proof owed, see `OPEN_GATES.md`):
  `systemone[].device` and `max_concurrency` on the register body, `systemone` load on the node heartbeat,
  `meta.systemone_batch` on link request meta, and the `/v1/systemone` and `/v1/systemone/batch`
  `iw.link-http-json/1` targets (`stream:true` refused with 400 `stream_unsupported` on every non-chat target).
  Slot semantics now distinguish schedulable `slots` from the `max_concurrency` admission bound, and a CPU-only node
  is first class (`cpu` device/backend, `gpus: []`, routable without GPU telemetry). Older peers are unaffected:
  every member is optional and omitted when absent. Casing of the new members is inconsistent and recorded as open.

- Additive, explicitly negotiated `dynamic_aliases: "2"` (spec 54) preserves level 1.
  Adds strict alias policies/revisions, instance-level preview and evidence, frozen reasons/events,
  native management schemas and bounded fixtures. D-002 extends only the existing Go operator UI;
  Rust retains policy/admission authority. Artifact validation is not production conformance;
  tasks A-T01–A-T08 and all runtime acceptance gates remain owed until separately evidenced.


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
- Final Rust protocol changes (spec 47 sections 5.2, 5.3, 6.10 to 6.12): `/challenge` is
  idempotent while unexpired; the tokenless node id must be `node_` plus 16 hex of the SHA-256 of
  the raw public key (`400` otherwise, operator enrollment takes any id, known-id `403` first); a
  proof-only node is released only after a long silence; per-source caps and rate limits are
  recommended; hardware-only and proved connections cannot file telemetry and keep only
  `busySlots`, `queueDepth` and `leaving` from heartbeats; heartbeat and telemetry bodies SHOULD
  be size-capped. Section 5.3's stale note about the Rust register store is removed. Vectors
  `enrollmentIdCases` and extended `enrollmentLifecycleCases`.
- Schemas `requests/node-hardware.json`, `requests/node-hardware-report.json`; fixtures; vectors
  `conformance/node-join-vectors.json`; reference model `conformance/node_join.py`; manifest
  scenarios `node_enrollment`, `hardware_registration`.
- Specification gap recorded, not a correction: the repository never defined the `/v1/node/*`
  bodies, so no earlier text is changed.


### Dynamic nodes and gateway-driven provisioning (added to 1.1.0, unreleased)

**Compatibility classification: minor, backwards-compatible, with one specification
correction.** Capability-gated: an older node never offers `iw.dynamic-node/1`, sends no
`dynamic` and reads `assignments: []` as before; an older gateway lists nothing and a dynamic
node registered to it stays hardware-only. The correction: spec 47 §5.1 said `assignments`
"MUST be `[]`" in this version; that was the reservation, and the text now says it is `[]` for
every registration that has not negotiated a capability that fills it.

- `specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md` and decision record
  `decisions/2026-10-15-dynamic-nodes-gateway-provisioning.md` (feature `IW-DYNNODE-001`, task
  `P5-T35`, `owed`).
- Capability `iw.dynamic-node/1`; register member `dynamic`
  (`schemas/v1/requests/node-dynamic-facts.json`); `assignments` entries `serve`, `measure`,
  `stop` on the register and heartbeat responses (`schemas/v1/requests/node-assignment.json`);
  heartbeat member `provisioning` (`schemas/v1/requests/node-provisioning-status.json`);
  `node-register-response.json` now allows up to 8 assignment entries.
- Rules: desired state repeated until the node agrees, withdrawal explicit, unknown entries
  skipped; pinned, resumable, digest-verified artifacts; only profiles with decode evidence at 90%
  of the context floor serve, unmeasured candidates are measured first and drafted; every card of
  an engine on one node; nothing is placed on a registration before its first `provisioning`
  report; only operator-enrolled credentials are provisioned; spec 47 §6.12 keeps `provisioning`
  on a hardware-only heartbeat when the capability is in force.
- The `dep_` deployment id is derived, never typed, as one SHA-256 over length-prefixed strings and
  count-prefixed lists: the model id, the profile name and version, the whole launch block
  (image, digest, command, environment in key order, privileges, mounts, shm size, engine,
  backend, label), the artifacts' paths and digests and, for a `serve`, the advert figures. A
  node recomputes it and refuses an entry whose id differs. Three known answers
  (`conformance/dynamic-node-vectors.json`) are recomputed by `conformance/runner.py`.
- Failure classes: `launch_failed`, `probe_failed` and `measure_failed` are permanent (not
  retried into the same placement while the gateway runs); `engine_exited`,
  `artifact_unavailable`, `digest_mismatch`, `disk_full` and the new reason `runtime_unavailable`
  (the container runtime is down, an image pull failed, a container name collided, a non-space
  filesystem error) expire after 600 seconds. `refused` is never a failure, but the same
  (node, model, profile) is not placed again for 60 seconds, doubling to 600. A holding its node
  never reports is dropped after 300 seconds as a transient failure; an engine beyond a model's
  `replicas` is sent a `stop`; of the active statuses a node reports for one model at most one is
  adopted, and a report is read for at most 64 entries.
- Plan order: quality tier, then measured decode at the floor, then profile name and version.
  The size of the serving group is not a key; on equal best scores the smaller quality tolerance
  sets the tier, as the shared profile ranking does. The idle reasons are `occupied`,
  `no_matching_profile`, `no_qualified_profile`, `failed_before`, `measuring_elsewhere`,
  `replicas_met`, `awaiting_status` and `refused_recently`.
- Bounds a gateway enforces: the `dynamic` member is at most 64 KiB as sent (unknown members
  count) and keeps to the schema's field bounds, with a 400 message cut to 200 characters; a
  measure candidate's name leaves room for `<candidate>-draft-<id>` within 128 characters (at
  most 71); a `measure` matrix has `maxTokens` of at least 2, concurrency at most 256 and each
  depth at least 10 x (`maxTokens` + 16); artifact paths do not collide on disk (`a` and `a/b`,
  `x` and `x.part`, `m.gguf` and `m.gguf.sha256`) and their sizes add up within 64 bits;
  `advert.slots` is at most 4294967295; a node ignores unknown advert members. A draft of an
  allowed candidate is admitted when `profilesAllow` is set; a draft is matched to the host's
  facts as they were when the `measure` was assigned; the operator view marks drafts and what is
  served from them `experimental` and lists `refusals`.
- Node behaviour recorded in the specification: a `file://` source is read only under an
  operator-configured source root; HTTP sources never target loopback or link-local addresses,
  follow at most three redirects and never downgrade from https to http; `$ARTIFACTS` mounts are
  read-only and confined to the deployment's directory; a node may reuse a verified file of the
  same size and SHA-256 from another deployment; a `stop` cancels an in-flight assignment; a node
  cuts status messages to 512 characters and keeps its report within 64 KiB, oldest terminal
  statuses first.
- A boot token of at most 12 base-36 characters (hash of clock, process id and a random value)
  replaces the start time in seconds in assignment ids.
- Specification corrections made before this entry was accepted: the first draft of the
  deployment-id rule did not count its lists (a command ending in the strings an artifact
  contributes hashed like that artifact) and left out environment, privileges, mounts, shm size,
  engine, backend, label and the advert; `disk_full` was listed as permanent.
- Fixtures under `fixtures/valid` and `fixtures/invalid`, one valid and several invalid for the
  new rules; operator view `GET /iw/v1/dynamic`.

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
