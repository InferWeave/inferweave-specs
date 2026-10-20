# 43 — Per-GPU Placement and Hot-Swap

## Goal

A multi-accelerator node serves more than one model, and demand moves between them faster than
nodes can be acquired or released. This document specifies how capacity moves between models
**one GPU at a time**, without taking any model offline, without killing work that a bounded
drain could have finished, and without thrashing a card between models whose load cost it cannot
repay.

It extends the fleet autoscaler — whose rebalance already moves capacity between models as a
swap — from whole nodes to individual GPUs, and specifies the node side that executes a swap.
It does not choose which model is in demand; that stays with the autoscaler's utilisation
sample.

## When the specification was the defect

The fleet autoscaler (`InferWeave/inferweave#302`) was implemented from an issue, with no
specification. Nothing in `03_NODE_BOOTSTRAP_DEPLOYMENTS.md` or `05_ROUTING_AFFINITY.md` said
who decides which model occupies a GPU, how long it must stay, or what happens to requests on a
GPU that is changing model.

An implementer following those documents literally would leave the runtime's own model router
deciding placement. On the host measured below, that router evicts by least-recent use, knows
nothing about devices, and stops an instance by force after a fixed timeout with no drain. The
sections that follow exist because each of those behaviours was observed.

## Measured basis

One host: two AMD Radeon AI PRO R9700 (32 GB each, Vulkan/RADV), llama.cpp model router
serving Qwen3.8-27B variants. Router behaviour was read from llama.cpp source at commit
`82d6bb2` (`tools/server/server-models.cpp`); timings were measured on the host's production
router binary, whose exact commit was not recorded. Measured 2026-09-12 unless dated otherwise.

**A least-recently-used runtime router thrashes a shared card.** With `models-max 1` and every
model pinned to one card, the router spawned a model instance 82, 19, 60 and 52 times per day
(2026-09-02 to -05). On 2026-09-04 it served 829 requests for one model and 1,043 for another
through that single slot; every alternation reloaded weights and discarded the prompt cache.

**Runtime eviction is not device-aware.** The router's scheduler picks the instance with the
oldest `last_used`, regardless of which device it occupies. With one model per card, a request
for a third model can evict the instance on the *other* card and then fail to fit on the
occupied one.

**Runtime unload does not drain.** Unload sends the instance an exit command and force-kills it
after `stop-timeout` (default 10 s). Five instances were force-killed this way on 2026-09-02
during model switches.

| operation | measured |
|---|---|
| unload, instance idle | 0.5–1.2 s |
| unload, instance serving | 332 s (one occurrence) |
| load, 27B Q4 lane with vision projector and drafter, 262,144-token context | 6.6–7.3 s; 17.2 s on the first load after boot |
| load, 27B Q6 lane with drafter, 131,072-token context | 7.9–8.3 s |
| load, mixture-of-experts model with host-resident experts | 62.2 s |

Load times are spawn-to-listening with the model files in the page cache, except the first
post-boot load.

**A device setting does not pin every component.** With only the main-model device set, the
drafter and the vision projector allocated on the other card: one instance held 1.8 GB of device
memory on the neighbouring card, another 1.1 GB of device memory plus 1.1 GB of host-mapped
memory. Setting the drafter and projector devices explicitly reduced cross-card device memory to
0 MB for both and raised the first instance's decode from 46.1–48.3 to 49.7–51.9 tok/s (context
depth under 500 tokens, 300-token generations, temperature 0). Cross-card allocation was found
only by per-process device memory accounting; neither instance reported an error.

**A runtime name addresses exactly one instance.** Router aliases must be unique across loaded
models, so two instances of one deployment cannot share a name. Balancing across instances
cannot be delegated to that runtime.

## Terms

- **GPU claim:** the autoscaler's record that one stable GPU (`26_RESOURCE_IDENTITY_REDISCOVERY.md`)
  on a held node runs one deployment.
- **Swap:** replacing a GPU claim's deployment with another.
- **Dwell:** the time a GPU must keep its current deployment before it may be swapped.
- **Healthy instance:** a service instance in `HEALTHY` (`03_NODE_BOOTSTRAP_DEPLOYMENTS.md`) that
  is admitting requests. `STARTING`, `WARMING` and `DRAINING` instances are not healthy.
- **Availability floor:** the minimum number of healthy instances a catalogued model keeps.

## GPU claims

A node claim records the node's acquisition and its minimum hold, as today. It holds one GPU
claim per GPU:

- stable GPU identity;
- deployment fingerprint;
- `loaded_at`: when this deployment last became healthy on this GPU;
- swap state and, while a swap is in progress, the previous deployment, the target deployment and
  each phase deadline.

The node minimum hold governs acquiring and releasing **nodes**. Dwell governs **swaps**. Neither
shortens the other.

A rebalance names `{node, gpu, from, to}` and moves exactly one GPU. It never changes the number of
held GPUs.

`loaded_at` and every swap deadline live on the claim, so a restarted controller cannot shorten a
dwell or forget a swap in progress.

## Per-model placement policy

Every catalogued model carries:

| key | default | meaning |
|---|---|---|
| `min_live_instances` | `1`; never below 1 for a catalogued model | availability floor |
| `min_dwell_secs` | derived, below | how long a GPU keeps this model before it may be swapped away |
| `drain_timeout_secs` | `120` | how long in-flight requests get when a GPU running this model is swapped |
| `load_timeout_secs` | 3 × measured p95 load time | a load exceeding it is a failed load |
| `swappable` | `true` | `false` pins the model: a GPU running it is never chosen as a swap donor |

A model's `min_dwell_secs`, when not configured, is:

```text
max(policy.min_gpu_dwell_secs, policy.dwell_load_multiple × p95_load_secs(model, gpu_class))
```

with `policy.min_gpu_dwell_secs = 300` and `policy.dwell_load_multiple = 10`. Applied to the loads
measured above: 300 s for the 27B lanes, about 10 minutes for the mixture-of-experts model. A model
that takes 25 minutes to load dwells about 4 hours unless configured otherwise.

These three defaults are **policy, not measurement**. The multiple bounds reload downtime to about
a tenth of a GPU's time on a model; it has not been tuned against fleet traffic.

`p95_load_secs` is measured per deployment and GPU class from the node's own load events
(Observability) and persisted with the deployment's capability record. **A model with no measured
load time is never chosen as a swap donor**, because the cost of bringing it back is unknown. It may
be a swap target; that load produces its first measurement.

## Availability floor

This section implements invariant 43.

1. Only healthy instances count toward a model's floor.
2. A GPU may be chosen as a swap donor only if its model keeps at least `min_live_instances` healthy
   instances on **other** GPUs for the whole swap.
3. A model at its floor is never a donor. To free a GPU running such a model, the autoscaler first
   raises another instance of it elsewhere and waits until that instance is healthy.
4. A catalogued model is always live. A model outside the catalogue may be advertised as
   known-but-cold and warmed on demand (`docs/site-gateway-capabilities.md`).

Consequence: a node that is the only host of a model cannot swap that model's GPU away. Capacity for
it moves only once another healthy instance exists.

## Swap lifecycle

A swap moves the GPU claim through the resolver states of `03_NODE_BOOTSTRAP_DEPLOYMENTS.md`.

1. **Decide.** The autoscaler emits the rebalance and persists the swap intent on the GPU claim:
   previous deployment, target deployment, phase deadlines.
2. **Drain** (`DRAINING`). The instance stops admitting. Routing stops selecting it. In-flight
   requests continue until they finish or `drain_timeout_secs` of the **donor** model elapses.
   Requests still running at the deadline are cancelled with the error below.
3. **Stop** (`STOPPED`). The node unloads the deployment through the runtime. The runtime's own stop
   timeout is a last resort, never the drain.
4. **Start** (`STARTING`). The node loads the target deployment with **every runtime component** —
   weights, drafter, vision or audio projector — pinned to the claimed GPU.
5. **Warm** (`WARMING`). Health check, then a real request through the full admission path
   (invariant 38).
6. **Healthy** (`HEALTHY`). The instance is advertised; `loaded_at` is recorded; dwell begins.

Cancelled requests carry `503`, reason code `INSTANCE_DRAINED`, `"retryable": true` and a
`retry_after_ms` estimate. The availability floor guarantees another healthy instance exists, so the
gateway reroutes within the bounded retry budget of `06_BACKPRESSURE_RETURN_TO_SENDER.md`. Sticky
sessions reroute with reason `drain` (`05_ROUTING_AFFINITY.md`).

A restarted node or controller resumes a swap from the persisted intent: a drain past its deadline
proceeds to stop; a start with no live runtime process restarts the load; a state it cannot
establish returns the GPU to the previous deployment.

## Failure handling

| failure | handling |
|---|---|
| drain deadline reached | cancel remaining requests with `INSTANCE_DRAINED`; record the count; proceed |
| target load fails: non-zero exit, failed health check, or `load_timeout_secs` exceeded | return the GPU to the previous deployment; record a start failure for the target model, which suspends it after the autoscaler's consecutive-failure threshold; dwell restarts when the rollback is healthy |
| out of memory on load, or below the admitted envelope | classify `GPU_OOM` or `GPU_OOM_BELOW_ADMISSION` (`36_GPU_WATCHDOG_RESCUE.md`); mark the deployment and GPU class as not fitting until requalified; roll back; never retry the same placement in a loop |
| rollback fails | enter the quarantine path of `31_RESOURCE_HEALTH_QUARANTINE.md` and `36_GPU_WATCHDOG_RESCUE.md`; count the GPU as lost capacity and re-evaluate every floor without it |
| runtime receives a request for a model that is not loaded | refuse with a retryable `503`; it never loads or evicts on its own |

The previous deployment is the known-good target of `36_GPU_WATCHDOG_RESCUE.md` principle 4 until
the target is healthy.

## Runtime constraints

A runtime used on a swapping node:

- has its own on-demand loading and eviction **disabled**. The autoscaler is the only placement
  authority; a runtime that evicts on request arrival reintroduces the least-recently-used thrash
  measured above.
- exposes one addressable instance per (deployment, GPU) pair, under a distinct name where the
  runtime requires unique names. Balancing across instances of one deployment is routing's job.
- pins every component of a deployment to the claimed GPU, and the node verifies placement from
  per-process device memory accounting after load. A component on another device is a failed load.
- is sized with the device memory headroom of `39_INFERENCE_RUNTIME_TUNING.md`; a swap never places a
  deployment into less headroom than its tuning record was measured with.

## Observability

Every autoscaler decision already carries the numbers that caused it. A swap decision additionally
carries: node, GPU, from and to deployment, per-model busy slots, per-model healthy instances
against each floor, and dwell elapsed against dwell required.

A swap emits events for each phase, correlated by swap ID (`09_OBSERVABILITY_RECEIPTS.md`):

- drain: in-flight at start, finished, cancelled;
- unload, load and warm durations;
- outcome: `healthy`, `rolled_back` or `quarantined`.

Measured load durations feed `p95_load_secs`, which feeds derived dwell.

A pass that does not swap says why:

- `GpuDwell { pending, next_eligible_at }`: every candidate GPU is inside its dwell;
- `AvailabilityFloor { model, healthy, floor }`: the only donors would breach a floor;
- `UnmeasuredLoadCost { model }`: the only donor has no measured load time.

## Required tests

Proof status: `owed` for every item (`P3-T23`, `P3-T24`, `P3-T25`).

Autoscaler, pure policy:

- a GPU inside its dwell is never a donor, and a controller restarted from persisted claims cannot
  shorten it;
- derived dwell equals `max(300, 10 × p95)`; a configured `min_dwell_secs` wins; a model with no
  measured load time is never a donor;
- property: over generated fleets and decision sequences, no model ever has fewer healthy instances
  than its floor, and a model at its floor is never a donor;
- a GPU running a model at its floor is freed only after another instance of that model is healthy;
- each new hold reason is emitted with its numbers;
- the autoscaler's existing invariants still hold.

Node executor, against a real runtime:

- a request that completes within the drain deadline finishes before unload;
- a request that exceeds it receives `503` `INSTANCE_DRAINED` with `retryable: true`;
- a failed load returns the GPU to the previous deployment and records a start failure;
- out of memory on load is classified and not retried into the same placement;
- killing the executor during `STARTING` resumes correctly from the persisted intent;
- weights, drafter and projector are all allocated on the claimed GPU, verified from per-process
  device memory accounting;
- with runtime autoload disabled, a request for an unloaded model is refused and evicts nothing.

Live evidence:

- on a multi-GPU node under load, swapping a GPU to a second instance of another model while a
  healthy instance of the donor model exists elsewhere: no model's healthy count falls below its
  floor at any sample, and every decision and phase event is recorded.

## Read-only telemetry and Nibbler qualification boundary

The 2026-10-20 observability approval includes evaluating the already registered
Nibbler for dynamic capacity. A hardware-only registration does not qualify it
as a serving instance, swap donor or availability-floor replacement. New capacity
observations and context offers are read-only inputs, never placement commands.
Only the existing owner rebalancer may act, after the runtime/executor, full-path
admission, watchdog/rollback and applicable floor/dwell proofs pass. Spec64's
single-engine restrictions remain; this approval does not add a live-swap path.
