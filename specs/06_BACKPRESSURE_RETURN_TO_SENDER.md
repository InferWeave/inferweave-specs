# 06 — Backpressure and Return-to-Sender

## Rule

No layer may convert downstream rejection into an unbounded local queue.

Topology may include:
client/local proxy → site gateway → regional gateway/controller → global/control layer → node.

Every layer has explicit queue/admission thresholds. When a downstream layer cannot accept work, capacity pressure propagates toward the original sender or another eligible route is tried within a bounded budget.

## HTTP semantics

- `503 Service Unavailable`: infrastructure/model/context/capacity unavailable.
- `429 Too Many Requests`: user/API-key/rate/FairShare restriction.
- `409 no_eligible_capacity` may be used by native route-preview/constraint APIs when no candidate can satisfy a hard requested constraint without actually attempting inference.

For actual OpenAI-compatible inference, prefer the 503/429 split above.

Include:
- retryable boolean;
- reason code;
- bounded `Retry-After` / retry-after-ms estimate when meaningful;
- model/deployment intent;
- request ID.

## Bounded retries

Retry/failover has:
- maximum candidates;
- maximum wall-clock admission budget;
- idempotency rules;
- no duplicate accounting;
- cancellation propagation.

## Client disconnect

Streaming proxy immediately cancels/relinquishes upstream work when the client disconnects unless an explicitly durable async job was requested.
