# InferWeave Protocol v1 — lifecycle

Lifecycle events are first-class protocol objects (`schemas/v1/events/event.json`), ordered per
source by a monotonically increasing `sequence`. Consumers MUST tolerate out-of-order federation
delivery and reconnect with a cursor (`Last-Event-ID` or equivalent); expired cursors trigger
snapshot reconciliation.

## Model residency

```text
absent → downloading → cached/staging/loading → warming → ready
      → degraded → draining → unloading → cached/absent
      → failed
```

Event types: `MODEL_DOWNLOAD_STARTED`, `MODEL_DOWNLOAD_COMPLETED`, `MODEL_LOAD_REQUESTED`,
`MODEL_LOADING`, `MODEL_READY`, `MODEL_DRAINING`, `MODEL_UNLOADING`, `MODEL_UNLOADED`,
`MODEL_LOAD_FAILED`, `MODEL_EVICTED`, `MODEL_REBALANCED`. Reasons: `demand`, `operator_request`,
`autoscale`, `rebalance`, `idle_timeout`, `memory_pressure`, `allocation_loss`, `preemption`,
`runtime_failure`, `hardware_failure`, `maintenance`, `upgrade`, `cache_pressure`, `unknown`.

## Allocation

```text
requested → pending → allocating → allocated → booting → staging → runtime_starting → ready
         → draining → preempting → terminated
         → lost → terminated/pending
```

## Event namespaces

`gateway.*`, `node.*`, `device.*`, `allocation.*`, `runtime.*`, `model.*`, `artifact.*`,
`routing.*`, `queue.*`, `capacity.*`, `autoscale.*`, `rebalance.*`, `health.*`, `request.*`,
`security.*`.

## Backpressure

Event streams MUST support slow consumers (bounded buffers, replay storage, or disconnect +
cursor recovery); a slow consumer never causes unbounded memory growth.
