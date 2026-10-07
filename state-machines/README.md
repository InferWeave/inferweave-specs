# InferWeave Protocol v1 — state machines

Each file specifies one canonical state machine: states, allowed transitions, and terminal
states. Invalid transitions are identifiable. State names are frozen machine-readable data
reconciled by test (invariant 41).

- `model-residency.md` — model variant residency lifecycle
- `runtime.md` — runtime instance lifecycle
- `node.md` — node lifecycle
- `allocation.md` — scheduler allocation lifecycle
- `job.md` — async job lifecycle

See `specs/45_PROTOCOL_V1.md` and the corresponding JSON Schemas under `schemas/v1/`.
