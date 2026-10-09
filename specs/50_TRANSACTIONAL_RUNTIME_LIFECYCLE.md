# 50 — Transactional Runtime Hot-Swap Lifecycle

## Relationship to existing state machines

[`state-machines/runtime.md`](../state-machines/runtime.md) already defines a
lifecycle of
`absent → starting → ready | degraded | draining → stopping → stopped | failed`.
[`specs/43_GPU_PLACEMENT_HOT_SWAP.md`](43_GPU_PLACEMENT_HOT_SWAP.md) defines GPU
placement hot-swap. This specification refines the runtime state machine into a
**transactional** lifecycle with explicit preparation, validation, and
unloading transitions, and reconciles the two so a hot swap is a single
transactional transition, not an independent set of ad-hoc steps.

## Transactional lifecycle

The canonical runtime lifecycle, in dependency order:

```
DISCOVERED
   │ resolve
   ▼
RESOLVING ──────────────┐ (resolution failed → FAILED)
   │ resolve ok
   ▼
PREPARING ──► DOWNLOADING ──► PREPARING   (weight/artifact acquisition, content-addressed)
   │ prepare ok
   ▼
RESERVING  (capacity/grant reservation under the rebalancer's authority)
   │ reserved
   ▼
STARTING
   │ started
   ▼
LOADING
   │ loaded
   ▼
WARMING
   │ warm
   ▼
VALIDATING  (probe that the runtime actually serves before READY)
   │ validated
   ▼
READY ◄──► BUSY / IDLE      (serving; the rebalancer may target it)
   │ drain
   ▼
DRAINING
   │ unload
   ▼
UNLOADING
   │ stopped
   ▼
STOPPED
```

Failure and cancellation edges: any of `RESOLVING`, `PREPARING`,
`DOWNLOADING`, `RESERVING`, `STARTING`, `LOADING`, `WARMING`, `VALIDATING`
may transition to `FAILED` (or, for cancellations, directly to `STOPPED`).
`DRAINING` and `UNLOADING` are terminal paths to `STOPPED`; a drain may be
interrupted back to `READY` only if the drain was cancelled before unload.

## Transactionality and the rebalancer

- `RESERVING` must be reconciled with the existing rebalancer's reservation
  model ([`specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md`](30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md)).
  A reservation is fenced and expires; a hot swap reuses the existing
  reservation authority and never creates a second scheduler.
- `READY ↔ BUSY / IDLE` transitions are the only states the rebalancer may
  target for placement/reclaim. A runtime in `VALIDATING` or `WARMING` is not
  yet schedulable.
- A hot swap is atomic with respect to the deployment: the old runtime is not
  removed from the routable set until the new one has passed `VALIDATING`.
  This preserves availability during swap.

## Invariants

1. **Single allocation authority.** The lifecycle's `RESERVING`/`DRAINING`
   transitions only express intent to the existing rebalancer; no second
   scheduler is introduced.
2. **Availability-preserving swap.** The outgoing runtime remains routable until
   the incoming runtime has validated.
3. **Validated-ready.** A runtime is never advertised `READY` without a
   successful `VALIDATING` probe.
4. **Terminal-state discipline.** `FAILED` and `STOPPED` are absorbing;
   `DRAINING`/`UNLOADING` cannot be interrupted back to `READY` once unload
   begins.

## Required tests

- state-machine-transitions: every allowed transition is enumerable and every
  forbidden transition is rejected by the machine model.
- availability-preserved: during a hot swap the routable set always contains at
  least the validated runtime.
- no-second-scheduler: `RESERVING` and `DRAINING` are expressed as events to the
  existing reservation authority, never as direct placement.
