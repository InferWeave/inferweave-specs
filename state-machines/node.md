# Node state machine

States and allowed transitions for a node. Frozen vocabulary (invariant 41).

States: `absent`, `registering`, `ready`, `degraded`, `draining`, `cordoned`, `unreachable`,
`stale`, `removed`, `failed`.

Allowed transitions:

```text
absent       -> registering | removed
registering  -> ready | degraded | failed
ready        -> degraded | draining | cordoned | unreachable | failed
degraded     -> ready | draining | cordoned | unreachable | failed
draining     -> ready | cordoned | removed
cordoned     -> ready | draining | removed
unreachable  -> stale | ready | removed
stale        -> removed | ready | unreachable
removed      -> absent
failed       -> absent | registering | removed
```

Terminal states: `removed`, `failed`. The protocol distinguishes `temporarily unreachable`,
`stale`, `removed`, and `terminated`.
