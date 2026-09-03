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

## Deployment context ceiling

Every deployment publishes `max_context_tokens`: the largest total context its loaded runtime
will accept. This is a property of the deployment, not of current load.

The pool a scheduler has budgeted and the ceiling a runtime will accept are different
quantities. Only the ceiling can make a request impossible, and free capacity never raises it.

Admission evaluates the ceiling before any capacity arithmetic:

- a request whose total context exceeds `max_context_tokens` is refused immediately as
  `CONTEXT_WINDOW_EXCEEDED`, and the refusal names the actual ceiling;
- a predicted peak context above the ceiling is refused on the same basis;
- effective capacity is additionally bounded by `min(available_pool, max_context_tokens)`.

Fail closed. A deployment whose ceiling is unknown is not admissible.

Refusing at admission is the point: a request accepted beyond the ceiling is only rejected
once the runtime has already spent the prefill, so the cost of the mistake is paid in full
before it is detected.

## Reservation liveness

Cancellation is the orderly release path and is not sufficient alone. A client that
disappears mid-stream, a crashed proxy or a dropped connection leaves a reservation held with
nobody to release it, and one leaked reservation can consume a node's entire concurrency while
health checks continue to report that node available.

Reservations therefore carry liveness:

- each reservation records a progress timestamp, refreshed on observable forward progress;
- expiry is evaluated on **time since last progress**, never on total elapsed time — a long
  legitimate request must not be reclaimed for being long;
- the reaper is a required component with a stated bound, not an implementation detail;
- reclamation is idempotent and releases every resource the reservation held;
- reclaimed reservations are recorded, because a rising reclaim rate is a defect signal.

## Queue observability

Whatever structure orders admission is the single source of truth for what is waiting. Every
queue view — API, dashboard or telemetry — reads from that structure.

An implementation that records only executing work and reports its queue from a second
structure satisfies the letter of bounded queueing while showing an empty queue to operators
whose clients are waiting.

Per-waiter position and estimated wait belong to the admission surface, not to a separate
telemetry collector. Where an estimate cannot be derived it is reported absent, never zero.

## Prediction calibration

Record predicted versus actual peak/resource use. Expose prediction error and use it to update safety margins. Never reduce margin solely to improve benchmark utilization.

## Safety

Admission prevents predictable OOM. A growing set of active sessions can reduce estimated additional capacity without changing active seat count.
