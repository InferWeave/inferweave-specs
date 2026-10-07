# InferWeave Protocol v1 — federation

A gateway may register with another gateway at arbitrary recursive depth. Each federated object
carries provenance: `origin_gateway_id`, `reporting_gateway_id`, `federation_path`.

## Rules

- **Loop prevention**: a gateway SHALL reject a federation path containing itself.
- **Independent deployments**: two gateways advertising the same `model_id` keep independent
  capacity, health, and performance.
- **Partial participation**: a remote gateway advertising only model/capabilities/slots
  participates without artifact or hardware; missing fields are `unknown`, not inferred.
- **Staleness**: disconnected capacity becomes stale/unavailable and is never advertised live.
- **Reconciliation**: reconnect reconciles without duplicate runtime identity or duplicate event
  replay.
- **Trust**: never auto-promoted by passing through a trusted gateway.

## Provenance

```json
{ "origin_gateway_id": "gateway-slurm", "reporting_gateway_id": "gateway-lab",
  "federation_path": ["gateway-slurm", "gateway-lab"], "source": "reported" }
```

## Snapshot + delta

Observability consumers retrieve a consistent snapshot (`snapshot_id`, `generation`,
`generated_at`) then receive events/deltas; all contained state belongs to one generation.
