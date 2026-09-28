# Buffered gateway recording — 2026-09-28

**Status:** Accepted for production  
**Decision owner:** InferWeave operator  
**Date:** 2026-09-28  
**Authorizes:** Implementation, review, merge, and bounded deployment to the existing Fry/Hive gateway path  
**Relationship:** Re-decides the admission-ordering requirement of D-006 and D-017; every other encryption, authorization, audit, retention, and storage-abstraction requirement remains unchanged

## Measured basis

The existing Hive Rust gateway became unavailable to callers while its Slurm
allocation and four model backends remained running. The failed boundary was
the gateway's Quobyte-backed JSONL outbox: request admission synchronously
depended on opening, appending, and synchronizing one shared-filesystem record.
A poisoned or blocked file operation therefore made otherwise serviceable model
capacity appear busy downstream of `llm.metabolomics.us`.

The implementation repository contains the incident regression and the exact
Quobyte recovery boundary in `crates/iw-gateway/src/outbox.rs`; the existing
service identity and bounded rollout path are recorded in
`decisions/2026-09-22-existing-gateway-rollout.md`.

## Context

Durable prompt history is valuable, but storage and inference have different
availability domains. Making storage acknowledgement a prerequisite for every
route caused a recording failure to become a total inference outage. Reopening
or retrying files cannot make admission safe because a filesystem syscall can
block indefinitely, and synchronous fallback across several stores merely
couples admission to more failure domains.

The operator explicitly accepted bounded record loss and directed that storage
must not refuse otherwise valid inference admission. The gateway therefore
needs one storage-neutral recording interface with bounded asynchronous
buffering. Explicit callers of the durable prompt-ingest API retain the strict
durability contract.

## Options

1. Keep durability before routing and add file retries or handle rotation.
2. Try several durable stores synchronously before refusing the request.
3. Decouple gateway admission from recording with a bounded non-blocking buffer
   and pluggable sinks.

## Decision

Choose option 3.

The gateway derives prompt identity and encrypts sensitive content before a
non-blocking enqueue. A dedicated recorder owns batching, sink I/O, retry, and
health state. The queue and retry state are bounded. Full or closed buffers drop
new records rather than backpressuring admission. Live-process drops are exposed
exactly by bounded metrics; an abrupt crash exposes only the configured maximum
possible loss and is never reported as zero known loss.

File, PostgreSQL, explicit discard, and future broker-backed implementations
share one batch sink contract. Runtime sink unavailability neither prevents
gateway startup nor changes serving health. Invalid static configuration may
still prevent startup.

The standalone durable prompt-ingest API remains fail-closed. A caller that
requires proof of durable submission uses that API and waits for its
acknowledgement; gateway admission does not claim such proof.

## Consequences

- A blocked or unavailable record sink no longer turns model capacity into a
  gateway-wide busy response.
- Requests continue while the recorder is delayed or dropping.
- Records may be lost on process failure, sustained sink outage, buffer
  overflow, encoding failure, or explicit discard mode.
- Prompt and response content is encrypted before it can enter a persistent
  adapter.
- File writes remain single-writer and may rotate after an uncertain write;
  stable event identities make replay logically idempotent.
- Operators can distinguish healthy, delayed, and dropping recording without
  exposing prompt content or unbounded labels.
- The previous specification was a cause of the incident: an implementer
  following “durable before route” literally would reintroduce the shared
  storage outage as an inference admission outage.

## Requirements affected

- `IW-PROMPT-001`
- invariant 17
- D-006 shared prompt ledger
- D-017 prompt storage abstraction
- P1-T07 prompt recording
- P1-T08 submission ordering

## Production scope

This record extends the existing-service exception in
`OPEN_GATES.md` only for the buffered recorder change on the already registered
Fry/Hive gateway path. It authorizes no new site, GPU runtime, worker allocation,
public anonymous access, or general multi-node qualification.

Release requires an implementation model distinct from the final reviewer,
fresh local validation of the reviewed revision, preservation of rollback
artifacts, a healthy restarted Hive gateway, parent-link recovery, and a real
inference smoke test through `llm.metabolomics.us`. Before rollout, a fault
injection must also prove that an unavailable or indefinitely blocked sink does
not exceed the bounded admission latency, buffer memory remains bounded, drops
and degraded recorder state are visible, and serving health remains healthy.

## Rollback/revisit trigger

Revisit when measured record loss is unacceptable, when a durable local broker
can acknowledge without sharing the serving failure domain, or when regulation
requires a specific workload class to fail closed. Such a workload must use an
explicit durable-ingest policy; it must not silently restore storage coupling to
ordinary gateway admission.
