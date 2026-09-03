# 12 — Model Tuning, Qualification and Capacity Profiles

Benchmarking is a first-class node subsystem because routing capacity must come from evidence.

## Fingerprint

Capture hardware/topology, RAM/VRAM, OS/kernel, driver, ROCm/CUDA/Vulkan, runtime/backend version, model/hash, tokenizer, precision/quantization, KV precision, attention, TP/PP, speculative/MTP, environment and launch command.

Material fingerprint changes invalidate qualification.

## Metrics

Never report one ambiguous TPS value. Record:
- TTFT;
- prefill TPS;
- decode TPS;
- aggregate decode TPS;
- requests/sec;
- streaming update gaps/tail latency;
- correctness/tool/JSON success;
- memory/KV;
- power/temperature/clocks where available.

Test cold, first, warm, prefix hit and prefix miss.

## Workloads

Versioned workloads:
- synthetic context;
- normal chat;
- source code;
- AutoSpec/Pi repository context;
- tool-heavy agent;
- structured output;
- long context.

## Matrix strategy

Do not brute-force every combination initially. Baseline backend first, then batching/attention, then quantization/placement, context, then speculative/MTP. Record individual samples plus distribution statistics.

## Profiles

Generate qualified profiles such as:
- lowest-latency
- interactive-agent
- highest-single-user-decode
- highest-aggregate-throughput
- long-context
- memory-efficient
- background-batch

Ordinary routing selects only qualified profiles. Experimental profiles remain lab/canary-only.

## R9700

Preserve explicit R9700 testing for current Qwen3.8-27B paths, including ROCm/Vulkan, vLLM/AITER/current compatible stacks, FP8/MXFP4 where supported, KV precision, prefix cache, continuous batching, MTP/speculation and dual-GPU TP/replica comparison. Exact runtime/kernel/container revisions are data, never hard-coded eternal architecture assumptions.

## Failure gates

Invalidate/flag runs on schema/correctness failure, OOM, backend crash, GPU reset, invalid numerics or corrupt output. Require soak and rollback gates before activation.
