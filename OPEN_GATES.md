# Open Gates

Every gate below is **BLOCKED** unless this file records otherwise.

A placeholder, example, environment default, test fixture, prototype, or merged pull request
must never be interpreted as production approval. Specification of a control is not
deployment of it, and implementation of a control is not staffing of it.

This file exists because these specifications run far ahead of any running system. Without a
register of what is *not* approved, a reader encounters thirty-eight confident documents and
reasonably concludes more exists than does.

## How to read a gate

- **BLOCKED** — not approved. No implementation may behave as though it were.
- **APPROVED** — approved, naming the record that approved it and the exact scope approved.
- A gate may be partially approved. The approved part names its scope precisely; every other
  part of that gate stays BLOCKED.

Closing a gate requires an entry here and a decision record. Neither alone is sufficient.

## Production deployment gate

**BLOCKED for new deployments, with a bounded existing-service exception.**
The operator authorized the console/traffic/topology release to the existing Fry
site gateway and its registered Hive Rust gateway service on 2026-09-22. See
[`decisions/2026-09-22-existing-gateway-rollout.md`](decisions/2026-09-22-existing-gateway-rollout.md)
for the exact scope and release conditions. This approval does not assert that
deployment has succeeded and does not open unrelated deployment or fleet gates.

On 2026-09-28 the operator additionally authorized implementation, review,
merge, and deployment of bounded asynchronous gateway recording to the same
existing Fry/Hive path after a Quobyte outbox failure blocked inference
admission while model capacity remained available. See
[`decisions/2026-09-28-buffered-gateway-recording.md`](decisions/2026-09-28-buffered-gateway-recording.md).
The exception covers only the recorder/admission boundary and its observability;
it opens no new deployment target or fleet capability.

**APPROVED, bounded existing Farm gateway visibility correction only.** The
operator's 2026-10-12 request authorized fixing and redeploying the missing
Farm gateway on Fry. The scoped decision and release conditions are in
[`decisions/2026-10-12-farm-gateway-zero-capacity-registration.md`](decisions/2026-10-12-farm-gateway-zero-capacity-registration.md).
This approval does not assert that PR #867 has merged, that Farm is visible
yet, or that any Farm GPU/model capacity is READY. New deployment targets and
unrelated alias traffic remain blocked by their own gates.

The archived `InferWeave/inferweave-*` implementation repositories were read-only as of
2026-09-03 and are not a deployed system.

A local RTX 4090 Qwen3.8-27B unified-KV experiment on 2026-10-03 completed a direct-engine
matrix for one near-260K, two 120K, three 80K and a long image request. A later run through
the Rust node facade served a 257947-token request, showed 0/1/1 current offers during a
117448-token request, and returned `Red` for an image at each of the three context classes.
The original two-slot 120K vision engine and authenticated gateway route were restored and
verified. This is **not** production approval: real-backend cancellation/reuse, Fry staging
mixed-class traffic, and runtime flag attestation were still owed at that stage. Reproduction data, the candidate
Compose flags and post-run image IDs are in
[`evidence/rtx4090-shared-context-2026-10-03/`](evidence/rtx4090-shared-context-2026-10-03/).

**APPROVED, bounded Bender shared-context rollout only.** The operator authorized
qualification, review, merge and replacement of the existing Bender RTX 4090 vision
service behind Fry. The accepted
[`2026-10-04 decision`](decisions/2026-10-04-bender-shared-context-rollout.md)
records exact tested artifact identities, the narrow Rust host-watchdog and one-shot
Fry operational-adapter exceptions, and the explicit CI/private GHCR waiver.
The staged runtime evidence is preserved under
[`evidence/rtx4090-shared-context-2026-10-04/`](evidence/rtx4090-shared-context-2026-10-04/),
including failed runs and the exact-build successful automatic rollback.

The final-image stage7 automatic rollback passed with SSH multiplexing explicitly
disabled: old engine 122880/2, registrar, enabled route and authenticated HTTP 200
were restored. Stage6's SSH sandbox failure and quarantine remain in the record.
**Production activation was completed after the reviewed PRs merged**, limited to
implementation commit [`a82ca88bc7b8235d5ce6c8ed876199321f927f21`](https://github.com/InferWeave/inferweave/commit/a82ca88bc7b8235d5ce6c8ed876199321f927f21)
and the stage7 image/watchdog identities in the ADR. Recorded runtime source hashes
match that reviewed commit; pre-activation runtime and validation gates are proven.
The rebuilt image passed the full-capacity matrix with staging workers active,
gateway-routed concurrency without retry, and an explicit blue-answer check at 260k.
Its 80k/120k long-image cases prove context/transport only; small-image color controls
passed at every class, and earlier long-color results retain their artifact scope.

Final spec review approved the scoped decision. After a test-fixture correction,
the final complete library suite passed 730/730 with two test threads; strict Clippy and
formatting passed. CI is waived, not proven; agent review does not staff the
independent-review gate below. Production activation `prod-20261004-0722` was observed healthy at
2026-10-04T07:41:55Z after code merge `5ffef477ff29c327e3248408d56c268227c5558e`
and spec merge `52e899752ead34c41371bc6ede53779a2301c121`. The exact approved
proxy/engine/watchdog identities were retained; the fence was ready with no rollback
or quarantine. Three production aliases advertised 260000/120000/80000 total context
and 1/2/3 idle offers. Live 120k work reduced offers to 0/1/1. Routed text, controlled
colors, legacy compatibility and two120/three80/mixed concurrency passed without retry.
Fry staging was restored. Sanitized `production-*` records in the evidence directory
support these observations.

Pi, Hermes and OpenCode catalog refresh and fresh text checks passed; Pi/OpenCode
fresh red-image checks also passed. **Fresh Hermes native image attachment
requests passed at c80k, c120k and c260k**, each exiting 0 and identifying the
red fixture. Additional c120k blue and c260k green controls answered according
to the image with the same color-neutral question;
`production-hermes-vision-all-contexts.json` records the results.
These short requests prove each client alias path, not full-context load. The stale
auxiliary vision route was removed, the three aliases gained `supports_vision=true`,
and unsupported global reasoning options were cleared while the existing default
model retained its prior `medium` setting through a model-specific override.
Hermes' global 8192 output limit also affects unrelated models; OpenCode's stale provider key was synchronized,
with private configuration backups retained. At 2026-10-04T16:29:33Z,
`production-health-9h.json` recorded both candidate containers running after 9.14
hours of uptime with zero restarts and no OOM, proxy HTTP 200, a ready fence, no
rollback or quarantine, and three unsuspended production aliases. This bounded
snapshot does not establish continuous availability, a sustained or 24-hour soak,
or fleet qualification. This approval opens no unrelated
deployment, fleet, GPU-reset or host-reboot capability.

The production client compatibility correction and sanitized observations are linked
to implementation commit
[`c41841f8b94592e3cded4d11b4bd07e1db59a6ac`](https://github.com/InferWeave/inferweave/commit/c41841f8b94592e3cded4d11b4bd07e1db59a6ac).
Its separate review approved the change; 13 focused tests and Ruff passed. The client
follow-up [PR #697](https://github.com/InferWeave/inferweave/pull/697) merged as
[`810632ab5006998a30bf4f8aa10fec4999a25247`](https://github.com/InferWeave/inferweave/commit/810632ab5006998a30bf4f8aa10fec4999a25247). It did not change the
promoted engine/proxy/watchdog identities. Both `pi-stack-pi-web` and
`pi-stack-pi-web-sessiond` listed all three aliases with 80k/120k/260k context,
8192 output tokens and image support. This proves model visibility in those
containers, not a separate browser/sessiond inference request; active sessions were
left intact.

## Independent review gate

**BLOCKED.** These specifications assume independent review in several places — phase gates,
high-risk changes, security suites, the two-reviewer requirement on retirement receipts.

**No independent reviewer is enrolled.** The project is operated by one person. Every
threshold that reads as M-of-N is presently 1-of-1, and the separation between an
implementation session and a review session is a procedural convention, not an independent
party.

This is recorded rather than left to be inferred. A control recorded as existing but unstaffed
invites reliance that is not warranted, which is worse than a control recorded as absent.

## Multi-node operation gate

**BLOCKED.** No multi-node InferWeave weave has run. Federation, regional relay, gossip
discovery, cross-site routing and owner-preemption across hosts are specified and unexercised.

The operational evidence these specifications draw on comes from a single-site gateway serving
a small number of upstreams. Behaviour at fleet scale is projected, not measured.

## Hardware coverage gate

**BLOCKED.** Specified telemetry covers CUDA, ROCm and Vulkan backends. Measured evidence
exists for a subset only. Any claim that a backend is supported requires a device fingerprint
and live telemetry from that backend recorded under `specs/23_GLOBAL_TELEMETRY_BENCHMARKS.md`.

## GPU placement and hot-swap gate

**BLOCKED.** Per-GPU placement and hot-swap (`specs/43_GPU_PLACEMENT_HOT_SWAP.md`, `IW-SCHED-002`)
is specified and unimplemented. No node swaps a GPU under autoscaler control, and the fleet
autoscaler (`InferWeave/inferweave#302`) remains library-only.

- Every required test of `P3-T23`, `P3-T24` and `P3-T25` is `owed`.
- The defaults `min_gpu_dwell_secs = 300`, `dwell_load_multiple = 10` and
  `drain_timeout_secs = 120` are policy choices. None was tuned against fleet traffic.
- Swap timings were measured on one two-GPU host with one runtime. The production router binary
  they were measured on has no recorded commit; its behaviour was read from source at `82d6bb2`.
- No swap has run across nodes, so the availability floor has not been exercised against a real
  second instance.
- The capacity reason codes, including `INSTANCE_DRAINED`, exist as prose in
  `implementation/ERROR_SEMANTICS.md` and one example. They are not frozen data reconciled by a
  test, so invariant 41 is unsatisfied for that vocabulary. This predates the change.

## Settlement and accounting gate

**BLOCKED.** Invariants 29 and 30 and decision `D-004` defer all blockchain and settlement
work. No token, treasury, wallet, mint, payout or transferable value exists or is approved.
Internal contribution accounting is not a claim on anything.

## Security qualification gate

**BLOCKED.** No independent audit, bug bounty, incident-response exercise or sustained
adversarial run has occurred. The threat surface is specified; it has not been attacked.

## Specification maturity gate

**PARTIALLY APPROVED.**

Approved: the specification bundle is authoritative for implementation sequencing, and
`scripts/validate_specs.py` proves its structural integrity.

The backpressure action vocabulary and version-one error vectors now exist at
`contracts/backpressure-action-codes.json` and
`contracts/backpressure-conformance-v1.json`. They define a contract but do not
prove that any Rust, Go, or Pi implementation conforms to it.

BLOCKED: other vectors required by `specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`
remain unpublished, and no cross-implementation backpressure conformance claim may be made
until each consumer runs the shared cases. Every `owed` proof status in the task graph is an
open gate on the control it names.

## Topology v2 operational qualification gate

**BLOCKED.** Spec 40 now defines the versioned authenticated topology HTTP
surface and corrects its prior v1 example mismatch. This does not demonstrate
that a real multi-site graph has been collected, that peer credentials are
provisioned, or that the deployed console consumes it. Those operational proofs
remain `owed` by P5-T11/P5-T13. Implementation unit and HTTP fixture tests may
prove individual controls; they do not satisfy the multi-node deployment gate.

The optional held-link topology correction in spec 40 addresses the observed
Hive descendant-visibility gap. Local wire and failure tests do not themselves
prove live parent-link inventory delivery. That deployment evidence remains
owed under the existing Fry/Hive service exception; unrelated controller and
GPU-worker releases are not authorized by this correction.

The optional configuration projection in spec 40 addresses missing per-node
hardware/deployment display and current-serving evidence. Schema and local
regression tests do not prove complete fleet device coverage or independently
verified residency. Live populated map and serving-color freshness evidence
remain `owed` to P2-T23/P5-T11/P5-T13 until recorded from the bounded Fry/Hive
rollout. Missing per-device descriptors on older workers remain unknown; a
future worker rollout is outside this release, and no GPU engine restarts or
placement changes are implied. Updated gateway and parent-link CLI must be
qualified together because older strict topology decoders reject enrichment.

The operator's shared-read map request retains operational configuration for
signed-in browser-session users while pseudonymizing device IDs and preserving
private address/label masking. Personal inference keys retain the existing
structural masked HTTP view without configuration; administrative bearer access
retains the full view. Actual HTTP handler regressions must verify these distinct
credential scopes. Raw-ID absence, within-view reference consistency,
cross-viewer handle separation and unchanged operator originals require explicit
implementation tests; live signed-in map visibility remains `owed` until verified.
This policy does not open anonymous access, administration or placement gates.
## Core protocol vocabulary (specs/44) — 2026-10-06

**BLOCKED for production use.** `specs/44_CORE_PROTOCOL.md` standardizes the
scheduler-neutral vocabulary for model identity, artifacts, capabilities, resource
requirements, capacity, lifecycle events, metrics, health, and federation
provenance. It is a specification only. No node, runtime, or gateway currently
emits or consumes this vocabulary in production; the model/runtime/capacity
surfaces remain those of the specs they amend (02, 03, 04, 05, 09, 20, 21, 23, 42).

Every required test in this specification is recorded `owed` by the canonical
tasks `P5-T18`–`P5-T23`. A schema, example, fixture, or local unit test does not
close this gate. Until those tasks land and are independently verified, an
upstream system must not rely on the protocol vocabulary being a deployed
capability, must not treat `unknown`-free advertisements as complete, and must not
assume health-probe/benchmark request classification, federation provenance, or
scheduler-neutral event mapping are enforced anywhere in a running system.

## Protocol v1 wire contract (specs/45) — 2026-10-07

**BLOCKED for production use.** `specs/45_PROTOCOL_V1.md` defines InferWeave Protocol v1, the
versioned, machine-readable, language-neutral wire contract that formalizes and supersedes the
spec-44 vocabulary into planes, stable identity, feature negotiation, canonical objects, JSON
Schemas, events, state machines, enums, error taxonomy, aliases, routing, jobs, conformance
levels, and cross-repo ownership. It is a specification only. No component emits or consumes
Protocol v1 in production, and no `schemas/v1/` schema, `state-machines/`, `conformance/`, or
`fixtures/` artifact is a deployed capability.

Every required test in this specification is recorded `owed` by the canonical tasks
`P5-T24`–`P5-T29` (feature `IW-PROTO-002`).

The canonical-protocol **artifacts are delivered and locally validated**: all `schemas/v1/`
object categories (common, errors, topology, model, resources, runtime, requests, events, jobs,
artifacts) and 30 JSON Schemas; the frozen canonical vocabularies under `contracts/protocol-v1/`
reconciled by a test guard; the OpenAPI (`openapi/inferweave-v1.yaml`); the conformance
profiles, fixtures, and `conformance/runner.py` harness; the compatibility matrix and release
manifest; the `docs/` set; and the `protocol-ci` workflow. `python3 scripts/validate_specs.py`
(+ `--self-test`) and `python3 conformance/runner.py` pass.

This does not close the production gate. **No node, runtime, or gateway emits or consumes
Protocol v1 in production, and no Protocol v1 endpoint exists in a running system.** Production
conformance by a running component, cross-repo CI execution against the `inferweave` reference
implementation, and independent multi-node verification remain `owed` by `P5-T24`–`P5-T29`. An
upstream system must not rely on Protocol v1 as a deployed wire contract.

## GPU memory accounting (specs/46) — 2026-10-07

**BLOCKED for production use.** `specs/46_GPU_MEMORY_INTELLIGENCE.md` defines the capability-gated
`iw.gpu-memory` family of Protocol 1.1.0: per-GPU physical, attributed and unattributed memory with
an explicit basis on every byte count, reservations, pressure, decision records, OOM postmortems
and read-only placement simulation. Its decision record
(`decisions/2026-10-07-gpu-memory-accounting.md`) is `Accepted for implementation` (2026-10-08). It is a specification with
schemas, four canonical contract fixtures and conformance fixtures that
`python3 conformance/runner.py` validates.

Unsatisfied, and recorded `owed` by `P5-T30`–`P5-T32` (feature `IW-GPUMEM-001`):

- a node producer whose physical memory is measured on **NVIDIA** hardware — not exercised;
- a node producer whose physical memory is measured on **AMD** hardware (ROCm, sysfs, DRM
  fdinfo) — not exercised;
- gateway composition of `safeSchedulable`, pressure and eligibility, the reservation ledger and
  the fleet snapshot — not built;
- the decision/event feed, OOM postmortems from a real OOM, and placement simulation — not built;
- nested-gateway de-duplication across real relays — not exercised.

No placement, eviction, packing or scaling behaviour may depend on this surface until those
tests are `proven` and an operator decision approves it.

## CLI mode grammar (spec 28 change request) — 2026-10-08

**BLOCKED. Not accepted.**
[`docs/specs/cli-unification/spec-28-change-request.md`](docs/specs/cli-unification/spec-28-change-request.md)
is a DRAFT. It proposes the `inferweave <mode> <command>` grammar as spec 28's addressable
contract, with every frozen spelling kept as an alias. It also proposes that the relay commands
join the JSON envelope and exit-code table, and it fixes the standard flags. Spec 28 and the frozen
command table are unchanged and stay authoritative. Each of the following is **unsatisfied**:

- spec 28 has not been edited, and the change has not been reviewed or accepted;
- no feature ID has been assigned and none is invented in the draft. There is no task-graph,
  implementation-sequence, task-card or coverage entry;
- the envelope and the four-row exit-code table that the draft extends are not in spec 28 at all.
  They are frozen only in the implementation repository (`docs/specs/cli.md`,
  `schemas/json-schema/cli_*.json`, task `P0-T03`);
- every test the change relies on (shim stdout and exit equality, deprecation line on stderr only,
  command-table drift, unchanged spec-28 conformance, relay-only static build) is `owed`, not
  `proven`;
- open questions D10 (gateway mode in the static node release) and D13 (removing the runtime
  shims) are undecided;
- independent review is unstaffed (see the independent review gate).

## Node join: hardware-only registration and tokenless enrollment (specs/47) — 2026-10-08

**BLOCKED for production use.** `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` defines the
optional `hardware` report on `POST /v1/node/register`, hardware-only registration, the
always-present `assignments: []` and the wire contract of tokenless proof enrollment. Its decision
record (`decisions/2026-10-08-open-proof-enrollment-and-hardware-registration.md`) is `Proposed`.
It is a specification with two schemas, schema fixtures, HTTP-level vectors and two Ed25519 known
answers that `python3 conformance/runner.py` checks.

Unsatisfied, and recorded `owed` by `P5-T33` (Rust gateway) and `P5-T34` (Go gateway), feature
`IW-NODEHW-001`:

- neither gateway implements hardware storage, hardware-only registration or `assignments`; no
  running gateway has replayed `conformance/node-join-vectors.json`;
- the Rust reference refuses `deployment: ""` at deserialization, and its proof-earned credential
  is minted in a store that `/v1/node/register` does not consult, so a node that enrolled by proof
  cannot yet register with the credential (read from source at `2c98035`, not run);
- the Rust proof store (keys, challenges, credentials) is in memory: the first-publisher-owns-the-id
  binding does not survive a restart, and `/key` and `/challenge` are unauthenticated and
  unbounded;
- the Rust reference accepts a tokenless challenge for any well-formed role; spec 47 requires only
  `node` (others `400 bad_request`), and the Go gateway's role set (`node`/`gateway`) must be
  narrowed to match; neither is changed or tested here;
- the tokenless-credential limits of spec 47 section 6.1 (403 on endpoint or models, 403 on a proof
  over an operator-enrolled id) are implemented and tested in the Rust gateway work tree
  (`GatewayEnrollment::adopt`, the `node_register` gate, `hardware_registration.rs`) but not on
  `main`, and the Go gateway is being aligned; the credential origin is held in memory only, so a
  restart forgets it;
- hardening of spec 47 sections 6.2 to 6.9 (promotion, links, known ids, bounded state, body caps,
  hardware lifecycle, rollback safety, no capacity from hardware-only heartbeats) is implemented
  in work trees (Rust `b7e696f`, Go `cdc0d69`), not on `main`, and is `owed` by `P5-T33` and
  `P5-T34`. Link refusal and "close every link" are not HTTP-level and have no vector;
- **conformance divergence:** the Go gateway keeps the stored `hardware` when a re-registration
  omits it, while spec 47 section 3.1 rule 8 (and Rust) clears it; the Go 429 codes also differ
  from the Rust `too_many_requests` (clients must key on the status); the Go register cap is
  128 KiB against the recommended 256 KiB;
- the Rust proof store is in memory, so section 6.8 rollback safety (persisting proof-only origin)
  is met by Go only;
- spec 47 sections 5.2 (derived tokenless id, idempotent challenge) and 6.10 to 6.12 are
  implemented in the Rust gateway (PR #761) and `owed` in the Go gateway: Go parity is in progress
  on the Go branch `feat/tokenless-idempotent-challenge-derived-id`, and until it merges the Go
  gateway replaces a pending challenge, accepts any tokenless id and has its own release TTL;
  neither is exercised by a running replay of the vectors;
- per-source caps and rate limits are keyed on the TCP peer address, so behind a reverse proxy they
  apply to the proxy as a whole (spec 47 section 6.11);
- the model-execution proof has a defined transcript but no wire surface; renewal and re-proof for
  an enrolled node have no wire surface;
- whether the Go standard-library Ed25519 verifier matches the strict verifier of the reference on
  small-order keys and non-canonical encodings is not tested;
- the Rust repository's own `conformance/MANIFEST.json` does not yet include these vectors;
- the open enrollment policy (a free node identity against the identity-scarcity assumption of the
  peer-trust design) has no accepted decision; the record is `Proposed`.

No deployment may enable open enrollment, and no placement or routing behaviour may depend on
`hardware`, until those tests are `proven` and an operator decision approves it.

## Universal runtime families and lifecycle (specs/48–53) — 2026-10-12

**BLOCKED for production use.** The IW-RT-001…006/B-T01…06 protocol artifacts define typed runtime
families, isolated adapter lifecycle methods, native family requests, immutable-key single-flight
loading, fenced safe-peak reservations, three transactional cache classes, availability-aware
swap, pipelines, durable jobs and executable conformance. These are protocol contracts only.

The offline conformance runner validates advertisements and positive/negative request bodies. It
prints `native HTTP: NOT RUN` unless an operator supplies `--live-base-url`; OpenAPI path existence
and schema validation are not evidence that a server handles a request. Even a live contract replay
does not by itself prove resource accounting, cache integrity, rollback or production readiness.

Unsatisfied and recorded `owed` by the amended B-T01…B-T06 tasks and the later runtime/gateway
implementation work:

- no production adapter implements and exercises all twelve lifecycle methods across the required
  process/container isolation boundary;
- no production manager has demonstrated waiter-independent cancellation for one immutable-key
  single-flight load;
- no production rebalancer has demonstrated idempotent fenced reservations, the full safe-peak
  resource envelope, crash reconciliation or progress-based expiry;
- the current artifact fetch implementation buffers bytes in memory and its legacy custom
  `digest128` cache identity is not SHA-256 integrity proof; streamed multi-GB acquisition,
  cryptographic verification, atomic publication, pinning and offline behavior remain unproven;
- no constrained-memory drain-and-swap or cross-node replacement has demonstrated rollback and
  the reported availability impact against a real runtime;
- no mixed-version gateway/node pair has exercised additive family fields, legacy jobs without
  `family`, or `completed` normalization to canonical `succeeded`;
- no mixed-version link has exercised the `/v1/node/register` capability-array intersection,
  negotiated `iw.link-native-request/1` dispatch, independently negotiated
  `iw.link-native-response/1` end-frame proof with exact 201/4xx/5xx relay, rejection on an older
  or request-only peer, exact `connectionId`
  plus Link-incarnation Hello/ack binding, or atomic dispatch across re-registration, replacement,
  credential expiry, or socket close; the family/endpoint, artifact-reference, response-byte/digest
  and canonical response-header bounds have also not been exercised against a production node;
- no real end-to-end demonstrations have loaded and served the required runtime families through
  native endpoints under production admission, owner priority and telemetry controls.

Runtime-family production integration remains owed until those real demonstrations and the
independent review are recorded as `proven`. The schemas, fixtures and local runner must not be
cited as operational qualification.

## Dynamic model aliases level 2 — runtime and rollout unsatisfied

Spec 54 / IW-ALIAS-001 / A-T01–A-T08 defines the operator's 2026-10-12 handoff. Schema,
OpenAPI, vocabulary and fixture checks prove artifact consistency only. All 29 runtime/UI/load
acceptance tests in contracts/dynamic-alias-acceptance.json are **owed**. No production gateway
may advertise level 2 based on this contract commit alone.

Unsatisfied gates: native Rust alias authentication and tenant isolation; validated edge identity
forwarding (existing Go relay strips identity); durable alias publication/CAS/idempotent rollback;
instance-generation joint capability evidence; owner atomic admission and stream-safe fallback;
GPU-loss/preemption/runtime integration; owner sharing/de-duplication/expiry; resumable alias
snapshots/events; complete UI journeys/visual/accessibility evidence; migration shadow parity,
measured p95 baseline/canary and feature-flag rollback. Existing exact-model paths must continue.
D-002's narrow Go UI exception supplies architecture authority, not proof of security or function.

Security follow-up: A-T02 requires a separately purposed edge Ed25519 delegation assertion,
request binding (method, target, body, preconditions, deadline, nonce), Rust-owned IdP
issuer/subject-to-tenant/role grants, replay protection and cross-language hostile vectors.
Spec 55 now specifies the exact signing transcript, key trust and PostgreSQL replay rules;
offline golden vectors prove only transcript consistency. The running authentication/grant/replay
boundary is unverified. No usable existing delegation mechanism was found; no OIDC forwarding, shared registration
credential or caller-provided identity shortcut is authorized. Alias API/traffic remains disabled
until independent security review and executable evidence close this gate.

## Runtime instance observation producer and ingestion (spec 56)

**BLOCKED for production use; implementation proofs owed.** The additive optional
`iw.runtime-observations/1` report and offline hostile vectors specify producer-to-owner
binding. They do not prove authenticated registration ingestion or runtime readiness. A-T05
still owes durable actual-load generation production, registration-incarnation/epoch replay
fencing, profile qualification by an approved verifier, independently authorized owner policy,
complete-snapshot expiry/tombstone invalidation, durable per-item sequence/content replay
fences, actual encoded-byte report bounds before parsing, physical resource-group de-duplication,
multi-GPU-loss propagation and atomic admission revalidation. A-T08 owes mixed-version live
rollout, latency/parity and failure/recovery evidence. Working Rust observation helpers and
local fixture success cannot close these gates or promote probes into verified tools/privacy.

## Alias execution identity and exclusive claims (spec57) — unsatisfied

Spec57, its schemas, public-seed signatures and serial hostile claim oracle are **offline contract
proof only**. They do not qualify `/v1/chat` or any other inference endpoint for level-2 aliases.
Management delegation (spec55), pure previews and runtime observations (spec56) cannot substitute
for current tenant infer grants or exclusive execution admission.

A-T02 owes native personal-key validation/revocation and current Rust tenant infer grants; separate
Go inference purpose/audience/path/body/semantic-header verification; grant/key revocation and
shared PostgreSQL nonce consumption. A-T04 owes shared operation/key claim transactions across
two parents, current holder/node fencing, reservation response-loss reconciliation, durable
DISPATCHED-before-send, no retry after ambiguous dispatch/partial stream, deadline/cancel cleanup,
exact-ID safety and redacted causal traces. A-T05 owes owner/node integration and one-use direct
permits; progressing GPU reservations cannot expire merely because a claim holder lease elapsed.
A-T06 owes a transparent Go signer/relay preserving stable operation identity, all accepted semantic
headers and cancellation without forwarding caller credentials. A-T08 owes fault-injected HTTP/DB/
owner/node concurrency and measured load on the actual implementation.

The retry horizon/retention setting, protected claim/grant authority deployment, signing trust and
owner reconciliation behavior must be configured and exercised before activation. None is inferred
from schemas or a single-process oracle. Traffic remains disabled until independent review and
these implementation gates pass. No operator approval or new credentials are represented as present.

Spec57 independent review additionally requires actual owner attempt-retirement persistence and
lost-response reconciliation across same-owner fallback, immutable operation/key choice, full
original/executable request materialization binding, and one claim consumption across distinct
permit IDs plus direct/relay delivery. Offline hostile vectors cannot close these runtime gates.


### Dynamic alias filtered pagination proof remains owed

Spec 54 permits an empty filtered page with a continuation and requires bounded advancing
scans, authorization/snapshot binding and explicit incomplete UI state. The list schema
already permits this response. These requirements do not establish runtime enforcement:
empty-page continuation, scan-budget exhaustion, repeated-cursor handling and authorization
revision invalidation at the Rust/Go boundary remain **unsatisfied/owed** under
A-T02/A-T06/A-T07/A-T08 and acceptance 20/27. No rollout gate is opened by this correction.

### Alias inference transport interoperability remains owed

Spec57's shared MIME/header vectors and offline classifier prove the bounded contract only.
A-T02/A-T06/A-T08 still owe running Go-to-Rust signature/byte preservation, endpoint semantic
validation, correlation non-authority and malformed transport rejection across the actual HTTP
boundary. Rust `c750d31d` and Go PR #476 at `2ceaf49` enforce the 8192 UTF-8 byte
correlation bound and share the canonical 36 MIME/12 header fixture, including multibyte
acceptance/rejection boundaries. Their fixture bytes agree with the canonical fixture
(SHA-256 `f485aaed3bc914df74eebc0ff9ee0d658e615c51ca7eac3c9101335963b93f2a`).
This component parity does not prove live cross-process HTTP interoperability or shared
execution-claim enforcement; those proofs remain **owed**. No deployed interoperability or
alias traffic activation gate is established by this evidence.

### Owner-to-node execution permit fence remains owed

Spec57's purpose-separated owner envelope and hostile serial oracle define authentication and
ordering only. A-T04/A-T05/A-T08 still owe actual durable node INTENT/SPENT fences across restart,
authenticated shared ConsumeDispatch and lost-acknowledgement fault injection, exact runtime
generation pinning through backend start, key/owner-incarnation revocation and negotiated Link
interoperability. Direct/client and node-proxy level-2 execution remain unsupported until separately
qualified against the same central claim fence. No production execution or activation is proven
by these schemas, public-seed signatures or offline scenarios.

PR #259 review correction: the earlier permit text incorrectly assumed native Link metadata
could preserve spec57 compatibility targets and semantic headers. The protected Request and
separate asynchronous consume control schemas now specify those missing bytes and bindings.
Running Link request/ack multiplexing, continued heartbeat/cancellation while awaiting consume,
late/wrong acknowledgement rejection, and post-fsync expiry/deadline/cancellation revalidation
remain **owed**. JSON-only bounded fixture success does not qualify multipart, chunking,
OpenAI SSE/tool streams, direct execution or node HTTP proxying.

## Model intelligence and existing UI cohesion — implementation versus qualification

**Implementation and merge authorized; all new qualification proof owed.** The
2026-10-12 operator kit authorizes spec 58 analytics in Rust and the current
embedded site UI, including optional theme parity. The scoped
[`decision`](decisions/2026-10-12-model-intelligence-ui-cohesion.md) amends D-002.
It opens no production rollout or automatic model-promotion gate. Passing this
repository's validator proves specification consistency only.

- **Owed — implementation:** token overlap/retry accounting, fixed-point rates,
  unique GPU allocation conservation, outcome/availability denominators, bounded
  observed SLO capacity, versioned evaluations, eligible Pareto recommendations,
  stage-gated opt-in/rollback, API authorization and existing-UI regression tests.
  Tasks P1-T20/P1-T21/P2-T03/P2-T05/P2-T07/P2-T08/P2-T10/P2-T16 own these tests;
  `contracts/model-intelligence-acceptance.json` records AC-MI-01 through AC-MI-07.
- **BLOCKED — private tenant/user analytics:** existing tenant headers are not
  grants. Verified principal-to-scope grants and cross-tenant denial tests are
  unsatisfied. Only explicitly authorized operator reports and separately
  allowlisted shared operational aggregates may be implemented; shared output
  must omit private identities/content/addresses.
- **BLOCKED — measured live capability claims:** normalized runtime usage, full
  timing/availability intervals, preemption causality, sustained hardware/workload
  SLO bins, task feedback, versioned configured prices and current owned-hardware
  eligibility require actual source evidence. Historical absence stays unknown;
  a merged endpoint or fixture does not satisfy these controls.
- **BLOCKED — activation:** per-fingerprint runtime qualification, privacy-safe
  shadow/canary evidence, explicit promotion policy, bounded rollback proof and
  production release authorization remain unsatisfied by this specification.
- **Owed — independent integration review:** verify all retained routes/actions,
  scopes, accessible responsive/theme screenshots, source/dist parity, bounded
  query performance and migration/rollback evidence against the actual UI.

Record implementation tests separately from live-source and hardware evidence.
Any later closure must name exact artifacts, commits, cohort/time window and
remaining unsupported sources; never mark the whole kit proven from unit tests.

### Model-intelligence implementation evidence checkpoint

Rust integration `35ac81e7b0a0c3cba23390c1adae092ea392ca0d` and bounded
operator Go transport have source/test mappings in
`evidence/model-intelligence-2026-10-12/README.md`; additive wire schemas are in
`openapi/model-intelligence.yaml`. Existing implementation tests and typed local
PostgreSQL fixtures do not close AC-MI acceptance or final P5 review. Current
Go reports are operator-only, with the existing registration-secret middleware
alternative; ordinary shared viewers and verified private tenant/user grants
remain unsupported. Shared-scope labels do not change that audience.

Full live availability/preemption intervals, raw billing/physical allocation
sources, complete task/logical linkage, sustained current hardware capacity and
qualified production evaluation imports remain **owed**. Before/theme-after
reports are bounded slices; final integrated route/browser/screenshots and
source/dist evidence are still owed at this checkpoint. No production gate closes.

## Exact-model HTTP JSON Held Link (spec59)

**BLOCKED / production proof owed.** Closed schemas and offline golden/hostile
stream and binding vectors are executable contract evidence only. Rust/Go mixed-version
path/status/MIME/body parity, current registration/socket atomic dispatch, cancellation,
credit starvation, terminal failure and no backend replay remain owed. This extension
opens no alias execution gate and cannot replace spec57 permits.

## Capability routing decision and mission events (spec60)

**UNSATISFIED / owed.** `specs/60_CAPABILITY_ROUTING_AND_MISSION_EVENTS.md` defines the
capability request, routing decision and mission event contracts. No gateway or router emits
`estimated_wait_ms` or `route_reasons` today, so gateway emission of the estimated wait and the
route reasons is **owed**. The schemas, fixtures and contract tests that would make the contract
executable are also owed and are not part of this change. `MAX_WAIT_BOUND_MS` (300000) is a value
chosen by the contract, not measured, and `quality_floor` is a `{metric_id, minimum}` pair whose
cross-deployment comparability is likewise unmeasured; its calibration against measured wait distributions is
owed. That the router never relaxes `quality_floor` to win a slot is a runtime property no test
exercises yet. Nothing in spec60 is `proven`, and no production gate opens.

## Alias precision, ad-hoc selection and resolution trees (spec61)

**PARTLY SATISFIED (contract shape); the rest UNSATISFIED / owed.**
`specs/61_ALIAS_PRECISION_ADHOC_SELECTION_AND_RESOLUTION_TREES.md` is a proposed additive amendment
of spec54 level 2: precision as a selection dimension, an ad-hoc evaluate-only selection, and a
four-level resolution tree with typed unmet requirements.

*Now present and checked by `tests/smoke/test_dynamic_alias_contract.py`:* the schemas
`schemas/v1/aliases/precision-classes.json` (versioned table, additivity checked), the ad-hoc body
(`selection`, optional `request_context`, closed, DYNAMIC only, exclusive with `alias_id` and
`definition`) on `resolve-request.json` and `simulate-request.json`, `adhoc-resolution.json` with
`resolution_tree`, `unmet`, `truncated` and `unmet_truncated`, the optional table-version pin
`selection.precision_table_version`, the three precision candidate reasons in the frozen reason
vocabulary and spec54's table, the precision and unmet vocabularies in
`contracts/protocol-v1/dynamic-aliases.json`, and acceptance entries 30 to 35. The ad-hoc
response fixture is the exact JSON the Rust producer serializes (InferWeave/inferweave test
`adhoc_wire_fixture_is_exactly_what_the_producer_serializes`), so the schema and the producer
agree on shape. This proves **shape only**; acceptance entries 30 to 35 stay `owed` because the
matrix demands a run against an implementation, and each carries `partial_evidence`.

*Still UNSATISFIED / owed:* the Go consumer beyond fixtures (required test 5); stamping the pin at
publish time (an absent pin means the validating build's current table); the precision-class table
is a classification, six of its tokens were observed in the reference lab gateway's model listings
on 2026-10-15 and the rest are unobserved; the bounds (64 model nodes, 256 instance nodes, 16
`unmet` entries, 16 allowed tokens) are design limits, not measurements, and are owed a measured
response-size check; the `capacity` shortfall depends on owner memory reporting (spec46) that is not
universal. Hosting requests, offers, approval, download and profile generation are not specified
here and no gate for them opens. No production gate opens.

## Federated provisioning: hosting requests (spec62)

**UNSATISFIED / owed.** `specs/62_FEDERATED_PROVISIONING_HOSTING_REQUESTS.md` records the delivered
`provision.*` contract (code at `inferweave/inferweave` commit `de43764a`; the code's own tests are
not run or counted by this change) and proposes an additive `acquisition` feature: a model
reference, request and offer additions, sizing evidence, phases inside `ACTIVATING`, an authority
model per owner mode, and safety rules. No schema, fixture, sender, consumer or test of the
extension exists, so every required test of spec62 is **owed** and nothing in it is `proven`. The
size estimator, phase duration estimates and every byte bound are deliberately unspecified because
none has been measured; they are owed measurements, and an estimate may not drive an automatic
decision until validated against measured sizes. Hugging Face metadata is a `declared` third-party
statement and is owed a measured comparison with fetched sizes. Alias `PROVISIONABLE` marking from
an advertised `acquirable` member is owed. No production gate opens.

Review round 1 (independent) corrected the delivered-contract record and added requirements, all
**owed**: the delivered lease is elapsed-time and violates invariant 37 (the extension changes
it); `activate()` is synchronous and must stop emitting `READY`; `autonomous` + `activate` is
refused today so autonomous acquisition has no activation path; the delivered `ProvisionFeature`
enum is closed so negotiation needs unknown-feature skipping or `iw.provisioning/2`; the
closed-object rejection of new members is new behaviour; `FITS` is unreachable for an unprofiled
model; first-fetch digest verification needs operator-approved digests; `shortfall` must not leak
free resources. No production gate opens.

## Link upstream role and authenticated gateways (spec63)

**UNSATISFIED / owed.** `specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md` proposes the link
role `upstream` (capability `iw.link-upstream/1`): a gateway holding a typed `api_key` credential dials
an upstream gateway and submits exact-model requests up the held link, with its own acceptor-created
binding (no registration), N upstreams, no transit by default, an acceptor-appended federation path with
a hop limit, request-id idempotency and one charge per boundary. It is gateway byte relay, so invariant
11 limits it to where direct transport is unavailable or forbidden. No schema, fixture, sender, acceptor,
dialer or test exists; every required test is **owed**. Bounds (catalog size, drain window, rate and
concurrency defaults, hop limit beyond 8, transit) are unspecified because none is measured. **Open
decisions** (`decisions/2026-10-15-link-upstream-role.md`): whether the Go site gateway implements the
acceptor side (touches the D-002 amendment), and whether this needs its own feature ID. The only
measurement is one unreproduced observation that the public HTTPS API accepted a key on a read. No
production gate opens.

## Implementation status of specs 61-63 (2026-10-15)

Nothing here opens a production gate.

* **Spec 61 (Rust, InferWeave/inferweave #1021 merged, #1029):** precision tokens/classes, ad-hoc
  `POST /inferweave/v1/aliases/resolve|simulate` with an inline `selection`, the resolution tree and
  `unmet` are implemented and deployed to the bender lab gateway (management/preview only). A signed
  edge request against it returned 200. **UNSATISFIED / owed:** rate limiting and audit of ad-hoc
  calls (no preview audit sink exists); stamping the table-version pin at publish (the pin member
  itself and the schema/contract additions now exist, see the spec61 gate above); a measured
  memory report in the production inventory (so `capacity` never appears); the Go console test 5 is
  covered by metabolomics-us/inferweave-gateway #549 against fixtures only. **Defect found by running
  it:** an ad-hoc selection with no stated preferences was rejected because stored-alias preference
  weights must sum to one; fixed in #1029 (neutral even weighting for ad-hoc only).
  The lab catalog is **empty** because legacy capability evidence is unverified, so resolve returns
  UNAVAILABLE with no `unmet` until nodes report verified capability profiles.
* **Spec 62 (pure slice, #1022):** types, sizing evidence, `fit`, redaction and feature-skipping are
  implemented behind no caller. **UNSATISFIED / owed:** required tests 2, 5, 6, 7, 9; the controller
  changes (progress-based lease, asynchronous ACTIVATING, autonomous activation); approval-digest
  recomputation; the `acquirable` capacity member; rate limiting of planning.
* **Spec 63 (acceptor slice, #1024):** default-off (`IW_LINK_UPSTREAM_V1`), refuses the role in
  production because no channel-binding exporter and no executor exist. **UNSATISFIED / owed:** the
  dialer, execution through admission and accounting, reuse of the existing principal-key file, the
  catalog frame, byte accounting and the relay circuit breaker, durable dedupe across restarts, the
  declared traffic class on the wire (every request is `private` today), and the Hello/ack schemas.
  **Spec defects found while implementing:** channel binding gives no proof of possession for a bearer
  key (TLS is the real protection); one Hello carries one credential so "both roles on one link" is not
  expressible; "optional allow-list" vs "absent bound denies"; the hop limit "8" vs "no default"; a
  refused Hello gets no acknowledgement.

### Update 2026-10-15 (later): spec 61 audit/rate limit and lab evidence

* **Implemented (InferWeave/inferweave #1039):** per-principal rate limit and an append-only audit of ad-hoc
  selection calls (`CALLER_RATE_LIMITED`, now recorded in spec 54's reason table and the alias contract JSON).
  **Still UNSATISFIED / owed:** the limit default (30/min) is an unmeasured placeholder and is per process and in
  memory; audit retention/partitioning is a documented runbook, not implemented; the audit table's append-only
  guard is only as strong as the application database role.
* **Implemented (InferWeave/inferweave #1037):** gateway-attested instance evidence plus an operator
  `IW_ALIAS_OWNER_POLICY`, so registered instances can appear in previews. **Still UNSATISFIED / owed:** node-attested
  lifecycle generation, `runtimeObservations` ingestion, qualification and privacy/residency/trust evidence
  (every row is `Advertised`/`UNKNOWN`; none is selectable); an owner-canonical resource-group identity.

### Update 2026-10-15 (latest): System One CPU capacity wire (specs 44, 47, 59)

Nothing here opens a production gate or marks a control available.

* **Specified, additive, optional:** `systemone[].device` / `max_concurrency` (spec 47 section 2.2), heartbeat
  `status.systemone`, link `meta.systemone_batch`, link-http targets `/v1/systemone` and `/v1/systemone/batch`
  (spec 59), and the CPU-only-node statement (spec 44). Reference implementation: InferWeave/inferweave #1045 (open at
  the time of writing, not merged); the Go gateway side is metabolomics-us/inferweave-gateway #557.
* **Proof status.** `proven` here: the offline spec-59 oracle, the new link-http vectors and the schema checks
  in `tests/smoke/test_systemone_wire.py` (the target vectors fail with the contract change removed). **Owed, UNSATISFIED:**
  gateway-side enforcement of `max_concurrency >= slots` and of the `device` token in either gateway; a mixed Rust/Go
  fleet routing to a CPU node with no GPU telemetry; heartbeat `systemone` ingestion; the Go `link_http`
  acceptance of the two new targets. Owed by inferweave #1045 and inferweave-gateway #557 until their tests exist,
  run and fail with the control removed. Measured capacity values (`max_concurrency` defaults, process counts) are
  not stated or relied on.
* **Open specification defects, not resolved by this change:**
  1. Casing: `systemone[]` entries are snake_case in a camelCase register body, the heartbeat object is camelCase.
     Both are recorded as normative today; one spelling must be chosen by decision.
  2. A System One node registers a real endpoint with `models: []` and a `systemone` list, a shape spec 47
     section 4 and `node-register.json` call invalid. Either the shape rule or the registration is wrong.
  3. Whether a System One request may use the legacy frame path (with `systemone_batch`, or body-classified) when
     `iw.link-http-json/1` is not negotiated, instead of the 503 `FEATURE_UNSUPPORTED` that spec 59 now requires
     for HTTP mode.
  4. The reference validator requires a non-empty `model` in the body on every link-http target; spec 59's oracle
     did not check it (now stated for System One only; chat and completions text is unchanged).
  5. The node-workload design (`systemone-node-workload.md`) lives only in the implementation repository.

