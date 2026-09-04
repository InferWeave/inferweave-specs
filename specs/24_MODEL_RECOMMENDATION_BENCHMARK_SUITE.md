# 24 — Model Recommendation and Benchmark Suite

## Goal

InferWeave should continuously learn the best model + runtime + deployment profile for each available hardware class and workload.

The system should answer:

- What is the best model for this exact GPU?
- What is the best model for this node/topology?
- What runtime/quantization/KV/context/batching configuration performs best?
- What is best for interactive coding, implementation, planning, review, tools, long context, throughput, energy efficiency, vision or image generation?
- Which untested candidate is most valuable to benchmark next?

There is no single universal "best model".

## Candidate Registry

Track immutable candidates:

```text
model_candidate
model_artifact
runtime_candidate
deployment_candidate
benchmark_suite
benchmark_case
benchmark_run
benchmark_sample
quality_result
performance_result
stability_result
recommendation
recommendation_evidence
```

For each model candidate record:
- family/name;
- exact revision/hash;
- architecture;
- total/active parameters;
- MoE structure if applicable;
- modalities;
- context envelope;
- tokenizer revision;
- license/policy;
- artifact sizes;
- supported quantizations/precisions;
- supported runtimes;
- known backend/hardware restrictions.

## Qualification Funnel

### A. Static feasibility
Reject impossible combinations before expensive work:
- unsupported backend/model;
- license/policy mismatch;
- insufficient VRAM/RAM;
- impossible KV/context envelope;
- unsupported precision/kernel/topology.

### B. Smoke
Verify:
- download/cache/verification;
- load;
- tokenizer/chat template;
- API behavior;
- deterministic tiny correctness sanity;
- no immediate NaN/crash/OOM.

### C. Performance
Measure exact configurations at multiple context/concurrency points:
- load/cold-start time;
- TTFT;
- prefill TPS;
- decode TPS;
- aggregate TPS;
- requests/sec;
- concurrency scaling;
- context scaling;
- cache hit/miss;
- VRAM/RAM/KV high water;
- power/energy;
- thermal behavior;
- errors/resets/OOMs.

### D. Quality
Use versioned evaluation adapters:
- LM Evaluation Harness-compatible tasks;
- coding tasks;
- tool/function-call tasks;
- long-context tasks;
- multimodal tasks;
- private InferWeave/AutoSpec suites.

Every dataset/task/scorer/version is persisted.

### E. Real Pi/AutoSpec Workflow Replay
Mandatory before recommending a model as best for coding-agent workloads.

Replay representative tasks:
- repo understanding;
- specification/planning;
- implementation;
- review;
- test generation;
- bug repair;
- tool use;
- long-context repo work.

Measure useful outcomes, not just tokens:
- task success;
- compile/tests pass;
- defect detection;
- tool-call correctness;
- iterations to success;
- wall time;
- tokens to success;
- independent reviewer score.

### F. Reliability / Soak
Run mixed sustained workloads:
- multiple sessions;
- variable context;
- cache hit/miss;
- cancellation;
- model reload;
- node reconnect;
- Slurm preemption;
- owner reclaim;
- thermal steady state.

## Recommendation Classes

Examples:

```text
best_interactive_coding
best_autospec_implementation
best_planning
best_review
best_tool_calling
best_long_context
best_latency
best_throughput
best_concurrency
best_energy_efficiency
best_memory_efficiency
best_vision
best_image
best_background_batch
```

Recommendations are always tied to a resource envelope.

## Evidence Classes

Every recommendation must declare one:

```text
measured_exact
measured_equivalent
cluster_observed
predicted
unqualified
```

Predicted performance must never be displayed as measured performance.

## Pareto Frontier

Persist multi-dimensional Pareto-optimal candidates rather than flattening everything into a single score.

Dimensions can include:
- quality;
- TTFT;
- decode TPS;
- aggregate TPS;
- concurrency;
- context;
- memory;
- energy;
- reliability;
- load time;
- license/policy.

Named deployment policies choose from the frontier.

## Active Experiment Selection

The benchmark controller should prioritize new experiments using:
- missing exact hardware/model evidence;
- model/runtime release changes;
- uncertainty;
- likely improvement;
- new workload needs;
- benchmark regression;
- available low-priority/ephemeral compute.

Background Slurm capacity is an ideal place for resumable exploration.

## Requalification Triggers

Invalidate/downgrade recommendations when any material fingerprint changes:
- GPU/firmware;
- driver;
- ROCm/CUDA/Vulkan;
- runtime/backend;
- container digest;
- model/tokenizer;
- quantization/KV;
- launch settings;
- topology;
- benchmark suite/scorer version;
- repeated instability.

## Global Learning

A new GPU/node can inherit a lower-confidence recommendation from equivalent cluster evidence, run a shortened confirmation suite, then promote it to `measured_exact`.

## Dashboard

Next.js should expose:
- recommended model/profile per GPU;
- recommended model/profile per workload;
- exact evidence/fingerprint;
- measured vs predicted status;
- Pareto frontier;
- quality/performance/reliability comparisons;
- confidence/sample counts;
- regression history;
- suggested next experiment;
- qualification action.

## API

```text
GET  /api/v1/model-candidates
GET  /api/v1/benchmark-suites
POST /api/v1/benchmark-runs
GET  /api/v1/benchmark-runs/{id}
GET  /api/v1/recommendations
GET  /api/v1/recommendations/resources/{resource_id}
POST /api/v1/recommendations/qualify
POST /api/v1/recommendations/recompute
```

## Explainability

Every recommendation must be reconstructable from immutable evidence:

```text
resource = gpu_...
workload = autospec_implementation
model = ...
deployment fingerprint = ...
benchmark suite versions = ...
quality = ...
p95 TTFT = ...
decode TPS = ...
aggregate TPS = ...
reliability = ...
energy = ...
samples = ...
evidence = measured_exact
```

## Image qualification

The suite also qualifies `modality: image` deployments (spec 14). An image
qualification profile records, per GPU class and precision:
- a latency matrix over `resolution × steps` with measured VRAM, latency and
  images/minute throughput;
- cold-start time (weight load);
- a quality signal from a fixed prompt set scored by independent vision-QA
  (`IW-IMG-002`).

It produces a `benchmark_profile_id` consumable by a `modality: image` manifest's
`validation.benchmark_profile_id`. See
`contracts/image-qualification-profile.example.json`. Recognized runtimes are
enumerated per modality in `contracts/backends.registry.example.json`.
