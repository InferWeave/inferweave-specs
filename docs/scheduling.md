# InferWeave Protocol v1 — scheduling

The protocol describes scheduling-relevant state without assuming a scheduler.

## Capacity

Structured capacity (`resources/capacity.json`): `requests`, `contexts`, `kv_cache`,
`gpu_memory`, `compute`; a compatibility `slots` integer may also exist. Explicit GPU memory
accounting (`total`, `weights`, `kv_cache`, `runtime_cache`, `active_requests`, `reserved`,
`other_models`, `system`, `unaccounted`, `free`) renders directly upstream.

## Seats

A **seat** is an abstract schedulable unit: the ability to accept an additional workload under
specified conditions (context size, modality, model, memory, concurrency, batching, priority).
Seats are not all equivalent.

## Admission

Outcomes: `accepted`, `queued`, `rejected`, `redirected`, `fallback`, `throttled`. A workload
whose context ceiling, modality, license, deny rule, or exact deployment requirement is unknown
is **not admissible** (invariants 6, 36). Routing respects the availability floor (invariant 43)
and never routes experimental serving profiles/models via ordinary production routing until
qualified (invariant 28).

## Placement

Hardware requirements and topology-sensitive placement distinguish `1x80GB` from `4x24GB`.
Support `required`/`preferred`/`avoided`/`forbidden` placement attributes and distributed
placement (one model over several GPUs or a worker group).

## Workload classes

`interactive`, `batch`, `background`, `system`, `benchmark`, `probe`, `maintenance`. Probes MUST
NOT count as user demand, reset idle timeout, or distort analytics. Deadlines and cancellation
are supported and propagate through federation.
