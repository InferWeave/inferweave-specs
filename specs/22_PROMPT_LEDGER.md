# 22 — Shared Prompt Ledger

## Requirement

Every inference request is offered to an encrypted recording pipeline, including
requests later accepted, rejected, capacity-blocked, policy-denied, failed,
cancelled or preempted. Recording is an observational side effect of ordinary
gateway service, not a prerequisite for admission.

The gateway derives stable prompt identity, encrypts sensitive content, and
uses a non-blocking enqueue into a bounded process-local buffer. A full, closed,
or unavailable recording path drops the record, increments bounded metrics,
and leaves request validity, policy, capacity, and routing decisions unchanged.
The prompt record remains the preferred ingress audit/history record when it is
successfully written; execution attempts reference its stable identity.

The separate durable prompt-ingest API retains a fail-closed contract. A caller
using that API does not receive a durable-submission acknowledgement until the
record is committed.

This applies to:
- chat/completions/responses;
- embeddings/rerank requests containing user text;
- AutoSpec/Pi requests;
- Workbench conversations;
- vision/image prompt text;
- RAG/tool-enhanced requests, including the exact final submitted model input envelope where policy allows;
- retries and failovers, with lineage to the original logical request.

## Direct-data-path compatibility

The system must preserve prompt recording without forcing inference bytes
through the gateway.

Ordinary gateway flow:

```text
client/local proxy ---> gateway/control plane
                         |              |
                         |              | 1. derive prompt_id/hash and encrypt
                         |              | 2. non-blocking enqueue
                         |              v
                         |      bounded recorder -> configured sink
                         |
                         | 3. issue route ticket independently
                         v
client/local proxy ---------------------> selected node
                  direct inference payload

selected node
    |
    | execution acknowledgement references prompt_id/hash
    v
control/accounting plane
```

The recorder is distinct from routing policy. File, PostgreSQL, discard, and
future external-queue adapters implement one batch sink interface; the request
path does not know which sink is configured. Sink startup, acknowledgement,
retry, flush, and synchronization never execute on or backpressure the
admission path.

The default buffer is bounded to 8,192 events, drops the newest event when full,
flushes up to 128 events or after 250 milliseconds, and retains at most one
failed batch for retry. Retry begins at 100 milliseconds and caps at 30 seconds.
These are configurable bounded policies, not durability guarantees. A sink call
that never returns may strand one dedicated recorder thread; it cannot create
unbounded replacement tasks or block request threads.

### Recording resource and retry policy

The versioned [frozen recording contract](../contracts/recording-outcomes-v1.json)
and [vocabulary document](../docs/contracts/recording-outcomes-v1.md) define
metric reasons, sink classes, health labels, policy defaults and invalid vectors.
Implementations vendor the pinned data and reconcile emitted labels and limits
by test; no runtime contract fetch is permitted.

The default encoded-event byte budget is 64 MiB across queued events and the
single retained batch, with at most 8 MiB per event and 16 MiB per batch. These
are configurable operator-selected policy ceilings, not measured hardware
capacity or throughput claims. Reserve bounded space before sealing/copying;
an event that cannot fit is dropped newest and counted. Count, byte, encoding,
entropy-unavailable, contention and closed-channel loss remain distinguishable.
Reject zero or inconsistent event/batch/total byte bounds before startup;
require event ≤ batch ≤ shared total. Count limits may be lowered but never
raised above 8192 queued events or 128 batch events, and must be rejected before
channel allocation if out of range. One encoded-byte reservation remains with
the event through queue, in-flight, retained and retry ownership, and is released
exactly once on terminal classification. Configured crash-loss count bounds
never exceed 8320 and do not make actual crash loss known.
Content never waits in a plaintext asynchronous queue. Managed envelope sealing
must not wait on another caller's RNG lock or perform entropy/storage reads on
the admission thread: one bounded pool of one-use prepared entropy may be
refilled by one dedicated worker. The fixed reservoir is independent of lowered
event count:8191 queued objects plus at most one preparing/sending object,8192
total. A prepared-object gauge includes a pending send and is not readiness.
Pool exhaustion drops recording; it never
falls back to blocking sealing or plaintext. A frozen sink or entropy refiller
cannot spawn replacements or make serving shutdown wait indefinitely.

A file recorder has no default disk budget: `disk_max_bytes` and
`disk_scan_limit` default to unset (`null`), and a budget applies only when an
operator sets either one. A configured budget counts only the sink's own
`recording-*.jsonl` files in the configured deployment directory. Historical
and uncertain partial writes in those files count after restart. Unknown capacity,
symlinks, an over-budget batch or an unqualified competing writer never grant
additional space. Any configured value is policy, not an acceptable disk-full target.
Budget exhaustion loses only new best-effort records with explicit counters;
no acknowledged durable data is automatically deleted or truncated. Retention
or drain of existing durable records is a separately authorized and audited
workflow. Shared-filesystem locking and exclusion of older, non-cooperating
writers require qualification before rollout.

A deployment that started and recorded on the pre-recording gateway must keep
starting with the **same** identity, so startup resolves it as that gateway did.
A non-blank explicit `--gateway-id` flag, else a non-blank `gateway_id` setting,
is used exactly as given; nothing on the recording filesystem is read, and an
odd value (surrounding whitespace, control character, leading `--`, over 256
bytes) is only warned about. Otherwise the gateway reads
`<outbox>/<name>/gateway-id`; a blank flag hiding a differing setting starts as
the stored ID with one warning. With no identity file it mints and saves one, as
before, warning once if `*.jsonl` history already exists (those files were
written under an identity that was not saved). If the save fails (read-only,
no hard links, no space) it logs the error, falls back to an explicitly partial
process identity and keeps recording. A malformed or unreadable identity file is
a startup error (exit 2). A stored identity is never silently replaced by a
minted one while claiming continuity. Recording-filesystem and database
outages remain independent of ordinary serving once static prerequisites are
valid. Protected alias/warehouse authority retains its own fail-closed store
requirements and cannot be fabricated from a recorder or discard adapter.

Batch sinks return per-event committed, permanent-loss or unresolved outcomes.
Only the unresolved subset is retried. Never-dispatched queued casualties are
known loss, but a sink worker that terminates after dispatch may already have
committed its in-flight batch. Report those unacknowledged outcomes separately
as unknown, never as committed or known lost. A permanent refusal after an
uncertain retry also cannot prove the earlier attempt did not commit. Closed
unknown-outcome reasons are worker termination, shutdown with unresolved work,
invalid sink outcome shape, and refusal after an uncertain retry. Do not spawn
a replacement worker. The configured crash-loss bound is separate from these
exact current-process counters and does not make abrupt crash loss known.
A dropped prompt may cause a dependent
fact/attempt to fail its parent constraint; that event is permanent measured
loss, while unrelated valid events may commit. Natural-key uniqueness alone
is insufficient evidence of identical retry. PostgreSQL may atomically commit
a metadata-only semantic receipt with the supported prompt/attempt/fact row;
matching input semantics acknowledge an identical retry, and different or
unprovable legacy semantics are explicit conflict loss. The semantic binding
includes original content hashes and logical fields, excludes randomized
ciphertext/key wrapping and database-generated timestamps, and must not depend
on round-tripping database timestamp precision. Receipts expire with authorized
parent retention. This adds no PostgreSQL response-capture capability: existing
unsupported response recording remains explicit loss, never false success.

The durable prompt-ingest service remains horizontally scalable and distinct
from the routing gateway. If a client explicitly chooses durable ingest and
cannot reach it, that request is not durably submitted and the API fails closed.

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

For gateway recording, runtime sink unavailability does not prevent startup.
Invalid static configuration remains a startup error. Each event has a stable
identity derived from its natural idempotency key so retry after an uncertain
write does not create a second logical record.

## Security

Because prompts may contain private code, credentials, personal data or proprietary documents:
- deny prompt-content reads by default;
- use scoped administrative/audit roles;
- record every content read/export;
- redact prompt bodies from application logs, traces and metrics;
- do not include prompt text in public snapshots, benchmark public datasets, receipts or contribution reports;
- optionally detect likely secrets and tag sensitivity without rewriting the stored original.

## Admission, loss, and retention

For ordinary gateway admission, only request validity, authentication, policy,
capacity, deadline, and routing errors may refuse inference. Gateway record-sink
state may not. An explicit durable-ingest call is a different contract: it must
withhold acknowledgement or fail when committed storage cannot be proven.

Gateway records can be lost when the process exits before flush, the bounded
buffer overflows, encoding fails, a sink outage outlasts the buffer, or explicit
discard mode is selected. This accepted loss is never represented as durable
success. Operators receive exact live-process counts for enqueue, overflow,
closed-channel, encoding, and discard outcomes, plus buffer depth, sink
failures, retry delay, last success, and a `healthy`, `delayed`, or `dropping`
state. An abrupt process exit cannot report the records it lost; operator status
therefore publishes the configured crash-loss upper bound (buffer capacity plus
one retained batch) and labels crash loss as unknown rather than zero. Serving
health stays independent of recorder health.

Retention duration for records that reach a durable sink remains
policy-configurable. Explicit durable-ingest acknowledgements retain their
committed-storage meaning.

## Incident correction

The former contract required durability before routing. On 2026-09-28 a
Quobyte-backed gateway outbox failed while the Hive allocation and model
backends remained available; because admission synchronously depended on that
file, all downstream requests appeared busy. The specification itself was part
of the root cause. Retrying or rotating a shared file improves sink recovery but
does not make synchronous storage safe for admission. The recorder boundary in
this specification prevents a future literal implementation from recreating
that outage.

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
