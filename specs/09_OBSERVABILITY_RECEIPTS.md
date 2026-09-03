# 09 — Observability, Route Explanations, Receipts and Public Snapshots

## Correlation

Every request/session/job carries stable correlation IDs across gateway, scheduler, relay, node and backend.

## Metrics and global telemetry warehouse

Every GPU publishes the full inventory/runtime/model/settings/power/thermal telemetry defined in `23_GLOBAL_TELEMETRY_BENCHMARKS.md`.

## Metrics

At minimum:
- request/result/error counts;
- queue/admission/TTFT/total latency;
- prefill/decode/aggregate TPS;
- active/resident/queued sessions;
- requested/committed/free context;
- KV used/free/estimated;
- model/runtime residency;
- cache hit/miss/eviction;
- node heartbeat/freshness;
- GPU/RAM/power/temp where available;
- routing decisions/rejections;
- FairShare wait/service/borrow/reclaim;
- relay/direct bandwidth and failures;
- OOM/GPU reset/runtime restart/quarantine.

## Route decision record

Content-free:
- request/session ID;
- requested constraint/policy hash;
- candidate privacy-safe IDs;
- rejection reason codes;
- score components;
- selection;
- fallbacks;
- timing buckets;
- outcome.

## Signed receipts

Completed work can emit signed content-free receipts for accounting/audit:
deployment fingerprint, node/service pseudonym or signed identity as appropriate, usage counters, timestamps/buckets, outcome, lease/request IDs and hashes/commitments. Never include prompt/output plaintext.

## Public snapshots

Generate signed aggregate snapshots with freshness metadata. Public UI never silently displays stale state as live.

At scale, browsers receive aggregates/faceted counts/cursor pagination, never millions of raw provider records.
