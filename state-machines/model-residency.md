# Model residency state machine

States and allowed transitions for a model variant occupying resources. Frozen vocabulary
(invariant 41); see `specs/44_CORE_PROTOCOL.md` and `schemas/v1/model/residency.json`.

States: `absent`, `downloading`, `cached`, `staging`, `loading`, `warming`, `ready`, `degraded`,
`draining`, `unloading`, `failed`.

Allowed transitions:

```text
absent      -> downloading | cached | staging | loading | failed
downloading -> cached | staging | loading | failed
cached      -> downloading | staging | loading | evicted(absent) | failed
staging     -> loading | failed
loading     -> warming | ready | degraded | failed
warming     -> ready | degraded | failed
ready       -> degraded | draining | unloading | evicted(absent)
degraded    -> ready | draining | unloading | failed
draining    -> unloading | ready
unloading   -> cached | absent | failed
failed      -> absent | downloading
```

Terminal states: `absent`, `failed`. Transition reasons use the canonical model lifecycle
reasons (`demand`, `operator_request`, `autoscale`, `rebalance`, `idle_timeout`,
`memory_pressure`, `allocation_loss`, `preemption`, `runtime_failure`, `hardware_failure`,
`maintenance`, `upgrade`, `cache_pressure`, `unknown`).
