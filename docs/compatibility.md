# InferWeave Protocol v1 — compatibility

## Versioning

Semantic versioning. `protocol: { name, version, minimum_compatible_version }`. Major = breaking,
minor = backwards-compatible additions, patch = clarification. A peer below
`minimum_compatible_version` is rejected with `PROTOCOL_VERSION_UNSUPPORTED`. Feature negotiation
is separate from version: peers advertise supported features and MUST tolerate unknown features.

## OpenAI compatibility

The data plane stays compatible with applicable OpenAI-compatible endpoints (`/v1/models`,
`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`) and extends via optional headers and
separate control endpoints, never by mutating the OpenAI surface. The `X-InferWeave-*` header
namespace is reserved.

## Streaming

Streaming explicitly defines start, chunks, finish, cancel, failure, and connection loss. A
stream ending without an explicit completion signal is distinguishable from success.

## Backwards compatibility

Existing InferWeave APIs must not abruptly disappear; adapters map legacy structures (e.g. slot
count) to protocol capacity and deprecate gradually. Older gateways advertising only
model/endpoint/slots keep functioning; missing fields yield `unknown`, not rejection.

## GPU memory (1.1.0)

The `iw.gpu-memory` family (`specs/46_GPU_MEMORY_INTELLIGENCE.md`) is additive and
capability-gated: an older node never sends `gpuMemory`, an older gateway never asks for the
fleet snapshot, and a malformed report never refuses the telemetry or heartbeat carrying it.
Topology v2 is never a carrier, because deployed decoders refuse unknown members there. New
configuration goes only under a new top-level `gpuMemory` object, never into an existing strictly
decoded object. Unknown enum values are kept verbatim and read through a documented fallback.
Spec 46 §10 is the full mixed-version matrix.

## Compatibility matrix

Machine-readable minimums per protocol version are in `conformance/compatibility.yaml`; they are
currently recorded `unknown` until a conforming reference implementation and gateway ship.

## Change workflow

Any protocol-visible change requires a specs PR (schemas, docs, examples, fixtures, conformance
tests), a compatibility classification, changelog update, reference-implementation update, and
downstream gateway validation. The spec change merges before or with the implementation.

## Hardware-only registration (1.1.0)

`specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` adds an optional `hardware` member to
`POST /v1/node/register` and an always-present `assignments: []` to its response. An older node
never sends `hardware` and ignores `assignments`; an older gateway ignores `hardware` and still
refuses a hardware-only body under its existing checks. A gateway stores `hardware` verbatim and
never uses it for routing or authentication.
