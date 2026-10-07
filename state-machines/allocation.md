# Allocation state machine

States and allowed transitions for a generic scheduler allocation. Provider-specific metadata
goes in `provider_metadata` and is never required by upstream. Vocabulary governed by invariant
41 (frozen machine-readable form published with the `P5-T25`/`P5-T26` conformance publication,
currently `owed`).

States: `requested`, `pending`, `allocating`, `allocated`, `booting`, `staging`,
`runtime_starting`, `ready`, `draining`, `preempting`, `terminated`, `lost`, `failed`.

Allowed transitions:

```text
requested         -> pending | allocating | failed
pending           -> allocating | terminated | failed
allocating        -> allocated | pending | failed
allocated         -> booting | staging | runtime_starting | failed
booting           -> staging | runtime_starting | ready | failed
staging           -> runtime_starting | ready | failed
runtime_starting  -> ready | failed
ready             -> draining | preempting | terminated | lost | failed
draining          -> ready | preempting | terminated | failed
preempting        -> terminated | lost
lost              -> terminated | pending | failed
terminated        -> (terminal)
failed            -> (terminal)
```

`pending -> terminated` represents cancellation before allocation completes (`cancelled` is not
part of the allocation vocabulary; it is reported as a `terminated` allocation with termination
reason `operator`). `lost -> pending` represents a lost-but-recoverable allocation being
requeued by the scheduler; whether a `lost` allocation requeues or terminates is scheduler
policy carried in `provider_metadata`, never required by upstream.

Terminal states: `terminated`, `failed`. Termination reasons: `completed`, `operator`,
`preempted`, `scheduler_reclaim`, `timeout`, `node_failure`, `hardware_failure`,
`runtime_failure`, `idle`, `scale_down`, `maintenance`, `unknown`.
