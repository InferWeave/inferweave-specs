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
