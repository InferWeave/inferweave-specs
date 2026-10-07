# 44 — Core Protocol: Scheduler-Neutral Model, Runtime, Capacity, Lifecycle, and Federation Description

## Goal

Extend InferWeave so nodes, runtimes, and gateways can describe AI workloads in a
standardized, modality-neutral way. The protocol must expose enough information for upstream
systems to understand:

- what a model/runtime can do;
- how good it claims/measures to be;
- what hardware it requires;
- how much capacity it currently provides;
- how fast it performs;
- how reliable it is;
- how frequently capacity disappears, and why;
- how much of the metadata is trusted or merely self-reported;
- where the model/runtime originated;
- whether the model is currently resident;
- how expensive it is to load;
- whether another runtime is a valid fallback.

The protocol must support heterogeneous federated InferWeave deployments where we do not
control remote nodes, model artifacts, quantizations, runtimes, schedulers, or hardware.
InferWeave must remain infrastructure-agnostic. Slurm must not become a protocol dependency.

This document is the canonical, scheduler-neutral source of truth for model capabilities,
serving requirements, capacity, runtime health, lifecycle events, reliability, and federation
provenance. It defines vocabulary only; it does not itself implement production code (the
specs repository never contains production InferWeave code).

## When this specification is the answer

Historical and current InferWeave control surfaces carry model, runtime, capacity and health
knowledge in several partially overlapping shapes (`02_PROTOCOL_AND_API.md`,
`03_NODE_BOOTSTRAP_DEPLOYMENTS.md`, `05_ROUTING_AFFINITY.md`, `09_OBSERVABILITY_RECEIPTS.md`,
`20_NODE_AUTOCONFIG_DISCOVERY.md`, `21_FEDERATION_ROLES.md`, `42_SITE_GATEWAY_CONFORMANCE.md`).
None is a modality-neutral vocabulary that an upstream gateway can read across a heterogeneous
federation and use to answer "what is advertised, what does it need, how much capacity, how
fresh, how trusted, and why did it disappear" without knowing the downstream scheduler. This
specification standardizes that vocabulary and reconciles the existing surfaces onto it.

It does not replace the deployment, admission, backpressure, ownership, watchdog or privacy
specifications; it composes with them (see §108 Relationships).

## Design principles

1. **Model type must not imply LLM.** A model type is one extensible label, never a rigid
   category that assumes text-only inference.
2. **Hardware requirements are first-class metadata.** They are carried beside, not derived
   from, the model identity.
3. **Runtime/deployment state is separate from canonical model identity.** A model's identity
   does not change when it is loaded, unloaded, scaled or moved.
4. **Artifact/quantization is separate from logical model identity.** The logical model is not
   its quantized artifact.
5. **Federated metadata retains provenance.** Origin survives aggregation and forwarding.
6. **Unknown metadata remains unknown rather than guessed.** A missing value is never invented.
7. **Metrics are extensible without protocol redesign.** New metric IDs are data, not code.
8. **Infrastructure-specific events map to generic InferWeave events.** Slurm, Kubernetes,
   Docker and static hardware emit the same generic events.
9. **Existing clients degrade gracefully when new fields are present.** New metadata is
   optional; older advertisements keep working.
10. **Health probes remain distinguishable from real traffic.** Probe demand never becomes
    user demand.
11. **Quality claims include source/provenance.** An intelligence or quality number without a
    source is not carried as a bare fact.
12. **Resource requirements and observed resource usage are separate.** What a model needs and
    what a runtime is currently using are two different fields.
13. **Advertised facts and locally observed facts are not conflated.** A remote gateway's claim
    and our own measurement of that runtime are both representable and neither overwrites the
    other.

## Core object model

The protocol distinguishes these logical entities. A logical model is not a quant, a weight
artifact, a runtime engine, a worker, a GPU allocation, a deployment, or a gateway.

```text
CanonicalModel
    │
    ├── Artifact
    │      │
    │      └── ServingProfile
    │
    └── capabilities / quality metadata

RuntimeInstance
    │
    ├── Deployment
    ├── capacity
    ├── resource usage
    ├── operational state
    └── observed performance

Gateway / Node
    │
    └── advertises models, artifacts, runtimes and events
```

- **CanonicalModel** is the logical identity (`model_id`).
- **Artifact** is the actual weights/quantization/precision loaded by a runtime.
- **ServingProfile** is an approved/preferred way to serve an artifact.
- **RuntimeInstance** is a schedulable serving target with a live deployment.
- **Gateway / Node** is the advertising and event-emitting surface.

Preserve these distinctions in every advertisement, event, and routing decision.

## Canonical model identity

A canonical model identity structure carries:

```text
model_id
display_name
family
version
model_type
provider
upstream_project
parameter_count
license
open_weight
modalities[]
capabilities[]
created_at
updated_at
```

Fields may be optional when unknown. `model_id` identifies the **logical** model, not the
quantized artifact:

```text
qwen3.8-27b
```

not:

```text
qwen3.8-27b-q6-k-xl-rocm-r9700
```

Display names are never assumed unique (`§74 Duplicate model names`). Canonical identity is
independent of the vendor/name (`Qwen`, `DeepSeek`, `Flux`, `Whisper`).

## Model types

Model types are an extensible set, not a rigid enum requiring a protocol release for every
future type. Initial known categories:

```text
llm
vision_language
embedding
reranker
prediction
image_generation
image_editing
video_generation
speech_to_text
text_to_speech
speech_to_speech
audio_understanding
music_generation
ocr
document_understanding
system_one
```

Unknown types are preserved and forwarded, never rejected. Future examples that must already
flow through the federation safely:

```text
three_d_generation
world_model
robotics_policy
scientific_specialist
```

## Capability advertisement

Capabilities are represented independently of model type and use extensible string IDs, never
hard-coded enums. Example capability IDs:

```text
llm.general
llm.code
llm.reasoning
llm.research
llm.plan
llm.tool_use
llm.structured_output
llm.long_context

vision.image_understanding
vision.document
vision.screenshot
vision.ocr

image.generate
image.edit
image.inpaint

video.generate
video.extend

speech.stt
speech.tts
speech.speech_to_speech
speech.voice_clone

audio.understand
audio.music_generate

prediction.binary
prediction.regression
prediction.timeseries

embedding.text
embedding.image

system_one.reflex
```

A model may advertise multiple capabilities.

## Capability constraints

A capability may carry limits or features as capability-specific, extensible properties:

```yaml
capability:
  id: llm.long_context
  properties:
    max_context_tokens: 131072
```

```yaml
capability:
  id: image.generate
  properties:
    max_width: 2048
    max_height: 2048
    supports_batching: true
```

```yaml
capability:
  id: speech.tts
  properties:
    streaming: true
    voice_cloning: true
    languages:
      - en
      - de
      - es
```

Model-specific constraints (maximum context, supported image formats, supported sample rates,
maximum video duration, supported languages, tool-calling support, JSON-schema support,
streaming support) are represented through capability properties, not one giant fixed model
schema.

## Artifact identity

An artifact is the actual weights/quantization/precision loaded by a runtime. Fields:

```text
artifact_id
model_id
format
precision
quantization
size_bytes
checksum
source
revision
created_at
```

Precision values:

```text
fp32
fp16
bf16
fp8
int8
mixed
```

Quantization values:

```text
q4
q5
q6
q8
awq
gptq
gguf-specific value
none
unknown
```

Do not assume one quantization framework. Remote gateways may omit artifact details; missing
artifact metadata must remain `unknown` (`§42 Federated artifact unknown`).

## Approved / preferred serving profiles

A serving profile is an approved/preferred way to serve an artifact:

```yaml
profile_id: qwen27b-balanced
model_id: qwen3.8-27b
artifact_id: qwen3.8-27b-q6
role: balanced
```

Roles (extensible):

```text
balanced
quality
throughput
low_memory
low_latency
long_context
experimental
```

An `experimental` serving profile is not selectable by ordinary production routing until its
qualification gates pass (invariant 28). Advertising an experimental profile advertises it for
evaluation and explicit policy use, never as a default production target.

A model may have one, multiple, or no advertised preferred profile. This supports fleets that
intentionally retain only one or two artifacts per model.

## Runtime engine metadata

A runtime instance advertises its implementation separately from the model:

```text
engine
engine_version
backend
runtime_version
```

Engine examples: `vllm`, `sglang`, `llama.cpp`, `tensorrt-llm`, `custom`. Accelerator backend
metadata: `cuda`, `rocm`, `cpu`, `mps`, `other`. Never assume engine compatibility from model
identity.

## Resource requirements

Every artifact or serving profile may advertise resource requirements. Separate **minimum**,
**recommended**, and **preferred**; do not compress them into one number.

```yaml
resource_requirements:
  accelerator:
    type: gpu
    min_count: 1
    preferred_count: 2
    min_vram_gb_per_device: 24
    total_vram_gb: 42

  system:
    min_ram_gb: 64
    recommended_ram_gb: 128
    disk_gb: 35
```

Accelerator types: `gpu`, `cpu`, `npu`, `tpu`, `other`. GPU is not mandatory. Unknown values
are permitted. Suggested accelerator fields: `accelerator_type`, `vendor`, `architecture`,
`min_device_count`, `preferred_device_count`, `max_device_count`, `min_memory_per_device`,
`total_memory_required`.

### GPU topology

Resource requirements support topology. These are not equivalent:

```text
1 × 80 GB
2 × 40 GB
4 × 24 GB
```

```yaml
placement:
  min_device_count: 2
  max_device_count: 4
  min_memory_per_device_gb: 24

  homogeneous_devices_required: true

  sharding:
    tensor_parallel: true
    pipeline_parallel: false

  interconnect:
    pcie: supported
    peer_to_peer: required
    nvlink: preferred
```

Fields describe actual constraints, not scheduler-specific concepts.

## Runtime compatibility

Artifacts/profiles may optionally advertise compatibility:

```yaml
compatibility:
  accelerator_backends:
    - cuda
    - rocm

  runtime_engines:
    - vllm
    - sglang

  architectures:
    - gfx1201
    - sm_90
```

This metadata may be incomplete. For **advisory** compatibility metadata, consumers must not
treat absence as incompatibility. This tolerance does **not** extend to hard constraints:
see the absence-tolerance rule below.

## Resource profiles / curves

A model's requirements may vary with workload parameters. Support extensible resource profiles.

For LLMs:

```yaml
resource_profile:
  dimensions:
    context_tokens: 131072
    concurrency: 2

  observed:
    vram_gb: 41
    slots: 2
```

For image generation: `width`, `height`, `batch_size`, `steps`. For video: `width`, `height`,
`duration_seconds`, `fps`. For speech: `concurrent_streams`. Resource dimensions are
extensible.

## Runtime instance

A runtime instance remains a schedulable serving target. It exposes at least:

```text
runtime_id
node_id
gateway_id
model_id
artifact_id
serving_profile_id
runtime_class
engine
status
capabilities[]
capacity
resource_usage
endpoint / transport information
```

Reuse existing RuntimeInstance/System-One abstractions where practical instead of introducing
duplicate concepts.

Runtime classes (`generative`, `system_one`, `diffusion`, `embedding`, `prediction`, `speech`,
`video`) are retained where useful for scheduling. Runtime class is not a substitute for
fine-grained capabilities.

## Runtime status

Generic runtime states (preserve compatibility with existing InferWeave state models where
possible):

```text
configured
starting
loading
ready
busy
draining
unloading
stopped
failed
unavailable
```

## Model residency

Explicit residency state lets upstream routing distinguish a **free slot on an already loaded
model** from a **model that must first be downloaded and loaded**:

```text
not_present
cached
loading
resident
unloading
failed
unknown
```

## Cold-start metadata

Expose available cold-start information:

```text
artifact_cached
artifact_download_required
estimated_download_seconds
estimated_load_seconds
observed_load_p50
observed_load_p95
last_load_duration
```

These may be self-reported or observed. Every value supports provenance where appropriate.

## Capacity advertisement

Every runtime/deployment advertises capacity. At minimum:

```text
total_slots
available_slots
busy_slots
reserved_slots
starting_slots
```

Where relevant, also expose `max_concurrency`, `current_concurrency`, `queue_depth`. The
protocol permits non-slot capacity models in the future.

### Slot semantics

A slot is:

> One unit of schedulable request capacity according to the serving runtime.

Slot count may depend on model, context length, batch policy, VRAM allocation, runtime
implementation, and request class. Do not assume a slot always represents one physical GPU.

### Dynamic capacity

Capacity advertisements are timestamped and expected to change independently of model identity:

```text
12 total
8 available
```

may later become:

```text
4 total
1 available
```

without changing the model or runtime ID.

## Pending capacity

Infrastructure adapters may report capacity expected but not yet usable:

```text
pending_slots
pending_runtime_count
pending_reason
estimated_ready_at
estimated_ready_seconds
```

The ETA is optional. Do not fabricate an ETA when the scheduler cannot provide one.

## Capacity confidence

Federated capacity carries confidence/source metadata and last-update timestamps:

```text
reported
observed
verified
stale
unknown
```

A stale downstream gateway must not appear equivalent to fresh capacity.

## Resource reservation

Distinguish:

```text
physical capacity
reserved capacity
allocated capacity
usable serving capacity
```

A runtime may reserve two GPUs while exposing four request slots. GPU count is not slot count.

## Hardware advertisement

Nodes advertise available hardware in a structured way. Reuse existing node hardware schemas
where available rather than duplicating them.

GPU fields: `device_id`, `vendor`, `model`, `architecture`, `vram_total`, `vram_available`,
`compute_capability`/architecture identifier, `interconnect`, `health`. System fields:
`ram_total`, `ram_available`, `cpu_count`, `disk_free`.

Hardware advertisement that reaches public telemetry uses privacy-safe identifiers only:
public `device_id`/`node_id` are pseudonymous and rotatable where practical, and no stable
private node address or home-location data is exposed (invariants 17, 18). Stable internal IDs
(`Identity stability`) are the control-plane identity; they are not the public telemetry label.

## Hardware group / placement metadata

Multi-GPU runtimes expose which devices comprise the placement:

```text
runtime_id: qwen-worker-4
devices:
  - gpu0
  - gpu1
```

This lets upstream systems understand actual resource consumption and fragmentation.

## Runtime resource usage

Observed runtime-resource telemetry uses generic metric telemetry where possible:

```text
gpu_utilization
vram_used
vram_reserved
cpu_utilization
ram_used
disk_io
network_io
```

## Performance telemetry

Performance measurements use the extensible metric system, not hard-coded global fields.

Generic metrics: `request_latency_ms`, `time_to_first_output_ms`, `throughput`, `queue_wait_ms`,
`load_time_ms`. LLM-specific: `tokens_per_second`, `prompt_tokens_per_second`,
`time_to_first_token_ms`. Image: `seconds_per_image`, `images_per_second`. Video:
`generation_seconds`, `generated_video_seconds_per_second`. Speech: `realtime_factor`,
`time_to_first_audio_ms`. Prediction: `predictions_per_second`.

## Metric definitions

A generic metric definition schema:

```text
metric_id
name
description
unit
direction
metric_type
applicable_capabilities[]
normalization
```

Examples:

```text
runtime.tokens_per_second
runtime.ttft_ms
runtime.queue_wait_ms

llm.coding_quality
llm.reasoning_quality

prediction.brier_score

speech.realtime_factor
```

`direction` allows `higher_is_better`, `lower_is_better`, `neutral`.

## Metric samples

Metric values are structured samples:

```text
metric_id
value
timestamp
window
sample_count
source
confidence
dimensions
```

Example:

```yaml
metric_id: runtime.tokens_per_second
value: 82.4
sample_count: 4812
dimensions:
  context_bucket: 32k-64k
  hardware: r9700x2
```

## Metric provenance

Every non-trivial metric supports provenance. Source types: `local_benchmark`,
`external_benchmark`, `operator`, `self_reported`, `observed`, `derived`, `imported`, `unknown`.
Provenance fields: `source_type`, `source_id`, `producer_gateway_id`, `producer_node_id`,
`benchmark_name`, `benchmark_version`, `timestamp`, `sample_count`, `confidence`. Upstream
forwarding preserves original producer information.

## Quality metadata

The protocol transports model-quality measurements but does not define one universal
"intelligence score." Quality metrics use the generic metric system:

```text
llm.coding_quality
llm.reasoning_quality
llm.tool_use_quality

image.prompt_adherence
image.typography_quality

speech.naturalness
speech.speaker_similarity

prediction.brier_score
prediction.calibration_error
```

The gateway/UI may derive composite scores later. The core protocol primarily transports
evidence.

## Benchmark result format

A standard interchange format for benchmark results:

```text
benchmark_id
benchmark_name
benchmark_version
model_id
artifact_id
runtime_id
metric_results[]
hardware_profile
runtime_engine
runtime_version
timestamp
parameters
provenance
```

Parameters may include context length, batch size, resolution, duration, sampling settings,
temperature, quantization. Results are attributable to the actual artifact/runtime where
possible.

## Operational reliability metrics

Reliability is transmitted as metric samples rather than hard-coded protocol fields unless an
existing field already exists:

```text
runtime.availability
runtime.request_success_rate
runtime.request_error_rate
runtime.timeout_rate
runtime.rejection_rate
runtime.oom_rate
runtime.stream_abort_rate
runtime.health_failure_rate
runtime.restart_rate
runtime.eviction_rate
runtime.interruption_rate
runtime.mean_recovery_seconds
runtime.capacity_volatility
```

## Time windows

Metric samples support windows such as `instant`, `1m`, `5m`, `1h`, `24h`. Do not force all
gateways to calculate every window; a gateway advertises only the windows it has.

## Histograms / distributions

For metrics where percentiles matter, support distributions or summaries: `P50`, `P90`, `P95`,
`P99`. Especially for latency, TTFT, queue wait, load time, recovery time. Avoid requiring
upstream consumers to approximate tail latency from averages.

## Counters

Support monotonic counters where useful:

```text
requests_total
requests_failed_total
evictions_total
oom_total
model_loads_total
model_load_failures_total
capacity_loss_events_total
```

Include reset semantics or runtime start timestamp so consumers can correctly calculate rates.

## Lifecycle event protocol

Generic lifecycle events. Event types are extensible and must include at least:

```text
runtime_registered
runtime_started
runtime_stopped
runtime_lost

model_download_started
model_download_completed
model_download_failed

model_loading
model_loaded
model_load_failed
model_unloading
model_unloaded
model_failed

runtime_degraded

capacity_added
capacity_removed

deployment_scale_requested
deployment_scaled_up
deployment_scaled_down
deployment_scale_failed
deployment_rebalance_started
deployment_rebalance_completed
deployment_rebalance_failed

node_joined
node_left
node_lost
device_lost
node_degraded
node_unavailable

gateway_joined
gateway_left
gateway_lost
```

This canonical list is authoritative (invariant 41). The operational sections below name the
behaviorally meaningful subset of these events for their own purpose; they are not required to
restate every event in the list, and no event type may be introduced in a section without also
appearing here.

## Interruption / eviction events

Explicit capacity-loss/interruption events:

```yaml
type: capacity_removed
runtime_id: runtime-123
slots_removed: 4
reason: scheduler_preempted
```

## Standard reason codes

Generic reason codes:

```text
scheduler_preempted
scheduler_reclaimed
scheduler_time_limit
scheduler_priority
operator_cancelled
operator_evicted
node_failure
node_shutdown
gateway_lost
network_failure
runtime_crash
model_crash
out_of_memory
health_failure
resource_exhausted
maintenance
configuration_change
unknown
```

Infrastructure-specific reason details are carried separately, never substituted for the
generic code.

## Slurm mapping

Slurm implementations may emit detailed metadata (`job_id`, `partition`, `slurm_state`,
`pending_reason`, `node_list`, `allocation`) but map lifecycle behavior to generic protocol
reasons:

```text
Slurm PREEMPTED → scheduler_preempted
Slurm TIMEOUT   → scheduler_time_limit
manual scancel  → operator_cancelled
```

Slurm is not exposed as a required abstraction to upstream clients.

## Event payload

Every lifecycle event supports:

```text
event_id
event_type
timestamp
gateway_id
node_id
runtime_id
model_id
artifact_id
severity
reason
message
metadata
provenance
```

Identifiers may be omitted where not applicable.

## Event sequencing

Events support reliable ordering where possible. Include `sequence`, `timestamp`, `source_id`.
Consumers tolerate reconnects, duplicates, delayed events, and missing historical events. Use
event IDs to allow deduplication.

## Recovery events

Capacity restoration is explicit:

```text
capacity_removed
reason=scheduler_preempted
```

followed by:

```text
runtime_started
model_loading
model_loaded
capacity_added
```

This lets upstream systems calculate recovery times without guessing.

## Load / unload events

Required events: `model_download_started`, `model_download_completed`, `model_download_failed`,
`model_loading`, `model_loaded`, `model_load_failed`, `model_unloading`, `model_unloaded`.
Include durations where known.

## Scale events

Required events: `deployment_scale_requested`, `deployment_scaled_up`, `deployment_scaled_down`,
`deployment_scale_failed`. Optional reason metadata: `demand`, `idle`, `resource_pressure`,
`operator`, `scheduler`, `rebalance`, `failure_recovery`.

## Rebalance events

Represent runtime relocation/rebalancing: `deployment_rebalance_started`,
`deployment_rebalance_completed`, `deployment_rebalance_failed`. Metadata may indicate old/new
node or site. Useful when capacity temporarily drops during movement.

## Node resource loss

Generic events: `device_lost`, `node_degraded`, `node_unavailable`. Reasons come from the
standard reason codes above (e.g. `scheduler_preempted`/`scheduler_priority`, `node_failure`,
`node_shutdown`, `maintenance`, `operator_cancelled`/`operator_evicted`, `network_failure`,
`unknown`). Do not invent a second, parallel reason vocabulary; the standard codes are
authoritative (invariant 41).

## Partial failures

A runtime with multiple devices may lose only some capacity. Do not force every capacity
problem to become `runtime_failed`. Allow `runtime_degraded` and `capacity_removed` while
continuing to serve reduced capacity.

## Degraded runtime

Support a `degraded` state or status flag:

```text
runtime ready
health degraded
4 / 8 slots usable
```

Operational health and serving state are not forced into one boolean.

## Health model

Represent at least `healthy`, `degraded`, `unhealthy`, `unknown`. Health is separate from
lifecycle state. `state: ready` with `health: degraded` is valid.

## Health reasons

Optional health-reason codes: `high_error_rate`, `high_latency`, `health_probe_failure`,
`partial_device_failure`, `memory_pressure`, `queue_saturation`, `upstream_instability`,
`unknown`. Higher-level gateways may derive these locally as well.

## Model lifecycle state

Support logical model/artifact lifecycle metadata, separate from runtime state:

```text
experimental
evaluating
validated
production
deprecated
retired
```

A production model may currently have zero live runtimes. An `experimental` model is not
selected by ordinary production routing until qualification passes (invariant 28); the
lifecycle state is carried so policy layers can gate on it rather than inferring it.

## Operator annotations

Allow optional operator metadata: `known_issues`, `operator_notes`, `warnings`. Structured
where practical; free-text acceptable. Examples:

```text
Known unreliable tool calling.
Experimental ROCm deployment.
Do not use above 128k context.
```

## Error taxonomy

Standardize major serving errors so upstream gateways can reason about them:

```text
no_worker
no_capacity
queue_full
model_unavailable
model_loading
runtime_unavailable
scheduler_unavailable
timeout
upstream_timeout
stream_interrupted
out_of_memory
invalid_request
capability_unsupported
context_too_large
internal_error
gateway_unreachable
```

Preserve detailed implementation-specific errors separately.

## Retryability

Errors indicate whether they are generally:

```text
retry_same_runtime
retry_same_model_elsewhere
retry_after_delay
use_fallback
non_retryable
unknown
```

This integrates with existing InferWeave response headers/error semantics (`06_BACKPRESSURE_RETURN_TO_SENDER.md`,
`implementation/ERROR_SEMANTICS.md`) rather than inventing a parallel mechanism.

## Capacity loss and active requests

When capacity disappears, emit information where available about affected requests:
`affected_request_count`, `active_request_count`, `requests_recoverable`. Do not require
exposing request contents.

## Request classification

Every request is distinguishable as `user`, `system`, `health_probe`, `benchmark`, `warmup`,
`internal`. This classification is critical: health probes must not be mistaken for production
demand.

## Health probe semantics

Health probes must:

- verify runtime/model health;
- update health state;
- contribute to health-failure evidence.

Health probes must NOT contribute to:

- user traffic;
- popularity;
- demand;
- usage accounting;
- autoscaling demand;
- scale-up decisions;
- unload prevention;
- idle timeout reset;
- balancing pressure;
- request-rate calculations.

This behavior is enforced consistently across InferWeave.

## Benchmark request semantics

Benchmark traffic is identifiable. Benchmark requests may contribute to benchmark measurements
but do not automatically count as ordinary user demand. Request class is exposed so policy
layers can decide whether benchmark traffic affects autoscaling.

## Capability contract / requirement matching

A capability-requirement structure usable by schedulers:

```yaml
capability: llm.code

requirements:
  context_tokens: 131072
  tool_use: true

preferences:
  quality: high
  latency: low
```

```yaml
capability: image.generate

requirements:
  min_width: 1024
  min_height: 1024

preferences:
  prompt_adherence: high
```

The core protocol lets the scheduler determine compatibility without relying solely on exact
model IDs.

## Capability matching

Runtime compatibility is evaluated using:

```text
requested capability
+
hard request requirements
+
runtime advertised capabilities
+
resource availability
```

Hard requirements determine eligibility. Preferences may influence ranking but must not turn
into compatibility requirements unless explicitly requested.

## Alias compatibility

Aliases resolve to capability-based targets:

```text
coding
coding-fast
coding-best
research
vision
image-fast
tts-realtime
```

Alias definitions may specify required capabilities, preferred metrics, minimum constraints,
and fallback behavior. Do not bind aliases permanently to one physical deployment. (Compose
with the multimodal alias rules of `43_GPU_PLACEMENT_HOT_SWAP.md`.)

## Fallback metadata

Models/profiles optionally advertise advisory fallback relationships:

```yaml
fallbacks:
  - target: glm-flash
    compatibility:
      - llm.code
      - llm.general
```

Fallback metadata is advisory. Schedulers may choose different compatible targets based on live
conditions.

## Routing decision metadata

Where InferWeave routing already produces decision metadata, expand it so upstream systems
understand why a runtime was selected. Structured factors:

```text
capability_match
context_match
availability
queue_pressure
latency
reliability
resource_fit
trust
fallback
```

Transmit structured reasons; do not embed UI wording in the protocol.

## Scheduling input

The scheduler has access to capability requirements, runtime state, available capacity,
resource requirements, hardware compatibility, queue state, trust/provenance, reliability
metrics, cold-start state, model/artifact lifecycle and qualification state, and the
availability floor. This specification does not require one fixed ranking formula; it provides
the information necessary for smarter routing. The information is never a substitute for a hard
constraint: routing must still respect the availability floor (invariant 43) and experimental
qualification (invariant 28), and must never route to a node that lacks the required
model/deployment/capability (invariant 5).

## No global composite quality in core

Do not implement a universal core formula (for example `quality × speed × reliability`) inside
the protocol. Different gateways and workloads weight factors differently. The core exposes
normalized evidence; higher layers may derive `fitness`, `risk`, and `recommendation` scores.

## Local vs federated preference

The core protocol does not assume local models always win, nor that federated capacity is
equivalent. It exposes enough metadata for policy layers to make that decision.

## Privacy

Do not put prompts, generated content, user identities, or secrets into model-intelligence
telemetry. The protocol exposes operational metadata only. Request IDs may be used where needed
for tracing.

## Model download information

For on-demand model loading, support artifact cache/download state:

```text
artifact_present
artifact_cached
download_in_progress
download_progress
download_source
estimated_remaining_seconds
```

Do not expose authentication credentials or signed secret URLs upstream.

## Staleness

Every advertisement is timestamped. Consumers determine whether data is stale:

```text
observed_at
advertised_at
expires_at
ttl_seconds
```

Timestamps and TTLs govern staleness, but they do not replace requalification: after a material
configuration change (engine, quantization, placement, context ceiling) a deployment's
capability claims expire and must be refreshed/requalified (invariant 16). `expires_at`/`ttl_seconds`
bound how long an advertisement may be believed; they do not make a materially changed
deployment's stale claims valid again.

Do not report remote availability indefinitely after a gateway disappears.

## Gateway disconnect

When a downstream gateway becomes unreachable:

- mark its capacity unavailable/stale;
- preserve historical identity;
- emit gateway/runtime loss events;
- do not delete all model knowledge immediately;
- do not continue advertising its capacity as live.

## Reconnection

When a gateway reconnects:

- reconcile current runtime state;
- avoid duplicate runtime identities;
- deduplicate repeated events;
- restore capacity based on new advertisements;
- preserve historical continuity where IDs are stable.

## Backwards compatibility

New model metadata is optional. Older gateways that advertise only `model`, `endpoint`, `slots`
continue to function. Missing **advisory** metadata fields produce `unknown` rather than
rejection.

## Absence tolerance and hard constraints

Absence tolerance is bounded by invariants 6 and 36. "Missing fields produce `unknown`" applies
to advisory and telemetry metadata (compatibility hints, throughput/quality claims, cold-start
estimates, provenance). It never applies to a hard constraint:

- security, privacy, license, modality, context, explicit deny rules and exact-deployment
  requirements are hard constraints (invariant 6);
- a deployment whose context ceiling is unknown is **not admissible**, and an absent capability
  claim is never read as an unbounded one (invariant 36).

Concretely: a runtime that advertises no `max_context_tokens`, no modality, or no license must
not be treated as unbounded, modality-neutral, or freely licensable. Capability matching
(`Capability matching`) must treat an absent hard-constraint property as **not satisfied**,
never as satisfied-by-default, even when the same absence is tolerated in advisory metadata.

## Versioning

Version protocol changes. Prefer additive evolution. Unknown fields, metric IDs, capability
IDs, model types, and lifecycle reasons are ignored or preserved rather than causing failures.

## Serialization

Use the repository's existing protocol serialization conventions. All new types support the
formats already used by InferWeave. Do not introduce a separate incompatible telemetry transport
unless technically necessary.

## Event transport

Reuse existing InferWeave streaming/event mechanisms. Lifecycle events, capacity changes, and
runtime changes are streamable to upstream gateways in near realtime. Periodic full-state
snapshots still exist so missed events can be reconciled. Use events for low-latency changes
plus snapshots for eventual correctness.

## Snapshot semantics

A full gateway/node snapshot exposes models, artifacts, runtimes, capacity, hardware, current
status, and a metrics summary. Snapshots represent current truth; events represent transitions.
Upstream systems recover after disconnect without replaying the entire historical event log.

## Identity stability

Use stable IDs for gateway, node, runtime, canonical model, artifact, and serving profile. Do
not derive IDs solely from IP addresses or transient scheduler job IDs. Scheduler job IDs may be
metadata.

Stable IDs are the internal/control-plane identity. When an ID is exposed to public telemetry or
federation peers it is pseudonymous and rotatable where practical, and is never a stable private
node address (invariants 17, 18). Stable internal identity and the public pseudonymous label are
two distinct values, reconciled by the emitting gateway.

## Duplicate model names

Never assume display name is unique. Canonical identity is independent of names like `Qwen`,
`DeepSeek`, `Flux`, `Whisper`. Multiple providers/artifacts may expose similar names.

## Remote naming

Preserve both canonical model ID and source-advertised model name when federation mapping is
uncertain. Do not force uncertain remote models into a known canonical identity.

## Canonical identity confidence

Optional mapping confidence: `exact`, `declared`, `mapped`, `heuristic`, `unknown`. Heuristic
mapping is never presented as exact identity.

## Model registry metadata

InferWeave may optionally know metadata such as Hugging Face repository, revision, checksum,
license, and parameter count, but federation participation must not require an external
registry. Self-hosted/internal models remain valid.

## Federation provenance

Every forwarded model/runtime/deployment retains its origin:

```text
origin_gateway_id
origin_node_id
advertising_gateway_id
hop_count
route_path
metadata_source
```

Never rewrite a remote deployment as though it originated locally.

## Trust level

Gateways/operators attach trust classification: `managed`, `trusted`, `unverified`, `unknown`.
Do not automatically promote trust because metadata passed through a trusted gateway. Preserve
origin trust separately from transport trust.

## Self-reported vs observed

Explicitly distinguish `self_reported` from `observed`. A remote gateway may claim `82 tok/s`
while our local upstream observations measure `64 tok/s`; both are representable and neither is
forced to overwrite the other.

## Federation aggregation

A gateway may advertise a Model with a locally hosted deployment plus remote deployments from
Gateway A and Gateway B. Preserve deployments independently. Do not collapse them into one fake
deployment merely because `model_id` matches.

## Federated artifact unknown

A remote gateway may know only `model_id`, `capabilities`, `slots`. This is valid. Do not
require `quant`, `artifact`, `hardware`, or `engine` for federation participation. Unknown
information remains explicitly unknown.

## Request-level runtime identification

Where possible, response metadata indicates `model_id`, `artifact_id`, `runtime_id`, `node_id`,
`gateway_id`. This permits upstream systems to correlate real-world performance with the actual
deployment.

## Request result telemetry

Where request telemetry is propagated, support result classification: `success`, `client_error`,
`server_error`, `rejected`, `timed_out`, `interrupted`, `fallback_success`, `fallback_failure`.
Do not require sharing prompt contents.

## Federation hop metadata

For routed requests spanning gateways, preserve useful hop data without exposing secrets:
`source_gateway`, `selected_gateway`, `origin_runtime`, `hop_count`. Avoid allowing unbounded
tracing data to explode request headers.

## Optional trace IDs

Use an existing request/trace identifier where available. It correlates routing decision,
runtime request, error, fallback, and lifecycle interruption without logging payload contents.

## Protocol test coverage

Comprehensive tests cover:

- serialization/deserialization;
- missing optional metadata;
- unknown capability IDs;
- unknown model types;
- unknown metric IDs;
- unknown event reason codes;
- backwards-compatible old advertisements;
- federated forwarding;
- provenance preservation;
- stale-capacity expiry;
- duplicate event handling;
- reconnect reconciliation;
- health-probe classification;
- benchmark traffic classification;
- partial capacity loss;
- model loading/unloading transitions.

## Federation tests

Test scenarios such as:

```text
Gateway A
  local Qwen Q6

Gateway B
  remote Qwen, unknown quant

Gateway C
  aggregates A + B
```

Verify that Gateway C preserves two independent deployments, original provenance, artifact
knowledge only for A, appropriate trust/source metadata, independent capacity, independent
health, and independent performance measurements.

## Scheduler-agnostic tests

Test at least Slurm-backed runtime, static Docker runtime, manual local worker, and remote
gateway. All must appear through the same generic protocol. No upstream logic requires Slurm
fields.

## Health probe tests

Verify that 100 health probes and 0 user requests yield user demand 0, and do not keep an
otherwise idle model artificially resident unless explicit policy says otherwise. Probe failures
must still affect runtime health.

## Event recovery tests

Simulate capacity 8 → scheduler eviction → capacity 0 → new allocation/loading → capacity 4 →
capacity 8. Verify correct lifecycle events and current-state snapshots.

## Resource compatibility tests

Test topology-sensitive models. A requirement of `2 × 24 GB` must not be considered compatible
with `1 × 48 GB` unless the model/profile explicitly supports that placement. Likewise `1 × 80
GB` must not automatically equal `4 × 24 GB`.

## Documentation

Document canonical model identity, artifact identity, runtime identity, capability IDs,
capability properties, the metric system, provenance, resource requirements, topology
semantics, event types, reason codes, health-probe classification, federation forwarding, trust
semantics, and backward compatibility. Include concrete examples.

## Example complete advertisement

A managed local model:

```yaml
model:
  model_id: qwen3.8-27b
  display_name: Qwen 3.8 27B
  model_type: vision_language

  capabilities:
    - id: llm.general
    - id: llm.code
    - id: llm.reasoning
    - id: llm.tool_use
    - id: vision.image_understanding

artifact:
  artifact_id: qwen3.8-27b-q6
  model_id: qwen3.8-27b
  quantization: q6

serving_profile:
  profile_id: qwen3.8-27b-balanced
  role: balanced

resource_requirements:
  accelerator:
    type: gpu
    min_count: 2
    min_vram_gb_per_device: 24

runtime:
  runtime_id: qwen-r9700-01
  node_id: fry
  engine: llama.cpp
  status: ready
  health: healthy

capacity:
  total_slots: 4
  available_slots: 3

provenance:
  source_type: observed
  trust: managed
```

`source_type` uses the metric-provenance vocabulary (`observed` here); `trust` uses the trust
vocabulary (`managed`). They are different dimensions and are never conflated.

## Example federated advertisement

A remote gateway may expose only:

```yaml
model:
  model_id: qwen3.8-27b
  display_name: Qwen 3.8 27B

runtime:
  runtime_id: remote-qwen-17
  gateway_id: remote-gateway-a
  status: ready

capacity:
  total_slots: 6
  available_slots: 4

artifact:
  quantization: unknown

provenance:
  source_type: self_reported
  origin_gateway_id: remote-gateway-a
```

This is valid. Do not infer the missing artifact or hardware.

## Example eviction flow

```text
capacity_removed
reason=scheduler_preempted
slots_removed=4

runtime_stopped
reason=scheduler_preempted

deployment_scale_requested
reason=failure_recovery

runtime_started

model_loading

model_loaded

capacity_added
slots_added=4
```

This sequence must be visible to upstream gateways using generic InferWeave semantics.

## Example error response

If a model has no capacity, return structured metadata:

```yaml
error:
  category: no_capacity
  retryability: retry_same_model_elsewhere

model_id: qwen3.8-27b

capacity:
  total_slots: 8
  available_slots: 0
```

Existing OpenAI-compatible behavior is preserved. InferWeave-specific details use the project's
existing extension mechanism/headers.

## Implementation priorities

Implement in this order.

**Phase 1 — Data model.** Canonical model identity, artifact identity, capabilities, resource
requirements, runtime/deployment metadata, provenance.

**Phase 2 — Capacity and lifecycle.** Richer slot/capacity advertisement, model residency,
load/unload events, scale/rebalance events, capacity-loss events, standard reason codes.

**Phase 3 — Metrics.** Generic metric definitions/samples, performance telemetry, reliability
telemetry, benchmark interchange, confidence/sample counts.

**Phase 4 — Federation.** Provenance forwarding, remote deployment preservation, trust
semantics, staleness, reconnect reconciliation, federation tests.

**Phase 5 — Routing integration.** Capability contracts, resource compatibility, cold-start
metadata, reliability signals, structured routing reasons, fallback metadata.

## Acceptance criteria

This work is complete when an upstream InferWeave gateway can determine, solely from the
protocol:

1. What logical model is being advertised?
2. What actual artifact is serving it, if known?
3. What capabilities does it provide?
4. What model/runtime type is it?
5. What context/resolution/language/etc. limits apply?
6. What hardware does it require?
7. How many accelerators are required?
8. What topology constraints apply?
9. What serving runtime is being used?
10. Is the model currently resident?
11. How long does it normally take to load?
12. How many slots exist?
13. How many slots are currently available?
14. Is capacity pending?
15. How fast does it run?
16. How reliable is it?
17. How frequently does it fail or disappear?
18. Why did capacity disappear?
19. Was the loss scheduler-related, operator-related, or model-related?
20. How long did recovery take?
21. Is the information locally managed, observed, or self-reported?
22. Which gateway/node originally advertised it?
23. How fresh is the information?
24. Is the runtime healthy, degraded, or unavailable?
25. Is an error retryable?
26. Can the same model be retried elsewhere?
27. Is a fallback model capability-compatible?
28. Was traffic a real user request, health probe, benchmark, or internal request?
29. Can unknown future model types/capabilities/metrics flow through the federation safely?
30. Can all of this work without knowing whether the downstream scheduler is Slurm, Docker,
    Kubernetes, static hardware, or something else?

The resulting protocol makes `inferweave/inferweave` the canonical, scheduler-neutral source of
truth for model capabilities, serving requirements, capacity, runtime health, lifecycle events,
reliability, and federation provenance.

## Frozen vocabularies

Every shared vocabulary this spec introduces — model types, capability IDs and properties,
precision/quantization values, serving-profile roles, runtime classes and statuses, residency
states, health states and reasons, metric IDs, source types, lifecycle event types, standard
reason codes, error categories, retryability, trust levels, mapping confidence, request classes
— is a shared vocabulary under invariant 41. It must be expressed as **frozen machine-readable
data**, published as a document, and reconciled by test; prose in this document is the
normative intent, not the contract itself. The canonical lists here are the source of truth for
that data and must be kept internally consistent: the canonical lifecycle list is the
authoritative enumeration, the operational sections may reference it without restating every
event, and no event type may be introduced in a section without also appearing in the list. The conformance task (`P5-T23`) publishes and reconciles these
vocabularies.

Protocol neutrality is not production-substrate approval. Naming Kubernetes (or any other
scheduler) as an event source does not approve it as a deployment substrate; adding one still
requires an ADR under D-018.

## Relationships

This spec composes with, and does not replace:

- `00_INVARIANTS.md` — every invariant binds; nothing here relaxes them.
- `02_PROTOCOL_AND_API.md`, `42_SITE_GATEWAY_CONFORMANCE.md` — serialization/API conventions.
- `03_NODE_BOOTSTRAP_DEPLOYMENTS.md` — runtime states and deployment lifecycle vocabulary.
- `04_CAPACITY_ADMISSION_SEATS.md`, `06_BACKPRESSURE_RETURN_TO_SENDER.md`,
  `implementation/ERROR_SEMANTICS.md` — capacity, queueing and error/retry semantics.
- `05_ROUTING_AFFINITY.md`, `07_FAIRSHARE_OWNER_PRIORITY.md` — routing, affinity, priority.
- `09_OBSERVABILITY_RECEIPTS.md`, `23_GLOBAL_TELEMETRY_BENCHMARKS.md`,
  `24_MODEL_RECOMMENDATION_BENCHMARK_SUITE.md` — telemetry, receipts, benchmarks.
- `16_SECURITY_PRIVACY_TRUST.md`, `22_PROMPT_LEDGER.md` — privacy and provenance of prompts.
- `20_NODE_AUTOCONFIG_DISCOVERY.md`, `21_FEDERATION_ROLES.md`, `25_SLURM_EPHEMERAL_PROVIDER_NODES.md`,
  `41_INTER_GATEWAY_CAPACITY_REQUESTS.md` — discovery, federation, scheduler adapters, capacity
  grants.
- `26_RESOURCE_IDENTITY_REDISCOVERY.md`, `30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md`,
  `31_RESOURCE_HEALTH_QUARANTINE.md`, `36_GPU_WATCHDOG_RESCUE.md` — resource identity, lifecycle
  events, health/quarantine, watchdog.
- `38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md` — proof status and conformance obligations.
- `43_GPU_PLACEMENT_HOT_SWAP.md` — per-GPU placement, dwell, availability floor, aliases.
