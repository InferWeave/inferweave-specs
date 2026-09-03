# 35 — Cluster Simulator, Churn and Chaos Harness

## Goal

Test network behavior at large scale without owning thousands of GPUs.

Synthetic nodes use the same protocol/contracts as real nodes wherever practical.

## Simulated dimensions

- GPU classes/VRAM/topologies;
- model inventories/caches;
- context/KV capacity;
- TTFT/prefill/decode distributions;
- load/warm times;
- power/thermal behavior;
- network RTT/bandwidth/loss;
- NAT/direct-connect success;
- Slurm allocation lifetimes;
- worker joins/leaves/requeues;
- owner reclaim;
- failures/resets/OOM;
- stale heartbeats;
- artifact corruption;
- duplicate identities;
- hostname hardware replacement;
- gateway/relay/site-connector failures;
- demand spikes;
- benchmark workload.

## Scenarios

Minimum scenarios:
- 10,000 ephemeral workers churn;
- 1,000 simultaneous joins;
- mass Slurm expiration;
- regional relay loss;
- gateway restart;
- duplicate GPU advertisement;
- stale lease after worker death;
- huge model cold-start storm;
- popular-model demand shift;
- prompt-store slowdown;
- telemetry-store slowdown;
- partial site partition.

## Determinism

Scenario seeds and configuration are recorded so failures reproduce.

## Assertions

Examples:
- never route to expired allocation;
- never duplicate authoritative GPU lease;
- owner priority always wins;
- no hard policy relaxation;
- gateway byte traffic stays bounded;
- direct-path preference maintained;
- queues bounded;
- prompt durability semantics upheld;
- aggregate telemetry/accounting reconciles;
- benchmark task not lost after preemption.

## Output

Generate:
- event timeline;
- capacity charts;
- routing decisions;
- queue distributions;
- failure/recovery stats;
- data-plane byte ratios;
- invariant violations;
- reproducible scenario artifact.

The simulator is a first-class CI/nightly tool.
