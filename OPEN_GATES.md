# Open Gates

## Autonomous background benchmark production qualification

**BLOCKED.** Spec 33 background scheduling policy and spec 46 shared-memory
admission require live target qualification. Local policy, journal, resource-ledger
and subprocess tests do not establish production readiness. Owed: NVIDIA/AMD
sharing headroom and serving-pressure validation, exact owned Slurm-step
cancellation/preemption, independent deployed recovery, a verified Hive 8×A100
canary, and a 24-hour interruption/recovery soak. Free VRAM, static qualification
templates and a successful process exit grant no production placement authority.
Keep the owning rebalancer, availability floors and scheduler authority in force.

The benchmark-policy implementation does not implement P5-T31's owning-gateway
composition/export. Physical node reports and generic heartbeat storage do not
constitute authoritative `safeSchedulable`, pressure and eligibility, nor a
qualified `/iw/v1/gpu-memory` endpoint. Live automatic sharing remains blocked
until that controller dependency is implemented and qualified; fixtures or a
successful/unauthorized HTTP probe do not satisfy it.

Every gate below is **BLOCKED** unless this file records otherwise.

A placeholder, example, environment default, test fixture, prototype, or merged pull request
must never be interpreted as production approval. Specification of a control is not
deployment of it, and implementation of a control is not staffing of it.

This file exists because these specifications run far ahead of any running system. Without a
register of what is *not* approved, a reader encounters thirty-eight confident documents and
reasonably concludes more exists than does.

## Owner cold-boot catch-up and epoch adoption — 2026-11-06

**UNSATISFIED / owed.** Spec 36 now defines explicit owner requalification of an
already-running external engine after a host reboot, keeping quarantine until
complete retained-boot journal/native evidence replay and a coherent durable
checkpoint/identity adoption. The approved design permits implementation, not
runtime adoption or automatic rescue. The existing guard's bounded current-boot
monitor is not a cross-boot catch-up API; deleting a cursor to initialize at the
tail is prohibited. Spec 28 external status remains read-only.

`IW-WATCH-001` / `P1-T20A` and `IW-WATCH-003` / `P3-T18A` owe complete history and
historical-scope provenance for scoped exemptions, boot-local stateful replay,
explicit whole-machine conservative candidate/coverage proof without exemptions,
native byte/append handoff, strict no-bootstrap startup, publication crash tests,
and fresh local
plus authenticated context/concurrent-session qualification. Implementation,
removal-sensitive tests, independent review, applicable repository checks and
owner production qualification are **owed**, not inferred from health, old proofs
or this specification. Disabled CI pools do not waive required checks. Missing
required provenance/lost records/new faults keep the resource quarantined.
Global-only candidate normalization/cross-record windows, all-transport loss IDs,
trusted kernel/driver loss recognition, protected collector configuration and
limited assurance receipts remain **owed** before adoption. Global journal
sequence continuity does not establish completeness of never-ingested events;
historical collector continuity and trusted producers remain declared assumptions.
Historical scopes may be absent only for complete candidate-free conservative
coverage, never for a scoped exemption or a claim that the machine is fault-free;
all existing
qualification, watchdog and rollback gates remain binding. No gate opens here.
See [operational evidence and limits](evidence/owner-coldboot-epoch-adoption-2026-11-06/README.md).

## Autonomous capability & limitations bench v1.0.0 — 2026-10-28

**BLOCKED. Unsatisfied.** Package `inferweave-autonomous-capability-bench-v1` (SHA-256
`66b15719d09f4ddb135f6ad8d69e476e91b65810a0db8b1d114afd2414dd8496`) is audited in the
implementation repository under
`docs/specs/inferweave-autonomous-capability-bench-v1-20261028T180332Z/inferweave-autonomous-capability-bench-v1/audit/`.

- **P1 (record metadata): merged, not deployed, not independently staffed-reviewed.** An optional
  `capability` block on `iw.bench-record/1`, merged as implementation commit
  `4e78b54a3413f5cbb20011a66a1bbdfaaa25f06c` (PR #1360); frozen vocabulary in
  [`contracts/capability-bench-vocabulary-v1.json`](contracts/capability-bench-vocabulary-v1.json).
  Proof status, reproducible with `cargo test -p iw-bench-record` at that commit:
  *proven* — a record without the block keeps its historical `content_sha256`, id, JSON and
  comparison/series keys (removing `skip_serializing_if` fails 2 tests); a changed grader hash
  changes the comparison key (removing it fails 1 test); a stored record that breaks the block's
  rules is refused on load (removing the load validator fails 1 test). *owed* — every other P1 rule
  (canonical/adaptive requirements, hash checks) has a test but no removal-mutation was run.
  No producer emits the block. `Record` rejects unknown fields, so readers must be deployed before
  any writer. A model agent (Codex) reviewed the change; that does not staff the independent review gate.
- **P2–P8: unsatisfied.** No new graders, mutation lifecycle, interactive harness, adaptive
  scheduler, statistics, dashboard views or rollout exist. Nothing has run on real hardware;
  no figure is measured.
- **Live placement remains BLOCKED.** Spec 33 (background scheduling) and spec 46 (shared-memory
  admission) govern background benchmark placement; this package's P5 is not approved to take
  production placement under either. Qualification conditions beyond those specs (sharing headroom,
  exact Slurm-step cancellation, a canary, a recovery soak) appear in an operator draft of the
  background-benchmark gate that is not on `main`; they are not defined by this entry and need a
  decision record before any live placement. Protected R9700 allocations and the operator's Mac
  are never eligible without explicit configuration.
- **Registry traceability owed:** feature IDs, task cards and `canonical-task-graph.json`
  entries for P1–P8 are not created, and specs 12/23/24 were not reconciled field by field.
- **Drift Watch extension (2026-11-08): registered, unsatisfied.** Scope adherence, stack fingerprint
  and paired drift alarms are merged in the implementation repository (PR #1491, `f9595585`) as an
  extension of this package, registered as `IW-BENCH-004` to `IW-BENCH-008` and tasks `P2-T25` to
  `P2-T29`, with frozen
  [`contracts/capability-bench-vocabulary-v2.json`](contracts/capability-bench-vocabulary-v2.json)
  (v1 untouched). All five tasks are `owed`; nothing is deployed and nothing has run on real
  hardware. Not proven here: this change reproduced no implementation test. Known limits, from the
  design: scope adherence is an upper bound (no catch-all egress recorder); the sandbox work
  directory is not size-capped; the real git is listable inside the sandbox; the drift statistics
  have no production history producer and Holm over a rolling pair does not control the error rate
  across repeated monitoring; the hardware guard works from names, so a protected machine under an
  unlisted name or bare address is not recognised; and the containment tests skip where `bwrap` is
  unusable (the Woodpecker `ci.sif` image), so those controls are proven only on hosts with it.
  Quantization baselines (`P2-T29`) are not started or planned. Scope and drift results must not
  feed routing eligibility. Evidence:
  [`evidence/drift-watch-traceability-2026-11-08/README.md`](evidence/drift-watch-traceability-2026-11-08/README.md).
  The P1–P8 traceability and the spec 12/23/24 reconciliation above remain owed.

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

## InferWeave Storage (specs/65) — 2026-10-16

**BLOCKED for production use.** `specs/65_INFERWEAVE_STORAGE.md` defines the `store` role, the
`iw.store/1` capability, the signed `iwg1` grant, the native and read-only S3 front ends, the
network exposure and single-writer controls of a store, the digest index and the multi-source
stager. Its decision record (`decisions/2026-10-16-inferweave-storage.md`) is `Proposed`.
Phase 1 is implemented in part in the reference implementation (branch `feat/inferweave-storage`,
commit `c92fb073`, **not merged** at the time of writing); Phase 2 is not built.

Unsatisfied, and recorded `owed` by `P5-T36` (feature `IW-STORE-001`, Phase 1) and `P5-T37`
(feature `IW-STORE-002`, Phase 2):

- the reference implementation carries unit, loopback HTTP, TLS-gateway, S3 client interoperability
  and stager tests; no independent review has run, and no blob has moved between two real clusters
  through a store. The farm staging figure (about 20 minutes for 30 GiB) is the motivating
  observation and is not a measurement of this system;
- **TLS (H1, O2, O14):** no store listener serves TLS; a non-private bind is plain HTTP, so a grant
  or an S3 signed request is visible to the network path. Until it exists no gated-scope blob may be
  served beyond a private network or a tunnel. The store only warns on a public bind;
- **per-listener blob scope (H6, O3):** a store has no scope tag per blob, so a publicly bound
  store does not refuse gated blobs; the operator must keep them out of its directory. Which models
  are gated is undecided;
- **grant forwarding across federation (O4):** a parent gateway cannot obtain a grant for a child's
  store on a node's behalf; it names the remote holder and the node asks that gateway, and the
  store lists that gateway's key as an operator extra. Transitive (grandchild) reporting and the
  trust anchor across federated gateways are not built;
- **per-range hashes (O7):** a corrupt assembly is attributed to a source only by the single-source
  retry; Phase 1 omits them;
- **presenter binding (O5):** a grant is a bearer token within its `node_id`; replay for up to 300
  seconds is accepted;
- **whole-blob grants (O11), the `max_request_bytes` cap (O12), the S3 credential model (O13), the
  ETag as SHA-256 (O16) and the S3 request cap (O17)** are decisions the specification states and
  no operator has approved;
- **abuse controls (H2, H3, H4, H5, H7):** lockout is per exact IP (an IPv6 `/64` can cycle
  addresses); the allow-list is read at start only; the request ceiling is a fixed window; there is
  no PROXY protocol option; a native client with one valid grant can rotate `X-IW-Node` values to
  dodge the identity lock and no address-wide backstop counter exists;
- **quarantine corroboration (O8):** the flag exists; its default is 1 and the right production
  value is unmeasured. A single node's report can quarantine a good store at the default;
- **first store location (O1):** no site operator has approved where the first store runs (a login
  node may breach cluster policy); no store is deployed anywhere;
- **Phase 2 is not built:** ingest leases (6.6), replication, repair, quota and eviction (10.1), the
  write path of the S3 front end (5A.8), the rendezvous with no inbound port (5B.10) and the
  epoch and no-replace publication (5C.6); failure modes F1 to F6, F10 to F14, F18 and F21 are
  `owed` with no test;
- the Rust client through `artifact_cache.rs` is not built; only `stage.py` stages from a store;
  hedging beyond throughput shifting is not built;
- integration with `specs/27` (the cache tiers) and `specs/64` (artifact sources) is undecided
  (O18), and `specs/40`, `specs/47` and the topology schemas of this repository are not yet amended
  for the `store` field and the `store` role;
- no conformance vectors exist in this repository for the `iwg1` transcript; the known answers live
  only in the reference implementation's tests.

No store may be deployed, no listener may be exposed beyond loopback or a private network, and no
gated or private model may be placed on a store, until those tests are `proven` against a running
fleet, TLS (or a tunnel) is approved for any non-private path, and an operator decision approves it.

## Dynamic nodes and gateway-driven provisioning (specs/64) — 2026-10-15

### Managed persistent onboarding extension — 2026-10-20

**BLOCKED for a claim of deployed/production-ready managed capability.** The operator has
authorized implementation, independent review, normal merge, and disposable Nibbler
installation/reset/qualification/restart work under
[`decisions/2026-10-20-node-onboarding.md`](decisions/2026-10-20-node-onboarding.md).
This bounded authorization permits the work to proceed; it does not mark its evidence complete
and opens no unrelated host reset or global catalogue activation.

`IW-DYNNODE-002` / `P5-T38` owns `iw.node-reconcile/1`, its strict `reconcile` control members,
per-card mixed-host facts, one-instance-per-deployment ownership, durable assignment/recovery
state and policy-scoped qualification/publication. `contracts/node-reconcile.json` acceptance
ONB-01 through ONB-12 is entirely `owed`: implementation, operator UI, clean install, actual
Pascal/Turing execution, real SIGTERM/SIGINT/graceful drop, host reboot, gateway restart,
watchdog/floor/rollback/quarantine, link inference/cancellation, and exact-artifact independent
release evidence. Schema fixtures and the offline decision oracle are contract checks only.

A throughput draft, healthy endpoint or restored container is insufficient for readiness.
Adoption and settle require current trusted qualification and watchdog generation; exhausted
attempts remain binding even when a status is terminal. Old owner permits are invalid after
restart. No synthetic fixture grants production authority. The original P5-T35 Beast evidence
below remains limited to its original `iw.dynamic-node/1` capability.

### Original dynamic-node capability

**BLOCKED for production use.** `specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md` defines the
`iw.dynamic-node/1` capability, the `dynamic` register member, the first non-empty `assignments`
entries (`serve`, `measure`, `stop`) on the register and heartbeat responses, the heartbeat
`provisioning` member, and the gateway's plan from desired models and measured runtime profiles.
Its decision record (`decisions/2026-10-15-dynamic-nodes-gateway-provisioning.md`) is `Accepted` (2026-10-16).
Three schemas and their fixtures are checked by `python3 conformance/runner.py`.

**Satisfied for the Rust reference implementation** (2026-10-16) — operational proof on host `beast` (2× R9700); `tasks/phase-5/P5-T35.md` is `proven`, full record in `evidence/dynamic-nodes-r9700-2026-10-16/`. Remaining follow-ups:

- the reference implementation (Rust gateway and node) carries unit, HTTP-on-loopback and
  scripted-gateway tests for every rule of the specification, **and a dynamic node has fetched
  real weights, launched a real profile through docker and served real inference through its
  gateway** (2026-10-16, host `beast`, 2× R9700 — `evidence/dynamic-nodes-r9700-2026-10-16/`); a
  separate adversarial review remains a follow-up;
- the two deployments the operator asked for (`qwen3.8-27b-modality-vision-quant-q8_k_xl` on two
  cards and `qwen3.8-flash_next-modality-vision-quant-q8_0` on eight, plain `q8_0` because the
  upstream repository publishes no `UD-Q8_K_XL` build (decision record); 120k to 260k context,
  every card on one R9700 host) have no shipped runtime profile with Q8 evidence at that depth: the reference
  configuration lists them as measurement candidates, so the first assignment on a real host is a
  `measure`, and the draft it yields has no quality block. Serving from a draft is permitted by
  the reference only where the desired model does not require a quality suite; a draft was
  produced on real hardware and is serving (the 27B, host `beast`, 2026-10-16); the 8-card
  Flash-Next still needs an 8-card R9700 host to produce its own draft;
- the Go gateway (`metabolomics-us/inferweave-gateway`) does not implement specs/64; a dynamic
  node registered to it is recorded hardware-only and assigned nothing;
- link-only dynamic nodes (behind NAT) and two engines on one dynamic node are non-goals of this
  version; a dynamic node is dialled at an operator-named address;
- the reference node fetches over `file://` (only under an operator-configured source root) and
  `http(s)://` only; the site-connector cache tiers of specs/27 are not consulted;
- the node behaviours recorded in specs/64 section 5 (the `file://` source root, the HTTP source
  restrictions, the content store, read-only confined `$ARTIFACTS` mounts, a `stop` that cancels
  an in-flight assignment, the node's own trimming of its report) come from the node branch of the
  reference implementation, which is not merged; they were not read against that code when this
  specification was last revised, and no test drives them against this specification;
- `conformance/node_join.py` still answers `assignments: []` for every registration, which
  remains correct for a registration that does not negotiate the capability; no vector drives a
  negotiated registration against a running gateway.

No production gateway may provision a dynamic node, and no drafted profile may serve production
traffic, until those tests are `proven` against a running fleet and an operator decision approves
it.

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
A design for the verifier's evidence store and record is **proposed, needs owner acceptance; it decides and
authorizes nothing**: `decisions/2026-10-16-proposed-qualification-verifier.md`.

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
11 limits it to where direct transport is unavailable or forbidden. (Superseded in part by the "Update
2026-10-16: spec 63 residuals" section below: the acceptor, executor, dialer and most tests now exist in the
Rust gateway; the closed schemas and vectors for its frames now exist too: see "Update 2026-10-16: spec 63 schemas and
vectors" below.) Bounds (catalog size, drain window, rate and
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

### Update 2026-10-16: spec 63 residuals (spec amended; Rust follow-up open)

Nothing here opens a production gate. Every Rust statement below is about default-off code.

* **Spec 63 amended** (this change) after the Rust implementation (InferWeave/inferweave #1024, #1051, #1062, merged).
  Defects resolved in the text: relay accounting versus "the executing gateway charges" (an upstream-executed row is
  ordinary and never relay-marked); the declared class now has a wire member (`meta.traffic_class`, spec 59 and
  `link-request-meta.json`, composing beside `meta.http`); `records_prompt_content` has assertion semantics (so a
  private request can reach an upstream that positively records nothing); a fresh request id per dispatch; catalog
  entries carry `max_context_tokens`; the `upstream` role carries `refused`; the vacuous disjoint stream-id rule is
  replaced; an empty-payload response head counts as output; one credential per Hello so one role per link; the
  allow-list is required; the hop limit has no default; a refused Hello gets no acknowledgement; the channel
  binding is replay resistance, not proof of possession; the traffic-class vocabulary is no longer cited to spec 44;
  token-budget, relay-breaker and drain semantics are specified. The two exceptions to spec 59 are named in spec 63.
* **Proven (merged Rust, each control shown by a mutant that its test kills; see the PR descriptions of #1051 and
  #1062):** required tests 1 (negotiation and binding, dialer and acceptor), 3 (allow-list, concurrency, rate, alias
  never resolved) and 5 (topology: no transit, independent upstreams, stale on disconnect, loop refusal), the
  accounting rows of test 6 (executing gateway charges; the dialer's record is `reported`; a repeated id is not
  executed twice across reconnects), the revocation and failover rows of test 7, success-response redaction, and the
  direct-path preference and byte counters of test 8.
* **Implemented in the open follow-up PR (InferWeave/inferweave #1072, not merged and awaiting independent review,
  so OWED until it merges; its description lists 18 mutants each killed by a named test):** the per-key token budget (key field, reservation at admission, charge from engine usage,
  24 h window, refusal `token_budget_exceeded`); the declared class on the wire and its use by the acceptor and
  dialer (test 4); the non-recording assertion (`IW_UPSTREAM_RECORDS_PROMPT_CONTENT=false`: no prompt content in the
  ledger row, no response capture, ack `false`) so private traffic can reach a local-domain non-recording upstream;
  the relay circuit breaker and per-link bandwidth bound (test 8); the drain wait for upstream requests in flight
  (test 7); the class sent only to an acceptor whose ack says `reads_traffic_class`; a cancelled request charged its
  whole reservation and streams asked for usage (independent review round 1); a fix to the metadata composition check that would have closed every classed upstream request.
* **UNSATISFIED / owed:** durable token counters and durable request-id dedupe (both are in memory and reset on an
  acceptor restart, so a restart refunds a spent budget); a measured default for every number (budget window and
  reservation, breaker threshold, cool-down and bandwidth bound, drain window, catalog bound, dedupe TTL); the
  HTTPS fallback and reconciliation with `INFERWEAVE_PRINCIPALS_FILE` (test 9: plaintext, unsalted principal file;
  needs per-key rate, concurrency, budget and dedupe state shared across two entry points, so it is not small);
  that the non-recording assertion suppresses only the two stores the gateway is
  known to keep (the ledger row's content and response capture), with no audit of any other store; a real-socket
  test that a request silent with no output opens the breaker (the 60 s bound makes it too slow; the decision is
  unit-tested only); the Go acceptor decision and the feature-ID decision of the decision record; the `transit`
  grant; a deployment. The 200-response bodies remain the node's bytes after redaction of known members only.


### Update 2026-10-16: spec 63 schemas and vectors

Nothing here opens a production gate; no catalog row is `verified`.

* **Now in this repository (offline only):** closed, bounded schemas `link-upstream-hello.json` (the `api_key`
  Hello: `role: upstream`, `credential_type`, `link_roles: ["upstream"]`, exactly two features, a fresh
  incarnation id, a 64-hex `channel_binding`), `link-upstream-hello-ack.json` (`kind: upstream_ack`; granted roles
  exactly `["upstream"]`, `upstream_binding_id`, `principal_label`, `records_prompt_content`, optional
  `reads_traffic_class`), `link-upstream-catalog.json` (at most 256 closed `{model_id, max_context_tokens,
  provenance: reported}` entries), `link-upstream-catalog-request.json` and `link-upstream-refused.json` (the
  twelve-code vocabulary); `meta.traffic_class` added to the closed `link-http-request.json` (so the spec 59 oracle
  accepts a classed request) with the same bound as `link-request-meta.json`; `link-hello.json` no longer
  demands a registration id of an `api_key` Hello. Valid and invalid fixtures (`fixtures/*/link-upstream-*` and
  `link-http-request-traffic-class-*`: 13 valid, 68 invalid), `conformance/link-upstream-vectors.json` (raw-wire cases decoded strictly, so a duplicate member or a
  non-finite number is refused; traffic-class order; the dialer's acknowledgement pairing; reversible refusals),
  the oracle `conformance/link_upstream.py`, the contract `contracts/protocol-v1/link-upstream.json`, a
  `link_upstream_profile` in `conformance/manifest.yaml`, `tests/smoke/test_link_upstream.py` (run by
  `validate_specs.py --self-test`) and five `meta.traffic_class` request vectors in `link-http-json-vectors.json`.
* **Rust (open pull request, awaiting independent review, so OWED until it merges):** the real encoder emits exactly
  the valid fixtures; the real receive path decodes them; every invalid fixture is refused by the schema; the frames a
  real dialer and acceptor exchange over a recording proxy pass the schemas; the acceptor's refusal codes are the
  schema's vocabulary. `validate_catalog` now also bounds `max_context_tokens` at 2^53 - 1.
* **Receiver leniency, recorded rather than fixed (the schema states what a conformant sender produces):** the Rust
  decoder ignores an unknown member of a Hello, an acknowledgement, a catalog, a catalog request and a `refused`
  frame; does not itself reject an empty or oversize `credential` (the key store refuses it, no acknowledgement);
  reads an unknown `refused` code as irreversible; and delivers a `refused` frame with an empty request id to no
  request. A dialer's own `upstream_unavailable` and `upstream_policy` codes are accepted by it but are not in the
  twelve-code vocabulary. **Corrected after review:** the real acceptor now refuses (no acknowledgement) an `api_key`
  Hello whose `role` is not `upstream` and whose `link_roles` is not exactly `["upstream"]` (an earlier draft of the
  Rust tests claimed this while the acceptor ignored `role`); its catalog drops an entry the dialer's
  `validate_catalog` would reject; the dialer-id alphabet names U+FEFF.
* **UNSATISFIED / owed:** the schemas are not production evidence, and every bound in them (256 entries, 2^53 - 1
  context, 64-character label, 256-character request id) is a placeholder; the channel-binding digest construction is
  not specified here (only its encoding), so no known-answer vector exists; the `role: "upstream"` Hello member and the
  frame kinds `upstream_ack`, `upstream_catalog` and `upstream_catalog_request` are taken from the Rust wire and are
  now named in spec 63; no Go implementation; the task card P1-T18 still says "tests owed" in general terms; all the
  items listed as owed in the "spec 63 residuals" section above.

### Update 2026-10-16 (final): what is merged, deployed and still owed for specs 56, 61, 62 and 63

This section supersedes the "open follow-up" wording above. Nothing here opens a production gate: every spec 62 and
spec 63 behaviour is default-off, and no catalog row is `verified`.

* **Spec 63 (Rust, merged: InferWeave/inferweave #1024, #1051, #1062, #1072):** the acceptor executor, TLS 1.3
  channel-binding exporter, N-upstream dialer, success-response redaction (an allow-list at every level, `model`
  replaced by the id the key requested, `logprobs`/`usage` reduced to known members), the per-key token budget
  (cancel before the head and streams without usage are charged their reservation or what was observed, whichever is
  larger), the declared class (`meta.traffic_class`, sent only when the ack says `reads_traffic_class`), the
  non-recording assertion, the relay circuit breaker and bandwidth bound, and the drain wait. Four independent
  security reviews (rounds on #1051, #1062, #1072) found and closed: Cancel-id memory exhaustion, TLS early-data
  stall, a disconnect that did not cancel the node request, the body-form probe marker, a blocking reader, request-id
  collisions across clients, a `logprobs` clone, and two token-budget bypasses. Still **owed**: the items in the
  "spec 63 residuals" section above (durable counters and dedupe, measured numbers, HTTPS fallback and principal
  reconciliation, audit of other content stores, the Go acceptor and
  feature-ID decisions, the `transit` grant). The 200-response body is no longer "the node's bytes": it is reduced
  to the allow-list.
* **Spec 62 (Rust, merged: #1022, #1041, #1070, #1075, #1077, #1078; specs #291, #293):** the hosting wire path
  (`iw.provisioning/2` only for peers authenticated with a spec 63 key, `hosting/<principal>` namespace, operator
  routes require the admin secret, egress hosts clamped to the owner's policy) and the node-side executor
  (`iw-weight-fetch`: egress and port pinned on every hop, credential to the first hop only, digest verified before
  rename, caps during the stream, resume from a `.part` file hashed whole, HF `_id` bound to the claimed
  repository id, network address vetting helper, driver watchdog and abandon path, resolve off the lock with
  tickets, rate and concurrency bounds, a deterministic lock-order test). Five independent review rounds closed a
  repository-id binding hole, an unpinned port, a hung-read wedge, a resolve-under-lock stall, a lock-order
  deadlock between the driver and the operator API, and cache and rate-limit abuse. **UNSATISFIED / owed:** no
  production `ObjectFetcher` (DNS vetting, pinned connect, redirect handling are specified in the trait but
  nothing implements them, so the downloader has only run against fakes), no installer flag, no real profile, load
  or validation hooks (nothing reaches `READY`), no production outbound `HostingPeerChannel` (so `hosting/ask` is
  404), no capacity-signal discovery (`acquirable`), no per-key hosting role (a dedicated keys file is required
  instead), no console endpoint (the spec defines none), the Go console rendering of required test 9, the
  operator-audience plan with eviction handles, licence checks for local sources, and a measured default for every
  number. Every required test of spec 62 beyond the controller and the pure slice stays **owed** until a real
  fetcher runs.
* **Spec 61 (Rust #1021, #1029, #1039, #1062; specs #289, #290):** the contract and schema additions now exist
  (precision-class table with an additivity check, ad-hoc request and response schemas with `resolution_tree` and
  `unmet`, the three precision reason codes, conformance fixtures; acceptance entries 30 to 35 stay `owed` with
  partial evidence). `selection.precision_table_version` was **validation-only**; it now also **binds
  classification** (spec amended 2026-10-16; the Rust change is an open pull request awaiting
  independent review, so it is OWED until it merges): a candidate that advertises another version, or none, is
  classified by its token under the pinned table, an unheld pin excludes with `PRECISION_UNVERIFIED` and the new
  `unmet` token `precision_table_version`. Proven there only with a test-only second table (production holds table 1
  alone), so no real second table has been exercised. A malformed ad-hoc selection is now 400
  `INVALID_CAPABILITY` (InferWeave/inferweave #1073) instead of 503.
* **Spec 56 (Rust #1063, #1073, #1074; specs #294):** node-attested runtime observations: an executor node
  (`--engine-catalogue`) sends a bounded, sequence-fenced snapshot of its own engines over the authenticated link
  (register and heartbeat), the gateway ingests it only from the current authenticated connection and only for the
  authenticated node, and for a row the owner policy already grants the alias inventory shows READY with
  `node-attested:<node>` provenance (confidence stays `Advertised`; capacity comes from gateway state). Producer
  side: a durable generation and epoch journal (0600, write-ahead sequence ceiling), UNLOADED tombstones, a new
  epoch before the owner's fence budget (spec 56 §2.1: nothing is forgotten within an epoch), and a paced
  `runtimeObservations.resync` diagnostic (5 minutes, doubling to one hour). Registration by an unknown or
  unproven node is a uniform 401, not a 400 that reveals which node ids hold credentials. **UNSATISFIED / owed:**
  no qualification verifier (the spec leaves the evidence store and record format undefined, so `qualification_id`
  and `owner_policy_id` stay opaque and nothing becomes `verified`; a design is proposed in
  `decisions/2026-10-16-proposed-qualification-verifier.md`, which needs owner acceptance and decides nothing); only executor nodes send observations, so the
  lab's `node join --model` nodes stay `UNKNOWN`; zero clock-skew tolerance (fails closed, as the spec requires);
  the gateway keeps observations in memory only; the owner remembers only 8 retired epochs; the one line that
  passes the producer into the join-loop re-registration decision has no running-loop test; same-epoch
  re-registration is not exercised against a real executor and gateway.
* **Lab deployment (2026-10-16):** the bender lab gateway (`iw-lab-gateway`, built from `main` after #1078) runs
  with `--no-builtin-models` (#1066). Nodes `node_9d943655cf39cd3d` (Qwen) and `node_acf41c7185b8782a` (beast)
  re-attach after a restart (first attempt `node not enrolled`, then admitted). An ad-hoc resolve returns both as
  `advertised`, excluded and unselectable. Not deployed: any spec 62 or spec 63 behaviour (flags off), farm and the
  other bender nodes (not joined to the lab gateway).

### Update 2026-10-16 (spec 62 peer channel, `acquirable`, discovery): what is proven and what is still owed

Nothing here opens a production gate: every behaviour is default-off (`--provision-hosting-peers-file`), the
owner's hosting wire is a separate flag, and no executor reaches `READY`.

* **Proven (Rust, InferWeave/inferweave #1101, each by a test that fails when the control is removed,
  checked by mutation):** the production outbound `HostingPeerChannel` over the weight downloader's own HTTPS core
  (own DNS, every address vetted, connect to the vetted address, TLS 1.3, webpki roots, SNI = host, port 443 only,
  no proxy, no redirect followed, no decompression), against loopback TLS with a test CA (the dial override exists
  under `cfg(test)` only); refusal of loopback, private, link-local, metadata and mixed answers; a peer is a
  configuration key, never a host (an unknown name sends nothing); each peer's bearer is read per exchange from a
  `0600` file of this user and goes to that peer's host only; a redirect is an error and is not followed; only a 200
  is a reply; replies are capped at 1 MiB by declared length, by streamed length and by a total body deadline;
  a closed-schema peers file with duplicate keys, duplicate names, address literals, ports, paths and queries
  refused at startup; duplicate object keys in a reply refused; a reply on another major refused; the owner's
  `acquirable` (derivation and every withholding condition), its closed wire shape, and its consumer rules; bounded,
  parallel, cached discovery over the same channel and an owner-gated operator route for it (admin secret only).
* **Specification defect found and fixed in this change (spec 62, "Relation to aliases"):** the text placed
  `acquirable` "in the capacity signal" and judged it by `sequence`/`observed_at`, but the delivered code never
  sends `ProvisionCapacity` to a peer, so the member had no carrier and no member names. This change records the
  carrier (the owner's `provision.capabilities` reply on `iw.provisioning/2`), the member names, the withholding
  rules and the freshness rule (receipt time, bounded cache). A future implementer following the old text literally
  would have had to invent all four.
* **UNSATISFIED / owed:** (1) nothing in the live alias-resolution path reads a discovered `acquirable`, so no alias
  candidate is marked `PROVISIONABLE` from it yet (a discovery answer exists and `Willingness::provisionable_for`
  is tested, but that is not reachability); (2) the owner's operator-audience plan with eviction handles and
  `FITS_AFTER_EVICTION`: the pure verdict and its redaction exist and are tested in `iw-core`, but the production
  planner has no source of runtime memory reports, so the verdict is unreachable, and the text leaves undefined the
  handle format and lifetime, how the owner's operator authenticates to receive handles, which route returns them, what
  an "authorized requester" is, and what a requester who is told the plan "as if no other tenant's model existed"
  may rely on when the owner would in fact have to evict (that requester is told `FITS` for a plan the owner can
  honour only by unloading something; answers are proposed in
  `decisions/2026-10-16-proposed-hosting-operator-audience.md`, needing owner acceptance); (3) the channel reaches port 443 only, so an owner must be fronted by a
  TLS terminator on 443 (the gateway's own TLS listener is a link port); no end-to-end run against a real owner
  over TLS exists; (4) the inbound side still parses with `serde_json::Value` (a duplicate key on a request or
  heartbeat is not refused); (5) the freshness of an `acquirable` answer is receipt time only, with no
  `sequence`; (6) every other required test of spec 62 stays owed as recorded above.

### Update 2026-10-16 (closing): durable counters, the pin, the upstream Hello checks and discovery follow-ups are merged

This supersedes any earlier line in this file that calls these items open or "awaiting review". Nothing here opens a
production gate; spec 62 and spec 63 behaviour stays default-off and is deployed nowhere.

* **Spec 63 durable counters and dedupe (InferWeave/inferweave #1102, #1106; opt-in by `IW_UPSTREAM_STATE_DIR`,
  default off, requires the role):** proven by tests that execute: spend, restart, still spent; the window rollover
  persists; a reservation in flight at a crash is charged in full; dedupe holds across a restart within its TTL; a
  clock set back refunds nothing; a damaged journal is quarantined and every budget is treated as spent until an
  operator reset, and that damage is not forgotten if the replacement snapshot cannot be written; a torn final
  record is dropped while mid-file damage is still damage; the journal and the dedupe snapshot are bounded (the
  journal compacts at 75% of its cap, and request ids are stored as a 128-bit digest); fsync, settle and slot-record
  failures refuse budgeted keys until healed; a dead flusher is detected. Two independent reviews and a follow-up
  closed a wedge at the size cap, damage forgotten after a failed startup, a torn-tail lockout, and a copy fallback
  that could follow a symlink. **Still owed:** power loss can lose up to one flusher interval (500 ms or less) of
  records; a forward wall-clock jump across a restart rolls windows early; ids beyond the snapshot budget may
  re-execute after a restart; compaction runs under the state lock; every number (the 500 ms flush, the 10 s stall
  limit, the 30 s back-off, the 4 kept damaged files, the 64 MiB cap) is an unmeasured placeholder; there is no
  metric for journal faults; a default deployment still resets its counters on restart; the HTTPS fallback and the
  principals-file shared state (required test 9) are not done.
* **Spec 63 upstream Hello checks (#1098):** the real acceptor now refuses an api_key Hello whose `role` is not
  exactly `upstream` or whose `link_roles` is not exactly `["upstream"]`, with no acknowledgement, on both listeners;
  the catalog sender drops entries the dialer would reject. The schemas, fixtures and vectors are merged (see the
  schemas section above). The role refusal is proven on the plain link by a test; the TLS listener is covered by the
  single call site only.
* **Spec 61 precision-table pin (#1097, #1099):** a held `selection.precision_table_version` now binds
  classification: a candidate that advertises the pinned version keeps its class and is verified; every other
  candidate is classified by its quantization token under the pinned table, a tokenless pinned candidate is
  `unknown`, and an unheld pin excludes with `PRECISION_UNVERIFIED` and the new `unmet` token
  `precision_table_version`. Production holds only table 1, so no second real table has been exercised. A Go console
  that closes the `unmet_requirement` enum must add the token.
* **Spec 62 discovery follow-ups (#1101, #1103):** failed discovery answers are not cached, unknown peer names never
  fill the cache, concurrent operator `hosting/ask` and `hosting/discover` calls are capped at 4 (429 beyond it), and
  inbound provisioning requests refuse duplicate JSON keys. **Still owed:** the alias `PROVISIONABLE` marking from a
  discovery answer; the operator-audience plan (the spec leaves the eviction handle format, lifetime and recipient
  undefined; proposed answers in `decisions/2026-10-16-proposed-hosting-operator-audience.md`); real profile, load and
  validation hooks (they fail closed, so nothing reaches `READY`; the boundary with spec 50 is proposed in
  `decisions/2026-10-16-proposed-hosting-hook-boundary.md`); a run against a
  real owner over TLS; a large weight download through the CDN redirect chain; the per-key hosting role; the Go
  console rendering; licence checks for local sources.
* **Not done and not mine to decide:** the Go-acceptor and feature-ID decisions of the spec 63 decision record
  (recommendations proposed in `decisions/2026-10-16-proposed-link-upstream-open-decisions.md`); the
  spec 56 qualification verifier (the spec leaves the evidence store and record format undefined; a design is proposed in
  `decisions/2026-10-16-proposed-qualification-verifier.md`); joining farm and
  the other bender nodes to the lab gateway; rotating the lab API key that was pasted into a chat.

### Update 2026-10-16 (proposed decision records for the owed design gaps): nothing is decided

Four records under `decisions/` are **Proposed, need owner acceptance, and decide and authorize nothing**. They do
not amend any spec, open any gate or change any item above from owed to anything else. Each is design only, cites
the spec lines and the `InferWeave/inferweave@a54e0398` code it relies on, and lists the owner's open questions.

* **Spec 56 qualification verifier** (the evidence store and record `qualification_id` should resolve to):
  `decisions/2026-10-16-proposed-qualification-verifier.md`. Still owed: all of it. No row can become `verified`.
* **Spec 62 operator-audience plan** (eviction handle, lifetime, recipient, route, "authorized requester", what
  `FITS` may be relied on for): `decisions/2026-10-16-proposed-hosting-operator-audience.md`. Still owed: all of it,
  and a source of runtime memory reports; `FITS_AFTER_EVICTION` stays unreachable.
* **Spec 62 profile and load hook boundary with spec 50**: `decisions/2026-10-16-proposed-hosting-hook-boundary.md`.
  Still owed: real hooks; the delivered hooks still fail closed.
* **Spec 63 open decisions** (Go acceptor side, own feature ID, invariant 11):
  `decisions/2026-10-16-proposed-link-upstream-open-decisions.md`. The three decisions of
  `decisions/2026-10-15-link-upstream-role.md` remain open.

### Update 2026-10-20: inference stream reliability incident

Spec 09 now separates control freshness, prefill, useful-output inactivity and
execution deadlines; spec 23/42 and the bounded diagnostics contract record the
operational requirement. See `contracts/inference-stream-reliability.json`
(AC-STREAM-01..08), IW-OBS-001/P1-T20 and IW-OBS-002/P1-T12A.

Local implementation, independent source reviews, regression/API/browser tests,
real disposable PostgreSQL reads, and isolated binary canaries are recorded in
`evidence/inference-stream-reliability-2026-10-20/README.md` and `rust.md`.
The pinned Rust release passed a 35-second synthetic prefill on a Hive CPU
allocation; Zapp's Go candidate passed loopback diagnostics checks. These are not
production-serving rollout or GPU qualification evidence.

The two persistence fixture failures are closed by test-only `efe0d866`:
repaired fixtures passed against both the candidate and unchanged upstream
production code. See the release-review evidence for exact scope; true repeated-ID
accounting remains separate and was not changed here.

**Owed:** new timed end-to-end error injection in each Link mode, three live-GPU
cases, production activation and comparable-traffic post-rollout measurement. A 180-second idle default is an operational policy,
not a measured hardware envelope. No production or qualification gate is opened.

### Update 2026-10-20: observability implementation and scoped rollout authorization

The operator approved the observability-performance design/plan, implementation,
independent review, merge and conditional deployment on the existing
Zapp/Farm/Hive/Whiteale path, plus qualification of already registered Nibbler.
The authority and exact boundaries are recorded in
`decisions/2026-10-20-observability-capacity.md`. This supersedes an earlier
absence of permission only within that scope; no prior evidence debt is erased.

**UNSATISFIED / owed:** AC-OBS-01..09 in
`contracts/observability-capacity.json`: runtime idempotency and request lineage;
local/remote timing provenance; CPU entitlement and owner-scoped context offers;
bounded authenticated persistence and retention; public privacy/cohort review;
real NVIDIA observe-mode reconciliation; production smoke/rollback and comparable
traffic measurements. Schema/fixture validation proves shape only. AMD hardware
proof remains owed independently. Spec46 shadow/on placement is not authorized
by telemetry restoration. Public profiles must use existing Next.js apps/web;
Go remains the existing operator adapter plus bounded own-edge observations.

Nibbler hardware registration is not serving qualification. A Go root lacking
spec64 cannot issue dynamic assignments. Rust ownership/executor, actual-profile
qualification, full-path admission, watchdog, rollback and floor safeguards
remain owed before Nibbler can contribute routable or rebalanceable capacity.
The new-family policy defaults (90/7 days retention, maximum 5-minute snapshot validity,
30 requests / 5 principals for public cohorts) are not measured envelopes or
privacy proof. No new control is recorded as proven by this specification patch.

Observability retention is scoped only to explicitly namespaced new-family
records and their derived caches/exports. Existing 730/365-day policies, legacy
records and shared backups are unchanged; retroactive purge requires a separate
reviewed migration and deletion authorization.

### Update 2026-10-20: internal terminal request observations and rollups

The approved observability design/plan now has a bounded internal normalized
contract in `contracts/request-observation.json`, with event and rollup schemas,
fixtures and offline replay/histogram conformance. This adds no export/public API,
publication policy or onboarding control. It retains Rust global authority and
Go own-edge observation scope.

**UNSATISFIED / owed:** AC-REQOBS-01..08 runtime instrumentation and trusted
lineage propagation, immutable replay/terminal-fact identity across restart,
HTTP200 stream-failure classification, phase/token provenance, exact historical
configuration/GPU attribution, bounded nonblocking persistence, real PostgreSQL
rollup/seal/replay/retention tests and coverage/drop reconciliation. Offline
schema/fixture/reference checks do not prove a deployed warehouse or loss-free
recording. Only new-family diagnostics/aggregates use 7/90-day retention; legacy
history and shared backups remain unchanged. No runtime gate closes here.

### Update 2026-10-20: retained failure-rollup companion

`iw.observability.failure-rollup/1` adds offline proven schema, vocabulary,
canonical-parent fingerprint, conserved marginal/correlated-timeout counts,
strict bounded decoding and deduplicated all-terminal mapping checks. See
`decisions/2026-10-20-request-failure-rollups.md` and spec23.

**UNSATISFIED / owed:** AC-REQOBS-09 runtime atomic parent/companion insert,
replacement, seal and prune across 5m/1h/1d, concurrent/restart replay conflicts,
late-ingest watermark fences surviving diagnostic/aggregate prune, 90-day
parent-aligned failure retention after 7-day diagnostic expiry, bounded loss
reporting and independently observed coverage. Public projection requires
per-published-cell principal/cohort evidence, suppression and reconstruction
resistance; this companion gives no publication authority. Legacy 730/365-day
retention and shared backups remain unchanged. No runtime gate closes here.

### Update 2026-10-20: private normalized telemetry HTTP carrier

The additive `contracts/private-observability.json` and
`openapi/private-observability.{yaml,md}` define current gateway-authenticated
single-event durable ingest and operator-only bounded snapshot reads. Offline
strict decoding, header/source/epoch boundary examples and DTO fixture checks
are recorded in `evidence/private-observability-2026-10-20/README.md`.

**UNSATISFIED / owed:** AC-PRIVATEOBS-01..06 real HTTP pre-buffer byte and
credential-header bounds, current-registration/revocation/epoch/lineage races,
durable outbox and ACK replay across restart, database concurrency and cursor
snapshots, source-independent population/loss checkpoints, and integration with
the atomic parent/failure generator and persistent seal/late-ingest fences.
Production collection remains default-off until those generator/fence prerequisites
are proven. No public/cohort authority, deployed warehouse, complete coverage,
new deployment target, legacy retention change or automatic public DTO projection
is established by the private carrier. Existing 7/90-day new-family and 730/365-day
legacy scope stays unchanged; existing authorized rollout boundaries remain in force.

## Role-scoped status UIs and external nodes (2026-10-22)

**BLOCKED for production.** The node, relay and gateway status pages, the CPU-node registration path and
external-node envelopes exist as draft pull requests under
[`decisions/2026-10-22-status-envelope-cpu-node-and-gateway-session.md`](decisions/2026-10-22-status-envelope-cpu-node-and-gateway-session.md).
Nothing is merged or deployed. Provider billing, provider API calls and exposure beyond loopback stay BLOCKED.
Independent review: BLOCKED (see the independent review gate). Screenshot baselines are recorded from a
real Rust stack with a labelled test-double engine on one host; they are not production evidence.

### 2026-10-25: benchmark conductor implementation boundary

IW-BENCH-003 now has a bounded conductor contract in spec 33. The current
implementation work adds local durable queue/fencing, typed driver calls,
placement, sweep-leaf journaling and a private operator projection. This records
no deployed capability and opens no production gate.

**Owed:** a real authenticated gateway adapter with atomic lease/drain,
owner-priority and availability-floor checks, current-clock start checks,
independent abandoned-lease recovery, and atomic full-path verification/release;
real engine lifecycle/cancellation/scratch recovery; end-to-end Hive smoke;
independent deployment review. The current gateway's operator drain/undrain
routes alone do not implement this lease contract. The web endpoint's real
admin-session/grant integration is also owed. Local fakes cannot prove any of
these controls. Hive allocation 24781153 and its explicitly active benchmark
mode are not available for automatic takeover or gateway restoration.

## Paid System One site attestation (2026-11-01)

**Status: UNSATISFIED. Accepted for implementation; nothing implemented, nothing deployed.**

A paid System One model is served from a Slurm job on Whiteale and advertised through the public
gateway, gated today by an operator-made, one-hour file attestation that the gateway enforces the owner
grant (`InferWeave/inferweave` `deploy/whiteale/jev/`). No specification described the policy file, the
loopback status endpoint, the file attestation, its one-hour expiry, or the rule that the site checks it
at every join and not while a link is held; `decisions/2026-11-01-gateway-served-site-attestation.md`
records what exists and the incident (6 min 3 s from link drop to serving after a gateway restart).

The decision owner accepted, on 2026-11-01, the gateway-served design for implementation: the capability
`iw.site-attestation/1` (`specs/67_SITE_ATTESTATION.md`, feature `IW-SITEATT-001`, task `P5-T39`), with the
Rust gateway as sole issuer and enforcer, binding by grant digest and operator enrollment (not node id),
and a paid runtime that may join any gateway and be scheduled or restarted by one. The operated renewer
was withdrawn the same day. This opens no production gate and approves no deployment.

**Implemented, not deployed (2026-11-02).** `InferWeave/inferweave` PR #1446 (`90686506`) implements
`iw.site-attestation/1` in the Rust gateway and node; Linux CI passed. This is not an operational claim: no
paid site runs on it, the public gateway is still the Go gateway, and Jev still uses the file attestation.

**Proven (fails when the control is removed):** default-deny enforcement before admission on every route
found; the capability listed only with a valid loaded policy and a byte-identical wire without it; the
enrollment check; the site's `verify` (a copy is useless to another instance, gateway, grant, model or
rollout); the wake at `expires_at`; withdrawal on refusal with no older attestation kept; no fallback to the
file while the capability is in force; the advert gate; and the grant digest comparison.

**Owed, UNSATISFIED (invariant 40):** a mutation check of the remaining spec 67 section 10 tests (the order
and individual refusal codes other than those above, two instances attested independently, `any` only when
explicit, the lifetime clamp); and the operational evidence in `tasks/phase-5/P5-T39.md` (a real site on a
Slurm node, restarted by its scheduler and re-attested; the same site on a second gateway). The file
attestation and `renew_attestation.py` remain the only mechanism in production until a cutover. An unplanned
link drop with an expired file leaves the site waiting until someone renews, which the owner accepted. The
paid vendor credential's delivery to a scheduled instance is not decided here and is owed separately.

## Legacy NVIDIA benchmark integration — 2026-10-28

**UNSATISFIED / owed:** production qualification for dual sm61/sm75 targets.
Read-only inventory observes serving workloads on both operator-named hosts;
it grants no benchmark lease or preemption authority. Deterministic catalogue,
planner, record-integrity and qualification changes do not establish a compatible
CUDA build, loaded artifact identity, measured memory reserve, agent-task quality,
stability, safe fallback, authenticated remote submission or deployed dashboard
integration. AC-MI-08 remains owed as full acceptance. Existing R9700/4090 and Slurm
ownership and production gates remain in force. No new deployment is authorized
by this entry.


### Legacy integration follow-up — 2026-11-04

Implementation PR #1457 merged as `50e9f3d87caa1bb401a4687444d34c57cf9bd749`.
Bounded source integration reuses the merged private submission, community
review/publication and workbench implementations. Logical recovery tests use a
persisted ACK journal, a fresh PostgreSQL connection and reconstructed service;
a surviving test listener is not OS-crash or power-loss proof. Authorization and
projection removal mutations fail the new web regressions. These checks establish
neither deployed enablement nor production qualification. Both legacy targets are
running operator benchmarks; alternate comparison resources require their own
scheduler allocation. No owner workload may be displaced and no static inventory
entry may manufacture a lease or open an existing production gate.
The pinned implementation report linked from
`evidence/legacy-nvidia-2026-10-28/README.md` records an owned single-TITAN RTX
Slurm pilot and deployed authenticated private intake/replay. This is experimental
single-card comparison evidence, not exact-target production qualification;
AC-MI-08 remains **owed / UNSATISFIED**. Private raw evidence remains outside Git.
Public publication, production promotion and deployed owner-view access are not
established. New conductor v2 stores retain canonical IDs; v1 preserves legacy
replay only and cannot supply canonical coverage or publication evidence.

## Held Link initial-credit and communication recovery qualification

The later [DNS-withdrawal capacity correction](evidence/dns-withdrawal-capacity-2026-11-05/README.md)
addresses ghost-advertised eligible capacity without relaxing recovery. Its
focused red/green regression and pinned implementation PR are recorded
separately; required Linux CI and production qualification remain owed in that
record. Engine-preserving refresh of a
registered direct-only producer after a transient DNS failure remains
**UNSATISFIED / owed**. Positive probing does not authorize direct restoration;
atomic fences, bounded producer/executor exhaustion and no-engine-shutdown proof
are prerequisites for the proposed fresh-registration recovery design, not
controls proven by the capacity correction. No production gate opens here.

Initial-credit interoperability now has bounded implementation evidence, not
production qualification. The Go/Rust fixture holds the consumer, exercises the
Rust implicit default window plus the Go explicit default-window grant, verifies
one-for-one replenishment, and proves that an item beyond the combined allowance
fails only its stream. This closes the specific buffer/grant mismatch in the
fixture. Sustained mixed-version load, cancellation under saturation, deployment
and post-rollout error-rate evidence remain **owed**. The compatibility buffer is
temporary until a negotiated convention can replace support for both implicit-
and explicit-initial-credit peers.

DNS recovery and linked-stream attribution also have bounded implementation
evidence, not production qualification. Rust HTTP integration tests reproduce a
DNS-broken endpoint being incorrectly restored by heartbeat, then prove that only
fresh registration or an authenticated held Link clears that withdrawal; a bad
credential and stronger withdrawal reasons remain held. Go tests distinguish
credit, sequence, stream-idle and shared-connection causes, and treat legacy EOF
before End as incomplete. Public `upstream_transport_error` semantics remain
unchanged and raw errors remain private. Mixed-version rollout, repaired-DNS
operation without a held Link, sustained failure-rate comparison, cancellation
under saturation and production operator-diagnostic retention remain **owed**.

## Benchmark attempt inspection boundary — 2026-11-04

**UNSATISFIED / owed.** Ownership is IW-UI-002 / P2-T18 for the inspector and
IW-BENCH-002 / P2-T03 with the ledger/storage owner for its backend prerequisites.
Authority: [spec10](specs/10_DASHBOARD_PORTAL.md) authenticated portal/history,
[spec15](specs/15_ASYNC_JOBS_ARTIFACTS.md) artifact ownership and retention,
[spec22](specs/22_PROMPT_LEDGER.md) scoped content access/audit/loss,
[spec34](specs/34_PROMPT_STORE_TIERING.md) encrypted storage, and the accepted
[Cognito decision](decisions/2026-10-25-bench-cognito-auth.md). Benchmark
`viewer/requester/reviewer/admin` roles and ledger content roles remain their
separate vocabularies; no implicit promotion between them is authorized.

The private attempt inspector owes all of:

1. **Tenant/owner policy and role mapping:** define the current verified registry
   principal/benchmark-role to scoped ledger-content policy, including revocation
   and expiry. A public model/task URL grants no content access.
2. **Authoritative producer linkage:** persist benchmark record/task-repeat to
   ledger prompt/request/attempt identifiers and ordering; do not join by model,
   time or presentation-row index.
3. **Capture/provenance:** define recorded prompt/output/check/artifact custody,
   integrity and retention, with explicit missing, partial and recording-loss
   disclosure. Missing historical transcripts remain unavailable.
4. **Private reader and audit:** compose a bounded authorized route with the
   existing encrypted prompt store and durable content-access audit, including
   denied/unknown-resource and audit-failure behavior. Do not create a parallel
   grant or audit authority.
5. **Integration proof:** real local OIDC/registry/ledger/BFF/browser checks for
   cross-tenant/owner denial, revocation, expiry, artifact binding, integrity and
   audit failure; production-pool qualification remains separate.

Closure must name its accepted mapping/linkage contract and exact implementation
commit plus guard-removal and integration evidence under the existing task's
completion record. None is supplied by public task-page navigation. This entry
opens no deployment, real-user grant, production-content ingestion or benchmark
execution authority.

## Guarded SpeedRequests and coverage v2 — owed

IW-BENCH-003/P2-T19 and IW-BENCH-002/P2-T03 acceptance AC-SPEED-01–08
in `contracts/benchmark-speed-execution.json` are **owed**. Offline schema and
conformance checks prove only contract shape and arithmetic examples. They do not
prove actual authority, recovery ordering, cancellation, resource safety, runtime
identity, observation authenticity, overlap, production readiness or qualification.
Owner composition and live safety, Slurm cancellation and resident attestation,
Hive canary, restoration and recovery soak remain open. E7–E9 observation
producers, additive payload v2 and exact coverage are separate engineering
prerequisites; existing v1 capsules lack observed exact axes. IW-GPUMEM-001's
separate memory and owner-composition gates remain unsatisfied.

The separate current owned-policy observation in
`contracts/benchmark-continuation-policy.json` and spec 33 is specified but not
implemented. Its offline descriptor and binding projections establish no deployed
authority or active withdrawal. Live ownership, policy withdrawal/unavailability,
cancellation under the original deadline, independent child/channel admission,
recovery, safe capacity, hardware and production qualification remain **owed**.

## Bounded gateway recorder resource policy — deployment proof owed

**BLOCKED for production adoption of this repair until independently reviewed
and qualified.** Spec22's configurable byte/disk policy and stable-identity
migration implement existing best-effort recording intent; they do not approve
an expanded rollout or new PostgreSQL response capture. Local component tests,
private PostgreSQL receipt tests and policy defaults cannot establish target
shared-filesystem lock semantics, exclusion of legacy writers, preservation of
the existing deployed identity, or integrated auth/alias/cancellation parity.
The source/evidence boundary is tracked in
[`evidence/bounded-recording-2026-11-06/README.md`](evidence/bounded-recording-2026-11-06/README.md).
No Farm serving artifact, GPU deployment or CI pool is changed by these proofs.
