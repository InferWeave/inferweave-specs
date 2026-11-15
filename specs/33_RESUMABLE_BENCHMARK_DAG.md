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

## Background execution policy (IW-BENCH-003)

Background campaigns use a live-reloaded, versioned policy. Each managed cluster
has an IANA timezone, daily execution interval and GPU percentage ceiling. The
ceiling is rounded down over fresh, healthy, authorized physical GPUs, including
cards already carrying benchmark work. It never includes another user's cluster
resources. Atomic benchmark reservations constrain aggregate use across workers;
they do not replace the owning allocation controller or Slurm authority.

Explicit cluster/node/model exclusions are hard constraints. A protected
incumbent model excludes its entire node. Existing healthy-instance floors and
owner priority remain in force. Shared execution obeys the same windows and
percentage ceiling; each participating card counts once, irrespective of how
many benchmark processes share it.

Before every cell, setup + estimated case + restoration + safety margin must fit
before the window closes. Policy, capacity, serving pressure and ownership are
rechecked while running. Work is interrupted and original services restored when
permission is withdrawn. Restoration remains permitted outside the execution
window and after exclusions change. Failed restoration remains recovery-required;
the scheduling deadline cannot be represented as proof of successful restoration.

Shared execution is limited to correctness, compatibility and exploratory work.
It requires a current owning-rebalancer grant under spec 46; physical free VRAM
alone is not permission. Known per-card peak requirements, serving-growth reserves,
fresh telemetry and safety headroom constrain admission independently. Capacity on
different cards is not pooled. Shared evidence never qualifies authoritative
exclusive latency or throughput results.

Worker events durably identify each exact cell and observed outcome before a
coordinator checkpoints it under its live claim attempt. Aggregate counts are not
cell evidence. Interrupted cells may resume; successful identities and artifact,
runtime, command, measurement-kind and execution-mode fingerprints remain stable.
Independent recovery preserves the original restoration obligation until the
database owner verifies cleanup and releases resource reservations. An expired
claim before the side-effect boundary can retry without inventing a restoration
obligation. An uncertain post-disruption outcome cannot.

Implementation/local tests do not satisfy the production GPU-memory qualification,
owned Slurm-step cancellation, target canary or interruption/recovery soak gates.

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
Tensor-parallel placement requires an explicitly attested compatible GPU-ID
group; missing topology must refuse multi-GPU placement.
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

## Guarded SpeedRequests execution profile

`contracts/benchmark-speed-execution.json` freezes the profile and acceptance IDs.
This is a specification, not a grant or proof of an implementation. Only
SpeedRequests is in scope; TaskSerial remains refused pending separate bounds work.
Ordinary constrained CLI, FakeEnv and generic leaf execution cannot run it. No
queue JSON, caller boolean, copied policy, durable PID or serialized lease conveys
authority. Mac, protected and unknown resources remain excluded; existing owner
priority, floors, scheduler and spec 46 memory rules remain independent.

Resolve the saved immutable leaf and actual private held owner, then open and hold
the prepared-leaf journal. Load a committed capsule before current policy, manifest,
readiness, corpus or catalogue checks. Import under that same held journal and
verify the canonical RecordID against the capsule and imported record. Recovery
remains available with policy absent/off, current manifest drift or an expired
execution deadline. Missing capsule is distinct from corruption, conflict and
unsupported version; only absence permits new-work admission. An import failure
retains the capsule and fence. A journal is neither authority to start work nor
proof that a child stopped. No rerun follows an ambiguous prior start.

New work requires a privately constructed capability tied to the actual resident
supervisor and its owned, unreaped Child, trusted current operator configuration,
exact saved leaf and held lease, NodeOwned acquisition, gateway admission and node
ownership, restoration fingerprint, verified endpoint and deployment. The child
independently checks this binding. A release channel is not authority by itself;
EOF before release refuses and loss during work triggers bounded cancellation.
Current operator and gateway policy must both allow the profile; absent or disabled
policy refuses new work, never recovery. Recheck live admission, ownership, floors,
CPU and per-request KV times concurrency, placement, safe allocation end, current
manifest and store precheck before a model client or HTTP call. Policy withdrawal
stops work through the existing supervisor path. A queued request or desired
configuration cannot override current authority. Unknown or failed child reap
keeps the lease fenced. Reap and verify the claimed RecordID before success;
Stop → Scratch → Restore → Verify → Release remains independently required.

The earlier withdrawal requirement did not freeze an ongoing policy-observation
interface. Following it by treating `admit-start` as a monitor would reject valid
owned work after its soft start window or while its engine is busy; treating
ownership status as policy permission would miss withdrawal. The private,
authenticated gateway operation `POST /api/bench/leases/continuation-policy`,
described by `contracts/benchmark-continuation-policy.json`, is the required
read-only current observation. Its strict request contains only `schema`, a fresh
32-character lowercase hexadecimal `nonce`, and the complete existing strict
`lease`; its strict positive response contains only `schema`, `nonce`, `lease_id`,
`node_id`, `hard_deadline`, and `policy_allows: true`. Both schemas use
`iw.benchmark-continuation-policy/1`. Each frame is at most 4 MiB. The nonce and
all response bindings must match this exchange and the actual durable owned lease;
reject duplicate or unknown fields, malformed data, wrong versions and mismatch.
The existing Lease type and bounds remain authoritative; the projection fixtures
are not a Lease schema. The nonce is correlation, not authentication, signature,
attestation or a permit. No credentials, prompts, outputs, private node endpoints
or owner bearers belong in this observation.

The gateway checks actual current ownership and immutable identity, current policy,
protection, owner priority, floors, safety and original hard expiry under its
existing authority. A released, expired, wrong or changed owner cannot receive a
positive observation. False, refusal, unavailability or unknown policy is not
positive; consumers require a fresh matching observation and cancel/refuse owned
work under the same captured original deadline when permission is absent or lost.
The operation does not mutate or renew leases, acquire resources, extend a start
window, reactivate a grant, claim idle capacity, or authorize execution. A passed
soft start window or busy/unknown engine alone does not reject current policy
observation, and busy/unknown is never represented as idle. Acquire and
`admit-start` retain initial idle, soft-window and full-new-work estimate checks.
Private Child/channel, node admission and ownership remain independent; historical
ownership status and return/recovery remain available despite policy withdrawal.
This interface and its consumer do not yet exist; runtime proof remains owed.

One original expiration covers preflight, capture, calibration, measurement,
preparation and commit. Parent captures monotonic remaining time and transmits the
original absolute expiration; child derives its own monotonic deadline once. Wall
clock rollback must not extend the parent deadline; Instants are never serialized.
Bound each control timeout by remaining time, reserve commit and cleanup margin,
and refuse work without it. Cleanup grace grants no more inference time. A stuck
fsync is bounded by the parent kill/reap fence, not claimed interruptible; a
committed capsule can be imported after expiration.

Use bounded corpus bytes and a versioned recipe coupled to the actual input hash,
with the actual generated bytes at most 4 MiB. Only bounded streaming transport
with complete terminal and provider-usage validation is eligible. Calibration is
setup, not measurement or deployment attestation; there is no separate model-list,
nonstream readiness, warmup or retry. At most four calibration calls plus C×R
measured requests are allowed. Incomplete or out-of-window evidence cannot form a
success capsule. Prepare once, commit, then import without rereading current
metadata. Calibration and provider usage do not prove backend concurrency.

The authenticated observation producer, additive v2 payload and source-backed
exact coverage (E7–E9) are later engineering dependencies, not implemented by this
contract. Slurm resident attestation is absent; scheduler authority remains and
unsupported Slurm execution is refused. Runtime, owned-child, recovery, safety,
Slurm, canary and production qualification evidence remains owed in OPEN_GATES.
