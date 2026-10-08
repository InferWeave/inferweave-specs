# InferWeave Protocol v1 — events

Events are first-class protocol objects (`schemas/v1/events/event.json`):

```json
{ "event_id": "...", "event_type": "...", "source_id": "...", "sequence": 231,
  "timestamp": "...", "trace_id": "...", "correlation_id": "...", "causation_id": "...",
  "payload": {} }
```

## Ordering and delivery

- Ordering is guaranteed per source by a monotonically increasing `sequence`.
- Global ordering is NOT guaranteed; consumers tolerate out-of-order federation delivery.
- Consumers reconnect with a cursor (`Last-Event-ID`); expired cursors trigger snapshot
  reconciliation.
- Event streams support slow consumers via bounded buffers, replay storage, or disconnect +
  cursor recovery.

## Namespaces

`gateway.*`, `node.*`, `device.*`, `allocation.*`, `runtime.*`, `model.*`, `artifact.*`,
`routing.*`, `queue.*`, `capacity.*`, `autoscale.*`, `rebalance.*`, `health.*`, `request.*`,
`security.*`.

## GPU memory events (1.1.0)

`specs/46_GPU_MEMORY_INTELLIGENCE.md` §7 adds a capability-gated feed (`iw.rebalance-decisions/1`)
with its own camelCase envelope (`schemas/v1/events/gpu-memory-event.json`): `gpu.memory.*`,
`runtime.*` placement and `rebalance.*` decision events, idempotent by `eventId`, resumed by a
`<producerEpoch>:<sequence>` cursor. The vocabulary is frozen in
`contracts/protocol-v1/gpu-memory-events.json`.

## Snapshot + delta

Observability consumers SHOULD retrieve a consistent snapshot then receive events/deltas. A
snapshot SHALL include `snapshot_id`, `generation`, `generated_at`; all contained state belongs
to the same generation.

## Metrics

Metrics use an extensible schema (`events/metric.json`) with provenance, windows,
distributions, and counters; samples carry source type, producer, and confidence. Request
metrics include `queue_ms`, `ttft_ms`, `duration_ms`, `input_tokens`, `output_tokens`,
`tokens_per_second`, `cache_hits`, `cache_misses`.
