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

## Normalized request observations (internal domain v1)

`contracts/request-observation.json` and
`schemas/v1/events/request-observation.json` define
`iw.observability.request/1`; the companion rollup schema defines
`iw.observability.rollup/1`. These are additive internal normalized domain
records feeding the existing Rust warehouse, not new HTTP/export APIs, Link
carriers, or public response schemas. Existing wire contracts remain unchanged.
Rust owns global normalization; the existing Go gateway contributes its own
bounded edge observations and authorized reads under the observability ADR.
New runtime acceptance AC-REQOBS-01..08 is **owed**.

Every record is closed-schema, `visibility: internal`, at most 64 KiB, and
rejects duplicate JSON keys recursively before decoding. IDs are bounded
canonical metadata (128 printable ASCII characters), never arbitrary caller
labels, request/response text, errors, environment maps or addresses. The
visibility marker is not an authorization grant. Internal node/GPU identities
require existing operator authorization and MUST NOT be served publicly.
Publication remains a separate allowlisted projection under spec58; this
contract introduces no publication policy or public serializer.

### Terminal identity, dataset and counting

A terminal event carries event_id, source_gateway_id, producer_epoch, sequence,
observed_at and metric_definition_version. The immutable event key is
(source_gateway_id, producer_epoch, event_id). Replay preserves the original
key and payload, including across a writer restart. Identical replay is a no-op;
a different payload under that key is rejected and counted. Event sequence aids
ordering but is not request identity. Wall time buckets observations; it cannot
establish a measured cross-machine duration.

observation_kind is one of ingress_terminal, attempt_terminal, hop_terminal.
The lineage object contains scope, logical_request_id, attempt_id,
parent_attempt_id, hop_id, parent_hop_id, trace_id, transport_request_id and
ingress_gateway_id. All identity fields are explicit nullable values; missing
historical lineage stays null. A trusted logical ID is minted once by the entry
gateway and remains unique across restarts. Reusing a caller's transport or trace
ID does not reuse that logical ID. Trusted attempts/hops have their own unique
attempt identity; a forward hop also has hop_id. Authenticated source binding
and trusted parent propagation establish lineage; client-supplied strings do not.

Only ingress_gateway_id emits that logical request's ingress_terminal event.
Physical execution attempts emit attempt_terminal; forwarding/retry-dispatch
observations that do not own execution emit hop_terminal, even if they have a
local attempt ID. Within each source, terminal logical/attempt/hop identities
are unique across restarts. A second event ID for the same trusted terminal fact
is rejected rather than counted again. Cross-hop reobservation relays the
original event or produces a separately typed hop event; it never manufactures
another ingress outcome. A batch call is one ingress request, regardless of
item count. Active/unfinalized work belongs to live state and does not become
historical success/failure through this terminal-only schema.

Lineage scope local_unlinked permits historical local evidence but forbids
claimed global logical ID, ingress owner or parent linkage. Its rates are
explicitly local; it cannot be included in trusted logical-request totals.
The sampling value all_terminal means the producer offers every terminal record
in that scope; losses remain explicit. diagnostic_only is a biased trace sample
and is excluded from reliability/throughput rate denominators.

Dataset is production, controlled or unknown. controlled requires the existing
canonical benchmark_sample_id; other datasets leave it null. Dataset assignment
comes from the trusted execution path, never a caller hint. Unknown historical
origin is not relabeled production. No rollup or percentile distribution mixes
these datasets.

### Outcomes and missing evidence

outcome.status is success, service_failure, rejected, cancelled or unknown.
Separate http_status (nullable), completion, reason_code, layer and phase
preserve the distinction between transport status and protocol completion.
Success requires protocol_success with reason none; HTTP 200 alone proves
nothing. A 200 stream ending in BACKEND_STREAM_FAILED is service_failure.
Cancellation requires cancelled completion; rejection requires confirmed
pre_execution_rejected. Unknown completion is unobserved. Transport failure
may establish a failed client-visible request while remote execution remains
unobserved; it does not prove the backend stopped.

reason_code reuses the exact frozen protocol error taxonomy, Link HTTP failure
codes and inference-stream timeout codes, plus explicit none/unknown. Layer is
ingress/gateway/link/node/backend/unknown/none, and phase is
queue/connect/prefill/decode/execution/unknown/none. Queue timeout is represented
by its existing deadline code plus queue phase, rather than a new error string.
Do not extract causes from free-form error text.

Success share is successful / (success + service_failure + rejected + cancelled).
Service failure rate is service_failure / (success + service_failure).
Unknown has its own count, and a zero denominator means an unknown ratio, not
zero. These definitions apply independently to each observation kind and
lineage scope; they never turn an execution attempt or hop into another user.
Inference success is not evidence of task-quality success.

### Monotonic phases, tokens and attribution

The normalized container maps the earlier timing vocabulary to bounded timings
spans and rollup metric names ending in `_ms`. A record has at most 32 spans,
with unique span_id and phase, nullable local parent_span_id, measurement,
clock and semantics. Parent references stay inside that event and are acyclic;
parent hop/attempt IDs establish cross-process lineage separately. No raw clock
ticks are compared between processes.

`contracts/request-observation.json` freezes phase names for local queue,
route processing, connection acquisition, DNS/TCP/TLS, upload, writer queue,
upstream wait, headers, first SSE event, first useful output, first visible
output, engine prefill/decode/execution, completion, link RTT and unattributed
cost. Each measurement is `{value?, basis, source}` in integer milliseconds.
Unknown/unsupported forbids value; measured zero remains a known sample.
Known durations require a local_monotonic or producer_monotonic clock.
Semantics is frozen per phase by contracts/request-observation.json: headers,
first SSE/useful/visible output and completion are offset_from_start; upstream
wait is inclusive_wait; link RTT is round_trip; all remaining phases are interval.
A producer cannot change semantics while retaining the same phase/metric name.
Offsets use that producer's request-start origin; parent inclusive waits already
contain child queue/execution, and must not be added to child intervals. Link
round trips include scheduling/ack cost and are not pure network latency.
TLS/connect setup on a reused connection is not charged again to each request.
Missing phases are unknown, never fabricated zero-cost spans.

Engine prefill/decode/execution intervals require measured engine_reported
provenance and the engine's monotonic clock. An HTTP first-token proxy is only
first_useful_output with offset_from_start semantics. TTFT includes upstream
queue/network work and cannot become engine_prefill. Existing benchmark records
that assigned TTFT to prefill without proof remain proxy/legacy-unknown evidence;
this contract authorizes no retroactive conversion. First SSE/headers/keepalive,
first useful output and first visible answer remain separate observations.

Tokens retain input_total, output_total, cached_input, context_consumed,
context_limit, processed_prefill_tokens and decode_output_tokens as quantities
with the same explicit basis and a finite source. They describe tokens, not SSE
chunks or characters. Cached input is a subset of total input; decode output is
a subset of total output. Never add either subset to its total. Unknown usage
and unsupported non-text token metrics have no numeric value. Configuration
limits are declared limits, not observed context consumed. True prefill rate
uses engine-processed tokens and engine-prefill duration; decode rate uses its
matching decoded-token count and interval. Partial/unknown denominators stay
visible. Aggregate output throughput uses exact reported output and covered
wall-clock duration, not a sum of overlapping per-request execution times.

Attribution captures nullable model/artifact/quantization/tokenizer,
runtime instance/name/version/image, deployment/configuration fingerprint,
resource/workload profile, cluster/node, GPU SKU/count/resource set and load
generation at observation time. Null means unknown, never "all configurations".
An empty known GPU set means CPU-only; null means missing attribution. Known
GPU count and resource set agree. Reuse canonical configuration identities; no
raw launch/environment/settings map is permitted. Never join an old event to
today's mutable configuration or infer GPU placement from a model name. Missing
exact identities exclude hardware ranking while preserving health evidence.

### Existing capacity HTTP carrier

The negotiated capability is `iw.observability-capacity/1` (hyphenated to match
federation capability grammar). On an authenticated node HTTP heartbeat, the
optional top-level `observabilityCapacity` member carries the unchanged canonical
`iw.observability.capacity/1` node snapshot. The capability token and payload
schema identifier are deliberately different. Decode the raw member strictly,
including recursive duplicate-key rejection, before accepting it under the
current authenticated node registration. A successful HTTP registration rotates
the producer epoch every time; a prior incarnation cannot regain freshness by
replay. Existing node/fleet schemas and ownership checks remain unchanged.

The current producer carrier is HTTP only; a Link carrier is unsupported and its
operational proof remains owed. Unowned physical exporters may report observed
hardware but cannot claim available owner CPU or serving offers. This transport
record does not close deployment/registration/admission proof gates. See
`contracts/observability-capacity.json` transport metadata.
