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

## API naming — OpenAI fidelity + `iw` prefix (invariant)
- The OpenAI-compatible surface MUST stay **byte-compatible with the OpenAI API**
  under `/v1/` (`/v1/models`, `/v1/chat/completions`, `/v1/completions`,
  `/v1/responses`, `/v1/embeddings`, `/v1/images/generations`), so any OpenAI
  client/SDK works unmodified.
- Every InferWeave-specific (non-OpenAI) endpoint MUST live under the **`iw`
  prefix** (`/iw/v1/…`), never under bare `/v1/`, so a future OpenAI addition can
  never collide with an InferWeave one. This is the rule that keeps the two
  surfaces from ever clashing as OpenAI evolves.
- Prometheus is served at `/iw/metrics`. Pure operational conventions that are
  neither OpenAI nor InferWeave-invented (e.g. `/healthz`) MAY keep their standard
  path.
- This supersedes any custom `/api/v1/*` namespace: InferWeave-custom is
  `iw`-prefixed.

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
  Image workers are admitted by a **model-aware probe** (spec 14, admission
  probe): identity via `GET /v1/models` at the default budget, then a real
  small generation (`size: 512x512` + advisory `inferweave.steps`) at a
  model-aware budget — the default (30 s) is the floor, a declared
  `probe_budget_secs` extends it, clamped at 300 s. The probe is always a
  real generation; a worker that cannot complete it within its budget is
  refused (422), never admitted unverified.

  A **gateway-role peer** is a control-plane identity, not a GPU worker. Its
  authenticated registration MAY carry `models: []` when it has no READY serving
  capacity, provided its authenticated role, endpoint and deployment identity
  are valid. Registration returns a `connectionId` before the peer can bind its
  held Link Hello; the held link is checked afterward and reported separately.
  A missing link cannot create model reachability. This does not qualify any model, create slots, or bypass the worker
  rule above. A successful empty model snapshot withdraws earlier model
  advertisements while preserving the live gateway identity. A failed snapshot
  read does not assert emptiness; failed registration updates must retry the
  last unacknowledged change. This correction is required to show an idle Farm
  gateway in topology without inventing supply.
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
  Stream diagnostics MUST distinguish downstream-reported inference idle and
  execution timeouts from an observed transport failure and from client
  cancellation. After headers commit, an HTTP 200 with a terminal SSE error is a
  failed attempt. Correlation exposes diagnostic and transport request IDs
  separately. Operator statistics are bounded, authenticated, content-free and
  explicit about recording coverage, observation window, reset time and whose
  timeout settings are known. Heartbeat freshness is not an inference timeout;
  see spec 09 and `contracts/inference-stream-reliability.json`.
- **C9 Chaining & bandwidth** — behave as a well-mannered link per B1–B5:
  admission-grant negotiation not payload relay, shortest data path, affinity
  first, unbuffered streaming, bounded chains.
- **C10 Federation boundary** — MUST NOT implement operator bootstrap/enrolment
  tokens (decision D-007); standalone, registers upward later without faking it.

## Endpoint surface
Public OpenAI-compatible plane follows `specs/02`. The concrete site-gateway
surface the reference implementation serves (auth class in parens):

**OpenAI-standard surface — under `/v1/`, byte-compatible with OpenAI:**
| Method · path | Auth | Contract |
|---|---|---|
| `GET /v1/models` | client | OpenAI list w/ `x_context_window`,`x_state` |
| `POST /v1/chat/completions` · `/v1/completions` · `/v1/responses` | client | §C2 |
| `POST /v1/embeddings` · `/v1/images/generations` | client | §C2 (SHOULD, by modality) |

The `POST /v1/responses` surface MAY expose image generation as a tool
(`"tools": [{"type": "image_generation"}]`, spec 14 §Responses API): a
request carrying the tool is translated onto the gateway's image
`/v1/images/generations` path — same workers, same admission — and MUST NOT
be served as a text request.

**InferWeave-custom surface — under the `iw` prefix (never bare `/v1/`):**
| Method · path | Auth | Contract |
|---|---|---|
| `POST /iw/v1/workers` | admin | all-or-nothing register (§C4) |
| `POST /iw/v1/workers/{id}/heartbeat` · `DELETE /iw/v1/workers/{id}` | admin | liveness / deregister |
| `GET /iw/v1/workers` · `GET /iw/v1/capacity` | client | fleet topology / capacity |
| `POST/GET /iw/v1/warmup` · `DELETE /iw/v1/warmup/{model}` | client | idempotent, bounded (§C5/6) |
| `GET /iw/v1/stats` · `/iw/v1/throughput` · `/iw/v1/dashboard` | client | observability (§C8) |
| `GET /iw/metrics` | client | Prometheus text (§C8) |
| `GET /iw/auth/{login,callback,logout,me}` · `/iw/keys*` | open/session | OPTIONAL OIDC + personal keys |

**Operational conventions** (not OpenAI, no clash risk): `GET /healthz` (open) MAY
keep its standard path — `200 {status:"ok",census}` / `503 {status:"degraded"}`,
fail-closed.

The reference implementation currently serves the custom endpoints under bare
`/v1/*` (and `/metrics`); those MUST be retained as **compat aliases** during the
transition to the `iw` prefix (see §API naming, §Divergences).

Full per-endpoint request/response/status detail lives in the companion
references `docs/site-gateway-capabilities.md` and `docs/site-gateway-endpoints.md`;
the auth classes, request bodies, and status codes summarised above are normative.

## Divergences from `specs/02` — RESOLVED by §API naming
The naming rule settles the earlier open gate:

| Concern | `02` said | Reference gateway | **Resolution** |
|---|---|---|---|
| text completion | `/v1/responses` | `/v1/completions` | both are OpenAI-standard; serve both under `/v1/`, `/v1/responses` canonical |
| worker/node admin | native `/api/v1/*` | `/v1/workers*`, `/v1/capacity` | **`/iw/v1/*`** (not `/api/v1/*`, not bare `/v1/`); current `/v1/*` forms kept as compat aliases |
| warm/stats/throughput | native admin vocab | `/v1/warmup`,`/v1/stats`,… `/metrics` | **`/iw/v1/*`** + `/iw/metrics`; current forms compat aliases |

This means `specs/02_PROTOCOL_AND_API.md`'s native `/api/v1/*` namespace SHOULD be
renamed to the `iw` prefix for system-wide consistency (flagged for `02`; the
`iw`-prefix rule here is authoritative for the gateway surface).

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

## Additive read-only capacity disclosure

A site exposing `iw.observability.capacity/1` uses the separate schema in
`schemas/v1/resources/observability-capacity.json`, authenticated owner-scoped
reads, and spec04 freshness/entitlement/offer semantics. It never adds members
to topology v2 or turns `Capacity.requests` into a fixed-slot grant. A consumer
adapts the authoritative answer and preserves missing/stale/unsupported states.
The 2026-10-20 observability ADR permits existing Go edge observation persistence;
it grants no global metrics, reservation or dynamic-provisioner authority.
