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

Published eligible capacity must apply the same out-of-routing predicates as
request selection. A withdrawn node contributes zero eligible capacity, including
owner capacity, even while its registration and readiness remain fresh. This is
a capacity projection, not deletion of the known model/deployment inventory or
its declared context ceiling. Healthy siblings retain their eligible capacity;
withdrawal does not cancel already accepted work or release its reservations.
Known context and currently servable context remain separate: a withdrawn node
cannot enlarge a serving offer through its context declaration.

The November 2026 DNS-withdrawal incident exposed a missing specification link:
freshness-only catalogue budgeting could advertise capacity that selection would
reject. An implementation following freshness alone would recreate that ghost
capacity. See [operational evidence](../evidence/dns-withdrawal-capacity-2026-11-05/README.md).

Possible internal decision:
`ACCEPT | QUEUE_BOUNDED | REROUTE | DEGRADE_CONTEXT_EXPLICIT_ONLY | REJECT_CAPACITY`.

Context degradation is never automatic unless client policy explicitly permits it.

## Deployment context ceiling

Every token-addressable deployment publishes `max_context_tokens`: the largest total context its loaded runtime
will accept. This is a property of the deployment, not of current load. A non-token runtime instead publishes and enforces its native input envelope under spec48; a fabricated token window cannot stand for a byte, shape or decision-input bound. Unknown native limits are inadmissible just as unknown token ceilings are.

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

## Read-only context-specific capacity observations

`iw.observability.capacity/1`, defined by
`schemas/v1/resources/observability-capacity.json` and
`contracts/observability-capacity.json`, is an authenticated read-only disclosure.
It is a separate additive response, never a member of strict topology v2 and
never a reinterpretation of the untyped Protocol v1 `Capacity.requests` object.
No existing route or negotiation changes implicitly; a consumer opts into the
versioned response. Its retrieval creates no reservation, lease or grant.

Each node snapshot carries producer_epoch, sequence, observed_at,
source_gateway_id, nullable owner_gateway_id, node_id, received_age_ms,
validity_ms and status. The source may relay; only the current authenticated
owner produces serving offers and available CPU. Origin identity and sequence
are preserved across relays, and received_age_ms accumulates monotonic elapsed
age across every relay plus consumer residence. observed_at is display/correlation
only, never a freshness clock. Duplicate/out-of-order sequences in an epoch do
not refresh age; an owner/producer restart changes its epoch and invalidates
cached offers. Ownership and epochs come from the established authenticated
resource binding, never from trusting these strings alone. Fresh means age is
strictly below validity_ms and identity/ownership remains current; an older or
unsupported response is unavailable, never empty measured capacity.

Physical idle GPUs, per-GPU free VRAM, CPU entitlement and serving offers are
four separate views. An idle GPU need not have a qualified loaded model. Free
VRAM need not be safely reservable. VRAM from different cards is not pooled into
one feasible allocation. Optional gpu_memory references the unchanged spec46
report shape, preserving its camelCase internals, ownership and capability
requirements; missing reports are unknown, never synthesized zeros.

CPU fields are physical_cores, logical_cpus, affinity_logical_cpus,
quota_millicores, owner_budget_millicores, reserved_millicores and
available_millicores. Every quantity carries basis and source; value is a
nonnegative safe integer and is forbidden for unknown/unsupported. Core counts
are inventory, not entitlement. The owner budget is bounded by effective CPU
affinity/cpuset and a finite cgroup quota when one applies; an unlimited quota
is represented as unsupported with source `cgroup_unlimited`,
not numeric zero. Unknown constraints make available capacity unknown.
Available millicores are max(0, effective owner budget minus held reserves),
with each reserve deducted once. Instantaneous utilization is separate telemetry
and MUST NOT be multiplied by core count to claim schedulable CPU.

Each serving offer identifies offer_id, capacity_pool_id, owner_epoch,
runtime_instance_id, load_generation, deployment_fingerprint,
resource_profile_id, gpu_resource_ids, requested_context_tokens,
max_output_tokens, workload_profile, additional_requests, basis, status,
valid_for_ms and exclusion_reasons. requested_context_tokens is total requested
context including the maximum output allowance; max_output_tokens cannot exceed
it. A context estimate must respect the exact deployment ceiling and measured
resource envelope. additional_requests is a quantity with provenance, not a
fixed slot count or admission grant. capacity_pool_id is an owner-assigned,
fleet-unique shared-budget identity. Repeated occurrences in an assembled fleet
must bind the same owner_gateway_id and owner_epoch; a mixed-owner or mixed-epoch
pool is invalid. An owner must choose a distinct pool identity when another owner
already owns that identity; relays preserve identities rather than merging them.
Offers sharing a pool are alternatives and cannot be summed. They may legitimately
name different contexts, workloads, resource profiles, deployment fingerprints,
GPU sets and co-resident runtime instances. Equality of these dimensions is not
a pool constraint. Before publishing, the owner validates each offer's own exact
runtime/load/deployment binding and GPU references against authoritative state;
a pool label alone is no evidence of those bindings. Unknown or stale
offers carry no numeric request estimate. A stale/unavailable/unowned snapshot
contains no usable offers and no numeric available CPU. Validity is capped at
300000 ms by initial policy. A fresh snapshot requires validity_ms > 0, and a
fresh offer requires valid_for_ms > 0. Offer validity cannot exceed
validity_ms minus received_age_ms at snapshot generation.
Fresh owner admission and independent node reservation still decide each request.

The v1 schema is closed. Duplicate JSON object keys at any depth are malformed
and rejected before decoding; unknown major versions and malformed responses
become unavailable and cannot preserve an earlier fresh claim past its expiry.
IDs and source strings are bounded metadata, never metric label dimensions.

### Fleet HTTP response

Authenticated admin `GET /iw/v1/observability/capacity` always returns
`iw.observability.capacity.fleet/1` as specified by
`schemas/v1/resources/observability-capacity-fleet.json`. Optional node_id filters
its scope; it still returns a fleet envelope. Required fields are schema,
source_gateway_id (the serving gateway), producer_epoch, sequence, generated_at,
served_age_ms, node_count and nodes; next_cursor is present only while more pages
remain. Every nodes member is one `iw.observability.capacity/1` snapshot with a
real registered/reported node identity. A gateway's own process CPU is not a
fabricated node report. node_count is the total filtered snapshot count, not the
page length; an empty scope says nothing about free serving capacity.

Reuse spec46 section 3.7 pinned pagination: up to 1024 nodes per page and a 32 MiB
snapshot/page-set cap, bounded caller limit, cursor/epoch/sequence consistency,
all-or-nothing assembly and deduplication by node identity. The opaque cursor
binds node_id and authorization scope; changing either invalidates it. Expired,
unknown, forged or pre-restart cursors return 410 and require restart; pin-budget
exhaustion returns bounded 503/Retry-After. Single-page responses create no pin.
Default pin TTL/share/cap remain 60 seconds / 5 seconds / 13; pins never extend
capacity validity. served_age_ms is elapsed since snapshot generation; add it
and local residence to each node's received_age_ms before judging freshness.
A complete fresh page set is still an observation, never a grant. Unknown nodes
or lost coverage are explicit; a partial page set is not a complete fleet.

Node status describes the state at snapshot generation. received_age_ms is the
node observation's accumulated age at that instant; valid_for_ms is the offer's
remaining lifetime from that instant. For a pinned/cached fleet, readers add
served_age_ms and their own monotonic residence. Effective freshness requires
that total node age remain strictly below validity_ms and elapsed fleet age
remain strictly below each offer's valid_for_ms. Equality is expired. Original
pinned status/values may remain for diagnostics after expiry, but readers mark
them stale and never advertise them as usable capacity; fetching another page
or duplicate sequence cannot reset those clocks.
