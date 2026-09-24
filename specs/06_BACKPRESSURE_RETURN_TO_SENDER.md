# 06 — Backpressure and Return-to-Sender

## Rule

No layer may convert downstream rejection into an unbounded local queue.

Topology may include:
client/local proxy → site gateway → regional gateway/controller → global/control layer → node.

Every layer has explicit queue/admission thresholds. When a downstream layer cannot accept work, capacity pressure propagates toward the original sender or another eligible route is tried within a bounded budget.

## HTTP semantics

- `503 Service Unavailable`: infrastructure/model/context/capacity unavailable.
- `429 Too Many Requests`: user/API-key/rate/FairShare restriction or bounded
  admission-queue saturation before dispatch.
- `409 no_eligible_capacity` may be used by native route-preview/constraint APIs when no candidate can satisfy a hard requested constraint without actually attempting inference.

For actual OpenAI-compatible inference, prefer the 503/429 split above.

Include:
- safe explanatory message;
- retryable boolean;
- replay-safe boolean and request state (`not_started`, `queued`, `dispatched`,
  `streaming`, or `unknown`);
- stable condition `code` and compatible `reason` (equal when both are present);
- readable action and frozen action code;
- bounded `Retry-After` / retry-after-ms estimate when meaningful;
- scope (`request`, `model`, `caller`, or `global`);
- model/deployment intent;
- request ID.

The additive OpenAI-compatible fields are published as shared contracts in
`contracts/backpressure-action-codes.json` and
`contracts/backpressure-conformance-v1.json`. Existing reason codes remain the
condition vocabulary; action codes separately tell a client what to do.

## Frozen action vocabulary

| Action code | Client action |
| --- | --- |
| `IW-ACT-BACKOFF` | Wait at least the declared delay, add positive jitter, then reconsider. |
| `IW-ACT-REDUCE-CONCURRENCY` | Lower parallel caller concurrency before reconsidering. |
| `IW-ACT-RETRY-ALTERNATE` | Try another eligible route within the same finite budget. |
| `IW-ACT-FIX-REQUEST` | Correct syntax, parameters, endpoint, or model identity. |
| `IW-ACT-AUTHENTICATE` | Supply or refresh valid credentials. |
| `IW-ACT-REQUEST-ACCESS` | Obtain permission or quota. |
| `IW-ACT-RESOLVE-CONFLICT` | Reconcile an idempotency or session conflict. |
| `IW-ACT-REDUCE-INPUT` | Reduce input or reservation to the published ceiling. |
| `IW-ACT-DO-NOT-RETRY` | Surface the terminal error without automatic replay. |

The status mapping is: `400`/`404`/`422` fix the request, `401` authenticate,
`403` request access, `409` resolve the conflict, and `413` reduce input.
`408`, `429`, `500`, `502`, `503`, and `504` may carry bounded transient
guidance only when the server can state it safely. `model_queue_full` with
`scope=model` is specifically a `429` admission-queue restriction: the model is
known and the request remains queued rather than lacking infrastructure.
An unknown model is `404`; a known model with no usable capacity is `503` and
must not be reclassified as `429`. This preserves the canonical distinction
between admission/policy restriction and infrastructure/capacity absence.

Producer-conformant vectors use only the documented condition/status/action/retry
combinations below. Synonyms and success statuses are not condition vocabulary.
Explicit client-input vectors are marked separately and may describe rejected or
hostile input without extending the producer contract.

| Condition | Status | Action code | Retryable |
| --- | ---: | --- | --- |
| `invalid_request` | 400 | `IW-ACT-FIX-REQUEST` | false |
| `authentication_required` | 401 | `IW-ACT-AUTHENTICATE` | false |
| `access_denied` | 403 | `IW-ACT-REQUEST-ACCESS` | false |
| `model_not_found` | 404 | `IW-ACT-FIX-REQUEST` | false |
| `request_timeout` | 408 | `IW-ACT-BACKOFF` | true |
| `idempotency_conflict` | 409 | `IW-ACT-RESOLVE-CONFLICT` | false |
| `CONTEXT_WINDOW_EXCEEDED` | 413 | `IW-ACT-REDUCE-INPUT` | false |
| `invalid_inference` | 422 | `IW-ACT-FIX-REQUEST` | false |
| `model_queue_full` | 429 | `IW-ACT-BACKOFF` | true |
| `caller_concurrency` | 429 | `IW-ACT-REDUCE-CONCURRENCY` | false |
| `internal_error` | 500 | `IW-ACT-DO-NOT-RETRY` | false |
| `invalid_upstream_response` | 502 | `IW-ACT-RETRY-ALTERNATE` | false |
| `NO_CONTEXT_CAPACITY` | 503 | `IW-ACT-RETRY-ALTERNATE` | true |
| `upstream_timeout` | 504 | `IW-ACT-RETRY-ALTERNATE` | true |

## Bounded retries

Retry/failover has:
- maximum candidates;
- maximum wall-clock admission budget;
- idempotency rules;
- no duplicate accounting;
- cancellation propagation.

Automatic replay additionally requires `retryable=true`, `replay_safe=true`,
no committed output, a documented action, and remaining attempt and elapsed
budgets. `dispatched`, `streaming`, and `unknown` states are not replay-safe
without a separate inference idempotency guarantee. When header and body delay
are produced by a conformant server, their values match exactly after converting
the whole-second header to milliseconds. For hostile client input where they
disagree, the larger valid value is the minimum; clients stop instead of shortening
a server minimum that exceeds their remaining budget.

## Client disconnect

Streaming proxy immediately cancels/relinquishes upstream work when the client disconnects unless an explicitly durable async job was requested.
