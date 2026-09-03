# 30 — Workload Contracts and Resource Lifecycle Event Log

## Workload Contract

Every schedulable request/job exposes enough intent for safe placement.

Fields may include:

```text
workload_class
requested_model/capabilities
input/context estimate
max_output_tokens
expected_duration
deadline
interactive
restartable
checkpointable
interruptible
streaming
session_affinity
privacy/policy
priority
quality_floor
latency_target
throughput_target
max_cost/contribution policy
```

The router uses these fields to decide whether an ephemeral/owner-preemptible resource is safe.

A long non-restartable session must not be assigned to an allocation that is likely to disappear first.

## Resource Lifecycle Event Log

Maintain append-oriented events for important resource state transitions:

```text
RESOURCE_DISCOVERED
RESOURCE_RECOGNIZED
RESOURCE_REPLACED
ALLOCATION_STARTED
WORKER_CONNECTED
WORKER_RECONNECTED
HARDWARE_CHANGED
SOFTWARE_CHANGED
DEPLOYMENT_ASSIGNED
ARTIFACT_FETCH_STARTED
ARTIFACT_READY
MODEL_LOADING
MODEL_WARMING
READY
SERVING
BENCHMARKING
DEGRADED
QUARANTINED
RECOVERED
DRAINING
PREEMPTED
DISCONNECTED
ALLOCATION_ENDED
```

Each event includes:
- event_id;
- occurred_at;
- provider/cluster/site;
- host/gpu identities;
- allocation/worker/connection if relevant;
- before/after state;
- reason/code;
- deployment/software fingerprint;
- related request/benchmark IDs where appropriate;
- content-free diagnostic metadata.

## Why

This supports historical questions such as:

```text
Why did gpu_X slow down during allocation Y?
What changed between two benchmark runs?
Was a request cancelled because of Slurm expiry or GPU health?
When did this physical GPU begin throttling?
```

Event history is never deleted just because the ephemeral worker disconnects.
