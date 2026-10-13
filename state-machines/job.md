# Async job state machine

States and allowed transitions for a long-running async job. Vocabulary governed by invariant 41
(frozen machine-readable form published with the `P5-T25`/`P5-T26` conformance publication,
currently `owed`);
see `schemas/v1/jobs/` and `specs/45_PROTOCOL_V1.md` ("Async jobs").

Canonical emitted states: `queued`, `preparing`, `running`, `finalizing`, `succeeded`, `failed`,
`cancelled`, `expired`. `completed` is a legacy read alias for `succeeded`; new producers never emit
it.

Allowed transitions:

```text
queued      -> preparing | running | cancelled | expired | failed
preparing   -> running | cancelled | failed
running     -> finalizing | cancelled | failed
finalizing  -> succeeded | failed
succeeded   -> (terminal)
failed      -> (terminal)
cancelled   -> (terminal)
expired     -> (terminal)
```

Terminal states: `succeeded`, `failed`, `cancelled`, `expired`. Cancellation is idempotent and
applies from any non-terminal state. Jobs may report progress (`fraction`, `stage`, `message`).

## Durable inference lifecycle (specs/52)

Jobs submitted through `POST /jobs` (single runtime-family inference request or pipeline
reference) follow the durable inference lifecycle:

```text
queued -> running -> succeeded | failed | cancelled
```

- `completed` from a legacy persisted/API record is normalized to `succeeded` before re-emission;
  `failed` and `cancelled` are valid terminal transitions from any non-terminal state.
- Progress is durable: progress events (`schemas/v1/jobs/progress.json`) are persisted so a job
  interrupted by a gateway or node restart resumes from its durable progress, not from scratch.
- Result by reference: on success the job carries a result reference to an artifact in the artifact
  cache model (`schemas/v1/artifacts/`), never an inline result body.
- No bypass: a durable job observes admission, capacity, fairshare, and owner-priority controls
  identically to synchronous inference; it is rejected when capacity or admission for its family
  is unavailable.
- `family` is required on new family-aware submissions but optional on legacy persisted jobs. It is
  never inferred from a model name.
