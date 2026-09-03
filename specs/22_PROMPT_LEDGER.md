# 22 — Shared Prompt Ledger

## Requirement

Every submitted inference request must create a durable, queryable prompt record in the shared database.

This includes requests that are later accepted, rejected, capacity-blocked, policy-denied, failed, cancelled or preempted. The prompt record is the ingress audit/history record; execution attempts reference it.

This applies to:
- chat/completions/responses;
- embeddings/rerank requests containing user text;
- AutoSpec/Pi requests;
- Workbench conversations;
- vision/image prompt text;
- RAG/tool-enhanced requests, including the exact final submitted model input envelope where policy allows;
- retries and failovers, with lineage to the original logical request.

## Direct-data-path compatibility

The system must preserve prompt persistence without forcing inference bytes through the gateway.

Recommended flow:

```text
client/local proxy
    |
    | 1. idempotent encrypted prompt ingest
    v
prompt-ingest service ---> shared prompt database
    |
    | returns prompt_id + immutable content hash
    v
client/local proxy
    |
    | 2. route request metadata + prompt_id/hash
    v
control plane
    |
    | 3. route ticket
    v
client/local proxy ---------------------> selected node
        direct inference payload

selected node
    |
    | 4. execution acknowledgement references prompt_id/hash
    v
control/accounting plane
```

The prompt-ingest service is horizontally scalable and distinct from the routing gateway, so storing every prompt does not force model traffic or response streams through the gateway.

If the client cannot reach prompt ingest, the request is not considered durably submitted. A local proxy may use a crash-safe outbox and complete ingestion before route acceptance.

Every submitted request receives a prompt record before routing. Execution/rejection/cancellation facts then reference that prompt ID.

## Schema

Logical entities:

```text
prompt_record
prompt_message
prompt_attachment_ref
prompt_execution_attempt
prompt_access_audit
```

Minimum `prompt_record` fields:
- prompt_id;
- tenant_id;
- user_id/service_account_id;
- api_key_id;
- session_id;
- request_id;
- logical_job_id if any;
- created_at;
- accepted_at;
- source client/workload;
- route policy hash;
- selected deployment fingerprint;
- selected node/service/GPU identifiers;
- original exact request format/content;
- normalized message representation;
- tokenizer/model metadata;
- input token count;
- content hash;
- encryption key reference/version;
- retention class;
- parent/retry/failover lineage.

## Storage

Initial shared store: PostgreSQL.

Requirements:
- partition by time and/or tenant;
- compress large text/envelopes where useful;
- encrypt content using envelope encryption with managed key references;
- keep searchable non-sensitive metadata separate from encrypted prompt blobs where useful;
- idempotency on `(tenant_id, request_id)` or equivalent;
- durable outbox for node/local-proxy ingestion;
- documented backup/restore and deletion workflows.

## Security

Because prompts may contain private code, credentials, personal data or proprietary documents:
- deny prompt-content reads by default;
- use scoped administrative/audit roles;
- record every content read/export;
- redact prompt bodies from application logs, traces and metrics;
- do not include prompt text in public snapshots, benchmark public datasets, receipts or contribution reports;
- optionally detect likely secrets and tag sensitivity without rewriting the stored original.

## Retention

The product requirement is to store every prompt. Retention duration remains policy-configurable, but no accepted prompt may bypass initial durable storage.

## Benchmarks

Prompt records may feed workload-shape statistics and private benchmark replays. Public/global benchmark publication uses derived aggregate features unless an explicit dataset-governance process approves prompt content release.

## Read-side integrity

The ledger is read far more often than it is written — every reconnect, every reconciliation,
every audit. A correct writer is not the same thing as a trustworthy reader.

Every read of an ordered record proves the whole record is gapless, not merely the page
returned. A gap below a reader's cursor is invisible to a page-shaped check while the stream
replays as complete, and an interrupted operation can then be closed on evidence drawn from a
record nobody verified.

Where that proof relies on a storage-engine property — that sequence numbers are integral,
that a uniqueness constraint holds — the premise is asserted against the live engine by
attempting the write that would violate it, because a declared type is not always an enforced
type.

Verification is a read-side check over the existing store. It introduces no second journal
implementation: two implementations of one ordering rule are two places it can drift.
