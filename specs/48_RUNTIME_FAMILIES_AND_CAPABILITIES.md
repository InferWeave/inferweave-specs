# 48 — Runtime Families and Typed Capabilities

## Relationship to Protocol v1 and Core Protocol

This specification extends the scheduler-neutral vocabulary of
[`specs/44_CORE_PROTOCOL.md`](44_CORE_PROTOCOL.md) and the wire contract of
[`specs/45_PROTOCOL_V1.md`](45_PROTOCOL_V1.md) with a canonical **runtime
family** classification and **typed capability** descriptors. It does not
replace the existing capability advertisement; it generalises it so that a
single node can describe non-LLM workloads without inventing ad-hoc fields.
Where this spec states an enum, schema, or event, Protocol v1 and the
machine-readable contracts remain authoritative for the wire format.

## Goal

Let a node and a gateway describe, advertise, route, and admit **any** model
runtime in a typed, modality-neutral way, including: LLM / reasoning / vision,
embeddings, reranking, speech-to-text, text-to-speech, music/audio, prediction
and classification, image, video, multimodal, scientific/custom, and RAG as a
pipeline.

## Canonical runtime-family registry

A runtime family is an opaque identifier that a node advertises and a gateway
understands by its capability contract. The canonical registry:

| family id        | input modality | output modality | primary quality signal        | example workloads      |
|------------------|----------------|-----------------|-------------------------------|------------------------|
| `llm`            | text,image     | text            | token throughput, quality     | chat, completion       |
| `reasoning`      | text           | text            | chain-of-thought tokens       | long-horizon reasoning |
| `embeddings`     | text,image     | vector          | embedding dimension, recall   | retrieval             |
| `reranking`      | text           | score           | ranking quality               | RAG re-rank           |
| `stt`            | audio          | text            | WER                           | transcription         |
| `tts`            | text           | audio           | naturalness, latency          | speech synthesis      |
| `audio`          | audio          | audio           | MOS                           | music/audio gen       |
| `prediction`     | numeric,text   | numeric,label   | calibration, AUC              | forecasting           |
| `image`          | text,image     | image           | image quality                 | image generation      |
| `video`          | text,image     | video           | temporal coherence            | video generation      |
| `multimodal`     | any            | any             | task-specific                 | mixed-modal           |
| `scientific`     | typed          | typed           | domain metric                 | custom scientific     |
| `rag`            | text           | text            | retrieval + generation quality| pipeline              |

## Typed capability descriptor

Extend `schemas/v1/model/capabilities.json` and `schemas/v1/model/model.json`
so a capability advertisement carries, in addition to existing fields:

- `family`: one of the canonical runtime-family ids above.
- `input_modalities`: non-empty set from a canonical modality enum.
- `output_modalities`: non-empty set from the same enum.
- `quality`: optional measured quality floor for the family (e.g. WER ceiling,
  embedding dimension, rerank quality, prediction AUC floor). A model never
  advertises a quality figure inferred from its name; every figure is either
  measured and evidenced, or explicitly `self-reported`.
- `context`: for token-addressable families, reuse the existing four-valued
  context vocabulary from `model_capabilities.rs`; for non-token families,
  `null` and a family-specific resource descriptor.
- `runtime_preference`: optional ordered list of accepted engine/backend ids.

A capability advertisement that names a `family` must be validated against the
canonical registry and must be consistent with the deployment manifest
fingerprint. Unknown family ids are rejected at admission, never silently
forwarded.

## Runtime adapter boundary

Every adapter implements one versioned lifecycle surface: `identity`, `capabilities`,
`hardware_requirements`, `validate`, `prepare`, `load`, `unload`, `health`, `metrics`, `cancel`,
`drain`, and `shutdown`. The descriptor is
`schemas/v1/runtime/adapter.json`; `schemas/v1/runtime/load-request.json` defines the load call.
Family execution methods remain separately typed so a lifecycle implementation cannot turn into an
untyped inference escape hatch.

Adapters execute in an isolated process or container and communicate with the node agent over a
versioned protocol. Persistent production roles still run under Docker Engine + Compose and Slurm
allocation workers under Apptainer. A child adapter process may execute inside one of those
containers. The isolation boundary does not authorize an unmanaged persistent bare-host service or
arbitrary adapter code in the Rust node process.

## Canonical modality enum

`text`, `image`, `audio`, `video`, `vector`, `score`, `numeric`, `label`,
`typed`. Machine-readable forms: `schemas/v1/model/capabilities.json`
(`family`, `input_modalities`, `output_modalities`, `quality`, `context`,
`runtime_preference`; `$defs.typed_admission` lists the fields admission
requires), `schemas/v1/model/model.json`, and the `TypedCapabilities` schema in
`openapi/inferweave-v1.yaml`. `quality.basis` is `measured` or `self-reported`.

## Mixed-version behavior

The runtime-family surface is additive and negotiated as `runtime_families: "1"`. A peer that does
not advertise it continues to exchange the pre-family Protocol v1 objects. New fields are omitted
on that link; the gateway never invents a family from a model name. Unknown feature names remain
forward-compatible under specs/45. Lifecycle, resource-reservation and cache extensions are
separately negotiated as `runtime_lifecycle`, `runtime_reservations`, and
`transactional_caches` level `"1"` so support for one cannot be mistaken for support for all.

## Invariants

1. **No inference from name.** A runtime never derives capabilities, quality,
   or context from its model name. All such data is explicit in the
   advertisement or explicitly self-reported.
2. **Family is typed and closed.** The registry is the single source of truth
   for family ids; unknown ids fail admission.
3. **Consistency with manifest.** Advertised typed capabilities must agree with
   the immutable deployment manifest fingerprint.

## Required tests

- typed-capability round-trip: advertise a non-LLM family (e.g. `embeddings`)
  and recover the descriptor unchanged.
- name-derived-rejection: a model whose advertisement omits `family` and
  `input_modalities` is rejected at admission.
- registry-closure: an unknown family id fails admission, not forwarding.
- adapter-contract: every lifecycle method is present and the adapter declares process/container
  isolation.
- mixed-version: a legacy peer omits additive fields and continues to validate without family
  inference.

## Generation-bound node producer input

Spec [56](56_RUNTIME_INSTANCE_OBSERVATIONS.md) defines the optional negotiated runtime
observation report, full-snapshot replay/expiry/tombstone rules, independent qualification and
owner policy references. Runtime probes do not verify unspecified feature fidelity or grant
capacity. Older or unqualified observations remain UNKNOWN for level-2 aliases.

## Native SystemOne input and shared-pool admission

`iw.systemone-admission/1` is an additive capability for decision/classification
runtimes. It does not make them generative token runtimes. Its registration
claim and heartbeat report bind an explicitly versioned native input envelope to
the actual runtime deployment and checkpoint/source provenance. The gateway and
worker validate the same envelope before admission and execution. Unknown,
unnegotiated, stale, malformed or mismatched evidence remains unavailable; it
never becomes a zero-token window, an assumed 1024-token window or inferred
capacity from another model.

The initial Laya policy uses UTF-8 serialized request bytes and explicit shape
bounds. The implementation must publish the exact effective limits and policy
fingerprint, including their unit, source package hash and checkpoint revision.
A bound is not a claim that the backend reads every token: a backend that
truncates retains that native behavior and must not advertise the input byte
limit as a tokenizer context size. Aliases derive only from explicit configured
public-to-logical mappings on that same registered runtime. Never infer identity
or eligibility from a model spelling.

Reports identify each real runtime capacity pool once, including its registration
incarnation/generation, exact eligible model capabilities and native-envelope
fingerprint, measured maximum concurrency and occupancy. Unknown queue or
per-origin counts remain absent. Relays preserve origin identity and accumulate
monotonic age; repeated observations cannot refresh an old generation. A parent
uses only current authenticated registration bindings and negotiated evidence.
Report authority includes the generation; reservation identity keeps the stable
physical pool across generations, so replacement registration cannot escape
held leases from the prior incarnation.
Its held reservations consume the same pool across all logical models and
aliases; cancellation releases the pool reservation once. Child admission remains
independently authoritative. A model capability may show an upper bound from
its eligible pools, but fleet available concurrency sums distinct physical pools,
never all model rows. This adds no second allocator or runtime service.

The November 11 Whiteale incident exposed a specification gap: the generative
admission catalogue excluded actual SystemOne runtime registrations, while the
parent invented a 1024-token context class. Implementing only model-name
conversion would preserve the missing input authority and shared-pool accounting
defects. See [bounded incident evidence](../evidence/systemone-native-admission-2026-11-11/README.md).

Required proofs are removal-sensitive envelope-boundary, stale/incarnation,
exact-model/alias, shared-pool cross-model occupancy and cancellation tests;
real linked parent/child admission; fresh accepted deployed reports; actual
normal-route decision inference and native-boundary refusals. Source/CI tests
do not establish production qualification. Paid policy and owner priority are
unchanged; no native report creates entitlement.

Frozen additive field vocabulary: [`contracts/systemone-native-admission-v1.json`](../contracts/systemone-native-admission-v1.json).

The fingerprint hashes UTF-8 compact JSON without whitespace or the fingerprint
member, with fields in the frozen contract's `orderedFields` order. Integers use
base10; strings use JSON escaping. The initial policy hash is
`4e7c3e4f54df4f530f9df35a32baa845e3067f57bcd4075e69dede12632ab0e5`.
State-character measurement must conservatively bound the native backend's
actual serialization (including structured-state separators and escaping);
compact reserialization cannot undercount a native structured-state limit.

Mixed-version legacy SystemOne routes retain their existing explicitly labeled
legacy behavior, with native capacity and input authority unknown. Negotiation
of the native capability (or an explicit new native-envelope claim) opts into
the new fail-closed boundary: missing/stale/mismatched native evidence cannot
fall back to legacy accounting. This repair does not infer paid exceptions
from model names or change separate paid gateway policy.

Until per-reservation acknowledgement/origin accounting exists, worker-reported
occupancy, child-gateway held leases and parent-held leases can overlap. Native
routing conservatively adds all three and clamps at the pool ceiling. It MUST
NOT use their maximum as an overlap estimate. The report publishes
`reportedInflight` (measured worker occupancy; absent grants no usable native
capacity), `gatewayHeld` and `occupancyBasis: conservative_sum` separately;
`inflight` is the clamped child conservative routing occupancy. Physical fleet
metrics use only measured worker occupancy and distinct pools; conservative
routing headroom is labeled separately and may be pessimistic. A held lease
releases its own reservation once, including after generation turnover; it
cannot release a newer incarnation's reservation.

For this protocol, pool concurrency and occupancy count state admission units,
matching Laya worker counters: a single decision costs one unit; a batch
reserves `min(number of states, selected pool maxConcurrency)` units until
completion/cancellation. Parent and child use the same cost and release it
once. A 64-state batch on a 16-unit pool holds 16 units, not one HTTP-request
unit; another model cannot reuse those units concurrently.
