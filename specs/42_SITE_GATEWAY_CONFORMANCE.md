# 42 — Site-Gateway Conformance (capabilities + endpoints)

**Status: normative, language-neutral conformance contract for a gateway.** A
gateway implemented in Rust (`InferWeave/inferweave`) and one implemented in Go
(`metabolomics-us/inferweave-gateway`, the current reference) MUST both satisfy
this so they are interchangeable to their clients, their workers, and to each
other when chained. This spec pins the *concrete* HTTP + behavioural contract;
`specs/02_PROTOCOL_AND_API.md` remains the public-surface authority and this spec
reconciles against it (see §Divergences). Conformance is proven per
`specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`. RFC 2119 key words apply.

## Core concept: gateways chain, and chaining saves bandwidth
A gateway is **composable**. It presents the client `/v1` contract downward, and
it MAY itself be a *client* of an upstream or peer gateway — the same `/v1`
contract at every hop, so a chain of gateways is built only from this one
contract. The purpose of chaining is to reach capacity that isn't local while
**moving as few bytes as possible**:

- **B1 — negotiate admission, not payload.** When a gateway lacks capacity it
  MUST obtain a *grant* from a peer (per `specs/41_INTER_GATEWAY_CAPACITY_REQUESTS.md`)
  on the control plane; it MUST NOT hold the client's request while it shops, and
  MUST NOT relay the request body hop-by-hop as a queue. A gateway with neither
  capacity nor grant returns-to-sender (`specs/06`), it does not wait.
- **B2 — settle the data path once.** After a grant, inference SHOULD flow over
  the **shortest** viable path to the granted worker — ideally the client (or the
  edge gateway) talks to the serving endpoint directly, rather than proxying the
  token stream through every intermediate gateway. Multi-hop *payload* relay is a
  bandwidth anti-pattern the contract exists to avoid.
- **B3 — affinity/local-first.** A gateway MUST prefer local/affine capacity
  before asking a peer, so the common case moves no cross-gateway bytes at all
  (`specs/05_ROUTING_AFFINITY`).
- **B4 — stream, don't buffer.** On the data path it does carry, a gateway MUST
  pass SSE through unbuffered (§C2), so it never accumulates a response.
- **B5 — bounded chains.** Chain depth and peer fan-out MUST be bounded; a
  request MUST NOT be able to induce unbounded gateway-to-gateway amplification.

A conformant gateway is therefore defined by what it presents (endpoints, below),
what it guarantees (capabilities, below), and how it behaves as one link in a
chain (B1–B5).

## Capabilities (MUST unless noted)
- **C1 Model advertisement** — OpenAI `{"object":"list","data":[…]}`; each entry
  carries a *servable* context window and a state (`hot|warm|cold`), never a bare
  id. Modality marked for non-text models.
- **C2 OpenAI-compatible inference** — proxy `chat/completions` + `completions`
  (SHOULD: `embeddings`, `images/generations`); unbuffered SSE on `stream:true`;
  client cancellation frees the worker; assign+echo `X-Request-Id`; **no worker →
  `503` + `Retry-After`** without blocking, and trigger async warmup (C6). Never
  logs prompt/response content.
- **C3 Auth** — every *client* call bears `Authorization: Bearer <operator-token
  OR personal-key>`; every *admin* call bears the separate registration secret;
  MUST refuse to start with an unset registration secret; all auth failures are
  an identical `401` (no credential oracle); OIDC human sign-in OPTIONAL (routes
  404 when unconfigured).
- **C4 Worker registry & liveness** — accept **all-or-nothing** registration
  (model|job_id, endpoint, card, slots≥1, ctx_window; reject, never zero-fill);
  validate endpoint against an allowlist (SSRF); heartbeat/deregister by id;
  TTL-freshness liveness; clamp future `last_seen`; self-reported capacity wins.
- **C5 Warm pool** — maintain ≥1 live worker per keep-warm model; reconcile
  desired-vs-actual **idempotently** on a repeating interval.
- **C6 Capacity acquisition** — request/release/list GPU capacity; workers connect
  **outbound** (never reach into an allocation); bounded (per-model/hour, fleet
  cap, submit rate); refuse cleanly when disabled.
- **C7 Idle release** — reap idle workers (default 1 h); never reap `hot`;
  drain-lead pre-warm before a walltime deadline.
- **C8 Observability** — health with a census that **fails closed**; per-model
  stats; SHOULD: throughput (tokens incl. cached, prefill/decode rates), a
  Prometheus `/metrics` surface, capacity summary, dashboard. Telemetry is
  metadata-only, non-blocking, "unknown" never fabricated-0 (`specs/09`, `23`).
- **C9 Chaining & bandwidth** — behave as a well-mannered link per B1–B5:
  admission-grant negotiation not payload relay, shortest data path, affinity
  first, unbuffered streaming, bounded chains.
- **C10 Federation boundary** — MUST NOT implement operator bootstrap/enrolment
  tokens (decision D-007); standalone, registers upward later without faking it.

## Endpoint surface
Public OpenAI-compatible plane follows `specs/02`. The concrete site-gateway
surface the reference implementation serves (auth class in parens):

| Method · path | Auth | Contract |
|---|---|---|
| `GET /healthz` | open | `200 {status:"ok",census}` / `503 {status:"degraded"}`, fail-closed |
| `GET /v1/models` | client | OpenAI list w/ `x_context_window`,`x_state` |
| `POST /v1/chat/completions`, `/v1/completions` | client | §C2; SHOULD `/v1/embeddings`,`/v1/images/generations` |
| `POST /v1/workers` | admin | all-or-nothing register (§C4) |
| `POST /v1/workers/{id}/heartbeat` · `DELETE /v1/workers/{id}` | admin | liveness / deregister |
| `GET /v1/workers` · `GET /v1/capacity` | client | fleet topology / capacity summary |
| `POST/GET /v1/warmup` · `DELETE /v1/warmup/{model}` | client | idempotent, bounded (§C5/6) |
| `GET /v1/stats` · `/v1/throughput` · `/v1/dashboard` · `/metrics` | client | observability (§C8) |
| `GET /auth/{login,callback,logout,me}` · `/keys*` | open/session | OPTIONAL OIDC + personal keys |

Full per-endpoint request/response/status detail lives in the companion
references `docs/site-gateway-capabilities.md` and `docs/site-gateway-endpoints.md`;
the auth classes, request bodies, and status codes summarised above are normative.

## Divergences from `specs/02` — TO RECONCILE (open gate)
The deployed reference gateway and `02` differ; a conformant contract must pick a
canonical form. Tracked here for resolution (see `OPEN_GATES.md`):

| Concern | `02` says | Reference gateway | Proposed resolution |
|---|---|---|---|
| text completion | `POST /v1/responses` | `POST /v1/completions` | support **both** aliases during transition; `/v1/responses` canonical |
| worker/node admin | native `/api/v1/*` (nodes, heartbeats, capacity) | `/v1/workers*`, `/v1/capacity` | move admin under `/api/v1/*`; keep `/v1/workers*` as compat aliases |
| warm/stats/throughput | native admin vocabulary | `/v1/warmup`,`/v1/stats`,`/v1/throughput`,`/metrics` | fold into native `/api/v1/*`; `/metrics` stays Prometheus-standard |

Until resolved, an implementation MUST serve at least the reference forms above;
after resolution, the canonical forms become MUST and the others compat aliases.

## Conformance (per spec 38)
Minimum for interchangeability: §C1–C10, the MUST endpoints + status behaviours
above, two shared secrets + identical `401`s + refuse-to-start-without-
registration-secret, `503`+`Retry-After` on no-worker, and the chaining/bandwidth
rules B1–B5. An impl MAY add routes; it MUST NOT remove a MUST route, weaken an
auth class, change a documented status code, or relay payload where a grant would
do. Reference implementation: `metabolomics-us/inferweave-gateway`.

## Relationships
`02` public/native API · `04` capacity/admission · `05` routing/affinity · `06`
backpressure/return-to-sender · `09` observability · `23` telemetry vocabulary ·
`38` conformance method · `41` inter-gateway capacity requests.
