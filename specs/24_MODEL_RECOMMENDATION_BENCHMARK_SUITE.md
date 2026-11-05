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
output limits and parameters, plus actual model artifact fingerprint (single-file SHA256 or the canonical compound
manifest fingerprint below) and execution mode.
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


## Backend artifact identity — iw.eval-artifacts/1

The former model-file-only wording excluded measured directory, HF snapshot and
Ollama workloads even where runtime adapters existed. The following extends the
existing typed `EvalModel.contentHash` provenance path; it introduces no registry,
network fetcher or download authority. Single-file fingerprints remain compatible.
A tag, model name, advertised digest or remote URL alone is not measured identity.

The shared `iw_bench_record::eval_artifacts::ModelArtifactManifest` has exactly
`schema`, `kind`, `fingerprint`, `files`; unknown fields are refused. Schema is
`iw.eval-artifacts/1`. Each file has exactly `name`, `bytes`, `sha256`, with bytes
an unsigned 64-bit integer and SHA256 a lowercase 64-hex digest. Supported kinds
are `file`, `directory`, `gguf-shards`, `ollama-manifest`, or
`hf-snapshot:<revision>` where revision is exactly 40 or 64 lowercase hex digits.
There are 1 to 10,000 files; empty manifests and empty directories are refused.
Names are unique, sorted relative UTF-8 slash paths
of at most 4096 bytes, with no absolute path, dot/traversal segment, backslash,
colon or control character. Total bytes use checked unsigned 64-bit addition.
Kind `file` has exactly one entry named `model` and its fingerprint is that file's
raw SHA256. Compound kinds use SHA256 of canonical JSON `{schema,kind,files}`;
`fingerprint` is excluded from its own preimage. Producer and importer use the
same existing record canonical encoder: recursively sort object keys, retain array
order, and sort the complete file cohort lexically by name. Bound the serialized
profile manifest to 4 MiB at creation as well as import.

Hash actual opened regular-file bytes with no-follow/nonblocking descriptor checks,
a read bounded by observed length plus one byte, and stable inode, ctime, mtime
and size observations. Directory identity includes the actual weights, tokenizer,
configuration and template files; enumerate at most 20,000 entries and depth 32.
Refuse symlinked subdirectories, special files and escaping file links. An
explicitly selected root directory alias may be canonicalized to its resolved
path; recapture the original reference at each required revalidation boundary. HF snapshot
file links may resolve only within that snapshot or the same repository's blobs.
HF `org/model` input resolves offline through the current local `refs/main` to an
exact revision and existing snapshot; the snapshot kind pins its revision even
when all files are regular files without blob links. Pass the resolved local path to the runtime,
never a mutable repository name. Resolve all GGUF shards through the existing launcher enumeration as one complete
file set, requiring the declared sequence to be complete. A first-shard-only old
fingerprint cannot establish full artifact identity: the compound fingerprint
invalidates incomplete resume identity while preserving historical records.
Directory bytes alone do not establish reference closure across runtime versions.
Verify known weight `*.index.json` files with JSON bounded to 4 MiB: `weight_map`
must be an object of string references, each an exact safe relative member of the
captured file cohort. In `tokenizer_config.json`, nonnull `tokenizer_file`,
`vocab_file`, `merges_file`, `spm_file`, `added_tokens_file`, `special_tokens_map_file`,
`chat_template_file` and each `fast_tokenizer_files` array entry must likewise name
an exact safe contained cohort member. A nonnull `fast_tokenizer_files` must be
an array of strings; malformed scalar/object values are refused. Refuse URLs, absolute/traversal paths and
unsupported external references; do not fetch or recursively resolve them. This
conservative closure check covers known keys only, not arbitrary code or dependency
attestation, and makes no claim of a demonstrated current-runtime exploit.
No resolution step downloads or follows arbitrary URLs.

Ollama input resolves the local preferred `manifests-v2` representation or current
legacy alias. Bound manifest JSON to 1 MiB and accept only the supported Docker v2
GGUF representation. Hash the actual manifest plus every config and layer blob,
verifying each expected SHA256 and size. Refuse conflicting duplicate entries,
missing/corrupt blobs, manifest lists, cloud models and unsupported representations.
Pin the local store using `OLLAMA_MODELS` and `OLLAMA_NO_CLOUD=1`; use the selected
canonical tag consistently across every request workload. vLLM/SGLang receive the
resolved local path with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
Approved environment settings must be recorded and applied identically, alongside
quote-safe argv; artifact resolution grants no GPU control environment authority.
Launch and replay share the versioned `local-model-inputs/1` environment policy:
remove inherited model/router, HF, draft-model and projector selector variables
that could replace the captured local inputs; preserve CUDA visibility and Slurm
allocation variables. Disable automatic projector selection unless an explicit
local projector is selected. Apply and record the same policy in launch and
replay, with required options negotiated against the selected executable's help.
Owned runtime listeners bind explicitly to loopback (`127.0.0.1`); bind provenance
uses `runtime_bind_policy=loopback/1`. Experiment identity must exclude reuse of
older unconfined history without rewriting it. This grants no network exposure.
Bind the actual selected request model and approved environment in experiment
provenance for nondefault backends. The artifact fingerprint is independent of
absolute location; experiment identity may change when the actual resolved model
path or environment changes, preventing reuse of unattested execution history.

Profile `provenance.model_artifact_manifest` embeds the canonical JSON string.
The canonical record importer bounds it to 4 MiB, validates schema, fingerprint,
complete file cohort and agreement with profile `contentHash` and `fileBytes`,
and exposes actual `model.files`. Old profiles without a manifest retain existing
behavior with unknown files; do not infer bytes from names or rewrite history.
Persist manifests append-only at `artifacts/<fingerprint>.json`: identical content
is idempotent; different content at the same identity is refused.

Revalidate the original reference before every launch, after stopping the owned
runtime and before final profile construction, including entirely resumed runs.
Reference or byte drift preserves pending/failed trial metrics and returns an error
without profile export. Refuse output paths within the artifact directory.
These are bounded before/after observations, not adversarial filesystem attestation
or complete hardware/runtime/tokenizer/grader/deployment attestation. Hashing may
warm host caches; record that limitation when interpreting cold-start or load-time
measurements. Exact-target safety, lease and production qualification gates remain
**UNSATISFIED**. AC-MI-09 is owed until actual control-removal evidence is recorded.
