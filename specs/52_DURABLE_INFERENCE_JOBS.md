# 52 — Durable Inference Jobs

## Relationship to existing surface

[`specs/15_ASYNC_JOBS_ARTIFACTS.md`](15_ASYNC_JOBS_ARTIFACTS.md),
[`state-machines/job.md`](../state-machines/job.md), and
[`schemas/v1/jobs/job.json`](../schemas/v1/jobs/job.json) already define a
durable async job and artifact model, primarily oriented at image/async
generation. This specification extends that model into a general **durable
inference job** contract covering all runtime families and pipelines, so that
long-running or queued inference (including pipelines) is submitted, tracked,
and resumed durably — not held open in a client request.

## Contract

Extend the job schema and state machine so a durable inference job:

- is submitted via `POST /jobs` (`[`specs/49`](49_NATIVE_CONTROL_PLANE_ENDPOINTS.md)`)
  carrying either a single runtime-family inference request or a pipeline
  reference ([`specs/51`](51_PIPELINES_AND_DURABLE_JOBS.md));
- has the lifecycle `queued → running → succeeded | failed | cancelled`, with
  durable progress events (reuse `schemas/v1/events/` and
  `schemas/v1/jobs/progress.json`);
- on success returns a **result reference** to an artifact in the existing
  artifact cache model (`schemas/v1/artifacts/`), not an inline body;
- is resumable/restartable across a gateway or node restart using the existing
  durable outbox/ledger discipline (the runtime's prompt-outbox and job ledger);
- observes the same admission, capacity, fairshare, and owner-priority controls
  as synchronous inference; a durable job does not bypass them.

A new family-aware job carries a typed `family` (from the
[`specs/48`](48_RUNTIME_FAMILIES_AND_CAPABILITIES.md) registry) so the job controller can route it
to an admitted runtime of that family. The member is additive: persisted legacy jobs without it
remain valid and readable, and a missing value is never inferred from a model name. New producers
emit `succeeded` as the successful terminal state. Readers accept legacy `completed`, normalize it
to `succeeded`, and never re-emit `completed`.

## Invariants

1. **Durable first.** Long-running inference is a job, never a held-open
   request.
2. **Result by reference.** Job results are artifact references in the artifact
   cache model.
3. **No bypass.** Durable jobs observe admission, capacity, fairshare, and
   owner-priority identically to synchronous inference.
4. **Family-typed submission.** Every new runtime-family submission names its family; legacy jobs
   without the additive member remain readable and are not silently family-routed.

## Required tests

- job-lifecycle: a job traverses `queued → running → succeeded` with durable
  progress, and `failed`/`cancelled` are valid terminal transitions.
- restart-resume: a job interrupted by a restart resumes from its durable
  progress, not from scratch.
- no-bypass: a durable job is rejected when capacity/admission for its family is
  unavailable, identical to a synchronous request.
- legacy-read: a job without `family` and with terminal state `completed` remains readable, is
  normalized to `succeeded`, and new output always emits `succeeded`.
