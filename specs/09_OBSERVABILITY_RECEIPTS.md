# 09 — Observability, Route Explanations, Receipts and Public Snapshots

## Correlation

Every request/session/job carries stable correlation IDs across gateway, scheduler, relay, node and backend.

An operator disclosure that assigns a separate diagnostic-record ID MUST label it
separately from the transport request ID and expose both when known. A record ID
is not a substitute for the request ID written in a downstream transport log.
Missing historical correlation is explicit, never synthesized.

## Inference stream timeouts and incident diagnostics

The normative vocabulary and acceptance cases are in
[`contracts/inference-stream-reliability.json`](../contracts/inference-stream-reliability.json).
These requirements extend IW-OBS-001 and IW-OBS-002; they do not create a new
scheduling plane, qualification claim, or production deployment approval.

Heartbeat freshness proves control-channel liveness; it MUST NOT determine how
long a healthy inference may prefill or pause. Inference has separately
configured, finite inactivity and execution bounds. The initial operational
defaults are 180 seconds of inactivity and 1800 seconds of execution, not
hardware performance claims. Queue budgets are not execution deadlines.

Headers, SSE comments/keepalives and role-only/empty metadata do not establish
generation. Prefill allowance remains applicable until nonempty content,
reasoning, or a tool/function-call delta establishes useful output. After that,
only useful output refreshes the generation progress clock. Parsing is bounded,
incremental across network/HTTP chunk/SSE boundaries, and must not accumulate
the inference response. An explicit execution deadline still applies to an
otherwise steadily progressing request; reservation reclamation remains governed
by invariant 37 and must not be confused with this request policy deadline.

Cancellation and observed link loss stop work and release resources promptly,
independently of either inference timeout. A timeout after HTTP headers have
been committed remains a failed attempt even when the status is 200. For SSE,
the serving hop emits a bounded structured error event when possible, never a
success completion marker. HTTP chunk framing remains valid. The event carries
an allowlisted code (`inference_idle_timeout` or `inference_request_timeout`)
and safe numeric measurements; arbitrary downstream error text is not telemetry.
An intermediate hop may report a downstream-reported timeout, but MUST NOT
claim which deeper hop failed merely because a route was selected.

Authenticated diagnostics provide effective local timeout settings with units
and provenance, separate observed downstream settings or explicit unknown,
finite failure reason/path/phase totals, and bounded recent failure samples.
Samples carry correlation IDs, selected route/backend where the audience is
authorized, effective timeout, elapsed/silent duration and phase. No request or
response text, credentials or user/session identities enter these statistics.
Prometheus labels are finite classifications, never request or caller IDs.
Counters disclose process-start/reset time; rolling summaries disclose the exact
half-open interval, recording source, capacity, eviction and coverage limits.
Neither historical failures nor since-start counters are presented as current
health. Recording and diagnostics remain bounded and cannot block admission.

Admission diagnostics distinguish current occupancy from cumulative rejection
reason/scope, expose effective policy/queue limits, and count missing versus
explicit subdivision metadata without exposing the identifiers. Shared
credentials intentionally share an authenticated parent. Omitted agent/session
metadata uses the parent's default subdivision; diagnostics MUST NOT fabricate
per-request identities to bypass that limit. User or FairShare limits cannot be
evaded by subdivision fan-out.

### Operational basis, 2026-10-20

Zapp was the production edge, and Hive was the serving peer. The closed
10:27:05–10:42:05 PDT window contained 39 upstream errors on Hive's Qwen 27B
route, 24 local queue timeouts, and three downstream busy outcomes. Four
correlated transport requests ended 30.09–30.26 seconds after first response
bytes; Hive revision `c673fad2ea3c5e122709854a6c118d7d4dd86d6e` reused the
30-second heartbeat freshness interval for stream silence. The peer connector
reported an HTTP chunked response ending before its final chunk. The 24 local
timeouts instead exhausted the agent bucket at 4/4 and waited 90 seconds.
These are incident measurements, not defaults or present-state assertions.

**Specification defect:** this spec previously required generic error counts and
TTFT but did not distinguish control freshness, first inference progress,
inference silence, or a diagnostic ID from a transport ID. Following it literally
allowed an apparently healthy 200 response to end early with only
`unknown / transport_failure`, forcing manual cross-host tracing. The explicit
semantics and evidence surfaces above repair that omission.

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

## Persisted metadata and performance lineage

The 2026-10-20 [ADR](../decisions/2026-10-20-observability-capacity.md) and
`contracts/observability-capacity.json` add AC-OBS-01..09. Immutable event_id
identifies one observation; retransmitting that event is idempotent. Distinct
attempt_id values are distinct physical attempts under logical_request_id;
trace/request IDs correlate transport hops but do not collapse retries. An edge
reobserving a downstream event preserves its origin identity instead of creating
a second global event. Missing lineage stays unknown, never inferred from text,
wall-clock proximity or a reused client request ID. Logical, attempt and hop
counts have separate denominators and declared recording coverage.

Durations use monotonic local clocks and milliseconds with source/basis. Record
local queue, upstream wait, response headers, first useful output and completion
separately; first headers is not TTFT. Do not subtract unsynchronized clocks or
infer remote prefill/decode from edge timings. Unknown downstream measurements
remain unknown. Existing spec58 metric envelopes and finite failure vocabularies
apply; request IDs and arbitrary model/error text never become metric labels.

For the new observability family only, initial policy retains its content-free
aggregate history for 90 days and its bounded operator diagnostic metadata for
7 days, using explicitly namespaced records in existing storage/rollup paths.
These defaults apply only to that new family and its derived caches/exports;
they do not shorten legacy request/benchmark retention (including existing
730/365-day policies), alter shared backup lifetimes, or authorize retroactive
purge. Any migration of existing records, caches or backups requires a separate
reviewed retention migration with its own deletion authorization. Shorter tenant
policies apply within the new family. Queue, batch, query-window, page, grouping and byte
limits must be finite and visible. Drop/eviction/coverage counters and store
failure are explicit; recording never blocks inference admission. Prompt/output
bodies, credentials and private identities are excluded from public data.

The frozen metadata names are event_id, logical_request_id, attempt_id, trace_id,
transport_request_id and source_gateway_id. Optional unavailable lineage fields
are omitted, not synthesized. Timing names are local_queue_ms, upstream_wait_ms,
response_headers_ms, first_useful_output_ms and completion_ms. Each uses the
quantity provenance shape (value/basis/source), with unknown values absent.
Headers/useful-output/completion durations share the local attempt-start origin;
queue and upstream wait are separately measured intervals and may overlap other
measures, so consumers must not sum them into an invented total. New field names
require a versioned contract update; arbitrary timing label strings are forbidden.
