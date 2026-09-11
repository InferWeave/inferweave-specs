# InferWeave site-gateway — exposed-endpoints specification (wire contract)

**Status: normative, language-neutral wire contract.** It defines the HTTP
surface every InferWeave site-gateway implementation MUST expose so a Rust
implementation and a Go implementation (or any other) are interchangeable to
their clients and workers. It is derived from the reference implementation
(`metabolomics-us/inferweave-gateway`, Go) but is expressed purely as HTTP +
JSON; no language type is part of the contract. Functional requirements are in
the companion [gateway-capabilities-spec](./site-gateway-capabilities.md). RFC
2119 key words apply.

## Conventions
- **Transport.** HTTP/1.1; JSON request/response bodies (`Content-Type:
  application/json`) except SSE streams and the Prometheus text endpoint.
- **Auth classes** (how a route is protected):
  | class | credential | on failure |
  |---|---|---|
  | *open* | none | — |
  | *client* | `Authorization: Bearer <operator-token OR personal-API-key>` | `401` + `WWW-Authenticate: Bearer` |
  | *admin* | `Authorization: Bearer <registration-secret>` | `401` |
  | *session* | valid human sign-in session (cookie) | `401`/redirect to sign-in |
  All auth failures MUST be indistinguishable across causes.
- **Request id.** Requests MAY send `X-Request-Id`; the gateway MUST assign one
  when absent and MUST echo it on the response.
- **Errors.** Non-2xx responses SHOULD carry a JSON body `{"error":{"message",
  "type"}}` (OpenAI-shaped) for `/v1/*` inference routes; other routes MAY use a
  plain-text body. Status codes are normative (below); bodies are advisory except
  where a field is called out as required.
- **Versioning.** OpenAI-compatible routes live under `/v1/`. Unknown routes MUST
  `404`.

## Endpoint catalog

### Health & identity
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/healthz` | open | See below. |
| GET | `/{$}` (root) | open | Human landing; MAY redirect to sign-in / key page. |

**`GET /healthz`** — MUST return `200` `{"status":"ok","census":{…}}` when
serving; `503` `{"status":"degraded",…}` when a keep-warm model has no live
worker past grace, or when health cannot be determined (fail closed). `census`
MUST expose running-vs-registered-vs-dispatchable counts. No auth.

### Inference (OpenAI-compatible) — auth: *client*
| Method | Path | Required |
|---|---|---|
| POST | `/v1/chat/completions` | MUST |
| POST | `/v1/completions` | MUST |
| POST | `/v1/embeddings` | SHOULD (models advertising the modality) |
| POST | `/v1/images/generations` | SHOULD (image models) |

- Request/response bodies MUST follow the OpenAI API for that route; `model` MUST
  select the served model.
- `"stream":true` MUST produce an unbuffered `text/event-stream`, one flush per
  chunk, terminating with the OpenAI `[DONE]` sentinel.
- No live worker for `model` MUST return **`503`** with **`Retry-After`** (and
  trigger async warmup per capability C6), without blocking the client.
- Client disconnect MUST cancel the upstream request.
- `400` for an unparseable body or unknown/blank `model`.

### Catalogue — auth: *client*
**`GET /v1/models`** → `200` `{"object":"list","data":[ {"id","object":"model",
"owned_by","created","x_context_window","x_state"} … ]}`. `x_context_window`
MUST be the servable context; `x_state` ∈ `hot|warm|cold`. Image models SHOULD
carry a modality marker.

### Workers (registry)
| Method | Path | Auth | Body / Result |
|---|---|---|---|
| POST | `/v1/workers` | admin | register (below) |
| POST | `/v1/workers/{id}/heartbeat` | admin | liveness bump; `204`/`200` |
| DELETE | `/v1/workers/{id}` | admin | deregister; `204` |
| GET | `/v1/workers` | client | fleet topology |

**`POST /v1/workers`** request (JSON) — required: (`model` OR `job_id`),
`endpoint`, `card`, `slots` (≥1), `ctx_window` (>0). Optional: `quant`,
`spec_type`, `gpus`, `tier`, `expires_at` (RFC3339), `last_seen`,
`gpu_layers`/`model_layers`, measured footprint. MUST be **all-or-nothing**
(reject, never zero-fill, if `slots`/`card`/`ctx_window` missing). MUST reject an
`endpoint` outside the allowlist (`400`). MUST clamp a future `last_seen`.
Success `200`/`204`.

**`GET /v1/workers`** → `200` `{"data":[ {"job_id","model","endpoint","card",
"quant","spec_type","gpus","ctx_window","slots","tier","source",
"last_request_ts","hold_until","expires_at"} … ]}`. A worker past its TTL MUST
NOT appear as routable (MAY appear flagged).

### Pool / lifecycle — auth: *client*
| Method | Path | Notes |
|---|---|---|
| POST | `/v1/warmup` | request a model be warmed to ≥1 worker; returns an ETA |
| GET | `/v1/warmup` | warm state per model |
| DELETE | `/v1/warmup/{model}` | release/stop keeping a model warm |

Warmup MUST be idempotent and MUST NOT exceed the acquisition backstops (C6);
when acquisition is disabled it MUST refuse cleanly (not hang).

### Observability — auth: *client*
| Method | Path | Result |
|---|---|---|
| GET | `/v1/stats` | per-model `{requests,errors,served_503,inflight,p50_ms}` + totals, uptime, events, capacity |
| GET | `/v1/throughput` | per model+card `{requests,prompt_tokens,cached_tokens,completion_tokens,prefill_tps,decode_tps,ctx_at_end}` (+ sample counts); unmeasured = `"unknown"` |
| GET | `/v1/capacity` | fleet capacity summary per model |
| GET | `/v1/dashboard` | aggregated fleet/utilisation view |
| GET | `/metrics` | Prometheus text (below) |
| GET | `/ui` | human status page (HTML) |

**`GET /metrics`** — Prometheus `text/plain; version=0.0.4`. MUST expose at least,
labeled by model (and card where applicable): request counts, prompt/cached/
completion token counters, prefill/decode rates, per-model errors/503s/inflight/
p50, uptime, and live workers by card. Unmeasured series MUST be omitted, never
emitted as a fabricated 0. Client-gated (a public deployment MUST NOT expose it
open).

### Operator sign-in & personal keys — auth as noted (present only if OIDC configured)
| Method | Path | Auth |
|---|---|---|
| GET | `/auth/login` `/auth/callback` `/auth/logout` | open (OIDC flow) |
| GET | `/auth/me` | session |
| GET/POST | `/keys`, POST `/keys/{id}/delete` | session |

If sign-in is not configured these routes MUST return `404` (not a fake success).
Personal keys minted here are presented to *client* routes as bearer tokens.

## Conformance checklist (minimum for interchangeability)
1. `GET /healthz` open, with `status` + `census`, fail-closed to `503`.
2. `GET /v1/models` in OpenAI list shape with context window + state.
3. `POST /v1/chat/completions` + `/v1/completions`, client-gated, streaming,
   cancellation, `X-Request-Id`, and `503`+`Retry-After` on no worker.
4. `POST/GET/DELETE /v1/workers[...]` admin-gated, all-or-nothing registration
   with endpoint allowlist + TTL liveness.
5. Warmup trio, client-gated, idempotent, bounded.
6. `GET /v1/stats` (+ SHOULD: `/v1/throughput`, `/v1/capacity`, `/metrics`).
7. Two shared secrets (client, registration) + optional OIDC; identical `401`s;
   MUST refuse to start with an unset registration secret.
8. No enrolment/bootstrap-token endpoint (C9).

An implementation MAY add routes; it MUST NOT remove a MUST route, weaken an auth
class, or change a documented status-code behaviour.
