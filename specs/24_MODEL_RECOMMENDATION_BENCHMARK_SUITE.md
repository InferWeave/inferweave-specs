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
GET  /iw/v1/model-candidates
GET  /iw/v1/benchmark-suites
POST /iw/v1/benchmark-runs
GET  /iw/v1/benchmark-runs/{id}
GET  /iw/v1/recommendations
GET  /iw/v1/recommendations/resources/{resource_id}
POST /iw/v1/recommendations/qualify
POST /iw/v1/recommendations/recompute
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

## Structured tool compatibility suite v1 (2026-10-28)

`contracts/tool-call-compatibility.json` freezes T01–T16, paths, evidence scopes, outcomes and
failure codes; `schemas/v1/runtime/tool-suite-report.json` freezes the closed camelCase report.
Reuse the existing benchmark Store. A `reportId` names its record; `reportSha256` is the hash
of the semantic binary transcript specified in the contract, not of serialized JSON bytes.
No separate benchmark service, scheduler or protocol registry is created.

Reports have schema version 1, suite version `"1"`, 1–32 repetitions and at most 1536 attempts.
Every attempt has a one-based repetition, case, path, scope and outcome. The tuple
(caseId, path, repetition) is unique. Failed, unsupported and owed attempts carry a closed reason;
`qualified` is a decision reason, never an attempt reason. Unknown binding is representable and
persistable but cannot qualify. Nonblank identity strings are bounded in UTF-8 bytes. Synthetic
transport and physical-lifecycle proof do not substitute for `actualModel` generation evidence.

A qualification candidate requires every repetition's actual-model passes for T02/T05/T06 on
`directRuntime` and `gateway`, plus T05 on `agent`, with no failure anywhere in the report.
Required passes have no failure reason. Parallel support requires T04 passes on both direct
runtime and gateway for every repetition. Suite v1 has no forced-choice evidence dimension, so
`forcedChoice` cannot be signed into a qualification even when manually requested. T01–T16
results remain visible as pass/fail/unsupported/owed; this minimum qualifying subset does not
claim completion of every matrix case or authorization for hot swapping.

The complete identity binds model/tokenizer revisions, quantization, runtime implementation and
version, hardware, context/concurrency/output/cache regime, profile/image/artifact/template
hashes, parser/backend and owner/node/instance/deployment/generation/epoch/GPU identities.
Keep unknown values unknown; a node boolean, throughput draft or configuration declaration is
not qualification. Material identity changes invalidate use of the old record. Three repetitions
and one-hour maximum lifetime are unmeasured policy defaults, not reliability estimates.
Native parser fixtures alone never qualify an actual model. Raw command arguments, prompts,
reasoning, outputs, secrets and private node/GPU identity are excluded from public diagnostics.

## Legacy NVIDIA evidence and complete qualification cohorts

The 2026-10-27 operator bundle requests sm61 dual GTX 1080 Ti and sm75 dual
RTX 2080 Ti evaluation through the existing catalogue, immutable benchmark
records, planner, qualification and dashboard. A hardware expectation is not
an enrolled inventory observation or a CUDA build qualification. Published weight
hashes establish declared artifact provenance; qualification still needs hashes
of the actual loaded files and the exact executable/container build.

Qualification policies may specify `minimum_free_vram_bytes_per_gpu` (bytes).
Old policies deserialize with zero for compatibility; zero adds no headroom
protection. Legacy campaigns must explicitly choose and validate a reserve.
A suggested 768 MiB is an unmeasured policy starting point, not a measured safe
limit. For each physical GPU, checked arithmetic must prove non-KV residency +
peak KV + reserve <= current owner-authorized allocatable VRAM. Residency, KV
and allocatable-memory maps must identify exactly the same GPUs; summed VRAM,
missing cards or arithmetic overflow cannot qualify a candidate. This read-only
assessment grants no lease or production-promotion authority.

Quality evidence must cover every applicable quality trial in the configuration
cohort (agent roles or explicitly scored trials; unknown legacy workloads remain
conservative). Successful throughput/context/vision-overhead measurements need
not invent quality scores. A failed or skipped configuration trial, or a missing,
nonfinite or out-of-range applicable quality score, prevents quality passing;
retain throughput observations but report aggregate quality as unknown rather
than a successful-only mean. An entirely throughput-only run has unknown quality,
not passing quality. Equivalent canonical configuration fingerprints are scheduled
once; duplicate planner inputs produce explicit prune records, not repeated work.

Before any remote record storage, validate the canonical record schema, metadata,
content SHA256 and safe canonical record ID. Reject tampering before creating files;
never execute attached artifacts or fetch embedded URLs during validation. SHA256
establishes integrity, not uploader identity or trust. Authenticated ingestion,
public projection and automatic promotion remain separate obligations in the
existing benchmark gateway, warehouse and Next.js workbench.

Evaluation configuration may carry an explicit `backendTunables` map. Llama.cpp
`split_mode` accepts `none`, `layer`, `row` or `tensor`, subject to the selected
runtime build advertising support; `tensor_split` requires finite
nonnegative decimal ratios with positive total and cannot accompany `none`.
Unknown options are refused, not silently ignored. Tunables participate in the
canonical configuration fingerprint. The exact selected executable must advertise
requested flags through bounded help inspection before launch. This negotiation
is not hardware/kernel qualification or a benchmark lease. Flags and values are
separate argv elements; no shell tokenization is used to launch a model path.

Operating-point residency requires agreement among all successful measured trials;
missing or conflicting residency remains unknown. The achieved context is the
minimum measured value in the applicable context-validation cohort. A missing
applicable measurement remains unknown, rather than borrowing configured context
or the largest observed value. Known throughput-only rows need no fabricated
context validation. Unknown context cannot establish an admissible context floor.

Experiment identity binds the complete requested workload, including repetitions,
output limits and parameters, plus actual model-file SHA256 and execution mode.
Resume excludes unrequested or incompatible workload/artifact/mode history; latest
attempt status controls reuse while earlier matching failed attempts remain in
profile denominators. Legacy incomplete experiment IDs are retained but rerun,
not rewritten. File hashing requires an opened regular file, with nonblocking,
no-follow descriptor checks before streaming special paths.


## Existing-workbench integration and source selection

The existing private conductor reader may use the configured file or authenticated
Rust gateway. An explicitly configured `bench.conductor_dataset` remains its source
even when `bench.gateway_url` also supplies grant authority. Without an explicit
file, the live source uses the current access session and freshly resolved backend
admin grant, the existing bounded transport and sanitized projection. A selected
source's refusal, stale data or validation failure never selects another source.
Private submission completion remains separate from consent/review/publication.

`llama.split_mode` remains the canonical matrix vocabulary. The old short
`split_mode` input may be normalized to it; conflicting aliases are refused and
only one effective flag is emitted. Explicit global settings pin the split axis
without repeating overwritten candidate cells. Recorded runtime commands preserve
argv boundaries and applied environment; a readable display string is not allowed
to misrepresent a successfully executed configuration.


Conductor store compatibility is versioned: historical v1 stores retain their
legacy leaf IDs and replay behavior; new v2 stores preserve canonical record IDs.
A v1 envelope cannot be relabeled or admitted to generic canonical-store reads,
coverage observations or publication. Private authenticated submission/replay is
not public publication or hardware production qualification. Implementation and
experimental single-card evidence are pinned in
`evidence/legacy-nvidia-2026-10-28/README.md`; full AC-MI-08 remains owed.
