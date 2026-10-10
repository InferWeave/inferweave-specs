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
