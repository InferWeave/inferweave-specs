# Allocation state machine

States and allowed transitions for a generic scheduler allocation. Provider-specific metadata
goes in `provider_metadata` and is never required by upstream. Frozen vocabulary (invariant 41).

States: `requested`, `pending`, `allocating`, `allocated`, `booting`, `staging`,
`runtime_starting`, `ready`, `draining`, `preempting`, `terminated`, `lost`, `failed`.

Allowed transitions:

```text
requested         -> pending | allocating | failed
pending           -> allocating | cancelled(terminated) | failed
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

Terminal states: `terminated`, `failed`. Termination reasons: `completed`, `operator`,
`preempted`, `scheduler_reclaim`, `timeout`, `node_failure`, `hardware_failure`,
`runtime_failure`, `idle`, `scale_down`, `maintenance`, `unknown`.
