# 15 — Durable Jobs, Events and Artifacts

Long-running image, indexing, benchmark and other non-chat work uses a native durable job model.

## Job states

`SUBMITTED → VALIDATED → QUEUED → LEASED → RUNNING → SUCCEEDED | FAILED | CANCELLED`

Optional intermediate `RETRY_PENDING` is explicit and bounded.

## Idempotency

Submission supports idempotency keys. Retrying the same logical submission does not create duplicate billable/completed work. Attempt IDs are distinct from job IDs.

## Events

Ordered sequence-numbered events support replay/resume (SSE is sufficient initially). Consumers can reconnect from a known event offset.

## Artifacts

Metadata:
- ID/job/request/owner;
- kind/content type;
- checksum;
- byte count;
- provenance/deployment fingerprint;
- created/retention times;
- access policy;
- storage locator hidden behind authorized grants.

Bulk bytes are not embedded in event logs.

## Cancellation

Cancellation propagates to active worker/runtime, releases reservations and scratch, invalidates unneeded transfer grants and produces a terminal event.

## Retention

Retention is explicit by tenant/policy/artifact class. Public receipts/snapshots never reveal private artifact content.
