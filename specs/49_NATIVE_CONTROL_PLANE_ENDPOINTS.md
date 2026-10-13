# 49 — Native `/inferweave/v1` Control-Plane and Inference Endpoints

## Relationship to existing surface

The gateway currently exposes OpenAI-compatible `/v1/chat/completions` and
`/v1/models`. This specification defines the native, namespaced
**`/inferweave/v1`** control-plane and inference surface built on Protocol v1
([`specs/45_PROTOCOL_V1.md`](45_PROTOCOL_V1.md)) and the typed capability model
([`specs/48_RUNTIME_FAMILIES_AND_CAPABILITIES.md`](48_RUNTIME_FAMILIES_AND_CAPABILITIES.md)).
The native surface does not replace the OpenAI-compatible surface; it is the
versioned contract for runtime-family-aware control and inference.

## Endpoint set

Extend `openapi/inferweave-v1.yaml` with the following namespaced endpoints,
all under `/inferweave/v1`:

- `GET /runtimes` — list runtimes with typed capabilities, residency, load
  state, and selection-reason metadata. Paginated.
- `GET /runtimes/{id}` — a single runtime's full descriptor.
- `GET /deployments` / `GET /deployments/{id}` — deployment manifests and live
  assignment/instance state (reuse the deployment vocabulary).
- `GET /capabilities` — the typed capability catalog a gateway can serve,
  filtered by `family` query parameter.
- `POST /rerank` — rerank endpoint for the `reranking` family.
- `POST /predictions` — prediction/classification endpoint for the
  `prediction` family (numeric or label outputs).
- `POST /embeddings` — embeddings endpoint for the `embeddings` family.
- `POST /pipelines/execute` — execute a typed inference pipeline (see
  [`specs/51_PIPELINES_AND_DURABLE_JOBS.md`](51_PIPELINES_AND_DURABLE_JOBS.md)).
- `POST /jobs` — submit a durable inference job (see
  [`specs/52_DURABLE_INFERENCE_JOBS.md`](52_DURABLE_INFERENCE_JOBS.md)).
- `GET /jobs/{id}` — durable job status and result reference.

## Contract requirements

- Every endpoint accepts and returns Protocol v1 schemas (no ad-hoc fields).
- Standalone JSON Schemas are authoritative for persisted/generated bindings: deployment is
  `schemas/v1/deployments/deployment.json`, and the three native family requests are
  `schemas/v1/requests/{rerank,prediction,embeddings}.json`. Their OpenAPI components must match
  the standalone value constraints as well as required fields and properties; CI resolves local
  reference spelling and rejects any validation-decision drift.
- Links that negotiate `native_link_requests: "1"` may dispatch the bounded native metadata in
  `schemas/v1/requests/link-request-meta.json`. Family/endpoint pairs are fixed (`embeddings` →
  `/embeddings`, `reranking` → `/rerank`, `prediction` → `/predictions`, other registered
  families → `/jobs`); method and content type are fixed to JSON `POST`, and the payload is capped
  at 16 MiB. Arbitrary/absolute URIs, proxy behavior, and inline bulk media are forbidden. Media
  uses content-addressed `artifact_refs`. Senders omit this additive metadata for older nodes.
- Family-specific endpoints reject requests whose family does not match their
  contract (e.g. `POST /rerank` rejects a non-reranking request) with a typed
  error from `schemas/v1/errors/`.
- All endpoints are discoverable and documented in `openapi/inferweave-v1.yaml`;
  the OpenAPI document is validated by a schema check.
- Native endpoints honour the same admission, capacity, routing-affinity, and
  fairshare policies as the OpenAI-compatible surface; they do not bypass
  capacity accounting.
- The `runtimes` and `deployments` list responses include a
  `selection_reason`/`placement_reason` field explaining why a runtime is the
  chosen target, so routing decisions are auditable.

## Required tests

- openapi-validation: `openapi/inferweave-v1.yaml` passes a strict schema and
  reference check.
- family-routing: a `POST /rerank` request is admitted only when the target
  runtime advertises the `reranking` family.
- parity: native endpoints observe the same admission and fairshare controls as
  the OpenAI-compatible surface (a shared conformance fixture).
- schema-parity: standalone deployment and family-request schemas make identical validation
  decisions to their OpenAPI components, including empty values, item counts, patterns and refs.
- link-native-dispatch: negotiation, family/path whitelist, method/content-type bounds, payload
  limit and artifact-reference grammar have executable positive and hostile fixtures.
