# 39 — Inference Runtime Tuning and Measurement

## Goal

Runtime configuration decides throughput by an order of magnitude or more, and the defaults
that circulate as community recipes are frequently wrong for a given model and card. This
document states what must be measured, what must never be assumed, and the specific errors
that have already cost this project real throughput.

It constrains how a deployment is tuned. It does not choose values: those are per-placement
and belong to the capability record (`03_NODE_BOOTSTRAP_DEPLOYMENTS.md`).

## A throughput figure without a context depth is not a measurement

Decode and prefill both fall sharply with context depth. Measured on one placement,
Qwen3.8-27B Q5_K_M:

| depth | prefill (pp4096) | decode (tg64) |
|---:|---:|---:|
| 0 | 1038 tok/s | 24.8 tok/s |
| 32,768 | 494 tok/s | 16.9 tok/s |
| 131,072 | 195 tok/s | 8.4 tok/s |

Decode fell 66% and prefill 81% across the range a long-context deployment actually serves.

Therefore every published or recorded throughput figure names the depth it was taken at.
A figure quoted without one is treated as taken at depth 0 and as not describing production.
Benchmarks used to qualify a deployment are run at the depth that deployment will serve.

## KV cache quantization is not free, and is often a net loss

Quantizing the KV cache is widely recommended to save memory. On a deployment carrying KV on
only a minority of its layers, the per-step dequantization cost can exceed the bandwidth it
saves. Measured at 131,072-token depth on the same placement:

| KV cache type | prefill | decode |
|---|---:|---:|
| q4_0 | 192 | 8.3 |
| q8_0 | 192 | 13.9 |
| f16 | 195 | 18.5 |

Prefill was unaffected; decode more than doubled from q4_0 to f16. Published long-context
benchmarks report the same direction on other hardware (+0.7% at 6K, -11.9% at 24K, -36.8% at
110K for q4_0 against f16), so this is a property of the technique, not of one card.

KV cache type is therefore a measured choice per deployment, never a default carried over
from another model. Where an uncompressed cache does not fit the target context, the
trade is recorded explicitly: it is a context-length decision, not a free saving.

## Thread count is the physical core count

Setting worker threads to the SMT thread count rather than the physical core count was
measured at a **19x** decode penalty on a CPU-offloaded mixture-of-experts deployment
(0.92 tok/s at 24 threads against 17.6 tok/s at 12, on a 12-core processor).

Memory-latency-bound work degrades catastrophically when two threads contend for one core's
execution ports and memory pipeline. Deployments set threads to physical cores unless a
measurement on that host shows otherwise.

## Accelerator memory needs working headroom

Filling device memory to capacity degrades throughput. Measured on a 32 GB card, the same
model at three expert-placement settings:

| device memory used | decode |
|---:|---:|
| 29.2 GB (3.4 GB free) | 17.6 tok/s |
| 32.6 GB (full) | 11.3 tok/s |
| 32.6 GB (full) | 10.9 tok/s |

Placement is tuned to the throughput peak, not to maximum occupancy. A capacity policy that
optimises for memory utilisation will select the wrong configuration.

## Backend selection is measured, not inherited

Two backends over the same device and model differed by 47% on decode at depth, with the
slower one winning slightly on prefill. Neither is universally correct.

A deployment records which backend it was qualified on. A backend change is a material
configuration change and produces a new deployment fingerprint under
`03_NODE_BOOTSTRAP_DEPLOYMENTS.md`.

## Speculative decoding is workload-dependent and degrades with depth

Draft acceptance, not draft speed, decides whether speculation pays. Measured with two
drafters on one model:

| drafter | code | prose | acceptance (code -> depth) |
|---|---:|---:|---|
| fused multi-token head | 46.7 | 37.6 | 0.63 at depth |
| external block-diffusion drafter | 51.8 | 24.3 | 0.759 -> 0.443 |

The external drafter won on short code and lost by 35% on prose, because its acceptance
collapsed and each draft costs a separate forward pass. Its published headline figure was
measured on a code benchmark and does not generalise.

A drafter is qualified against the workload class it will serve, at the depth it will serve,
and its acceptance rate is recorded alongside its throughput. A drafter whose acceptance is
not recorded is not qualified.

## Mixture-of-experts placement has a hard ceiling

Where expert weights exceed device memory, the resident fraction sets throughput and moving
further work onto the device buys very little. Measured:

| expert layers on device | decode |
|---:|---:|
| 0 of 48 | 15.0 |
| 4 of 48 | 15.9 |
| 8 of 48 | 16.3 |
| 14 of 48 | 17.1 |

Moving 29% of the model onto the device bought 13.7%; the host-memory path dominates
regardless of split. The device-resident case is bounded by device bandwidth over the active
parameters per token, and is an order of magnitude higher.

Consequently a mixture-of-experts deployment whose experts do not fit device memory is
qualified as a low-throughput placement and advertised as such. It is not made fast by
placement tuning, and a capacity policy must not schedule it as though it were.

## What a tuning record must contain

Every qualified deployment records, as measured values and not as configuration intent:

- prefill and decode at depth 0 and at the depth the deployment serves;
- KV cache type, with the measurement that chose it;
- backend and version;
- thread count, and the physical core count of the host;
- device memory used and device memory free at the throughput peak;
- drafter, its acceptance rate, and the workload class it was measured on.

A configuration flag copied from another deployment, another model, or a community recipe is
an assumption. It becomes a specification only once measured on the target placement.
