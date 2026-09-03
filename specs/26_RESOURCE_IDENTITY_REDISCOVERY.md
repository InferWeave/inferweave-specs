# 26 — Stable Resource Identity, Ephemeral Worker Identity and Rediscovery

## Problem

A Slurm job is temporary, but the underlying machine/GPU may return many times.

InferWeave must distinguish:

1. the **provider/site**;
2. the **stable physical host**;
3. each **stable physical GPU/resource**;
4. the **temporary Slurm allocation**;
5. the **temporary InferWeave worker process/session**.

Performance history belongs primarily to stable resources + immutable deployment/software fingerprints, not to one temporary worker process.

## Identity Hierarchy

```text
provider_id
  └── cluster_id
       └── host_id                     stable physical/logical host
            ├── gpu_id                 stable GPU
            ├── gpu_id
            └── host_generation
                 └── allocation_id     temporary Slurm allocation
                      └── worker_instance_id
                           └── connection_id
```

## Stable IDs

### `provider_id`
Identity of the contributing organization/site/operator.

### `cluster_id`
Stable identity of one scheduler/cluster domain.

### `host_id`
Stable InferWeave identity for the scheduler node / physical host.

Prefer an explicit site-persisted identity record.

Recommended resolution order:
1. existing signed InferWeave host identity persisted in approved shared/local storage;
2. site controller mapping of `(cluster_id, scheduler_node_name)` to `host_id`;
3. gateway reconciliation using stable scheduler name + hardware fingerprint;
4. create a new host identity if no safe match exists.

Scheduler hostname alone is an identity hint, not authentication.

### `gpu_id`
Stable identity for a physical GPU where hardware exposes a stable device UUID/serial.

Preferred derivation:
- provider-scoped mapping of vendor device UUID/serial;
- otherwise a persisted site mapping;
- PCI address is only a fallback hint because topology can change.

For virtual GPU/MIG/partitioned resources, distinguish:
- physical GPU identity;
- partition/slice identity;
- allocation-visible resource identity.

## Host Generation

A scheduler hostname may survive hardware replacement.

Therefore store:

```text
host_id                 stable site/scheduler concept
host_generation_id      changes when material hardware identity changes
```

If `gpu-node-17` is rebuilt with new GPUs:
- preserve relationship to `host_id`;
- create a new generation;
- do not pretend old GPU performance applies to the new hardware.

A change in the number of visible GPUs is a material hardware identity change and creates a
new generation, whether devices were added or lost. Watchdog expectations, resource envelope
and published context ceiling are all re-derived for the new generation rather than
inherited.

## Ephemeral IDs

### `allocation_id`
Uniquely identifies the Slurm allocation within a cluster.

Canonical namespace:

```text
slurm:<cluster_id>:<job_id>:<array_task_or_step_if_needed>
```

Do not assume job ID is globally unique across clusters.

### `worker_instance_id`
Random ULID/UUID created for each InferWeave worker process start.

A requeued allocation/process restart creates a new worker instance even if `allocation_id` remains related.

### `connection_id`
Unique gateway connection/session instance.

## Registration / Rediscovery

At every worker start:

1. authenticate with allocation/site-scoped credentials;
2. submit cluster/scheduler identity hints;
3. submit current hardware discovery;
4. submit stable GPU UUIDs where available;
5. gateway resolves/creates stable `host_id` and `gpu_id`s;
6. gateway detects material hardware changes;
7. gateway creates new `worker_instance_id` session record;
8. gateway associates the new allocation/worker with historical resources;
9. worker advertises only GPUs actually allocated/visible now;
10. current software/runtime/model fingerprints are recorded fresh.

## Example

Day 1:

```text
host_id = host_123
gpu_id = gpu_A
allocation = slurm:cluster-west:98311
worker = worker_01
R9700 + runtime X + model Q + profile P
```

Day 7, same scheduler node/GPU:

```text
host_id = host_123
gpu_id = gpu_A
allocation = slurm:cluster-west:99107
worker = worker_22
```

InferWeave immediately has access to historical evidence for `host_123/gpu_A`, but still re-discovers:
- current driver/runtime;
- power/thermal settings;
- topology;
- model cache;
- health.

If the exact deployment fingerprint matches, old benchmark evidence remains applicable with recency/confidence rules.

## Performance History Keys

Benchmark and serving data must retain:

```text
provider_id
cluster_id
host_id
host_generation_id
gpu_id[]
hardware_fingerprint
software_fingerprint
deployment_fingerprint
allocation_id
worker_instance_id
request_id / benchmark_run_id
```

This allows:
- lifetime performance history per physical GPU;
- per-driver/runtime comparisons;
- degradation detection;
- thermal/power trend analysis;
- identifying unusually good/bad nodes of the same GPU class;
- contribution history across many ephemeral reservations.

## Recommendation Reuse

When a known GPU returns:
- load its most recent qualified recommendations;
- check current hardware/software fingerprint;
- reuse exact-match profiles immediately or after a small confirmation smoke;
- downgrade evidence if software/driver/settings changed;
- schedule requalification if needed.

This avoids repeating expensive full benchmark suites every reservation.

## Model Cache Rediscovery

Registration reports artifact cache inventory.

The gateway can prefer a deployment already cached on this node/site.

This is especially important for short Slurm reservations.

## Duplicate Detection

Gateway must detect:
- same GPU accidentally advertised by two worker instances;
- stale prior allocation still connected;
- requeue/process restart;
- scheduler allocation overlap errors.

Only one authoritative routable lease for a physical allocation-visible GPU should exist unless explicit partitioning allows otherwise.

## Authentication vs Identity

Never trust stable IDs alone for authentication.

Authentication should use:
- site enrollment;
- short-lived allocation credentials;
- signed gateway tickets.

Stable identity exists to correlate history.

## Data Retention

Do not delete host/GPU history merely because a worker disconnects.

Worker/allocation records become historical.

Stable host/GPU resource records persist and accumulate:
- uptime;
- contribution;
- benchmarks;
- serving observations;
- errors;
- power/thermal characteristics;
- software/deployment history.
