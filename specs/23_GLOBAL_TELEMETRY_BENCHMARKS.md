# 23 — Global GPU Telemetry, Configuration Fingerprints and Benchmark Warehouse

## Goal

InferWeave maintains a complete continuously updated technical inventory and telemetry history for every participating GPU so it can:
- route safely;
- compare hardware/runtime/model configurations;
- qualify deployments;
- estimate capacity;
- detect regressions;
- generate global benchmarks;
- calculate contribution/work/energy facts.

## Static / slowly-changing GPU inventory

Per physical GPU:
- stable internal GPU ID and privacy-safe public ID;
- node/host ID;
- vendor, model, architecture, PCI/device IDs;
- VRAM capacity/type where available;
- board/vendor identifiers;
- PCIe generation, width and negotiated link;
- NUMA locality;
- peer/interconnect topology;
- supported data types/features;
- driver version;
- firmware/VBIOS version when safely available;
- power limit range/default;
- telemetry capability flags.

Host:
- CPU/model/core topology;
- RAM;
- NUMA;
- storage devices/capacity/performance profile;
- OS/kernel;
- network interface/link/bandwidth class.

## Software/runtime fingerprint

For every active deployment/profile:
- model family/name;
- exact model revision/hash;
- tokenizer revision/hash;
- quantization/weight format;
- activation precision;
- KV precision;
- runtime/backend name and exact version/commit;
- llama.cpp/vLLM/AITER/ROCm/CUDA/Vulkan or future equivalent versions;
- PyTorch/framework version;
- kernel/custom kernel package and commit;
- container digest;
- launch command and normalized environment variables;
- attention implementation;
- batching/microbatch settings;
- chunked prefill;
- prefix caching configuration;
- TP/PP;
- speculative/MTP/drafter model/revision/settings;
- maximum tested context;
- safety/resource envelope;
- benchmark/qualification suite version;
- benchmark dataset/task name and exact revision/version (for example LAMBADA, MMLU or other suites when used).

A material fingerprint change triggers requalification.

Background benchmark records also retain execution mode and co-residency basis.
Shared exploratory/correctness/compatibility evidence cannot be merged into an
exclusive serving-performance baseline. See spec 33 for live scheduling policy,
resource ceilings, resumable cell evidence and restoration requirements.

## High-frequency telemetry

Collect where supported:
- timestamp;
- GPU utilization;
- memory controller/utilization;
- VRAM used/free/reserved;
- temperature(s);
- hotspot temperature;
- power draw;
- power limit;
- clocks;
- fan speed;
- throttle reasons;
- ECC/error counters;
- GPU reset/recovery events;
- host CPU/RAM/swap;
- disk/scratch pressure;
- network bytes/RTT/loss observations;
- backend queue depth;
- active/resident/queued seats;
- KV used/free/reserved;
- model residency/load state.

## Per-request measurements

Link every request/attempt to:
- prompt ID;
- deployment fingerprint;
- physical GPU(s);
- session;
- route decision;
- queue/admission;
- TTFT;
- prefill tokens/time/TPS;
- decode tokens/time/TPS;
- aggregate throughput contribution;
- streaming gap/tail percentiles;
- input/output tokens;
- cache hit/uncached tokens;
- resource high-water marks;
- energy estimate/measured joules where available;
- outcome/error/cancel/preemption;
- owner vs shared-network workload;
- contribution/accounting units.

For streaming failures, distinguish heartbeat freshness, prefill, useful-output
inactivity and an explicit execution deadline. Preserve the serving timeout's
allowlisted reason, effective limit and silent duration through relays; a 200
status after committed headers is not successful completion. Operator summaries
show both diagnostic and transport request IDs, selected serving route, recording
coverage and counter reset time. See spec 09 and
`contracts/inference-stream-reliability.json` for the vocabulary and acceptance
cases. Never infer another gateway's effective limits from this gateway's config.

## Storage

Use PostgreSQL initially for:
- inventory/fingerprints;
- qualification metadata;
- request facts;
- raw telemetry at bounded resolution;
- aggregated rollups.

Partition high-volume tables and roll up raw telemetry over time:
- seconds/minute-level raw for recent operations;
- minute/hour/day rollups for long-term comparisons.

If PostgreSQL becomes the bottleneck, split the telemetry warehouse behind the same logical API without changing node/gateway contracts.

## Global benchmarks

Produce comparisons by exact dimensions:
- GPU model/topology;
- runtime/backend/version;
- model/revision;
- precision/quantization;
- context;
- concurrency;
- workload class;
- cache state;
- region/network class;
- power/thermal envelope.

Never publish one universal TPS number without these dimensions.

Outputs:
- p50/p95/p99 TTFT;
- prefill/decode/aggregate TPS;
- requests/sec;
- energy/token or energy/request where measurable;
- memory efficiency;
- context capacity;
- reliability/OOM/reset/error rate;
- owner preemption effects;
- price/contribution efficiency if enabled later.

## Qualification and regression

A node/profile is production-qualified only from measured evidence.
Flag version/config changes and regressions. Store raw benchmark samples plus summary stats.

## Contribution analytics

Contributor credit can use verified accepted-work facts:
- successful useful work;
- measured GPU time;
- tokens/pixels/steps as workload-appropriate;
- energy estimates;
- latency/reliability;
- challenge/verification results.

Self-reported performance alone is never authoritative.

## Privacy

Global public benchmark data must not expose:
- prompt bodies;
- user/session identities;
- private node addresses;
- exact private workload timestamps when that creates traffic-analysis risk.

Internal authorized operators may correlate prompt IDs with performance for debugging/benchmark replay.


## Persistent resource history

All telemetry/benchmark facts must reference the stable resource identity hierarchy in `26_RESOURCE_IDENTITY_REDISCOVERY.md`.

Temporary Slurm allocation/worker IDs are retained as dimensions, while lifetime GPU performance history aggregates primarily by stable `gpu_id` plus hardware/software/deployment fingerprint.

## Complete collection and capacity provenance

The initial observability rollout restores supported inventory, runtime/model
fingerprints and live per-GPU sensors through existing producers, then spec46
memory in observe mode. A scalar carries its source, unit and measured/derived/
estimated/declared/unknown/unsupported basis; unknown and unsupported have no
numeric value. A zero requires an actual zero observation. NVIDIA validation
must name pinned hardware/software/profile and sensor coverage; AMD validation
remains separately owed. CPU utilization and entitlement are different measures.

The read-only `iw.observability.capacity/1` schema and spec04 define entitlement
and context offers. Use the owner's report, preserve epoch, sequence and age,
and never deduce admission from aggregate VRAM or fleet utilization. The bounded
edge-persistence ADR permits existing Go local observations with local coverage;
Rust remains the global normalization and warehouse authority. Request history
uses the spec09 event/attempt/logical lineage and provenance, not duplicate hop
counts. Initial retention for explicitly namespaced new-family records only is 90 days
aggregate / 7 days diagnostic metadata, with explicit coverage and stricter
policy overrides. Existing warehouse/request/benchmark records, legacy 730/365-day
policies, shared caches and backups retain their existing policy. This change
authorizes no retroactive purge; changing them requires a separate reviewed
retention migration.

## Internal request-observation rollups

`contracts/request-observation.json` and
`schemas/v1/events/request-observation-rollup.json` define the internal
`iw.observability.rollup/1` domain consumed by Rust storage/normalization.
No new public or export endpoint is defined. Go-local edge windows remain
explicitly local and cannot become a second global warehouse.

A rollup has an immutable source_gateway_id/producer_epoch/rollup_id identity,
revision, metric_definition_version, exact attribution, dataset,
observation_kind and lineage_scope. revision replaces that row atomically;
replaying it never adds another delta. Same revision with changed payload is
rejected. Later revisions preserve dimensions/window and coverage.counter_epoch and advance as_of;
sealed rows cannot be revised through ordinary ingestion. Event identities and
terminal-fact uniqueness are checked before aggregation (spec09), including
replays after restart and repeated caller transport IDs.

Windows are UTC half-open [window_start, window_end), aligned to 300/3600/86400
seconds for 5m/1h/1d. Boundaries use canonical whole-second UTC timestamps
without fractional seconds; interval/grid checks use exact duration arithmetic.
as_of is at least window_end. A sealed row is finalized;
unsealed rows may receive late valid events before the owner's persisted sealing
watermark. Beyond a seal or the retained horizon, late replay is rejected and
counted, not used to recreate expired diagnostics or double-count aggregates.
No numeric lateness allowance is invented here. Sealing/deduplication evidence
must outlive the retained aggregate it protects. Pruning 7-day diagnostics must
not delete/rebuild away independent 90-day materialized rows.

counts contains success/service_failure/rejected/cancelled/unknown and total.
Each ratio preserves its numerator and denominator using spec09's definitions.
Each optional metric row identifies metric, unit, basis and measurement source,
plus eligible_count, known_count, missing_count, unsupported_count, sum and a
versioned histogram. For each included metric, provenance rows partition all
terminal observations exactly; every row has eligible = known + missing +
unsupported. An absent metric means not reported, never zero. Aggregate sum=0
with known_count=0 is the empty accumulator, not evidence of a zero measurement.
A mean requires positive known_count and uses sum/known_count. Known sources and
estimated/declared sources are kept in separate provenance rows. Phase semantics
are part of metric_definition_version through the frozen phase-to-semantics map;
an interval cannot be merged into an offset metric with the same phase name.
Rollups apply the same exact GPU resource-count reconciliation as events.

Histograms use the frozen bounds in `contracts/request-observation.json`:
non-cumulative disjoint integer bins (previous bound, current bound], with zero
included in the first bin and a final overflow bin. Counts sum to known_count;
sums must be consistent with the occupied intervals. Millisecond and token
histograms have separate v1 boundaries. Merge only identical metric/unit/bin
version/source/basis/dataset and compatible exact attribution/counting scope.
Merge counts and sums with checked integer arithmetic, then derive quantile
intervals; do not average p95s or means without sample weights, invent within-bin
precision, or merge arbitrary differently bounded histograms. No scalar percentile
is an authoritative rollup input.

The initial composable unit is one source/producer epoch/counter epoch over
nonoverlapping windows, preserving configuration and provenance. Adjacent 5m
windows can contribute to a complete hour; incomplete coverage remains explicit.
Overlapping revisions/5m-vs-1h windows cannot be added. A fleet projection needs
prior canonical event deduplication and a separately accounted union of source
coverage; summing per-source durations or hop totals is not a global denominator.
Different configuration, dataset or counter-reset boundaries remain separate
rows. Broader comparisons cannot reinterpret unknown attribution as a wildcard.

coverage identifies status, counter_epoch, covered_ms, unknown_ms,
expected_events (nullable), accepted_events and nullable dropped_events,
write_failures, duplicates_ignored, replay_conflicts, late_events_rejected,
trace_sampled_events, trace_dropped_events and ingestion_lag_ms. Covered and
unknown duration partition the window; accepted_events equals total. Expected
is the independently observed eligible terminal population, not a copy invented
from stored rows. Complete coverage requires a known expected count equal to
accepted and no known/unknown recording loss or conflict. Unknown counter values
are null, never zero. Counter values apply to this row's source/window, not
since-start totals silently assigned to every bucket. Trace sampling/loss is
separate from all-terminal recording; biased diagnostic traces cannot establish
unbiased request rates. Capture/write/query work stays bounded and cannot block
admission; 64 KiB rows, 128 metric provenance rows and the existing bounded writer
and query policies apply.

These new-family records alone use 7-day diagnostic / 90-day aggregate retention.
Legacy 730/365-day history, existing benchmark evidence, static configuration
catalogs and shared backup policy remain unchanged. No retroactive purge or
new content recording is authorized; a separate reviewed migration and deletion
authorization is required for legacy retention changes. Runtime, PostgreSQL,
restart, sealing and retention proof for AC-REQOBS-01..08 remains **owed**.

### Additive failure-rollup companion

`schemas/v1/events/request-observation-failure-rollup.json` defines
`iw.observability.failure-rollup/1`, an internal companion to the unchanged
`iw.observability.rollup/1`. The decision is
`decisions/2026-10-20-request-failure-rollups.md`; AC-REQOBS-09 applies to
IW-OBS-001, IW-TEL-001 and IW-BENCH-002 through P1-T20/P2-T03.

The companion has exactly `schema`, `visibility`, `parent` and `breakdowns`.
`parent` binds source_gateway_id, producer_epoch, rollup_id, revision, sealed and
fingerprint. All dimensions, window, metric version and coverage are inherited
from that exact parent; no companion copy can change them. A missing companion,
parent mismatch or unsupported companion means failure breakdown **unavailable**,
not zero; an older valid v1 parent remains readable on its own. A validated
companion with all-zero maps and zero parent non-success counts is observed zero.

`breakdowns` requires exactly service_failure, rejected, cancelled and unknown.
Each status requires complete, closed `reason_counts`, `layer_counts` and
`phase_counts` maps. Every value is a nonnegative safe integer; every map sums
exactly to that status's parent count. Reasons use the existing event outcome
reason_code enum minus `none`, including explicit `unknown`. Layers and phases
use the complete existing event outcome enums, including `none` and `unknown`;
`none` is valid in a non-success event's layer/phase and must not be discarded or
reclassified. The timing-span phase vocabulary is a different vocabulary and
must not be substituted. No free-form error text or unmappable synthetic reason
category is introduced. These are marginals, not a general joint distribution.

Each status also requires `timeout_phase_counts`: exactly DEADLINE_EXCEEDED,
BACKEND_TIMEOUT, inference_idle_timeout and inference_request_timeout, each
mapping every existing outcome phase to a safe integer count. Each reason row
sums to its reason_counts value; for each phase, the sum across timeout rows
cannot exceed phase_counts. Queue-timeout count is the checked sum of the
`queue` cells in this table, never an intersection inferred from independent
marginals. A missing timeout reason in source instrumentation remains unknown;
the consumer cannot manufacture a timeout from HTTP status or elapsed time.

Only validated, canonical, deduplicated `all_terminal` events in the exact parent
cohort contribute. Diagnostic-only events never enter either denominator, and
retries, attempts, hops, datasets and source/producer epochs keep their existing
counting boundaries. Parent coverage has its independent expected-event/drop/
lag evidence; a complete set of reason-map keys or an absence of failures does
not prove complete event capture. Source capture and query-health coverage must
remain independently visible wherever a projection presents these counts.

The companion is at most 65,536 UTF-8 bytes before parsing. Reject duplicate
object keys recursively, invalid UTF-8, nonfinite/fractional/unsafe numbers,
unknown properties, missing map keys and integer overflow. Checked addition is
required for each marginal, cross-table row/column and merge; refuse the entire
pair on overflow, without clamping, wrapping or partial persistence.

#### Canonical parent fingerprint

`iw-parent-canonical-json/1` serializes the entire validated parent value, including
coverage, using these fixed rules: recursively sort object keys by Unicode scalar
value; preserve array order; emit no insignificant whitespace; use lowercase
`true`, `false`, `null`; encode safe integer values as ordinary decimal integers
without a plus sign, leading zeroes, fraction or exponent. Parent wire numbers
must be parsed as exact decimals before validation/canonicalization: equivalent
`1`, `1.0` and `1e0` normalize to `1`, and integer negative zero normalizes to `0`.
This preserves frozen v1 mathematical-integer semantics; fractional or unsafe
values are rejected before any binary-float rounding. Companion integer counters
retain their strict integer-only encoding. Strings emit Unicode
scalars directly in UTF-8, except quote and backslash use `\"` and `\\`, controls
U+0008/0009/000A/000C/000D use `\b`/`\t`/`\n`/`\f`/`\r`, and other U+0000..001F
use lowercase `\u00xx`. Slash is not escaped; non-ASCII characters are not
ASCII-escaped; unpaired surrogates are refused; Unicode normalization is not
performed. The fingerprint is `sha256:` plus lowercase hexadecimal SHA-256 of
those bytes. Input key order and whitespace are immaterial. The fixed Unicode,
escaping and fingerprint vectors are in
`conformance/request-observation-failure-rollup-vectors.json`.

#### Pair lifecycle, retention and publication boundary

At each 300/3600/86400-second resolution, parent and companion are an atomic
materialized pair: insert, revision replacement, sealing and prune succeed or
fail together. Same parent identity/revision with a changed companion is a
conflict even if its marginal totals still match. A later unsealed revision
replaces both payloads and their fingerprint together; it never adds a delta.
The existing immutable dimensions, monotonic as_of and counter-epoch rules
apply. Ordinary ingestion cannot revise a sealed pair. Read a consistent pair
snapshot, never a new parent joined to an old companion. Aggregate replacement
across all three resolutions for one accepted terminal fact must be transactional
with its identity/terminal-fact deduplication evidence; an injected write failure
must leave none of the affected pairs partially updated.

Retain every companion for exactly its parent's new-family aggregate lifetime
(default 90 days, stricter owner policy wins). Pruning 7-day event diagnostics
must leave the materialized failure companion and its parent intact. Retain seal
and replay evidence at least through the aggregate they protect. Before accepting
an event, consult the persisted late-ingest/sealing watermark and the retained
window horizon for every affected resolution; reject/count an event crossing a
closed or expired boundary atomically before any event/dedupe/pair mutation.
Pruning a diagnostic or aggregate row never clears the fence or permits a late
replay to recreate it. Legacy 730/365-day records and shared backups remain
untouched. Failure companions introduce no second retention namespace or public
export authority.

Public projection, if separately authorized, needs authorized principal/cohort
evidence and the existing privacy policy for **each published cell**, including
status, reason, layer, phase and timeout-phase intersections. A parent cohort's
request/principal threshold does not authorize a sparse subcell. Suppress cells
without sufficient evidence, apply complementary suppression to prevent
reconstruction from totals/marginals, and avoid identifier/timestamp drill-down
that defeats aggregation. Do not store principal identities in the companion.
There is no public endpoint or publication approval in this contract.

Offline schema, vocabulary, parent-binding, conservation, strict decoding and
all-terminal mapping checks are **proven** by `tests/smoke/test_failure_rollups.py`
and the fixture/vector validator. Runtime database transaction, restart, all-three-
resolution seal/prune/watermark fencing, bounded ingestion and per-cell public
privacy tests remain **owed**; this offline proof does not close those gates.

### Private HTTP carrier for normalized observations

The additive private carrier is `contracts/private-observability.json` and
`openapi/private-observability.{yaml,md}` (AC-PRIVATEOBS-01..06). Its single-event
POST binds a current authenticated gateway-role node to an authorized source,
retained producer epoch and trusted lineage; its GETs expose validated internal
diagnostics and exact parent/failure bundles only to existing operator authority.
Enforce the 64 KiB event bound before generic body buffering, reject duplicate
security headers before map collapse, and acknowledge only durable acceptance or
identical durable replay. Event/rollup/failure v1 shapes remain frozen.

Publisher outbox identities survive restart until ACK; independent capture/drop
checkpoints establish coverage, never accepted-row counts. Bounded snapshot
pagination preserves query identity and parent revisions, with explicit missing
companions and read health. All routes default disabled; production collection
requires paired generation, atomic revision/seal/prune and persisted late-ingest
fences first. Public publication authority and retention scope are unchanged.

## SpeedRequests coverage identity and evidence

Coverage is bounded and advisory. `contracts/benchmark-speed-execution.json`
defines v2 separately from legacy v1; never reinterpret v1 concurrency, whose
existing actual/per-engine wording is an objective, as measured backend generating
concurrency or as requested HTTP load. V2 binds an actual saved leaf and exact
suite and specification version, corpus recipe and input hash, load, output and
sampling settings, seed and cache state. Admission prompt-depth ceiling and final
reported prompt-depth window are different axes. Each measured request's final
provider-reported usage establishes the window; calibration usage does not.
Provider usage retains its provenance and is not independently verified token truth.

Requested concurrency C, HTTP overlap, and backend generating concurrency are
separate. For the minimal overlap objective, every measured wave has positive
duration with C HTTP requests overlapping. Intervals are half-open; ends sort
before starts on ties. Report raw overlap maximum and histogram separately. Any
other duration or fraction objective is explicit in cell identity. HTTP overlap
never proves simultaneous backend generation. Unknown backend concurrency remains
unknown, not zero or a wildcard; a backend-generating requirement cannot pass
without appropriate observation.

A validated workload, an exact-known-axis match and qualification are distinct
results. Compare only identical measured dimensions and semantics; mismatches or
unknowns cannot satisfy exact cells. Current v1 capsules lack observed runtime,
GPU and deployment facts; requested provenance and configured declarations cannot
fill those axes. They can be valid workload evidence without exact coverage.
Qualification requires independent measured proof and is never inferred from a
fixture, submitted record or exact match. E7–E9 must provide authenticated owner
observations, additive payload v2 and producer receipts before source-backed exact
coverage can be claimed. Slurm resident attestation remains absent.

## Frozen benchmark execution metadata (2026-11-23)

`contracts/benchmark-trust-controls.json` records the additive future-execution provenance and public comparison obligations under existing IW-BENCH-002/IW-UI-002 owners. Existing measurement/privacy boundaries remain; no alerting, monitoring or notification changes are included after the operator declined publication alerts. Native and review public values must be frozen stored facts; historical unknowns remain unknown.
