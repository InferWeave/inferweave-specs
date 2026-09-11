# InferWeave site-gateway — capability specification (conformance)

**Status: normative conformance contract.** This document defines the
capabilities *any* implementation of an InferWeave **site gateway** MUST provide,
independent of language or internal structure. `metabolomics-us/inferweave-gateway`
(Go) is the **reference implementation**; where this spec and the reference
disagree, this spec governs the *contract* and the reference governs
undocumented detail. The wire contract is in the companion
[gateway-endpoints-spec](./site-gateway-endpoints.md); this document is the
*functional* contract.

Key words MUST / MUST NOT / SHOULD / MAY are per RFC 2119.

## 0. What a "site gateway" is
An OpenAI-compatible front door that presents a site's local and borrowed GPU
capacity as one endpoint: it advertises models, authenticates callers, routes
inference to live workers, keeps important models warm, borrows/releases GPU
capacity on demand, expires idle capacity, and reports what it is doing. It is
site-local; federation (registering upward into a network) is explicitly out of
scope (C10).

## Terminology
- **Worker** — one serving backend for one model at one endpoint, with a card
  (GPU model), a context window it can actually serve, a slot count, and a tier
  (`hot` | `burst` | `local`). Identified by a job id (`""` for a static local
  worker).
- **Model** — an advertised id with the context window it can serve and a state
  (`hot` | `warm` | `cold`). Capability is per model **and** context class — a
  bare model name without a servable context window is not a valid advertisement.
- **Caller classes** — *client* (inference/read callers), *worker/registrar*
  (backends announcing themselves), *operator* (a signed-in human managing keys).

## C1 — Model advertisement
- MUST expose a catalogue of models in OpenAI `{"object":"list","data":[…]}`
  shape, each entry carrying at least: id, object=`model`, a context window, and
  a state.
- MUST advertise both live-servable models and known-but-cold models it can warm.
- MUST advertise the context window a model can *actually* serve, never a bare id.
- SHOULD mark modality for non-text models (e.g. image-generation).

## C2 — OpenAI-compatible inference
- MUST proxy `POST /v1/chat/completions` and `POST /v1/completions` to a live
  worker for the requested model, preserving OpenAI request/response semantics.
- SHOULD also proxy `/v1/embeddings` and `/v1/images/generations` for models that
  advertise those modalities.
- MUST stream Server-Sent Events unbuffered when the request sets `"stream":true`,
  flushing each chunk.
- MUST propagate client cancellation to the upstream (a disconnected client MUST
  free the worker).
- MUST assign an `X-Request-Id` when absent and echo it on the response.
- When no live worker can serve the model, MUST answer **`503`** with a
  **`Retry-After`** header, and MUST NOT block the client while capacity is
  sought; it MUST additionally trigger an asynchronous warmup (C6) unless
  capacity acquisition is disabled or rate-gated.
- MUST NOT expose or log prompt/response *content* in telemetry (C8).

## C3 — Authentication & authorization
- MUST authenticate every *client* request (inference, catalogue, read views)
  with `Authorization: Bearer <secret>`, accepting **either** a shared operator
  token **or** a personal API key; a request with neither MUST get `401` with a
  `WWW-Authenticate: Bearer` challenge.
- MUST gate every *administrative* route (worker register / heartbeat / delete)
  behind a separate shared **registration secret**; MUST refuse to start with an
  open (unset) registration secret.
- Authentication failures MUST be indistinguishable across causes (unknown key,
  revoked key, wrong token → one identical `401`); the endpoint MUST NOT become
  an oracle for which credentials exist.
- MAY offer human sign-in (OIDC) for a personal-API-key management surface; if
  offered, those routes MUST require a valid session and MUST be disabled (404)
  when sign-in is not configured.
- Personal-key requests SHOULD carry an attributable identity (subject/email/key
  id) for usage and revocation; shared-token requests carry none.

## C4 — Worker registry & liveness
- MUST accept worker registration carrying at minimum: model **or** job id,
  endpoint, card, `slots >= 1`, and a valid context window. Registration MUST be
  **all-or-nothing** — a payload missing slots/card/ctx MUST be rejected, never
  stored zero-filled (a half-registered worker would advertise capacity that
  cannot be verified).
- MUST validate a worker's endpoint against an allowlist before storing it
  (SSRF / prompt-interception / blackhole defence); MUST reject endpoints outside
  it.
- MUST accept heartbeats and deregistration keyed by job id.
- MUST treat a worker not seen within a TTL as not routable (liveness by
  freshness); MUST clamp a client-supplied `last_seen` that is in the future
  (a worker MUST NOT be able to pin itself live forever).
- MUST expose the current worker set (topology) to clients.
- The registration API is the worker's own voice: self-reported capacity MUST win
  over anything a background sweep infers.

## C5 — Warm pool / desired state
- MUST let an operator declare desired replicas per model/tier ("keep-warm"), and
  MUST maintain at least one live worker for each keep-warm model.
- MUST reconcile desired-vs-actual **idempotently** and safely on a repeating
  interval (running it every minute MUST NOT ratchet capacity up).

## C6 — Capacity acquisition (borrowing GPUs)
- MUST be able to request and release GPU capacity from the site's scheduler,
  and to list capacity it currently holds.
- MUST treat workers as connecting **outbound**: the gateway asks for capacity
  and waits for the worker to register; it MUST NOT assume it can reach into a
  scheduler allocation.
- MUST bound acquisition: a per-model acquisitions-per-hour backstop, a total
  fleet cap, and a global submission rate limit; MUST degrade safely (refuse, not
  crash) when acquisition is disabled or unavailable.
- MAY delegate the scheduler mechanics to external, separately-tested scripts.

## C7 — Idle release
- MUST reap workers idle beyond a configurable timeout (default **1 hour**).
- MUST NOT reap a `hot`-tier worker regardless of idleness.
- SHOULD pre-warm a replacement before a worker's known walltime deadline
  (drain-lead) so draining does not drop capacity.

## C8 — Observability
- MUST expose a health endpoint that reports serving vs degraded AND a census
  (running vs registered vs dispatchable), and MUST **fail closed** (report
  degraded) when it cannot determine health. A keep-warm model with zero live
  workers beyond a grace period MUST read degraded.
- MUST expose per-model request stats (requests, errors, 503s, in-flight, a
  latency percentile).
- SHOULD expose per-model+card throughput (tokens, cache hits, prefill/decode
  rates), a Prometheus `/iw/metrics` surface, a capacity summary, and a dashboard
  aggregate.
- Telemetry MUST record only metadata (model, worker, card, token counts, timing,
  status) — never prompt or completion text — and MUST be non-blocking (a metric
  MUST never delay or fail a user request); unmeasured values MUST be reported as
  "unknown", never fabricated as 0.

## C9 — Federation boundary (explicitly out of scope)
- MUST NOT implement operator-issued bootstrap/enrolment tokens or an enrolment
  endpoint (rejected design D-007). A conformant site gateway is standalone; it
  is expected to *register upward* into a network later, but that path MUST NOT
  be designed out and MUST NOT be faked with local tokens.

## Configuration surface (SHOULD expose)
A conformant gateway SHOULD be configurable for at least: listen address; the
client (operator) token, the worker/registration secret, and (optional) personal
API-key store; keep-warm model list; idle timeout, prune/reap/reconcile
intervals, drain-lead; acquisition bounds (per-model/hour, fleet cap, submit
rate); optional OIDC issuer/client for sign-in; optional telemetry sink. Secrets
MUST come from the environment or secret store, never a committed file.

## Conformance
An implementation is conformant when it satisfies every MUST above and passes the
wire contract in [gateway-endpoints-spec](./site-gateway-endpoints.md).
"Provides at least the same functionality" means: all MUSTs, plus the SHOULDs it
chooses to advertise behave as specified. Additional endpoints/behaviour are
permitted provided they do not weaken any MUST (e.g. do not widen an auth gate).

## Relationship to InferWeave/inferweave-specs
This governs the deployed **site** gateway (the Go reference impl + any
re-implementation). `InferWeave/inferweave-specs` is authoritative only for the
separate Rust `InferWeave/inferweave` program; vocabulary alignment with it is a
carried constraint, not ownership.
