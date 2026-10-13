# Runtime instance state machine

Transactional lifecycle for an inference runtime instance, per
[`specs/50_TRANSACTIONAL_RUNTIME_LIFECYCLE.md`](../specs/50_TRANSACTIONAL_RUNTIME_LIFECYCLE.md).
Vocabulary governed by invariant 41 (frozen machine-readable form published with the
`P5-T25`/`P5-T26` conformance publication, currently `owed`).

States, in dependency order: `DISCOVERED`, `RESOLVING`, `PREPARING`, `DOWNLOADING`, `RESERVING`,
`STARTING`, `LOADING`, `WARMING`, `VALIDATING`, `READY`, `BUSY`, `IDLE`, `DRAINING`, `UNLOADING`,
`STOPPED`, `FAILED`.

Legacy vocabulary mapping: `absent` = `DISCOVERED`, `starting` = `RESOLVING`..`VALIDATING`,
`ready` = `READY`/`BUSY`/`IDLE`, `degraded` = `READY` with a degraded health signal,
`draining` = `DRAINING`, `stopping` = `UNLOADING`, `stopped` = `STOPPED`, `failed` = `FAILED`.

Allowed transitions:

```text
DISCOVERED  -> RESOLVING | FAILED | STOPPED
RESOLVING   -> PREPARING | FAILED | STOPPED
PREPARING   -> DOWNLOADING | RESERVING | FAILED | STOPPED
DOWNLOADING -> PREPARING | FAILED | STOPPED
RESERVING   -> STARTING | FAILED | STOPPED
STARTING    -> LOADING | FAILED | STOPPED
LOADING     -> WARMING | FAILED | STOPPED
WARMING     -> VALIDATING | FAILED | STOPPED
VALIDATING  -> READY | FAILED | STOPPED
READY       -> BUSY | IDLE | DRAINING | FAILED
BUSY        -> READY | IDLE | DRAINING | FAILED
IDLE        -> READY | BUSY | DRAINING | FAILED
DRAINING    -> UNLOADING | READY | FAILED
UNLOADING   -> STOPPED | FAILED
STOPPED     ->
FAILED      ->
```

Rules:

- Every transition not listed is forbidden and is rejected with a typed error
  (e.g. `RESOLVING -> READY`).
- `FAILED` and `STOPPED` are absorbing (no outgoing transitions).
- `DRAINING -> READY` is only a drain cancellation before unload; once `UNLOADING` begins there is
  no path back to `READY`.
- `READY` is only reachable from `VALIDATING` (validated-ready) or from the serving states.
- Cancellation before serving goes directly to `STOPPED`; failure goes to `FAILED`.

Terminal states: `STOPPED`, `FAILED`.

## Rebalancer authority

`RESERVING` and `DRAINING` are expressed only as events to the existing rebalancer
(see [`specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md`](../specs/30_WORKLOAD_CONTRACTS_RESOURCE_EVENTS.md));
the lifecycle introduces no second scheduler.

- `RESERVING` is a fenced, expiring reservation under the rebalancer's authority, never direct placement.
- `DRAINING` is an intent event to the rebalancer, never a second scheduler.
- Availability preserved: the outgoing runtime stays routable until the incoming runtime has
  passed `VALIDATING` when simultaneous or cross-node capacity exists. If it does not, the
  controller records and performs a constrained drain-and-swap; it does not claim zero downtime.
- Only `READY`/`BUSY`/`IDLE` are targetable by the rebalancer; `VALIDATING` and `WARMING` are not
  yet schedulable.

## Load identity, waiters and rollback

One in-progress load exists per immutable `deployment_key`, never per alias or request. Waiters
attach with independent ids. Cancelling a waiter cannot cancel another waiter; the underlying load
ends only when the final waiter leaves, the fenced reservation is revoked, or a fatal failure is
classified. A stale fencing epoch cannot publish readiness.

If the old and new deployments cannot coexist on a node, the transaction chooses either an
explicit drain-and-swap or a cross-node replacement. Load, warm, validation or cutover failure
restores the preserved known-good deployment and route. Failed rollback quarantines the device.
