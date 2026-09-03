# 34 — PromptStore Abstraction and Storage Tiering

## Requirement

Every submitted prompt remains durably stored as specified by the Prompt Ledger.

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

Prompt ingestion is on the submission path, so storage must have:
- idempotency;
- durable retry/outbox;
- health/backpressure;
- explicit degraded behavior.

Do not silently accept a prompt that cannot satisfy the durable-storage requirement.
