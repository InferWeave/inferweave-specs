# Specs and PR reconciliation (read-only audit)

Specs repo HEAD: `e99d6552e5ec2c2711024b0f275948f6f86ca8b3` (#284). Date 2026-10-16.
Package files are untracked (`?? docs/specs/inferweave-unified-runtime-provisioning-20261015/`).
`python3 scripts/validate_specs.py` fails in this sandbox (jsonschema `_RefResolutionError: unknown schema`); nothing was proven by it. No tests were run.

## 1. Located master specs

| Item | Location | Summary / status |
|---|---|---|
| Oct 8 Universal Runtime Framework | `docs/specs/2026-10-08-universal-runtime-framework.md` (160 lines; provenance banner: "captures the request, does not claim features exist") | Profile-driven universal runtime; 12 adapter lifecycle methods; 13 runtime families; selection pipeline; transactional hot swap; 3 caches; rebalancer = sole allocator; workstreams A-O; acceptance and E2E demo. Realised as specs 48-53 + B-T01..06 (OPEN_GATES "Universal runtime families", BLOCKED, all owed). |
| Oct 9 Architecture Consolidation | NOT FOUND as a document anywhere (grep docs/, specs/, decisions/, implementation/, tasks/, git log). Only matches: the package's `01-AUDIT.md` (names it), `FEATURE_PRESERVATION_MATRIX.md:3` (generic), `schemas/v1/resources/rebalance-decision.json:82` (an enum value "consolidation", unrelated). | Treat as missing input. Closest substitutes: `decisions/2026-10-12-dynamic-alias-authority.md` (amends D-002, Rust authority, Go = UI/relay), `decisions/2026-10-07-gpu-memory-accounting.md`, and open inferweave PR #1013 "migrate all gateway functionality to Rust; Go becomes the frontend". Ask the operator for the text. |
| Oct 10 Federated Model Provisioning | Master spec text not in repo. Phase 0 audit: `docs/federated-provisioning-audit.md` (426 lines, dated 2026-10-12, status through Item 5 / inferweave PR #916 `bcfc9473`; Phase 1 SHAs `af0abef0`,`1698a4d1`,`9b1d1726`,`7f8cdf0b`,`5e336b65`,`43cdb0c2`,`35feffa5`,`1d048168`,`9d89e1ab`,`70f16215`; Phase 2 PR #881 `6a227e09`). Contract: `specs/62_FEDERATED_PROVISIONING_HOSTING_REQUESTS.md` (353 lines, added by #278 `b9af1dd`, code ref `de43764a`). | Delivered: `provision.*` messages, 8-state machine, owner policy modes, controller, HTTP transport, operator API. Spec 62 adds hosting/acquisition, sizing evidence, phases in ACTIVATING, authority per owner mode. Autonomous mode (Item 6) is open specs PR #266. |
| Package | `docs/specs/inferweave-unified-runtime-provisioning-20261015/inferweave-unified-runtime-provisioning/` 00-09 + README + START_HERE (all read, ~10 KB total) | Design package, explicitly "NOT evidence of a live code audit". `evidence/capability-ledger.yaml` has 3 stub rows, `repository_sha: null`, all `unknown`/`audit_required`. |

Related specs (headings and relevant content verified):
- VRAM: 43 Per-GPU Placement/Hot-Swap (claims, dwell, availability floor, swap lifecycle); 46 GPU Memory Intelligence (report, fleet, reservations, pressure with `forecast`, decisions, OOM postmortem, simulation §9); 56 Runtime Instance Observations (producer/ownership/qualification, not memory).
- CPU/GPU/hybrid: no dedicated spec. `schemas/v1/resources/reservation.json` has cpu/accelerator; spec 50 §Runtime reservation admits CPU-only (`accelerator: cpu`, no fake GPU quantities); spec 45 device types include `cpu`, `apple_gpu`; `gpu-memory-runtime.json:391` lists `metal`. No `execution.preference`/hybrid/offload/NUMA field in `schemas/v1/model/{placement,requirements}.json`.
- Slurm/Apptainer: 25 Slurm Ephemeral Provider Nodes (incl. mandatory Apptainer substrate); 37 Container Deployment Standard (Docker/Compose + Apptainer; Podman/K8s/bare-metal need ADR).
- Profiles/aliases/routing: 54 Dynamic Model Aliases (level 2), 55 Alias Edge Delegation, 57 Alias Execution Identity/Claims, 60 Capability Routing + Mission Events (schemas exist: `schemas/v1/routing/*`, `events/mission-event.json`), 61 Alias Precision/Ad-hoc Selection/Resolution Trees. Profiles: 12 (tuning/capacity profiles), 39 Runtime Tuning, 24 Recommendation/Benchmark Suite.
- Unmerged: specs PR #279 "[IW-DYNNODE-001] Dynamic nodes and gateway-driven model provisioning (spec 64)" with implementation PRs inferweave #1014/#1015/#1016 (head SHAs `48545218`,`9fc8062d`,`03004130`). Spec 64 does not exist on main; it overlaps this package.

## 2. The 15 hardening capabilities mapped

| # | Capability | Existing spec coverage | Gap |
|---|---|---|---|
| 1 | Predictive memory pressure | `46 §6 Pressure`: states, hysteresis, optional `forecast` (`growthBytesPerMin`,`timeToPressureSecs`, needs `minSamples`; never overrides safety). Schema `resources/pressure.json`. | EXTEND. No predictor algorithm, no pre-emptive action contract, no test of forecast. Producer/gateway composition owed (P5-T31). |
| 2 | Context-aware capacity | Inv 3, 36; `46 §3` `safeSchedulable`, `kvGrowthReserve`, `runtimeGrowthReserve`; `04`; `context_admission` (audit doc); spec 39 (throughput needs depth). | Mostly covered. Owed with GPUMEM tasks. |
| 3 | Transactional reservations | `46 §5`; `50 §Runtime reservation contract` (fenced, idempotent, safe-peak, `resourceDomainKey`, `placementGroupId`); `schemas/v1/resources/reservation.json`; inv 37; `62` provision lease. | Covered; two reservation models exist (46 vs 50 vs 62 lease) - see conflicts. All proofs owed. |
| 4 | Crash recovery | `50` (reconciliation, progress expiry); `46` anomalies/postmortem; `62` snapshot restore (delivered `35feffa5`); specs 26, 36 watchdog, 31 quarantine. | Covered in prose; no crash-recovery conformance test. OPEN_GATES: "crash reconciliation ... owed". |
| 5 | Runtime/hardware compat validation | `48` adapter `hardware_requirements`/`validate`; `schemas/v1/model/requirements.json` (cuda/rocm/compute_capability/device_types); `docs/compatibility.md`; `37 §Host/container compatibility`. | Covered at schema level; no compatibility matrix fixture; CPU/Metal not in requirements schema. EXTEND. |
| 6 | Unified-memory accounting | None. No spec uses "unified memory". Only `apple_gpu` (45) and `metal` backend enum value. `46 §2.4` placement classes are unrelated. | NEW (extend 46 `Quantity` basis/`physical` domain so RAM and VRAM share one pool). Package 03 requirement unmatched. |
| 7 | Predictive prewarming | `32` (forecast/pre-stage artifacts, assign on Slurm GPU appearing); `50` caches, optional prewarm; `41`; Oct-8 §5 "optional predictive prewarm". | EXTEND 32 (it prestages artifacts, not warm loads). IW-FORECAST-001 task P3-T15 (proof status field absent). |
| 8 | Adaptive CPU/GPU benchmarking | `12`, `24`, `33`, `39` benchmark/tuning; IW-TUNE-001/002. No CPU/hybrid benchmark mode keyed by execution mode. | EXTEND 12/39 (benchmark key must add execution mode, offload layers). |
| 9 | Energy-aware scheduling | Energy only as a metric (`12:22` power/temp, `24:83,147` `best_energy_efficiency`, `45:403` power draw) and DECISIONS_REQUIRED mention. No scheduling objective. | NEW (small), must stay below hard constraints (inv 6-7). |
| 10 | Auto runtime profile optimization | `39`, `12`, `36` rescue "known-good profile", inv 15, 42; `24 §Active Experiment Selection`. | EXTEND 39/24; profiles immutable per inv 15 so optimization = new candidate deployment, gated by inv 28. |
| 11 | Perf regression detection | `23 §Qualification and regression`, `31` (TTFT/prefill/decode regression), `24 §Requalification Triggers`, P2-T09. | Covered in prose; REUSE 31/23. |
| 12 | Compatible memory/cache sharing | `25`/`27`/`28` artifact caches; `50 §Transactional caches`; inv 8 (prefix affinity), inv 9; `04 shared GPU`. No spec for sharing KV/weights between instances. | NEW or extend 50; weights sharing is partly "weights counted once" (audit doc `capacity.rs`). |
| 13 | Capacity forecasting | `32`, `46 §6 forecast`, `41`, IW-GRANT-004 "forecast signals". | REUSE 32 + 46. |
| 14 | Provisioning simulation / dry-run | `46 §9` simulation (`POST /iw/v1/gpu-memory/simulate`, read-only), `54`/`61` `simulate`/`resolve` ad-hoc, `62` dry-run planner `provision_planner.rs`, 35 cluster simulator. | REUSE. Three dry-run surfaces already; do not add a fourth. |
| 15 | Placement recommendations | `24` recommendation classes, `61` resolution tree + typed `unmet`, `46` decision records, `60` routing decision. | REUSE 61 + 24; recommendation output from 46 simulation. |

## 3. Contracts, tasks, status, gates

| Area | Artifacts | Status |
|---|---|---|
| GPU memory | `schemas/v1/resources/*` (gpu-memory-*, pressure, reservation, placement-simulation-*, rebalance-decision), `contracts/gpu-memory/01-04*.fleet.json`, `contracts/protocol-v1/gpu-memory-*.json`, tasks P5-T30/31/32 (IW-GPUMEM-001) | Specified. All three tasks `owed`. OPEN_GATES "GPU memory accounting": BLOCKED; NVIDIA/AMD measured producers, gateway composition, event feed, simulation not built. Impl PRs merged in inferweave: #873, #993, #1000. |
| Hot swap | spec 43, P3-T23/24/25 (IW-SCHED-002) | `owed`; gate "GPU placement and hot-swap" BLOCKED (autoscaler library-only; inferweave issue #328 open). Defaults 300s/10x/120s untuned. |
| Runtime families | specs 48-53, `schemas/v1/{runtime,deployments,model,pipelines,jobs,artifacts}`, `conformance/runtime-family-vectors.json`, `runtime_protocol.py`, B-T01..06 | Offline conformance only; "native HTTP: NOT RUN"; gate BLOCKED. |
| Aliases | 54-57, 61, A-T01..08, `contracts/dynamic-alias-acceptance.json` (29 acceptance tests owed) | Gates BLOCKED; 61 partially implemented in Rust (#1021, #1029, #1039, #1037). |
| Routing/mission | 60, schemas `routing/*`, `events/mission-event.json` (added #275/#276/#280/#281) | Schemas+fixtures exist; gateway emission owed (issues inferweave #1002-#1004). |
| Provisioning | 62, `docs/federated-provisioning-audit.md`, P5-T17 (IW-GRANT-004) | Delivered code per audit doc (not re-verified); spec 62 extension owed. Merged since: inferweave #1022 (pure slice), #1041 (controller lifecycle). OPEN_GATES not updated for #1041 (see conflicts). |
| Forecast/prestage | 32, P3-T15 | No gate entry; no schema. |
| Slurm | 25, 37, P3-T05/06/10/21 | No dedicated open gate besides production deployment gate. |
| Overall task proof | 33 tasks `owed`, 1 `proven` (P0-T01A) | |
| CPU/hybrid | none | No schema, task, fixture, or gate. Open inferweave PR #1045 (System One on CPU) is implementation without a spec. |
| Unified memory, energy, prewarm, sharing | none | No schema/fixture/task. |

## 4. Conflicts

Spec-to-spec:
1. Spec 62 vs invariant 37: delivered provisioning lease is elapsed-time (300 s TTL, `tick(now)`); inv 37 and spec 50 require progress-based expiry. Spec 62 changes it; inferweave #1041 (merged 2026-10-15) claims to deliver it, but OPEN_GATES (spec62 section) still lists it owed. Gate text is stale or the claim is unverified - do not cite either as proven.
2. `docs/federated-provisioning-audit.md` header calls spec work "Missing" for provisioning in specs repo (§2.10) with a banner noting it is historical; spec 62 supersedes. Reader must use 62.
3. Three reservation vocabularies: 46 (`reservation.json`, states), 50 (`runtime_reservations/1`, `progressTimeoutMs`), 62/provision state machine (`RESERVED/APPROVED/ACTIVATING`). Package 03 asks for one ledger; unification is not specified.
4. Spec 62 sizing/`fit` and spec 61 `capacity` unmet both depend on spec 46 memory reports that are not universal; `FITS` unreachable for unprofiled models (62 review round 1).
5. Spec 64 (open specs PR #279) overlaps 62 and package 05/06 (dynamic nodes, gateway-driven provisioning); unmerged.
6. D-002 amended narrowly for Go alias UI only (`decisions/2026-10-12-dynamic-alias-authority.md`); open PRs gateway #556 "prefix aliases (stopgap)" and #555 add Go routing paths, which strain "Go = UI/relay" (inv from package 02).
7. Spec 63 internal defects recorded in OPEN_GATES (hop limit 8 vs no default, etc.) - not this scope.

Package vs repo:
- 02 "Rust authoritative, Go no routing" is consistent with D-002 only in part: D-002 permits Go UI consuming Rust alias APIs; Go legacy selection still exists.
- 03 "Apple unified memory shares ONE pool, never double count": no repo spec; must be new, extending 46.
- 03 reservation field `TTL` conflicts with inv 37 (use progress-based expiry, not TTL).
- 03 "atomic CAS" is stronger than specs 46/50 wording (idempotent + fenced); acceptable as implementation detail.
- 04 adapter methods match 48/Oct 8 (12 methods). OK. 04 adapter target list adds TensorRT, Infinity, ONNX etc.; all within 48 registry unverified.
- 05 proposes `execution.preference auto/cpu/gpu/hybrid`, `cost/energy`, `KV placement`: none exist; "extend existing profile schema" is correct but no CPU/hybrid fields in `schemas/v1/model/*`. Also profile immutability (inv 15) means these are deployment fields, not mutable profile fields. Fallback "GPU->CPU only if allowed" must obey inv 6-7.
- 06 modes `disabled/advertise_only/approval_required/autonomous`: match `ProvisioningMode` in 62; but autonomous+activate is refused in delivered code (OPEN_GATES) - owed. 06 message list (capacity, request, offer, approve, reserve, commit, status, renew, revoke, release) differs from delivered `provision.*` (capabilities/request/offer/reserve/approval/activate/revoke/heartbeat): "commit/status/renew/release" are not messages today. Reuse delivered names.
- 06 "Slurm adapters report ... no invented ETA": consistent with 25 and 62 ("phase duration estimates unspecified").
- 07 says "Go UI" shows fleet; D-002 limits Go to UI role - consistent. UI work must use Rust typed APIs.
- 08 phases P0-P7 collide in naming with repo phases P0-P5/A/B; use package-prefixed IDs.
- 01 requires files `inventory.json, contract-map.yaml, duplicate-map.md, baseline.md, decisions.md, dependency-dag.md`; only capability-ledger.yaml exists, with 3 stub rows.
- START_HERE tells extraction into `docs/specs/inferweave-unified-20261015-<run-id>/`; actual dir is `...-20261015/inferweave-unified-runtime-provisioning/` (cosmetic).
- Repo rule (AGENTS.md): any behavior change needs spec + decisions + `contracts/feature-registry.json` + task graph + coverage + `validate_specs.py`. Package has none of these.

## 5. GitHub (read-only; minimal queries, <=10 each)

Open PRs, inferweave-specs: #279 spec 64 dynamic nodes (head `8da2254d`); #266 provisioning audit Item 6 autonomous (`eb45378d`); #207 spec-28 CLI CR draft (`218ffaeb`).
Open PRs, inferweave (10 of more): #1045 CPU System One (`222b45ef`); #1044 beast lab unit; #1043 prefix aliases (`45497606`); #1023 fry image; #1020; #1016/#1015/#1014 spec 64 stack; #1013 migrate gateway functionality to Rust (`c4e906a7`); #983.
Open PRs, gateway: #558; #556 prefix aliases stopgap (`7374d704`); #555 systemone batch route; #552 drain before reaper; #548 Go-vs-Rust parity harness (`0f9a4292`); #489; #488; #465; #464; #452.
Open issues, inferweave (122 open): #328 per-GPU placement/hot-swap (2026-09-20); #1001-#1006 spec 60 route reasons/estimated wait/usage (autospec generated); clippy cleanup #977-#980. Closed relevant: #842 advisory rebalancer reservation policy (G-01), #302 autoscaler, #714.
Open issues, gateway: #197 placement tests VRAM fit but not throughput; #171 MoE sized as dense. Closed #449, #22.
Open issues, specs: none matching (closed P3-T05/06/07/09/10 issues #82-#87).
Recent merged: inferweave #1041 (spec 62 controller lifecycle, 2026-10-15), #1022, #1012, #1000, #993, #917 (scheduling observability crate), #916, #873, #870; specs #284, #283, #282, #278, #281, #280, #276, #275; gateway #557, #554, #553, #551, #549, #547, #546, #545.
No open PR or issue covers: unified-memory accounting, energy-aware scheduling, memory/cache sharing, profile auto-optimization, perf-regression detection. Partial hits: capacity/forecast (#328, #842), CPU execution (#1045).

## 6. Decision per capability (reuse > extend > new)

| Capability | Decision |
|---|---|
| 1 predictive pressure | extend 46 §6 (forecast) |
| 2 context-aware capacity | reuse 46/inv 36 |
| 3 transactional reservations | reuse 50 + 46; reconcile with 62 lease |
| 4 crash recovery | reuse 50/62 snapshot; add conformance tests |
| 5 compat validation | extend `requirements.json` + 48 `validate` |
| 6 unified memory | new, as extension of 46 Quantity/physical domain |
| 7 prewarming | extend 32 |
| 8 CPU/GPU benchmarking | extend 12/39 |
| 9 energy-aware | new, minimal, objective only |
| 10 profile optimization | extend 39/24 |
| 11 regression | reuse 23/31 |
| 12 sharing | new/extend 50 |
| 13 forecasting | reuse 32 + 46 |
| 14 simulation | reuse 46 §9 / 61 simulate / 62 planner |
| 15 recommendations | reuse 61 + 24 |

Prerequisites before implementation: obtain Oct 9 text; reconcile spec 64 (PR #279); correct OPEN_GATES for #1041; every new behavior needs the AGENTS.md traceability set and stays `owed` until a failing-when-removed test exists.
