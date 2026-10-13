# 45 — InferWeave Protocol v1: versioned, machine-readable, language-neutral wire contract

## Status

**SPECIFICATION ONLY — BLOCKED for production use.** This document defines the InferWeave
Protocol v1 wire contract. No component currently emits or consumes Protocol v1 in production.
Every required test is recorded `owed` by the canonical tasks `P5-T24`–`P5-T29` (feature
`IW-PROTO-002`). See `OPEN_GATES.md`.

## Relationship to `specs/44_CORE_PROTOCOL.md`

Per decision in this repository, **InferWeave Protocol v1 formalizes and supersedes the
scheduler-neutral core protocol vocabulary of `specs/44_CORE_PROTOCOL.md`** as a versioned,
schema-backed, language-neutral wire contract. The layering is:

```text
specs/44 — Core Protocol: the scheduler-neutral VOCABULARY (principles, object semantics)
specs/45 — Protocol v1: the VERSIONED, machine-readable WIRE CONTRACT built on that vocabulary
```

Spec 44 remains normative as the vocabulary layer; where Protocol v1 states a wire format,
enum, event, state machine, or schema, Protocol v1 is authoritative. A value or field that
exists in the vocabulary but is not yet given a Protocol v1 wire definition remains representable
via the extension namespace until the next minor Protocol v1 release defines it.

## Goal

Define a complete, versioned, machine-readable, language-neutral **InferWeave Protocol v1**
describing communication between gateways, nodes, relay nodes, runtime adapters,
schedulers/resource managers, clients/SDKs, upstream and downstream federated gateways, and
observability/administration systems. The protocol supports the full InferWeave architecture now
and provides extension points for future workloads without requiring protocol redesign.

## Guiding principle

An upstream gateway must be able to understand what resources exist, what they can do, what
they are doing, how reliable they are, why requests were routed to them, what changed, and why
it changed — without knowing how those resources are physically orchestrated. That is the core
contract of InferWeave Protocol v1.

## Scope and non-dependence

Protocol v1 must not depend on Slurm, Kubernetes, Docker, Apptainer, CUDA, ROCm, a particular
runtime, a specific InferWeave deployment, or `metabolomics-us`. Those are **implementations of
the protocol**. Provider-specific details are carried as optional metadata, never as required
fields, and never as fields the protocol logic must understand. The following must all remain
conceptually equivalent upstream and require no fundamental protocol change:

```text
bare-metal workstation
multi-GPU workstation
Docker host
Apptainer host
Slurm allocation
Kubernetes deployment
cloud VM
remote partner gateway
desktop relay
edge device
future accelerator
```

## Repository ownership

The direction of dependency SHALL be:

```text
inferweave/inferweave-specs        (canonical protocol)
        ↓
inferweave/inferweave              (reference implementation)
        ↓
protocol consumers                 (clients, SDKs, tooling)
        ↓
metabolomics-us/inferweave-gateway (protocol consumer + operational control plane/UI)
```

The protocol is deliberately specified first. Neither the Go gateway nor existing Rust structs
define protocol behavior. `inferweave/inferweave` must not silently invent protocol-visible
structures: any new protocol-visible field, enum, event, endpoint, capability, error, or state
requires a Protocol v1 spec change first (see "Protocol change workflow").

### `inferweave/inferweave-specs` (this repository)

Canonical source of truth. Owns protocol documentation, versions, JSON Schema, OpenAPI, event
schemas, state-machine definitions, canonical enums, compatibility rules, error taxonomy,
examples, feature negotiation definitions, test fixtures, conformance fixtures, the protocol
changelog, migration documentation, generated schema artifacts, and SDK-generation inputs.

### `inferweave/inferweave`

Reference implementation. Implements Protocol v1, exposes protocol-defined control-plane and
observability APIs, implements federation, generates/consumes events, exposes topology and
resource state, implements capability negotiation and compatible request metadata, provides
reference conformance tests, rejects incompatible behavior where required, and remains backwards
compatible per the compatibility rules.

### `metabolomics-us/inferweave-gateway`

A protocol consumer and operational control plane/UI. Supports Protocol v1 and consumes protocol
state rather than InferWeave implementation internals. It may provide authentication,
authorization, organizational policy, analytics, historical storage, UI/dashboards, model
catalog UX, administrative workflows, site-specific routing policies, and observability
aggregation. It must not fork the protocol. Organization-specific metadata uses the extension
namespace.

## Protocol planes

Protocol v1 SHALL define three planes.

### Data plane

Inference workloads: chat completions, text completions, embeddings, reranking, vision,
speech-to-text, text-to-speech, image generation/editing, video generation, music generation,
prediction, and async inference jobs. The data plane SHALL remain compatible with existing
industry APIs wherever practical; OpenAI-compatible APIs are the primary compatibility target
for applicable workloads.

### Control plane

Registration, federation, topology, capability negotiation, model lifecycle, runtime lifecycle,
model placement, capacity, autoscaling, draining, rebalancing, aliases, artifact management,
administrative operations, and desired state.

### Observability plane

Health, telemetry, topology, utilization, events, lifecycle history, routing explanations,
accounting, failures, queues, capacity history, node history, model history, and allocation
history.

## Protocol versioning

Every InferWeave-speaking component SHALL expose its protocol version:

```json
{
  "protocol": {
    "name": "inferweave",
    "version": "1.0.0",
    "minimum_compatible_version": "1.0.0"
  }
}
```

Semantic versioning applies. Major: breaking compatibility (`1.x -> 2.x`). Minor:
backwards-compatible feature additions (`1.1 -> 1.2`). Patch: clarification or
backwards-compatible corrections. `minimum_compatible_version` is the oldest minor the peer can
negotiate against; a peer advertising a version below it must be rejected with
`PROTOCOL_VERSION_UNSUPPORTED`.

## Feature negotiation

Version alone is insufficient. Each peer SHALL advertise supported protocol features:

```json
{
  "features": {
    "events": "1",
    "async_jobs": "1",
    "dynamic_aliases": "1",
    "gpu_memory_breakdown": "1",
    "artifact_references": "1",
    "routing_explanations": "1",
    "desired_state": "1"
  }
}
```

Protocol 1.1.0 adds the GPU memory family `gpu_memory`, `rebalance_decisions`,
`placement_simulation` and `card_coresidency` (`specs/46_GPU_MEMORY_INTELLIGENCE.md` §1). Each
feature at level `"1"` names one `iw.<name>/<major>` capability (`iw.gpu-memory/1`,
`iw.rebalance-decisions/1`, `iw.placement-simulation/1`, `iw.card-coresidency/1`), the grammar the
link and HTTP surfaces negotiate: a capability is in force only when both sides list it, and a new
major is a new capability. The pairing is frozen data in
`contracts/protocol-v1/gpu-memory-capabilities.json`.

Never assume a feature exists because a peer runs a particular InferWeave release. Peers MUST
tolerate unknown features (ignore, preserve, forward) and MUST NOT reject a peer for
advertising an unknown feature. A feature a peer advertises at a higher level than the local
component supports is negotiated down, never assumed.

Protocol 1.1.0 also defines additive runtime-family features `runtime_families`,
`runtime_lifecycle`, `runtime_reservations`, `transactional_caches`, and
`native_link_requests` at level `"1"`
(`specs/48`–`specs/53`). Each is negotiated independently. When absent, the sender uses the legacy
Protocol v1 shape and omits its additive fields; it never infers a runtime family or treats version
alone as proof that lifecycle, reservation, cache, or native link-dispatch behavior is present.
`native_link_requests: "1"` names `iw.link-native-request/1`. A sender may then attach the
bounded `LinkRequestMeta.native` shape in `schemas/v1/requests/link-request-meta.json`: a typed
family, its fixed relative endpoint, `POST`, `application/json`, declared payload bytes, and
artifact references. It cannot carry an arbitrary URI, method, content type, or proxy target.
Large media travels through content-addressed artifact references rather than inline link frames.
The sender omits `native` for an older peer; receiving an unnegotiated `native` field returns
`FEATURE_UNSUPPORTED` and does not dispatch it.

## Stable identity model

Every important protocol object has a stable ID. Required identity classes: `gateway_id`,
`node_id`, `device_id`, `allocation_id`, `runtime_id`, `model_id`, `model_variant_id`,
`residency_id`, `request_id`, `trace_id`, `session_id`, `job_id`, `event_id`, `artifact_id`,
`alias_id`. Physical address is not identity: `node_id` is not an IP address, `runtime_id` is
not a port number, `gateway_id` is not a hostname. Addresses may change while logical identity
remains stable. Identity schemas are under `schemas/v1/common/identity.json`. Public exposure
of a node/device identifier is pseudonymous and rotatable where practical and is never a
stable private node address; stable internal identity and the public pseudonymous label are
distinct values (invariants 17 and 18).

## Request and trace identity

Every request SHOULD carry `request_id`, `trace_id`, `span_id`, `session_id`, `mission_id`,
`job_id` where applicable. `request_id` is required; `trace_id` is strongly recommended. IDs
MUST propagate through federation; retries MUST remain traceable; child requests MUST preserve
causal relationship (via `trace_id`/`parent_span_id`). This lets the path
`Client -> gateway -> gateway -> scheduler -> worker -> runtime` be reconstructed as one
distributed operation.

## Time semantics

All externally visible timestamps use UTC ISO-8601 (e.g. `2026-10-07T03:17:43.321Z`).
Durations SHOULD use monotonic clocks internally. Where relevant expose `observed_at`,
`source_timestamp`, and `age_ms`. Gateways SHOULD detect substantial clock skew and report it
rather than silently trusting a skewed peer's timestamps.

## Registration

Nodes and gateways SHALL register using a common registration structure:

```json
{
  "identity": {},
  "protocol": {},
  "features": {},
  "capabilities": {},
  "resources": {},
  "endpoints": {},
  "security": {},
  "extensions": {}
}
```

Registrations support initial registration, re-registration, reconnect, metadata change,
capability change, and graceful unregister.

The generic envelope above is not the `POST /v1/node/register` request body. That node-control
wire, its optional `hardware` report, hardware-only registration, the `assignments` response
member and tokenless proof enrollment are defined by
`specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` (additive, Protocol 1.1.0).

## Heartbeats and liveness

Heartbeat messages SHALL report at minimum `source_id`, `sequence`, `timestamp`, `health`:

```json
{ "source_id": "...", "sequence": 4821, "timestamp": "...", "health": "healthy" }
```

Health states: `healthy`, `degraded`, `draining`, `unreachable`, `stale`, `failed`, `unknown`.
A missed heartbeat must not immediately imply permanent deletion. The protocol SHALL
distinguish `temporarily unreachable`, `stale`, `removed`, and `terminated`.

## Federation

A gateway may register with another gateway, at arbitrary recursive depth. Each federated
object carries provenance:

```json
{
  "origin_gateway_id": "gateway-slurm",
  "reporting_gateway_id": "gateway-lab",
  "federation_path": ["gateway-slurm", "gateway-lab"]
}
```

Federation MUST prevent routing loops: a gateway SHALL reject a federation path containing
itself. Two gateways advertising the same `model_id` keep independent deployments, capacity,
health, and performance. Disconnected capacity becomes stale/unavailable and is never advertised
live. Reconnect reconciles state without duplicate runtime identity or duplicate event replay.

## Trust and provenance

Reported information includes origin and confidence where appropriate. Standard provenance
sources: `direct`, `reported`, `measured`, `verified`, `estimated`, `cached`,
`operator_supplied`, `unknown`. Example:

```json
{ "value": 82.3, "source": "measured", "observed_at": "...", "age_ms": 112 }
```

Trust is never auto-promoted by passing through a trusted gateway. Provenance schema:
`schemas/v1/common/provenance.json`.

## Trust domains and authentication

Federated resources may advertise trust domain and privacy attributes (see "Data handling /
privacy attributes"). Canonical trust domain examples: `local`, `trusted`, `partner`,
`external`, `untrusted`; actual policy remains gateway-specific. Authentication metadata is
extensible and MUST NOT force one system; potential mechanisms include bearer token, mTLS,
signed registration, and service identity. Upstream credentials MUST NOT automatically be
forwarded downstream; each gateway authenticates independently to its peer.

## Resource hierarchy

Canonical hierarchy, each level independently queryable:

```text
Gateway
  Node
    Device
      RuntimeInstance
        ModelResidency
```

## Canonical objects and JSON Schemas

The canonical object schemas live under `schemas/v1/` and are authoritative for the wire
format. Every object category (common, errors, topology, model, resources, runtime, requests,
events, jobs, artifacts) is published as JSON Schema under `schemas/v1/`; production
conformance by a running component remains `owed` by canonical task `P5-T25`. Protocol 1.1.0
adds the `iw.gpu-memory` schemas of `specs/46_GPU_MEMORY_INTELLIGENCE.md` under
`schemas/v1/resources/` and `schemas/v1/events/`. This section states the
object semantics; the JSON Schema is the contract. See "Schema layout and rules" for the
authoritative schema rules.

### Node

`schemas/v1/topology/node.json`. A node exposes `node_id`, `hostname`, `state`, `allocation`,
`system`, `devices`, `runtimes`, `capabilities`, `labels`, `extensions`. System information may
include CPU architecture, CPU count, RAM, operating system, runtime environment, container
environment, and scheduler allocation.

### Device

`schemas/v1/topology/device.json`. Device type is not limited to NVIDIA GPUs. Device types
include `nvidia_gpu`, `amd_gpu`, `intel_gpu`, `apple_gpu`, `tpu`, `npu`, `cpu`, `other`. A
device exposes `device_id`, `type`, `vendor`, `model`, `memory`, `utilization`, `health`.
Unknown device types remain representable and are preserved/forwarded.

### GPU memory model

Devices expose explicit memory accounting with at minimum `total`, `weights`, `kv_cache`,
`runtime_cache`, `active_requests`, `reserved`, `other_models`, `system`, `unaccounted`, `free`.
Upstream dashboards must render this directly. Every value is bytes; `reserved` is logical and is
never part of a physical total. Protocol 1.1.0 defines the detailed, provenance-carrying superset
(`specs/46_GPU_MEMORY_INTELLIGENCE.md`): per-GPU physical, attributed and unattributed memory,
mutually exclusive categories, logical reservations, runtimes, slots and allocations, each byte
count with an explicit basis. `specs/46` §11 maps every field above onto it.

### Device telemetry

Devices SHOULD expose compute utilization, memory utilization, temperature, power draw, power
limit, clock rate, memory bandwidth utilization, ECC state, hardware errors, and throttling
state. Unknown fields remain `unknown`, not silently `0`.

### RuntimeInstance

`schemas/v1/runtime/runtime-instance.json`. An active inference runtime (e.g. llama.cpp, vLLM,
SGLang, Laya, diffusers, a Whisper/TTS runtime, a custom prediction runtime). Exposes
`runtime_id`, `runtime_type`, `version`, `state`, `devices`, `capabilities`, `resident_models`.

### Model identity

`schemas/v1/model/model.json` and `model-variant.json`. Model identity is deterministic and
reproducible. A model variant captures base model, revision, quantization, precision,
tokenizer, context capability, conversion tool/version, artifact digests, and runtime
requirements. Example:

```json
{
  "model_id": "qwen/qwen3.8-27b",
  "variant_id": "qwen3.8-27b-q8",
  "revision": "...",
  "quantization": "q8",
  "tokenizer_digest": "...",
  "artifact_digest": "sha256:..."
}
```

Model display names are not canonical identifiers.

### Model types

Extensible workload classes. Initial canonical types: `llm`, `embedding`, `reranker`, `vision`,
`speech_to_text`, `text_to_speech`, `audio`, `image_generation`, `image_editing`,
`video_generation`, `music_generation`, `prediction`, `multimodal`, `other`. Unknown future
types remain representable.

### Capability advertisement

`schemas/v1/model/capabilities.json`. Capabilities are explicit; never infer features from model
names. Capabilities may be structured limits (e.g. `vision: { supported, max_images, formats }`)
rather than bare booleans, and may declare a support mode `native`, `translated`, `emulated`,
`unsupported`, or `unknown`. Advertised and observed capabilities remain separate with lifecycle
`advertised -> probed -> verified -> degraded -> disabled`; a gateway may mark a claimed
capability degraded after repeated failures.

### Hardware requirements

`schemas/v1/model/requirements.json`. Models SHALL optionally advertise hardware constraints:
minimum GPU count, VRAM, CPU RAM, architecture, compute capability, CUDA, ROCm, runtime,
interconnect, and topology constraints.

### Distributed placement

`schemas/v1/model/placement.json`. The protocol does not assume a model resides on one device.
Represent `one model -> several GPUs`, `one runtime -> several GPUs`, and
`one model -> distributed worker group` explicitly.

### Model residency

`schemas/v1/model/residency.json`. A model variant occupies resources somewhere. Canonical
states: `absent`, `downloading`, `cached`, `staging`, `loading`, `warming`, `ready`, `degraded`,
`draining`, `unloading`, `failed`. State machine in `state-machines/model-residency.md`.

### Artifacts

`schemas/v1/artifacts/artifact.json`. Large model and generated artifacts use a common
descriptor: `artifact_id`, `type`, `mime_type`, `size_bytes`, `checksum`, `expires_at`,
`locations`. Nodes report cache state (`cached`, `partial`, `missing`, `pinned`, `evictable`),
last access, cache pressure, and download progress to support model-on-demand loading.
Generation APIs may return an artifact reference instead of forcing large output inline; the
protocol is storage-provider-neutral (implementations may integrate systems such as Magpie).

### Capacity

`schemas/v1/resources/capacity.json`. Capacity is structured, not a single integer `slots`.
Expose `requests`, `contexts`, `kv_cache`, `gpu_memory`, `compute`. A compatibility `slots`
field may still exist.

### Seats

A **seat** is an abstract schedulable unit representing the ability to accept an additional
workload under specified conditions. Seats may depend on context size, modality, model, memory,
concurrency, batching, and priority. Do not assume all seats are equivalent. Seat and admission
semantics build on `specs/04_CAPACITY_ADMISSION_SEATS.md` and the core capacity vocabulary.

### Allocation

`schemas/v1/topology/allocation.json`. External schedulers are represented generically.
Canonical allocation states: `requested`, `pending`, `allocating`, `allocated`, `booting`,
`staging`, `runtime_starting`, `ready`, `draining`, `preempting`, `terminated`, `lost`,
`failed`. Provider-specific metadata goes in `provider` / `provider_metadata` and upstream must
not require knowledge of it. Canonical termination reasons: `completed`, `operator`,
`preempted`, `scheduler_reclaim`, `timeout`, `node_failure`, `hardware_failure`,
`runtime_failure`, `idle`, `scale_down`, `maintenance`, `unknown`. State machine in
`state-machines/allocation.md`.

## Desired state vs observed state

The protocol SHALL separate desired from observed state:

```json
{ "desired": { "replicas": 3 }, "observed": { "ready": 2, "loading": 1, "pending": 0 } }
```

Use this model for replicas, runtime instances, aliases, caches, allocations, node availability,
and model residency. Autoscaling exposes desired/observed/pending/ready/failed replicas and
emits events with a reason.

## Admission, queue, and priority

Admission outcomes: `accepted`, `queued`, `rejected`, `redirected`, `fallback`, `throttled`;
admission metadata SHALL explain the decision. A workload whose context ceiling, modality,
license, explicit deny rules, or exact deployment requirement is unknown is **not admissible**
(hard constraints, invariant 6; unknown ceiling, invariant 36); the `unknown`-on-missing rule
applies only to advisory/telemetry metadata. Queue state exposes depth, oldest request age,
estimated wait, priority distribution, model queues, and capacity waiting (exact queue position
is optional). Canonical workload classes (separate from numeric priority): `interactive`,
`batch`, `background`, `system`, `benchmark`, `probe`, `maintenance`.

### Probe traffic

Health probes are explicitly marked (e.g. header `X-InferWeave-Workload-Class: probe`).
Probes MUST NOT count as user demand, MUST NOT reset model idle timeout, MUST NOT trigger
scale-up unless explicitly configured, MUST NOT prevent model unload, and MUST NOT distort usage
analytics.

### Benchmark traffic

Benchmark requests SHALL use `workload_class = benchmark` and may be excluded from autoscaling
and utilization policy decisions.

### Deadlines

Requests may carry `deadline`, `max_queue_ms`, `max_execution_ms`. Schedulers SHOULD avoid
assigning work that cannot reasonably finish before the deadline.

### Cancellation

Cancellation MUST propagate `client -> gateway -> gateway -> runtime`, applies to synchronous
requests, streams, queued requests, and async jobs, and MUST be idempotent.

### Retry semantics

Every protocol error SHALL state whether retry is safe (`retryable`, `retry_after_ms`). For
workloads capable of side effects or expensive duplicate execution, support `idempotency_key`.

## Error envelope and taxonomy

Canonical error envelope:

```json
{
  "error": {
    "code": "MODEL_NO_CAPACITY",
    "category": "capacity",
    "message": "...",
    "retryable": true,
    "retry_after_ms": 10000,
    "request_id": "...",
    "trace_id": "...",
    "model_id": "...",
    "gateway_id": "...",
    "node_id": "...",
    "runtime_id": "...",
    "details": {},
    "fallbacks": []
  }
}
```

Schema: `schemas/v1/errors/error.json`. Error categories: `protocol`, `authentication`,
`authorization`, `routing`, `model`, `capacity`, `runtime`, `hardware`, `allocation`,
`artifact`, `timeout`, `cancellation`, `upstream`, `internal`. Canonical codes include
`PROTOCOL_VERSION_UNSUPPORTED`, `FEATURE_UNSUPPORTED`, `MODEL_NOT_FOUND`,
`MODEL_UNAVAILABLE`, `MODEL_NO_CAPACITY`, `MODEL_LOADING`, `MODEL_FAILED`,
`NO_COMPATIBLE_WORKER`, `NO_CAPACITY`, `QUEUE_FULL`, `NODE_UNAVAILABLE`,
`RUNTIME_UNAVAILABLE`, `RUNTIME_CRASHED`, `ALLOCATION_PENDING`, `ALLOCATION_PREEMPTED`,
`ALLOCATION_TERMINATED`, `DEADLINE_EXCEEDED`, `REQUEST_CANCELLED`, `UPSTREAM_UNAVAILABLE`.
In v1.0.0 this taxonomy is normative prose; it is published as frozen machine-readable data
reconciled by test under invariant 41 by canonical task `P5-T26` (currently `owed`).

Errors may advertise compatible fallback options:

```json
{
  "fallbacks": [{ "model": "qwen3.8-27b-q6", "reason": "compatible_lower_memory_variant" }]
}
```

## Aliases

`schemas/v1/model/alias.json`. Aliases are first-class protocol objects and never pretend to be
a concrete model. Aliases may specify constraints (family, context, modality, quality, runtime,
quantization, availability, latency, reliability). Responses should optionally expose resolution
metadata (`requested_model`, `resolved_model`, `alias_id`). Alias targets are advisory unless
marked required; an alias never binds permanently to one deployment.

## Routing and affinity

Routing decisions are explainable and track candidate discovered/excluded/ranked/selected,
fallback triggered, and affinity preserved/broken. Routing must respect the availability floor
(invariant 43) as a hard constraint, and experimental serving profiles/models are not selected
by ordinary production routing until their qualification gates pass (invariant 28). A routing
explanation API
`GET /inferweave/v1/requests/{request_id}/routing` exposes requested model, alias resolution,
candidates, selected route, fallbacks, and retries. Affinity (session, cache, node, runtime,
data locality) is advisory unless marked required. Request resource estimates, data locality,
and warmth/startup-cost may inform routing.

### Warmth / startup cost

Model availability distinguishes `resident`, `warm`, `cached`, `remote`, `missing` and
advertises an estimated activation cost (e.g. `startup_estimate_ms`).

### Cache

Advertise support for prefix/prompt caching, KV reuse, and session state, and expose hits,
misses, bytes, entries, evictions. Schedulers may use cache locality during routing.

### Placement constraints

Support `required`, `preferred`, `avoided`, `forbidden` for placement attributes.

## Draining, rebalancing, and administrative operations

Nodes/gateways announce impending shutdown via `state: draining`, `drain_deadline`, and
`accept_new_requests: false`. Rebalancing generates explicit events when model placement
changes because of the rebalancer (`REBALANCE_STARTED`, `REBALANCE_PLAN_CREATED`,
`MODEL_DRAIN_STARTED`, `MODEL_MOVED`, `REBALANCE_COMPLETED`, `REBALANCE_FAILED`). Canonical
administrative operations: `drain`, `undrain`, `cordon`, `uncordon`, `restart_runtime`,
`load_model`, `unload_model`, `pin_model`, `unpin_model`, `rebalance`, `evacuate_node`,
`enter_maintenance`, `leave_maintenance`. Operations MUST produce events.

## Health model

Health is multidimensional: separate `process_alive`, `runtime_healthy`, `model_ready`,
`capacity_available`, `accepting_traffic`, `hardware_healthy`. A single `"healthy": true` is
insufficient.

## Events

`schemas/v1/events/event.json`. Events are first-class protocol objects. Base envelope:

```json
{
  "event_id": "...",
  "event_type": "...",
  "source_id": "...",
  "sequence": 231,
  "timestamp": "...",
  "trace_id": "...",
  "correlation_id": "...",
  "causation_id": "...",
  "payload": {}
}
```

Ordering is guaranteed per source by a monotonically increasing sequence; global ordering is not
guaranteed; consumers MUST tolerate out-of-order federation delivery. Consumers reconnect using
a cursor (`Last-Event-ID` or protocol equivalent); expired cursors trigger snapshot
reconciliation. Event namespaces: `gateway.*`, `node.*`, `device.*`, `allocation.*`, `runtime.*`,
`model.*`, `artifact.*`, `routing.*`, `queue.*`, `capacity.*`, `autoscale.*`, `rebalance.*`,
`health.*`, `request.*`, `security.*`.

The canonical lifecycle-event vocabulary is defined in `specs/44_CORE_PROTOCOL.md`; Protocol
v1 assigns each a wire `event_type` and schema under `schemas/v1/events/`, published as frozen
machine-readable data reconciled by test under invariant 41 by canonical tasks `P5-T25`/`P5-T26`
(currently `owed`). Model lifecycle transitions emit events (`MODEL_DOWNLOAD_STARTED`,
`MODEL_DOWNLOAD_COMPLETED`, `MODEL_LOAD_REQUESTED`, `MODEL_LOADING`, `MODEL_READY`,
`MODEL_DRAINING`, `MODEL_UNLOADING`, `MODEL_UNLOADED`, `MODEL_LOAD_FAILED`, `MODEL_EVICTED`,
`MODEL_REBALANCED`) with standard reasons (`demand`, `operator_request`, `autoscale`,
`rebalance`, `idle_timeout`, `memory_pressure`, `allocation_loss`, `preemption`,
`runtime_failure`, `hardware_failure`, `maintenance`, `upgrade`, `cache_pressure`, `unknown`).
Protocol 1.1.0 adds the `gpu.memory.*`, `runtime.*` placement and `rebalance.*` decision events
of `specs/46_GPU_MEMORY_INTELLIGENCE.md` §7 on their own capability-gated feed; their frozen
vocabulary is `contracts/protocol-v1/gpu-memory-events.json`.

### Snapshot + delta model

Observability consumers SHOULD retrieve a consistent snapshot then receive subsequent
events/deltas. A snapshot SHALL include `snapshot_id`, `generation`, `generated_at`; all
contained state belongs to the same snapshot generation.

### Event backpressure

Event streams MUST support slow consumers (bounded buffers, replay storage, or
disconnect + cursor recovery). A slow consumer MUST never cause unbounded memory growth.

## Unknown state semantics

Never collapse `false`, `0`, `null`, `unknown`, `not_reported`, `unsupported`; they have
different meanings. Schemas MUST preserve them. Unknown fields/values are preserved and
forwarded, never silently coerced. This builds on invariant 6 / invariant 36 handling in
`specs/44_CORE_PROTOCOL.md` and `specs/00_INVARIANTS.md`.

## Telemetry, metrics, accounting, and quality

Request metrics: `queue_ms`, `ttft_ms`, `duration_ms`, `input_tokens`, `output_tokens`,
`tokens_per_second`, `cache_hits`, `cache_misses`. Resource metrics: GPU utilization, VRAM, RAM,
runtime concurrency, active requests, queued requests, capacity, model loading/unloading, cache
utilization. The extensible metric schema (`schemas/v1/events/metric.json`) transports metric
definitions and structured samples with provenance, windows, distributions, and counters; it
does not hard-code global fields. Accounting exposes canonical records for tokens, GPU-seconds,
runtime-seconds, images, audio-seconds, video-seconds, jobs, requests, and storage bytes (this
does not imply billing). Reliability exposes measurable historical indicators (request success
rate, error rate, rejection rate, eviction count, preemption count, availability, median startup
latency, capacity volatility) and does not define subjective reliability scoring in the base
protocol. Model quality metadata is optional, and every value indicates a source
(`benchmark`, `operator`, `upstream metadata`, `measured`, `inferred`).

## Data handling / privacy attributes

Federated resources SHOULD optionally advertise `prompt_retention`, `response_retention`,
`logging`, `ephemeral_execution`, `training_usage`, `storage_location`, `trust_domain`. This
allows routing policy to prevent sensitive jobs from reaching unsuitable peers. This builds on
`specs/16_SECURITY_PRIVACY_TRUST.md` and invariant 6.

## OpenAI compatibility and InferWeave extensions

The data plane SHALL precisely define which APIs InferWeave claims compatibility with. Initial
compatibility SHOULD cover applicable endpoints such as `/v1/models`, `/v1/chat/completions`,
`/v1/completions`, `/v1/embeddings`, with more added as InferWeave gains modalities. InferWeave
extensions prefer optional headers and separate control endpoints over mutating the
OpenAI-compatible surface. Reserve the `X-InferWeave-*` header namespace (e.g.
`X-InferWeave-Request-ID`, `X-InferWeave-Trace-ID`, `X-InferWeave-Model`, `X-InferWeave-Alias`,
`X-InferWeave-Workload-Class`, `X-InferWeave-Gateway`, `X-InferWeave-Retry-After`).

## Streaming

The streaming protocol SHALL explicitly define stream start, chunks, finish, cancel, failure,
and connection loss. A stream ending without an explicit completion signal MUST be
distinguishable from successful completion. This is required so clients do not interpret
interrupted streams as successful responses.

## Async jobs

Long-running workloads use `POST/GET/DELETE /inferweave/v1/jobs[...]`. Canonical emitted states:
`queued`, `preparing`, `running`, `finalizing`, `succeeded`, `failed`, `cancelled`, `expired`.
Readers accept legacy `completed` as `succeeded`; new producers never emit it. `family` is additive
for runtime-family submissions so legacy stored jobs remain valid. Jobs may report progress
(`fraction`, `stage`, `message`). State machine in `state-machines/job.md`.

## Extension namespace

All protocol objects may contain `extensions` keyed by `organization-or-vendor`:

```json
{ "extensions": { "metabolomics-us": { "cost_center": "lab-ai", "deployment": "production" } } }
```

Core readers MUST ignore unknown extension namespaces. Schema: `schemas/v1/common/extensions.json`.

## Discovery, control, observability, and administrative endpoints

At minimum the protocol defines these control/observability surfaces (OpenAPI under
`openapi/inferweave-v1.yaml`): `GET /inferweave/v1/protocol`, `/topology`, `/gateways`,
`/nodes`, `/devices`, `/runtimes`, `/models`, `/aliases`, `/capacity`, `/health`, `/events`,
and `GET /inferweave/v1/requests/{request_id}/routing`. Administrative operations are defined
separately from public inference APIs; exact authorization policy is implementation-specific.
Compression SHOULD be supported for large topology/event responses.

## Transport independence

HTTP + JSON is the normative v1 transport. Schemas and semantics MUST remain
transport-independent enough to support later gRPC, WebSocket, QUIC, and binary streaming
without redefining the object model.

## Schema layout and rules

The protocol artifacts live under:

```text
VERSION
CHANGELOG.md
docs/                       protocol documentation (architecture, federation, lifecycle,
                            scheduling, events, compatibility, security, extensions)
openapi/inferweave-v1.yaml  OpenAPI for HTTP surfaces
schemas/v1/                 JSON Schema per object class
  common/  topology/  model/  resources/  runtime/  requests/  events/  errors/  jobs/  artifacts/
state-machines/             model-residency.md, runtime.md, node.md, allocation.md, job.md
fixtures/                   valid/, invalid/, federation/ conformance fixtures
conformance/                README.md, manifest.yaml, scenarios/ conformance suite
tools/                      generator / tooling inputs
```

**Schema rules.** JSON Schema is authoritative for protocol objects. Schemas SHALL use stable
IDs, reject malformed enums, document optional vs required fields, preserve forward
compatibility, support extensions, and avoid implementation-specific fields. Generated
Rust/Go/etc types MUST NOT become the protocol authority. CI SHALL ensure examples conform to
JSON Schema and OpenAPI.

**State-machine documentation.** State transitions are explicitly specified and invalid
transitions identifiable. Example (`state-machines/model-residency.md`):

```text
ABSENT -> DOWNLOADING -> CACHED -> LOADING -> WARMING -> READY
      -> DRAINING -> UNLOADING -> CACHED
```

## Conformance levels

Define conformance profiles: `IW-DATA`, `IW-NODE`, `IW-GATEWAY`, `IW-FEDERATION`,
`IW-OBSERVABILITY`, `IW-ADMIN`, `IW-FULL`. A lightweight node need not implement every
administrative feature. `conformance/manifest.yaml` declares profiles and their required
scenarios; `conformance/scenarios/` holds the reusable tests (schema validation, protocol
discovery, feature negotiation, registration, heartbeat, topology, events, retries, errors,
aliases, federation, capability advertisement, snapshot consistency, backwards compatibility,
and, from 1.1.0, `gpu_memory_accounting` (spec 46), `node_enrollment` and `hardware_registration`
(spec 47)).

## Compatibility matrix

A machine-readable matrix (`conformance/compatibility.yaml`) records minimum implementation
versions per protocol version. Do not hardcode this information only in prose.

## Published protocol artifacts

Each released protocol version publishes immutable artifacts: a tarball, OpenAPI schema, JSON
Schema bundle, event schema bundle, and conformance fixtures. Release tags: `v1.0.0`,
`v1.1.0`, etc.

## Protocol change workflow

Any PR affecting protocol-visible behavior must answer whether it changes the InferWeave
Protocol. If YES: create/update the `inferweave-specs` PR, update schemas, documentation,
examples, fixtures, and conformance tests, assign a compatibility classification, update the
changelog, update the reference implementation, and validate downstream gateway compatibility.
The spec change merges before or together with the implementation.

## Cross-repository CI

Automated compatibility CI pulls `inferweave-specs` HEAD and runs `inferweave` conformance
tests, SDK conformance tests, and gateway client tests. Protocol changes must not silently break
consumers. The `inferweave` build fails if the reference implementation violates the advertised
protocol version; the Go gateway validates its client against the shared schemas and fixtures
and does not maintain independently copied protocol enums.

## Acceptance criteria

### `inferweave-specs` (this PR)

This PR delivers the canonical Protocol v1 specification (`specs/45_PROTOCOL_V1.md`), the
versioned layout scaffold (`VERSION`, `CHANGELOG.md`, `docs/`, `schemas/v1/`, `state-machines/`,
`openapi/`, `fixtures/`, `conformance/`, `tools/`), the foundational `schemas/v1/common/` and
`schemas/v1/errors/` JSON Schemas, and the full program decomposition (feature `IW-PROTO-002`,
tasks `P5-T24`–`P5-T29`, all `owed`). The remaining canonical-protocol deliverables — the
per-category `schemas/v1/` object schemas, the complete OpenAPI, the conformance scenarios and
fixtures, the compatibility matrix, and the cross-repo CI — are the tracked outcome of
`P5-T25`–`P5-T29`, which are `owed`, not complete.

### `inferweave/inferweave` (tracked, `owed`)

Advertises the protocol version, passes the conformance suite, exposes topology, emits lifecycle
events, reports devices and VRAM, reports models and capabilities, supports federation, supports
aliases, exposes standardized errors, supports snapshots/events, and preserves OpenAI
compatibility.

### `metabolomics-us/inferweave-gateway` (tracked, `owed`)

Consumes Protocol v1, does not depend on Slurm-specific APIs for topology, displays protocol
topology, detailed GPU memory use, model lifecycle, allocation lifecycle, capacity history,
errors/rejections, aliases, routing explanations, and federation provenance, handles unknown
protocol fields, and remains compatible with older supported protocol versions.

## Invariants binding

Protocol v1 must not weaken the invariants in `specs/00_INVARIANTS.md`, in particular #6 (hard
constraints), #16 (requalification after config change), #17/#18 (pseudonymous public node IDs),
#28 (experimental not routable), #36 (unknown ceiling => not admissible), #40 (proof status),
#41 (frozen data reconciled by test), and #43 (availability floor). Resolved decisions D-001
(Rust), D-005 (direct-first), D-010 (Slurm-as-adapter), and D-018 (Docker/Apptainer substrate)
are binding; naming a scheduler or substrate does not approve it as a deployment substrate.

## Open gates and evidence

Every required test of `P5-T24`–`P5-T29` is `owed`. A schema, example, fixture, or local unit
test does not close the production gate. Until those tasks land and are independently verified,
no upstream system may rely on Protocol v1 being a deployed capability.

## Task traceability

Feature `IW-PROTO-002` maps to canonical tasks `P5-T24`, `P5-T25`, `P5-T26`, `P5-T27`, `P5-T28`,
`P5-T29`. See `contracts/feature-registry.json`, `contracts/canonical-task-graph.json`, and
`implementation/`.
