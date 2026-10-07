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
