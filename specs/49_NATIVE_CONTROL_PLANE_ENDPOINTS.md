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
- Links that negotiate `native_link_requests: "1"` through the exact-registration and exact-Link
  incarnation handshake in `schemas/v1/requests/link-{hello,hello-ack}.json` may dispatch the
  bounded native metadata in `schemas/v1/requests/link-request-meta.json`. A registration feature
  observed by node id is insufficient: the exact capability must first be offered and returned in
  the `/v1/node/register` `capabilities` arrays defined by spec 47 section 2.1. The gateway must
  atomically select the held Link, verify its
  stored binding is still current, and enqueue the request. Family/endpoint pairs are fixed (`embeddings` →
  `/embeddings`, `reranking` → `/rerank`, `prediction` → `/predictions`, other registered
  families → `/jobs`); method and content type are fixed to JSON `POST`, and the payload is capped
  at 16 MiB. Arbitrary/absolute URIs, proxy behavior, and inline bulk media are forbidden. Media
  uses content-addressed `artifact_refs`. Senders omit this additive metadata for older or unbound
  nodes. Missing/revoked binding returns `FEATURE_UNSUPPORTED`; the error envelope and retry fields
  are unchanged.
- HTTP-facing native Link relay additionally requires independently negotiated
  `native_link_responses: "1"` / `iw.link-native-response/1` on that same registration and Link
  incarnation. A node sends body fragments as the existing ordered `token.payload` strings, then
  adds a `response` member to the existing `end` frame:

  ```json
  {
    "kind": "end",
    "request_id": "request-1",
    "response": {
      "status": 201,
      "headers": {
        "content-type": "application/json",
        "location": "/inferweave/v1/jobs/job-1"
      },
      "body_bytes": 55,
      "body_sha256": "sha256:c4bc50b8d02444e17cf6f05db75e0b2c3cf27d4cc301242475b6a669599521c4"
    }
  }
  ```

  The authoritative metadata schema is
  `schemas/v1/requests/link-response-meta.json`. Status is an integer in 200–299 or 400–599;
  redirects are not relayed. Headers are a closed lower-case object containing only
  `content-type: application/json`, decimal-seconds `retry-after` for 429/503, and a relative
  `/inferweave/v1/jobs/{id}` `location` for 201/202. The body is the byte-for-byte UTF-8 encoding
  of the concatenated token payloads in sequence order, capped at 16 MiB; `body_bytes` and
  `body_sha256` bind those exact bytes. Status 204 binds the empty body and its SHA-256 digest. A
  non-empty body is valid JSON.

  The schema uses JSON Schema Draft 7 integer semantics: finite JSON numbers with no fractional
  part, including lexical forms such as `200.0` and `2e2`, are accepted for `status` and
  `body_bytes` and normalized to integers before comparison or relay. Non-finite extensions such
  as `NaN` and positive or negative infinity are not JSON and invalidate the proof.

  The receiving gateway emits no upstream status, headers, or body until the `end` proof validates.
  It uses the validated, normalized metadata status and never interprets a top-level body member
  such as `code` as an error signal. Missing metadata, a byte or digest mismatch, invalid
  JSON/UTF-8, a disallowed
  header/status combination, or an oversized body is `502 invalid_upstream_response`. A
  request-only peer remains valid for its prior negotiated Link behavior, but is ineligible for
  native HTTP relay that needs response semantics; selection uses direct HTTP or another eligible
  deployment, otherwise returns `FEATURE_UNSUPPORTED` before dispatch. Legacy Hello frames,
  metadata-free chat streams, and older peers remain unchanged.
- Spec57 level-2 owner permits use the separately negotiated closed protected Request schema
  `schemas/v1/requests/link-alias-request.json` and distinct consume control frames. They do not
  extend `meta.native` endpoint mappings or imply compatible SSE/tool-stream responses. See
  spec57 section 5.1; activation proof remains owed.
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
- link-native-dispatch: exact registration/Link-incarnation negotiation, acknowledgement echo,
  replacement/re-registration/withdrawal revocation, family/path whitelist, method/content-type
  bounds, payload limit and artifact-reference grammar have executable positive and hostile
  fixtures; response-proof fixtures cover exact 201/4xx/5xx relay, success bodies with a top-level
  `code`, missing proof, tampered bytes, invalid metadata and request-only legacy peers.
