# Runtime instance state machine

States and allowed transitions for an active inference runtime instance. Vocabulary governed by
invariant 41 (frozen machine-readable form published with the `P5-T25`/`P5-T26` conformance
publication, currently `owed`).

States: `absent`, `starting`, `ready`, `degraded`, `draining`, `stopping`, `stopped`, `failed`.

Allowed transitions:

```text
absent   -> starting | failed
starting -> ready | degraded | failed
ready    -> degraded | draining | stopping | failed
degraded -> ready | draining | stopping | failed
draining -> stopping | ready
stopping -> stopped | failed
stopped  -> absent | starting
failed   -> absent | starting | stopped
```

Terminal states: `absent`, `stopped`, `failed`.
