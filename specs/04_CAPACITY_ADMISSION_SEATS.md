# 04 — Seats, Context/KV Capacity and Admission

## Terms

- **Seat:** one active logical inference session.
- **Resident session:** session state/resources retained while not actively decoding.
- **Queued session:** waiting; not counted as an active seat.
- **Capacity envelope:** measured resources available to a specific deployment/backend/hardware profile.

Seat count is descriptive, not admission capacity.

## Per-session accounting

Track:
- session/user/project/workload IDs;
- current context tokens;
- cached-prefix tokens;
- maximum requested generation;
- estimated conversation growth reserve;
- KV bytes allocated/measured when available;
- predicted peak KV;
- runtime memory;
- active/prefill/decode/idle state;
- FairShare class;
- lease and node/deployment.

## Shared accounting

Model weights/runtime residency are accounted once. Per-session KV/runtime state is separate. VRAM, RAM, KV, compute, thermal, disk and bandwidth pressure remain independently observable.

## Admission

Gateway pre-admission predicts feasibility. Node performs authoritative local reservation before accepting the lease.

Possible internal decision:
`ACCEPT | QUEUE_BOUNDED | REROUTE | DEGRADE_CONTEXT_EXPLICIT_ONLY | REJECT_CAPACITY`.

Context degradation is never automatic unless client policy explicitly permits it.

## Prediction calibration

Record predicted versus actual peak/resource use. Expose prediction error and use it to update safety margins. Never reduce margin solely to improve benchmark utilization.

## Safety

Admission prevents predictable OOM. A growing set of active sessions can reduce estimated additional capacity without changing active seat count.
