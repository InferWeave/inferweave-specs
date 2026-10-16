# Audit part: runtime, adapters, lifecycle, profiles/aliases, federation, Slurm/Apptainer, benchmarking

Repo `/home/user/inferweave` @ `7171259` (squashed history; per-file baseline `a142f83` 2026-10-13, so `git log` carries no per-feature SHAs). Read-only static audit; no tests or builds were run. Paths are under `crates/`. Statuses: complete / partial / broken / missing / duplicated / unknown. "Test-only" means the code exists with unit tests but nothing in a production path calls it. Spec requirement text came from package files 04/05/06 (each is 3 lines); full specs 25/48/50/53-55/57/60-63 were not re-read, so spec-number claims rest on module headers.

## 1. Headline findings
1. **Two parallel runtime stacks.**
   - Typed-family stack: `iw-core::runtime_family::RuntimeFamilyAdapter` -> `iw-node::{runtime_manager,hot_swap,effective_profile}`. Per-engine behavior is simulated (see 2.1), and nothing outside `iw-node` calls it.
   - Real engine stack: `iw-core::swap_executor::SwapDriver` -> `iw-cli::{apptainer_driver,container_driver,engine_driver,engine_executor}` (llama.cpp and vLLM only).
   - Spec 04's twelve-verb adapter exists only in the first stack. Real execution exists only in the second.
2. **Swap is not transactional per spec 04.** `swap_executor` is drain -> unload -> load -> warm. It rolls back only before unload, and otherwise returns `Abandoned` (card empty or unknown). There is no prepare-candidate, reserve-peak, health-check, route-cutover, release-old sequence.
3. **Artifact cache is content-addressed but not cryptographic, and it is not wired to real I/O.** The digest is a seeded splitmix-style 128-bit hash. No downloader, resume or quota enforcement is wired in production.
4. **Execution preference (auto/cpu/gpu/hybrid), backend allow-list, NUMA and cost/energy are absent from every profile schema.** The code is deliberately GPU-only: test `missing_devices_are_refused_not_cpu_fallback`.
5. **Federation provisioning is substantial** (modes, owner policy, 8-message wire, state machine, fencing epoch, store, operator API, HTTP route). Gaps: no real `PhaseExecutor` implementation (test-only), `Autonomous` is documented as a later workstream, and the transport is attached only in tests.
6. **Slurm: a neutral `SchedulerAdapter` trait has no real implementation.** The spec's state set (queued/wait reason, staging, downloading, loading, warming, ready, preempted, cleanup) is not modeled. `AllocationState` has only Pending/Active/Released/Failed.
7. **`iw-runtime-bench` is an orphan workspace member.** No crate depends on it. Its benchmark, regression and optimize logic is duplicated by `iw-core` (`benchmark_*`, `requalification`) and `iw-cli` (`benchmark_runtime`).

## 2. Adapter trait and backend families

### 2.1 Trait
| Item | Evidence | Status |
|---|---|---|
| 12-verb trait: identity, capabilities, hardware_requirements, validate, prepare, load, unload, health, metrics, cancel, drain, shutdown | `iw-core/src/runtime_family.rs:337` `RuntimeFamilyAdapter` (also `family()`). Defaults are no-ops; `cancel`/`drain` take `&self`. | **Partial.** The trait matches the spec's names, but it is not async and not request-parameterized. `validate()` takes no manifest or hardware argument. `FamilyHardwareRequirements` has only `min_vram_mib` and `notes` (`:261`). `FamilyCapability` is a bare name (`:248`), so there is no quantization, offload, context, concurrency, streaming or checkpoint reporting. |
| Production use of the trait | `hardware_requirements()` has zero callers. The `iw-node` coordinator is used by no other crate. | **Test-only** |
| Implementations | `embeddings.rs:146`, `reranking.rs:130`, `stt.rs:129`, `tts.rs:125`, `prediction.rs:160`, `audio_gen.rs:122`, `typed_family.rs:141`, `rag.rs:164`, wrapped by `iw-node/src/runtime_manager.rs:39` | **Mock-launcher only.** `embeddings.rs:187` `load()` only flips an enum state (or fails on `simulate_load_failure`). No process, container or HTTP call. |
| Family registry | `runtime_family.rs:76` has 13 families: Llm, Reasoning, Embeddings, Reranking, Stt, Tts, Audio, Prediction, Image, Video, Multimodal, Scientific, Rag. Unknown ids are rejected. | Complete as a closed enum |
| Other "adapter" traits (different shapes) | `iw-core::eval_backends::InferenceBackend:32`, `benchmark_runner::BenchmarkEngine:271`, `benchmark_suite::SuiteEngine:137`, `image_generation::ImageRuntime:519`, `iw-embedding-runtime::EmbeddingRuntime:188` (async), `iw-diffusion::backend::DiffusionRuntime:78`, `iw-systemone::SystemOneBackend`, `iw-cli::engine_driver::EngineRuntime:59`, `iw-runtime-bench::runtime::BenchmarkRuntime:335`, `iw-cli::benchmark_runtime::BenchmarkRuntime:116` | **Duplicated** (see section 10) |

### 2.2 Backend families
| Family / engine | Evidence | Status |
|---|---|---|
| llama.cpp (LLM) | Real: `iw-core/src/engine_container.rs` (spec rendering, `OWNED_FLAGS`, `ROUTER_FLAGS` ban), `iw-cli/src/apptainer_driver.rs:652` and `container_driver.rs:125` (`impl SwapDriver`), `iw-node/src/engine_cfg.rs` `llama_cpp_config` | **Complete for serving** (the only fully real path). It is not under `RuntimeFamilyAdapter`. |
| vLLM | Telemetry/capacity only: `iw-node/src/vllm.rs`; engine args via `engine_catalogue`; `iw-cli/benchmark_runtime/container.rs` | **Partial.** Capacity reading plus benchmark launch. Serving driver is generic (container). |
| SGLang | `iw-cli/src/benchmark_runtime/unsupported.rs` "documents extension point, refuses every call"; named in `iw-runtime-bench::runtime` | **Missing** as a real adapter |
| ONNX / TEI / Infinity (embeddings, rerank) | Enum variants only: `embeddings.rs:20-26` (Infinity/Tei/Onnx), `reranking.rs:21-23` | **Stub (mock load)** |
| faster-whisper / whisper.cpp | `stt.rs:20,22` enum only | **Stub** |
| Piper / Kokoro | `tts.rs:20,22` enum only | **Stub** |
| MusicGen / StableAudio | `audio_gen.rs:21,23` | **Stub** |
| XGBoost / ONNX prediction | `prediction.rs:21,23` | **Stub** |
| Diffusers | Real path: `iw-image-worker/src/lib.rs` spawns `deploy/runtime/diffusers/diffusers_backend.py` per request (V0, short-lived) | **Partial** (per-request subprocess, no lifecycle, no residency) |
| ComfyUI (constrained) | `iw-diffusion/src/comfyui.rs:712`, `comfy_supervisor.rs`, `remote.rs:271`, `mock.rs:208`, workflow allow-listing (`workflow.rs`). Measured doc: `docs/benchmarks/diffusion-comfyui-measured.md`. | **Partial-to-complete.** Job-oriented trait with capabilities/health/capacity/cancel. Separate from `RuntimeFamilyAdapter`. |
| PyTorch / TensorRT | 0 hits for TensorRT; PyTorch appears once, in `gpu_memory.rs` | **Missing** |
| OCI / Apptainer | `apptainer_driver.rs` (36 tests), `container_driver.rs` (4 tests), `engine_container.rs` | **Complete for llama.cpp/vLLM-style OpenAI servers** |
| Video | Family enum only; no adapter | **Missing** |
| Scientific / custom | `typed_family.rs` (`CustomEngine::{Custom,Scientific}`) | **Stub** |
| Embeddings runtime crate | `iw-embedding-runtime` (709 lines: trait, fingerprint, `FakeEmbeddingRuntime`) | **Partial** (fake only; fingerprint is useful) |

## 3. Model lifecycle, hot swap, rollback
| Item | Evidence | Status |
|---|---|---|
| Swap phases and rollback | `iw-core/src/swap_executor.rs:55` `SwapDriver`, `:193` `run_swap`, `Outcome::{Completed,RolledBack,Abandoned,Refused}`; `gpu_claim.rs:33` `SwapPhase`, `:333` `roll_back`, `:359` `abandon_swap`, `:377` `abandon_unknown`; `swap_failure.rs` ledger refuses re-tries of placements that cannot work. Tests: `iw-core/tests/swap_executor.rs` (26). | **Complete for stop-then-start. Not blue/green.** Rollback is honest only before unload. |
| Spec-04 transactional swap (prepare candidate, reserve peak, health-check, route cutover, release old) | No cutover or peak-reserve code. `grep cutover` finds nothing relevant. | **Missing** (gap) |
| Validation gate before swap | `iw-node/src/hot_swap.rs` `SwapCoordinator::plan` (effective profile + adapter `validate`), 7 tests | **Test-only** (no caller outside `iw-node`) |
| Crash recovery of a swap | `gpu_claim.rs:293` `resume_phase`, `ClaimFile` (`:449`) persist/load; `iw-core/tests/claims_survive_a_restart.rs`; `iw-cli/src/engine_driver.rs` `adopted`/`clear_card` (adopts a still-serving engine, refuses to load beside another deployment's engine); `iw-cli/src/node_watchdog.rs` durable attempt marker, quarantine instead of repeat | **Complete for GPU claims/engines** (the strongest area). Not generalized to family adapters or to provisioning leases. |
| Drain | `iw-drain` crate (a data-drain crate, not the model drain); `engine_driver.rs` polls in-flight via `requests_in_flight` (`llamacpp:requests_processing`, `vllm:num_requests_running`) | Complete for engines |
| Live-state migration | Not promised anywhere | OK |
| Routing cutover on swap | `claim.is_serving` / `serving_count` (`gpu_claim.rs:238,413`) gate advertisement | Partial |

## 4. Artifact cache and checksum
| Item | Evidence | Status |
|---|---|---|
| Content-addressed, resumable, quarantine, tiered, eviction | `iw-core/src/artifact_cache.rs`: `content_digest:82`, `ArtifactFetch::{append:393 (contiguous only), complete:420}`, `CacheInventory`, `CachePolicy`, eviction by priority/LRU; `cache_registry.rs`, `cache_key.rs`. Tests: `iw-core/tests/artifact_cache.rs`. | **Partial: a pure model with no I/O.** `ArtifactFetch` buffers the whole artifact in memory (`received`). Used only by `slurm_site_e2e.rs` and tests. |
| Cryptographic digest | `content_digest` -> `identity::digest128` (`identity.rs:457`) is a custom splitmix/multiply mix, 128-bit, seeded. Not SHA-256. | **Broken for integrity/provenance.** It detects accidental corruption only. It cannot meet the spec's "checksum/signature" requirement. Compare `iw-cli/src/deploy.rs:129` (`sha256:` pin for images) and `iw-core::signature` (Ed25519). |
| Signature verification of model artifacts | Ed25519 exists for node proofs (`signature.rs`), not for artifacts | Missing |
| Model discovery | `iw-cli/src/model_discovery.rs` reads `manifest.json` from a shared dir (size on disk as the weights charge); `iw-node/src/weights.rs` `WeightSource` | Partial (no license discovery, no fetch) |
| Quotas, shared locks, provenance | Quota: capacity/pressure in `CachePolicy`. Staging lock: commit `4810ed8` "bound staging lock wait, sweep stale partials" (#1034). No provenance record. | Partial |
| Duplicate hash primitives | `digest128` for cache and fingerprints; sha2 for HMAC (`iw-federation/mac.rs`) and image pins; `reproduction`/`cache_key` use their own canonicalization | Duplicated |

## 5. Profile schema, aliases, routing, fallback
| Item | Evidence | Status |
|---|---|---|
| Profile YAML/JSON schema | `iw-core/src/runtime_profile.rs:134` `RuntimeProfile {name,version,match{gpu,host,model,serves},launch,quantization,kvOffload,quality,evidence,probe}` (camelCase, `deny_unknown_fields`, `from_yaml:162`); `profile_select.rs`, `profile_filter.rs`, `profile_launch.rs`, `profile_drift.rs` (RP-10), `profile_decision.rs`, `profile_report.rs`, `resource_profile.rs` | **Complete for engine-launch profiles** (the schema to extend) |
| Second profile system | `iw-node/src/profile.rs` (`ProfileCatalog`, `ProfileTuning {quant,ctx_provided,slots,kv_bytes_per_token,vram_bytes}`), `profile_policy.rs`, `effective_profile.rs`; gateway `profile_store.rs` and `server_profiles.rs` | **Duplicated** (different shape) |
| `execution.preference` auto/cpu/gpu/hybrid, allowed backends cuda/rocm/metal/vulkan/cpu, CPU threads/NUMA, offload layers, RAM/VRAM/peak, KV placement, SLO (TTFT/tps), cost/energy, explicit fallback permissions | Only `kvOffload` (host_gib, required) and `quantization` exist. No `execution` block. No NUMA, cost or energy fields. | **Missing** (extend `RuntimeProfile` and `schemas/json-schema/`; do not add a third schema) |
| JSON Schemas | `schemas/json-schema/` has 121 files (`model_profile`, `deployment`, `logical_route*`, `route_swap_mode`, `runtime_fingerprint`, `capability_preferences`...). None for runtime profile, provisioning or leases. | Partial |
| Alias levels and evaluation | `iw-core/src/alias_resolution.rs` (2598 lines, `evaluate_alias:160`, `AliasFallbackPolicy`), `alias_tree.rs` (`evaluate_adhoc`, 4-level tree), `alias_precision.rs`; protocol `iw-protocol/src/v1/aliases.rs`; storage `iw-storage::aliases`; gateway `alias_service.rs` (1463) + `alias_service/tests.rs` (1813) + `alias_edge_assertion.rs`, `adhoc_limit.rs` | **Complete as preview/administration** ("no admission/provision API" by design) |
| Capability routing and fallback | `logical_route.rs` (routes with ordered `fallbacks`, `MAX_FALLBACKS=16`, hard-constraint invariant 7), `routing.rs` (1978), `routing_preference.rs`, `route_preview.rs` (explainability), `context_routing.rs`, `model_capabilities.rs`, gateway `router.rs` | **Complete** for model/node fallback. **Missing** for hardware-mode fallback (GPU -> other GPU -> hybrid -> CPU) and "no silent downgrade" tied to SLO. |
| Hysteresis | `adaptive/controller.rs`, `autoscaler.rs`, `gpu_swap_policy.rs`, `repack.rs` (GPU-side) | Partial; not applied to hardware-mode placement |
| Structured explanations | `route_preview.rs`, `profile_decision.rs`, `alias_resolution` rows | Complete |
| Runtime/hardware compatibility validation | `engine_container::GpuSupport` (apptainer flag and visible-devices var per vendor), `gpu_detect.rs`, `host_generation.rs` (requalification on hardware change), `gpu_preflight.rs`, `runtime_profile::MatchRules`; `effective_profile.rs` "compatibility matrix" (`iw-node`, test-only) | **Partial.** Profile `match` and vendor flags work. Adapter-level backend-vs-hardware validation is unused (`hardware_requirements()` has no caller). |

## 6. Federation
Note: `iw-federation` is **telemetry** federation only (enrolment, HMAC, collector); its `lib.rs` states it confers no placement authority. Provisioning lives in `iw-core`, `iw-protocol` and `iw-gateway`.

| Item | Evidence | Status |
|---|---|---|
| Modes disabled/advertise_only/approval_required/autonomous | `iw-core/src/provisioning.rs:73` `ProvisioningMode` (default Disabled), `OwnerPolicy:98` {mode, allowlist, emergency_stop}, `permits()`; 10 tests | **Complete at the gate. Policy is thin.** Missing per spec 06: model-digest/license, runtime, CPU/GPU quotas, reserve, priorities, privacy, preemption windows, maintenance. `Autonomous` is documented as "later workstream", though bounded caps exist in `provision_acquisition.rs` (`AutonomousCaps`, `PeriodCaps`). |
| Capability negotiation | `fed_capabilities.rs` (`PROVISIONING_V1="iw.provisioning/1"`, `V2` hosting ext) | Complete |
| Wire messages | `iw-protocol/src/provision.rs:471` `ProvisionMessage`: capabilities, request, offer, reserve, approval, activate, revoke, heartbeat (873 lines) + `provision_hosting.rs` (1401 lines, 16 tests) | **Partial vs spec list.** Spec asks for capacity, request, offer, approve, reserve, commit, status, renew, revoke, release. Mapping: capacity -> `Capabilities` + `provision_capacity`; approve -> `Approval`; commit -> `Activate`; renew/status -> `Heartbeat`; **release has no message** (a state transition only, `release_transition`). |
| State machine | `ProvisionState` (`provision.rs:111`): Desired, Offered, Reserved, Approved, Activating, Ready, Revoked, Expired, Failed, Released | Complete |
| Lease fencing | `fencing_epoch` in reserve/activate/heartbeat (`provision.rs:381,404,425,445`); `provision_controller.rs` module header: single-use token, monotonic epoch, `tick(now)` expiry, `preempt` for local clients; test "no reactivation of released reservation" (`provision.rs:692`) | **Complete in the pure core** |
| Controller | `iw-gateway/src/provision_controller.rs` (2584 lines; 14 unit tests), `provision_client.rs`, `provision_transport.rs`, `provision_http.rs`, `provision_store.rs` (durable), `provision_operator.rs` (owner API), `provision_acquisition.rs` (`PhaseExecutor:319`, counters) | **Partial.** Tests: `iw-gateway/tests/provision_acquisition.rs` and `gateway_e2e.rs:659` only. **No production `PhaseExecutor`** (only the test `Exec`, `provision_acquisition.rs` tests:108), so nothing downloads or loads on behalf of a lease. |
| Server wiring | `server.rs:2462` route, `:1497` `with_provision_transport`; 404 unless attached | Partial (attached in tests only; `grep` finds no production caller) |
| Multi-parent, cycle/replay | `fed_multi_parent.rs` (stable capacity identity, no double count, loop prevention; 8 tests); `MAX_PROVENANCE_HOPS`; `fed_demand.rs`, `fed_scale.rs`; `peer_reputation.rs`; `reassertion.rs` | Complete in pure logic. Double-allocation across two parents on one host is not shown by a store-level test (**owed**). |
| Capacity signal and planner | `provision_capacity.rs` (privacy-filtered), `provision_planner.rs` (dry-run preview), `provision_hosting.rs` (fit, estimator) | Complete as dry-run |
| Fault tests (partition, retry, duplicate commit, revoke, node crash) | Unit tests for revoke and release exist. No partition or crash injection. `iw-sim` (3399 lines) not examined. | **Unknown / owed** |
| Protocol and schemas | No `provision*` file in `schemas/json-schema/` or `conformance/vectors/` | Missing |

## 7. Slurm and Apptainer
| Item | Evidence | Status |
|---|---|---|
| Neutral scheduler trait | `iw-core/src/scheduler.rs:284` `SchedulerAdapter {name, allocate, status, release...}`, `AllocationState {Pending, Active, Released, Failed}` (`:66`); only `FakeScheduler` (test, `:357`) implements it | **Partial / test-only** |
| Real Slurm adapter | None. Slurm calls are ad hoc: `iw-cli/src/cluster_keepalive.rs` (sbatch/squeue keep-alive with outcome-unknown handling), `slurm_worker_init.rs` (1657 lines, allocation-scoped worker via env `SLURM_*`), `slurm_tools.rs` (locate binaries), `deploy/hive/slurm/{runtime,scale,tests}` | **Missing** as an adapter. Pieces are scattered. |
| Spec states (queued + wait reason, allocated, staging, downloading, loading, warming, ready, draining, preempted, failed, cleanup) | `slurm_drain.rs` `DrainState {Active, Draining, Disconnected}`, `DrainCause`; `slurm_classify.rs` `TerminationKind {Preempted, Expired, Finished, Failed, NodeFailure}`, `PreemptionClass`; no wait-reason or ETA field (grep) | **Partial.** Preempt/drain/expiry present. Queue wait reason, staging/downloading/loading/warming and cleanup states missing. "No invented ETA" is satisfied vacuously. |
| Allocation-scoped worker identity | `slurm_worker.rs` `SlurmAllocationKey`, `SlurmWorkerRegistry` | Complete (pure) |
| Opportunistic benchmarks | `slurm_bench.rs` | Complete (pure) |
| Site E2E / reconnect | `slurm_site_e2e.rs` (5 tests), uses artifact cache | Complete (pure) |
| Apptainer | `apptainer_driver.rs`: `instance start/stop/list --json`, workaround for empty `%startscript`, pipe drain/reap on timeout (commit `dfd5cfc`, #992); `engine_driver.rs` `impl EngineRuntime for ApptainerDriver`; defs in `deploy/apptainer/` | **Complete** for engine instances. It is not exposed through a federation lease or `SchedulerAdapter`. |
| Rust API / Go UI surfacing | The UI is Next.js (D-002), not Go. `ui_telemetry.rs`, `runtime_view.rs`, `provision_operator.rs` provide Rust APIs. | Requirement wording conflict (spec 06 says "Go UI"; AGENTS.md says Next.js) |
| Duplicated types | `scheduler::AllocationState` vs `gpu_memory::AllocationState` (`gpu_memory.rs:310`) | Duplicated name, different meaning |

## 8. Benchmarking, evidence, auto-optimization
| Item | Evidence | Status |
|---|---|---|
| Keyed evidence | `iw-core/src/benchmark_warehouse.rs:~49` `BenchmarkDimensions {gpu_id, runtime_name, runtime_version, model_repository, model_hash, context_tokens, concurrency, settings}` -> fingerprint partition, no cross-partition aggregate. `benchmark_stack.rs` adds quant/KV/etc. | **Mostly complete.** The spec key (model digest + quantization + runtime + hardware + context + batch + concurrency + **mode** cpu/gpu/hybrid) lacks `mode` and `batch`. Quant is in `benchmark_stack`, not in the warehouse key. |
| Confidence / staleness | `benchmark_expectation.rs`, `requalification.rs` (796 lines, "Evidence is qualified under one exact ...", regression gate `:290`), `host_generation.rs`; retention only in the warehouse | Partial (staleness decay not found) |
| Regression detection | `iw-core::requalification::RequalificationGate` (production-side), `iw-runtime-bench::history.rs:218` `detect_regressions` + own `ComparisonKey:49` (model repo/rev, quant, engine, cell, TP/PP) | **Duplicated**; the second has no caller |
| Optimization / auto-tune | `iw-runtime-bench::optimize.rs` (plan/run within budget from advertised tuning dimensions, skipped list), `recommendations.rs`; core: `recommendation.rs`, `pareto.rs`, `benchmark_selection.rs` (1456 lines), `model_intelligence_recommendations.rs`; promotion: `runtime_profile.rs` ("a promoted benchmark candidate"), `adaptive/controller.rs` | **Partial.** Recommendation engines exist. **No closed loop** that auto-applies a profile change with hysteresis, and `iw-runtime-bench::optimize` is an orphan. |
| Benchmark engines | `benchmark_http_engine.rs` (OpenAI-compatible), `iw-cli/benchmark_runtime/{container,unsupported}.rs`, `benchmark_container.rs`, `eval_*` | Complete for llama.cpp/vLLM/Strata. SGLang refuses. |
| Reproduction vs published | `reproduction.rs` (17 tests), `iw-runtime-bench::reproduction.rs`/`discrepancy.rs`, `iw-cli/src/reproduce.rs` | Duplicated (core vs runtime-bench) |
| Measured data | Repo root `bench.jsonl`, `benchmarks/`, `docs/benchmarks/` | Unknown (not inspected; AGENTS.md forbids quoting figures unreproduced) |

## 9. Crash recovery and reconciliation (summary)
- GPU claims persist and resume (`gpu_claim.rs:293,449`, test `claims_survive_a_restart`).
- Engines are adopted or refused (`engine_driver.rs`).
- Watchdog quarantines (`node_watchdog.rs`).
- Autoscaler `reconcile` (`autoscaler.rs:4266`) and adaptive `reconcile` (`adaptive/controller.rs:863`, epoch-fenced owner) exist.
- Gateway outbox eviction (commit `afa2e64`, #1035).
- Provisioning leases persist in `provision_store.rs`.
- **Unknown:** whether the gateway reloads leases and reconciles them against running engines after restart (no test found).

## 10. Duplicated implementations
| Concern | Copies |
|---|---|
| Benchmark runtime lifecycle (prepare/start/wait_ready/benchmark/collect/stop) | `iw-cli/src/benchmark_runtime/mod.rs:116` and `iw-runtime-bench/src/runtime.rs:335` (2076 lines), plus `iw-core` `BenchmarkEngine`/`SuiteEngine` |
| Regression/comparison key | `iw-core/requalification.rs` + `benchmark_warehouse` fingerprint vs `iw-runtime-bench/history.rs` |
| Image request type | `iw-core/image_generation.rs:124` and `iw-diffusion/src/request.rs:99`; also trait `ImageRuntime` vs `DiffusionRuntime`; `iw-image-worker` vs `iw-diffusion-worker` |
| Embedding adapter | `iw-core/embeddings.rs` (family adapter) vs `iw-embedding-runtime` (async trait) |
| Profile catalogs | `iw-core/runtime_profile.rs` vs `iw-node/profile.rs` + `profile_policy.rs` |
| Swap | `swap_executor`/`SwapDriver` (real) vs `iw-node/hot_swap.rs` (validation gate, unused) |
| Allocation state | `scheduler::AllocationState` vs `gpu_memory::AllocationState` |
| Digests | `digest128` custom vs sha2/Ed25519 |
| Quantization enum | `iw-runtime-bench/quant.rs:30` vs strings in `benchmark_stack`/profile `quantization: Option<String>` |

## 11. Decision matrix
| Capability | Status | Decision | Risk |
|---|---|---|---|
| Adapter trait | partial | **Extend** `RuntimeFamilyAdapter` (request-parameterized `validate`; richer `FamilyCapability` and `FamilyHardwareRequirements`; async or job form). Add real adapters wrapping `SwapDriver`/`EngineContainer` so the two stacks **consolidate**. | High: wiring `iw-node` into `iw-cli` is the main integration |
| llama.cpp/vLLM adapters | complete (real) | **Reuse** | Low |
| SGLang, TEI, ONNX, whisper, TTS, TensorRT, PyTorch, video | stub/missing | **New** (per-family, each behind capability proof) | Medium. Do not assume compatibility. |
| Diffusers/ComfyUI | partial/complete | **Consolidate** `iw-diffusion` + `iw-image-worker` + `image_generation` types | Medium |
| Hot swap | stop-then-start | **Extend** `run_swap` with blue/green variant when peak VRAM fits, else keep current path and label it non-transactional | High: GPU contention |
| Artifact cache | model only | **Extend** `artifact_cache` with SHA-256 (and optional Ed25519), file-backed streaming, then wire to `site_connector`/model fetch | High: current digest not cryptographic |
| Profile schema | partial | **Extend** `RuntimeProfile` with `execution{preference,allowedBackends,cpuThreads,numa,gpuLayers,fallback}`; retire/merge `iw-node` profile | Medium |
| Aliases / routing | complete | **Reuse**; **extend** with hardware-mode fallback and no-silent-downgrade explanations | Low-Medium |
| Federation modes/wire/fencing | mostly complete | **Reuse/extend**: add release/status messages if needed, owner-policy fields, schemas + conformance vectors, a production `PhaseExecutor`, production wiring of the transport | High: autonomous mode with real downloads |
| Slurm adapter | missing (trait + scattered CLI) | **New** real `SchedulerAdapter` consolidating `cluster_keepalive`/`slurm_worker_init`; extend state set and wait reason | Medium |
| Apptainer | complete | **Reuse** | Low |
| Benchmark / regression / optimize | duplicated | **Consolidate** into `iw-core` (+ keep `iw-runtime-bench` as library if made a dependency of `iw-cli`); add `mode`/`batch` to key; add closed-loop with hysteresis | Medium |
| Crash recovery | strong for GPU | **Extend** to leases/adapters | Medium |

## 12. Open items for the owner
- Per-feature `git log` SHAs are unavailable (single squashed baseline `a142f83`).
- Tests were not executed here. "Tests exist" means test functions were found by grep, not that they pass.
- `iw-sim`, `iw-systemone*`, `iw-scheduling`, `iw-tunnel` and `iw-relay*` were not audited in depth. Fault-injection coverage for federation is therefore unknown, not missing.
- Specs 25/48/50/53/54/55/57/60-63 and the dynamic-aliases master spec were not re-read in full. Statuses rely on module headers citing them.
