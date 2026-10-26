# 33 — Resumable Benchmark DAG

## Goal

Benchmark/qualification work must survive Slurm preemption and other ephemeral-resource loss.

## Decomposition

```text
benchmark_campaign
  └── suite
       └── deployment/profile
            └── workload
                 └── case
                      └── repetition
```

Each leaf is:
- immutable;
- independently schedulable;
- idempotent;
- small enough to fit common backfill windows;
- committed as soon as complete.

## Scheduler

Workers lease benchmark leaves with deadlines.

A lease includes:
- benchmark task ID;
- required hardware/resource class;
- deployment fingerprint;
- estimated runtime;
- input artifact references;
- result schema;
- lease expiry.

If a worker disappears:
- incomplete lease expires;
- task returns to READY;
- completed samples remain committed.

## Partial campaigns

A campaign can produce provisional evidence before 100% completion, but recommendation confidence reflects missing samples.

## Slurm integration

Before assigning a leaf:

```text
estimated setup/load time
+ estimated case runtime
+ result flush margin
< remaining safe allocation time
```

Prefer already-loaded/cached profiles.

## Checkpointable long evaluations

For evaluations that cannot be decomposed sufficiently, define explicit checkpoint artifacts with immutable continuation metadata.

## Dashboard

Show:
- campaign completion;
- pending/running/expired tasks;
- resource classes;
- confidence achieved;
- remaining expected compute;
- preemption losses;
- resume history.

## Benchmark conductor contract (IW-BENCH-003)

The conductor uses bounded durable states `READY`, `LEASED`, `RUNNING`,
`SUCCEEDED`, `FAILED`, `CANCELLED`, and `RETRY_PENDING`. Immutable leaf
identity binds the model/runtime fingerprint, workload/sampling and resource
budget; changing a worker's endpoint does not create a new sample identity.
Completed results are journaled before idempotent record-store import.

A fresh authenticated gateway observation must explicitly report idle, healthy,
and benchmark-leaseable capacity. Free VRAM is not authorization. The gateway
atomically rechecks owner priority, deployment availability floors and current
registration when acquiring a fenced lease. Lease intent is persisted before
external side effects. Node admission and scheduler authority remain independent.
The lease records GPU identities, deployment fingerprint, KV/context and CPU
budgets, the prior gateway deployment and a conservative allocation deadline.
Progress renews an inactivity lease, never the underlying scheduler allocation.
Setup, workload and flush margin must fit before the safe allocation end.

A typed executor starts and polls one sweep leaf using the persisted lease and
leaf identities. Queue input carries no shell commands. Each start independently
checks current time, lease ownership and deployment attestation. Stop fences all
workers before durable result reconciliation; ambiguous starts and lost replies
must be reconciled, not treated as proof that no worker ran.

Completion, failure, cancellation, expiry and graceful shutdown retain the node
fence through: stop owned engines/workers; release owned scratch; restore the
prior deployment; verify that exact deployment through real authorization and
admission; release the gateway lease. Final release atomically rechecks that
proof. Failed or timed-out recovery keeps the node unschedulable and is visible
as recovery required. A process crash is not a graceful return: the adapter
must retain fencing and recover abandoned ownership independently.

The private operator dataset exposes campaign counts, queue states, lease/GPU
placement, preemption loss and verified-return status. Prompts, outputs,
credentials and result bodies stay inside the authenticated evidence store.
Implementation constants for polling, queue caps and recovery deadlines are
operational bounds, not measured hardware envelopes.
