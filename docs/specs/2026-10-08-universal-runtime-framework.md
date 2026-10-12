> Provenance: Operator-provided implementation specification; implementation requested 2026-10-12. This document captures the request and does not claim that the described features exist.

# InferWeave Universal Runtime Framework

Complete implementation specification | 2026-10-08

Repositories: inferweave/inferweave (runtime), inferweave/inferweave-specs (protocol), metabolomics-us/inferweave-gateway (routing and UI), existing InferWeave SDK repositories (clients).

## 1. Goal

Transform InferWeave from an OpenAI-compatible LLM worker manager into a universal, profile-driven distributed AI runtime. Automatically resolve, provision, download, load, hot-swap, unload and monitor heterogeneous models without restarting the node. Preserve existing worker behavior, YAML/JSON tuning profiles, aliases, benchmarks, Slurm integration, protocol compatibility and local-owner priority. The existing rebalancer remains the sole GPU allocation authority; do not build a second scheduler. Prefer validated quality and correctness over small performance gains. Open-weight, self-hosted models only by default; no silent proprietary fallback.

Precondition: inspect current repositories and all applicable existing specifications. Proposed names and schemas below are targets, not assertions about existing code. Reuse existing profile parsers, caches, rebalancer, event streams, and protocol conventions.

## 2. Architecture and contracts

Definitions: artifact = verified weights/tokenizer/dependencies; model = ID/revision/quantization/modalities; runtime = versioned execution engine; capability = typed operation; deployment = immutable model+runtime+effective profile+policy+resource contract; instance = deployment running with fenced reservation; pipeline = typed versioned DAG; job = durable execution with cancellation/progress/artifacts.

Lifecycle adapter methods: identity, capabilities, hardware_requirements, validate, prepare, load, unload, health, metrics, cancel, drain, shutdown. Separate typed execution interfaces for chat, embedding, reranking, transcription, speech synthesis, prediction, image, video, audio and pipelines. One runtime may implement multiple capabilities. Use isolated runtime processes/containers, not arbitrary code inside the Rust node. Version schemas and conformance fixtures in inferweave/inferweave-specs first.

## 3. Required runtime families

|Family                   |Initial adapters                                           |Requirements                                      |
|-------------------------|-----------------------------------------------------------|--------------------------------------------------|
|LLM/reasoning/vision     |existing OpenAI workers, llama.cpp, vLLM, SGLang           |streaming, tools, context, KV cache               |
|System-1/reflex          |ONNX, small llama.cpp, native                              |deadlines, protected residency                    |
|Embeddings               |Infinity, TEI, ONNX, compatible llama.cpp                  |dense/sparse, dimensions, normalization, batch    |
|Reranking                |TEI, Infinity, cross-encoders                              |scores, rank, batch                               |
|STT                      |faster-whisper, whisper.cpp                                |timestamps, optional streaming                    |
|TTS                      |Piper, Kokoro-compatible                                   |voices, audio formats, optional streaming         |
|Music/audio              |MusicGen/AudioCraft, Stable Audio Open, AudioLDM-compatible|async, duration, sound effects, license           |
|Prediction/classification|ONNX Runtime, PyTorch, XGBoost, custom                     |typed feature/output schemas, calibration         |
|Image/edit               |existing image spec, Diffusers, constrained ComfyUI        |pinned workflows, async artifacts                 |
|Video                    |Diffusers video, constrained ComfyUI                       |frames, duration, async, checkpoint if supported  |
|Multimodal               |compatible LLM/specialists                                 |advertise each input/output modality              |
|Scientific/custom        |isolated Rust/Python/OCI/Apptainer/ONNX                    |admin approval, typed, sandboxed                  |
|RAG                      |pipeline executor + retrieval adapters                     |embed→retrieve→rerank→generate with real citations|

RAG is a pipeline, not a standalone model runtime. System-1 is a latency class. Augur owns training, backtesting, features and registry; InferWeave serves its versioned prediction deployments. OpenViking and application memory own indexes and access policies.

## 4. Profile-driven automatic selection

Reuse existing YAML/JSON model/hardware/quantization/context/runtime/benchmark profiles. Extend only with optional capability, runtime preference, residency, cold-start, quality floor, prewarm and rollback fields. Legacy profiles must work unchanged. Selection: authenticate → resolve alias/capability/modality/schema/context/deadline → enumerate resident/cached/cold-startable/authorized-downloadable deployments → apply hard license/security/quality/quantization/hardware/driver/memory constraints → resolve immutable effective profile and benchmark evidence → score eligible candidates for quality, residency, queue, startup, execution time, reliability, locality and priority → reserve through existing rebalancer → prepare/load/execute → record decision and rejected alternatives. Administrator constraints override request overrides. Never silently downgrade quantization, context, calibration or output contract.

Illustrative extension (reconcile actual schema):

```yaml
model: {id: example/embedding-model, revision: pinned, capabilities: [embeddings]}
runtime: {selection: automatic, preferred: [infinity, onnx, llama.cpp], hot_reload: true}
deployment: {mode: on_demand, idle_timeout: 300s, minimum_residency: 120s}
resources: {accelerator: auto, vram: auto, allow_shared_gpu: true}
optimization: {use_existing_profiles: true, prefer_benchmarked_runtime: true, allow_quantization_fallback: false}
recovery: {rollback_on_regression: true}
```

## 5. Hot loading and transactional swap

States: DISCOVERED→RESOLVING→PREPARING/DOWNLOADING→RESERVING→STARTING→LOADING→WARMING→VALIDATING→READY↔BUSY/IDLE→DRAINING→UNLOADING→STOPPED, plus classified failures/cancellation/recovery. Swap: validate replacement profile/artifact → reserve → prepare/load → health and capability smoke test → atomically route new requests → drain old → release resources. Roll back on failure. If two versions cannot fit simultaneously, controlled drain-and-swap or cross-node reroute; never promise unconditional zero downtime. Preserve unrelated active requests. Single-flight load keyed by immutable deployment; multiple callers await one load, individual cancellation does not cancel others. Support minimum residency, idle eviction, cooldown, hysteresis, protected real-time models and optional predictive prewarm. Ordinary model/profile/runtime updates do not restart the node.

## 6. Three caches

Reuse existing model downloads, NVMe and shared storage. Cache: (1) verified weights/tokenizers/processors; (2) pinned OCI/Apptainer runtime environments and dependencies; (3) hardware-specific validated optimization profiles, compiled kernels and benchmarks. Content-addressed keys include model revision, quantization, runtime version, GPU architecture, driver/ABI and profile. Require checksum, atomic publication, resumable/deduplicated downloads, quotas, pinning, corruption detection, GC, offline reuse, S3/RustFS and shared Slurm sources. No unverified dependencies in the Rust node process.

## 7. Rebalancer, Slurm and multi-parent

Existing rebalancer exclusively grants reservations. Track weights, KV cache, activations, runtime workspace, auxiliary models, temporary loading peaks, CPU RAM, disk, GPU count/topology and headroom. Distinguish estimated/reserved/observed/peak/reclaimable/free; admit by safe peak usage, not weights alone. Reservations are idempotent, expiring, fenced and reconciled after crash/partition. Support shared GPU, multi-GPU, permitted CPU offload, pinned System-1 and opportunistic background models. Local hardware-owner requests outrank upstream shared capacity. Across multiple parents, advertise stable physical resource identities, avoid double counting and routing loops, expire stale advertisements, propagate withdrawal/reconnect. Slurm/Apptainer: accelerator-specific images, shared caches, preemption and allocation-expiration handling; distinguish runtime crash, model incompatibility, node loss, Slurm eviction and network failure.

## 8. Pipelines, jobs and artifacts

Typed versioned DAGs for RAG, STT→LLM→TTS, prediction ensembles, image/audio/video and scientific workflows. Validate stage schemas, parallelize independent stages, schedule via rebalancer, release unnecessary reservations, propagate cancellation/timeouts, checkpoint only when supported, and preserve provenance. RAG indexes remain application-owned; citations reference actual retrieved documents. Durable async jobs for media/batch with submitted/queued/preparing/running/completed and cancelling/cancelled/failed/retrying/paused (only when supported). Idempotency, replayable progress, retention, signed S3/RustFS artifact URLs, resumable transfers; avoid huge binary transfers through gateway hot paths.

## 9. Protocol and SDKs

Preserve supported OpenAI-compatible /v1/chat/completions, /v1/responses, /v1/embeddings, /v1/audio/transcriptions, /v1/audio/speech, /v1/images/generations, /v1/images/edits, /v1/models. Claim compatibility only where semantics match. Proposed native /inferweave/v1/runtimes, /deployments, /capabilities, /rerank, /predictions, /pipelines/execute, /jobs; finalize in specs. Standardize auth, request IDs, structured errors, retry hints, cancellation, version/capability negotiation and accounting. Update Go, Rust, Java, Scala, TypeScript, JavaScript and Python SDKs using canonical schemas and shared conformance. SDKs must not implement their own runtime selection.

## 10. Gateway observability

Extend existing light-theme Go gateway UI, not a separate app. Show runtime family/version/instances, loaded/cold/downloadable deployments, effective profiles, lifecycle events, quality explorer, selection/rejection reasons, GPU VRAM by weights/KV/workspace/auxiliary/reserved/free, Slurm state, multi-parent resource lineage, eviction reasons, cold-start histograms, failures and rollback. Distinguish estimated from observed values. Common metrics: start/load durations, crashes, queue, active requests, VRAM peak/reserved/observed, evictions, swap outcomes. Quality: LLM TTFT/tokens/s, embedding retrieval metrics, rerank NDCG/MRR, STT WER, TTS intelligibility, prediction calibration/Brier/log loss, media quality, System-1 deadline success. Avoid high-cardinality labels; IDs in traces/events.

## 11. Security, reliability and quality

Isolate third-party runtimes in least-privilege containers/processes with resource, filesystem, network and GPU limits. Verify artifacts/images/licenses; profiles are data, never arbitrary executable shell scripts. Approved registries, tenant isolation, scoped identities, secrets protection, audit logs, quotas, signed artifact access. No silent proprietary fallback. Classify transient transport, OOM, incompatibility, corruption, resource revocation, Slurm preemption and crash separately. Bounded retries/backoff, circuit breakers, quarantine bad deployments and rollback known good. Benchmark pinned model/runtime/profile/hardware for latency, throughput, peak memory and quality; valid JSON is not evidence of model quality.

## 12. Workstreams and repository ownership

A. Audit/migration (inferweave/inferweave): inspect existing workers, profiles, rebalancer, cache, Slurm, telemetry and tests; reuse map.

B. Canonical protocol (inferweave/inferweave-specs): schemas for runtime, capability, deployment, lifecycle, reservation, pipeline, job, error, version negotiation; fixtures.

C. Runtime Manager (inferweave/inferweave): registry, typed adapters, supervisor, readiness, health, single-flight loads, draining, events; wrap legacy workers first.

D. Profile resolver (inferweave/inferweave): backward-compatible YAML/JSON extension, deterministic merge, compatibility matrix, benchmark scoring, effective profile, hot reload/rollback.

E. Hot swapping (inferweave/inferweave): load/unload, model/quantization/runtime upgrades, transactional switching, cooldown, prewarm, recovery.

F. Caches (inferweave/inferweave): model/runtime/optimization caches, NVMe/shared/S3/RustFS, OCI/Apptainer, integrity, quotas.

G. Rebalancer (inferweave/inferweave): sole allocation authority, peak memory, fenced reservations, reconciliation, owner priority, multi-GPU.

H. Adapters (inferweave/inferweave): H1 legacy LLM; H2 embedding/rerank; H3 STT/TTS; H4 prediction; H5 image; H6 music/audio; H7 video; H8 scientific/custom; conformance for each.

I. Pipelines/jobs (inferweave/inferweave): typed DAG, stage scheduling, durable jobs, cancellation, artifacts, provenance.

J. Slurm (inferweave/inferweave): Apptainer provisioning, GPU matching, caches, expiration/preemption.

K. Multi-parent (inferweave/inferweave, specs): stable capacity identity, fencing, loops, priority, reconnect.

L. Gateway (metabolomics-us/inferweave-gateway): capability routing, aliases, lifecycle/VRAM UI, quality explorer, failures.

M. SDKs (existing SDK repos): Go/Rust/Java/Scala/TypeScript/JavaScript/Python generated contracts and tests.

N. Benchmarks (inferweave/inferweave): family quality, cold starts, swaps, memory, regression gates.

O. Migration/integration (all): mixed-version compatibility, rolling upgrades, fault injection, rollback and documentation.

Dependency order: A→B→C/D/F→E/G→H/I/J→K/L/M→N/O. Parallelize only independent work after contracts stabilize. Every workstream delivers code, tests, docs, telemetry and acceptance evidence. No duplicate scheduler/profile store.

## 13. Acceptance criteria

☐ Existing workers, aliases, profiles and SDKs still work.

☐ Embedding, STT, TTS and prediction requests auto-select, load and execute without node restart.

☐ Verified artifact caching and single-flight concurrent loading work.

☐ Profile/model/runtime hot swap validates, switches, drains and rolls back; unrelated active requests survive.

☐ Selection uses existing profiles, compatibility and quality evidence, with explainable decisions.

☐ Existing rebalancer alone allocates GPU using peak-memory reservations and fencing.

☐ Shared GPU, System-1 priority, local-owner priority, multi-parent and Slurm preemption work safely.

☐ RAG stages return genuine provenance; media jobs support progress, cancellation and secure artifacts.

☐ All adapters pass conformance; all seven SDK languages pass shared fixtures.

☐ Gateway displays lifecycle, VRAM, selection reasons, failures and quality regressions.

☐ Security, isolation, rollback and mixed-version tests pass.

## 14. Required end-to-end demo

Start with Qwen LLM resident. Request embeddings: select/load compatible runtime, return valid vectors, no node restart. Request STT: load speech runtime without interrupting LLM. Request prediction: load versioned deployment, validate features, return typed probabilities. Constrain VRAM: rebalancer evicts eligible idle model, protects active/local work. Publish profile update: validate, hot swap, drain old. Inject replacement failure: roll back. Route through two parents: prove one physical reservation and owner priority. Expire Slurm allocation: withdraw capability and recover/reroute where eligible. Verify gateway lifecycle, VRAM, cold starts and decision explanations.

## 15. Pi Engineering / AutoSpec execution instructions

1. Audit repository HEAD and existing specs; write compatibility map and dependency graph.
2. Submit canonical protocol PR to inferweave/inferweave-specs first.
3. Create dependency-ordered issues/worktrees for A-O; avoid conflicting core edits.
4. Reuse existing rebalancer, profiles, caches, benchmarks, Slurm and gateway; refactor only as necessary.
5. Implement feature flags, incremental migration, tests and rollback at each milestone.
6. Require independent review and capability-specific quality/conformance before merging adapters.
7. Update Go gateway and SDKs from canonical protocol contracts.
8. Do not mark complete without evidence for each acceptance criterion and the end-to-end demo.
9. Deliver migration notes, examples, runbooks, rollback instructions and cross-repo status report.

Definition of done: Automatic profile-driven runtime selection and hot loading across LLM, embeddings, speech and prediction on shared hardware, without node restart, with correct resource ownership, rollback, backward compatibility and telemetry; extensible to every other runtime family.

END OF SPECIFICATION
