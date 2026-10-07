# Node state machine

States and allowed transitions for a node. Vocabulary governed by invariant 41 (frozen
machine-readable form published with the `P5-T25`/`P5-T26` conformance publication, currently
`owed`).

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
