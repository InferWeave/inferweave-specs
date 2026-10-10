# Async job state machine

States and allowed transitions for a long-running async job. Vocabulary governed by invariant 41
(frozen machine-readable form published with the `P5-T25`/`P5-T26` conformance publication,
currently `owed`);
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

## Durable inference lifecycle (specs/52)

Jobs submitted through `POST /jobs` (single runtime-family inference request or pipeline
reference) follow the durable inference lifecycle:

```text
queued -> running -> succeeded | failed | cancelled
```

- `succeeded` corresponds to the `completed` state above; `failed` and `cancelled` are valid
  terminal transitions from any non-terminal state.
- Progress is durable: progress events (`schemas/v1/jobs/progress.json`) are persisted so a job
  interrupted by a gateway or node restart resumes from its durable progress, not from scratch.
- Result by reference: on success the job carries a result reference to an artifact in the artifact
  cache model (`schemas/v1/artifacts/`), never an inline result body.
- No bypass: a durable job observes admission, capacity, fairshare, and owner-priority controls
  identically to synchronous inference; it is rejected when capacity or admission for its family
  is unavailable.
