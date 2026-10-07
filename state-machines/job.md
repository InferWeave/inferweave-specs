# Async job state machine

States and allowed transitions for a long-running async job. Frozen vocabulary (invariant 41);
see `schemas/v1/jobs/` and `specs/45_PROTOCOL_V1.md` ("Async jobs").

States: `queued`, `preparing`, `running`, `finalizing`, `completed`, `failed`, `cancelled`,
`expired`.

Allowed transitions:

```text
queued      -> preparing | running | cancelled | expired | failed
preparing   -> running | cancelled | failed
running     -> finalizing | cancelled | failed
finalizing  -> completed | failed
completed   -> (terminal)
failed      -> (terminal)
cancelled   -> (terminal)
expired     -> (terminal)
```

Terminal states: `completed`, `failed`, `cancelled`, `expired`. Cancellation is idempotent and
applies from any non-terminal state. Jobs may report progress (`fraction`, `stage`, `message`).
