# 34 — PromptStore Abstraction and Storage Tiering

## Requirement

Every record accepted by a durable sink remains stored as specified by the
Prompt Ledger. Gateway admission uses bounded best-effort recording and may
lose a record under the explicit conditions in spec 22.

The implementation must not assume prompt bodies remain in one PostgreSQL row forever.

## Logical abstraction

```text
PromptStore
  put()
  get()
  verify()
  delete_by_policy()
  export_authorized()
```

PostgreSQL remains authoritative for:
- IDs;
- tenant/session/request linkage;
- hashes;
- encryption metadata;
- retention;
- access/audit metadata;
- storage locator.

Prompt payload bytes may live in:
- PostgreSQL initially for small deployments;
- encrypted S3-compatible/object storage for large payloads;
- other approved backends later.

## Tiering policy

Possible policy:
- small prompt payloads inline;
- large contexts/attachments in encrypted object storage;
- content-addressed encrypted chunks where privacy design permits;
- lifecycle tiering according to retention.

The API contract is independent of the physical backend.

## Encryption

Use envelope encryption and backend-independent integrity hashes.

Never expose storage URLs directly without scoped short-lived authorization.

## Availability

The explicit durable-ingest API is on its caller's submission path, so its
storage must have:
- idempotency;
- durable retry/outbox;
- health/backpressure;
- explicit degraded behavior.

Do not acknowledge the durable-ingest API when its durable-storage requirement
was not satisfied. Ordinary gateway admission is a separate contract: it never
waits for this storage path and reports recorder delay or loss through bounded
operator telemetry.
