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
