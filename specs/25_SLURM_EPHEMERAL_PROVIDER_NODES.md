# 25 — Slurm Allocation-Scoped Ephemeral Provider Nodes

## Goal

A Slurm allocation can temporarily become InferWeave capacity.

The lifecycle is:

```text
Slurm grants GPU allocation
        ↓
InferWeave worker starts inside allocation
        ↓
worker connects outbound to InferWeave gateway/control plane
        ↓
worker registers stable resource identity + current allocation + live discovery
        ↓
gateway assigns desired model deployment(s)
        ↓
worker obtains/loads models
        ↓
worker advertises READY capacity
        ↓
InferWeave routes work to it
        ↓
reservation approaches expiry / Slurm preempts
        ↓
worker drains, flushes facts, unregisters/disconnects
```

Slurm remains the resource authority.

InferWeave never uses a cluster GPU outside an allocation.

## Allocation-Scoped Worker

Example:

```text
inferweave-node   --mode=slurm-allocation   --gateway=https://...   --allocation-id="$SLURM_JOB_ID"
```

The worker discovers only resources visible/allocated to the job.

It must never advertise GPUs outside that allocation.

## Registration Handshake

The worker sends:

```text
ProviderIdentity
StableHostIdentity
StableGpuIdentity[]
WorkerInstanceIdentity
SchedulerAllocation
HardwareFingerprint
SoftwareFingerprint
ConnectivityCandidates
ArtifactCacheInventory
RuntimeCapabilities
ReservationEnd
```

The gateway reconciles these with known historical resources before creating a new serving session.

## Gateway-Assigned Deployments

After registration the worker asks:

```text
What should I run with these resources until this allocation expires?
```

The gateway returns one or more `DesiredDeployment` assignments:

```text
deployment_id
model revision/hash
runtime/profile
artifact manifest
artifact locations
context envelope
workload classes
priority
qualification requirements
lease deadline
```

The selection considers:
- GPU/host capability;
- historical best recommendations for the same resource;
- model demand;
- current model availability elsewhere;
- artifact/cache locality;
- load/warmup time;
- remaining allocation lifetime;
- benchmark/qualification needs;
- contribution/fairness policies.

The gateway should assign useful deployments, not simply let each worker choose independently.

## Model Bytes Do Not Need to Flow Through Gateway

The gateway is the deployment authority, not necessarily the artifact byte server.

A `DesiredDeployment` should normally contain signed/pinned artifact references that the worker pulls from:
1. shared HPC filesystem/cache;
2. node-local persistent cache;
3. regional object/cache service;
4. model source/object store;
5. gateway artifact relay only as a fallback.

This preserves the direct-data-plane principle.

## Reservation Lifetime Awareness

Every ephemeral worker advertises:

```text
allocation_started_at
allocation_expires_at
latest_safe_new_session_at
expected_preemption_class
revocable = true
drain_grace
```

The gateway must factor remaining allocation time into:
- model selection;
- whether a new model is worth loading;
- session placement;
- benchmark placement.

Example:
A 20-minute remaining allocation should not spend 15 minutes downloading and warming a model.

## Drain / Disconnect

At reservation expiry or preemption signal:

1. immediately set state `DRAINING`;
2. reject new admissions;
3. notify gateway;
4. revoke/expire new route tickets;
5. finish or cancel according to grace policy;
6. flush prompt execution links, telemetry, benchmark samples and contribution facts;
7. persist final allocation summary;
8. exit/disconnect.

A normal Slurm expiry is not considered an infrastructure fault.

## Slurm Pool Controller

A site may optionally run a small controller that keeps low-priority InferWeave provider jobs submitted.

The controller requests capacity; Slurm decides when it runs.

Do not pollute core InferWeave routing with Slurm-specific scheduler behavior.

Use a generic:

```text
ResourceSchedulerAdapter
```

with Slurm as the first implementation.

## Low-Priority / Preemptible Capacity

Recommended site semantics:
- InferWeave jobs are low-priority/standby/backfill;
- normal HPC jobs win;
- InferWeave jobs can be cancelled/requeued/preempted;
- allocation lifetime is bounded;
- site admins own Slurm QOS/partition/account configuration.

## Connectivity

Compute nodes often cannot accept public inbound traffic.

Use standard InferWeave connectivity:

```text
outbound worker → gateway/control plane
direct client/proxy ↔ worker if network permits
regional/site relay otherwise
gateway relay only last resort
```

No public inbound compute-node port is required.

## Gateway replacement liveness

When an allocated worker follows a replacement gateway, its supervisor may
keep the old session alive until the new session is ready. Liveness supervision
belongs to the worker across that handoff, not to either gateway session:

- A healthy successor's heartbeat or rejoin attempt must keep the worker's
  liveness clock current. An old session waiting for that successor must not
  release the allocation because its own heartbeat stopped.
- The successor inherits the fact that the worker has already registered. If
  it blocks before registering with the replacement, the worker must still
  release the allocation after the bounded stall window.
- A withdrawn or completed successor must not leave a watchdog that can later
  terminate a healthy original session.

**Incident basis (Hive, 2026-10-12).** During a gateway replacement, two
workers followed the new address and their old sessions ended. Each worker
then logged `no heartbeat or rejoin progress for 300s` and exited, even though
the successor had registered with the new gateway. The old supervisor had
stopped updating its own clock while waiting for the successor, and its
watchdog terminated the whole process. Replacement Slurm jobs remained queued
for priority, turning that false liveness failure into missing model capacity.
Conformance must cover both a healthy successor beyond the old watchdog window
and a successor blocked before registration after the old session ends.

## Benchmark Synergy

Ephemeral Slurm capacity is valuable for global benchmark exploration.

When not serving higher-priority InferWeave work, an allocation may run:
- candidate model qualification;
- runtime/profile tuning;
- regression checks;
- recommendation exploration.

Benchmark tasks are resumable and preemptible.

## Security

- allocation-scoped short-lived worker credentials;
- credentials expire with allocation;
- no Slurm administrative credentials in worker;
- stable resource identity is separate from authentication;
- prompt/model caches obey site policy;
- no cross-allocation secrets;
- public data hides private scheduler job/user/account information.

## Expected Scale

InferWeave must safely handle rapid churn:
- many workers joining;
- many workers leaving;
- requeue onto different hosts;
- the same physical host returning repeatedly;
- the same host returning with different allocated GPU subsets.

Stale capacity must expire quickly and never remain routable after the allocation ends.


## Mandatory Apptainer substrate

Slurm allocation workers are deployed with Apptainer, not Docker.

The worker launch artifact must:
- use a pinned/signature-verified image;
- expose only Slurm-allocated GPUs;
- use current supported NVIDIA/AMD GPU integration;
- bind approved caches/shared filesystems;
- retain no identity solely inside the disposable container;
- support watchdog drain/restart inside the allocation;
- never require Docker socket/daemon access.
