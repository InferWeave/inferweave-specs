# 10 — Cross-repository audit synthesis (milestone 1)

Status: **audit gate**. Static audit only: no builds, no tests, no hardware were run or used.
Repo SHAs: inferweave `7171259` (history squashed to `a142f83`, per-feature SHAs unavailable),
inferweave-specs `e99d655`, inferweave-gateway `fb5310d`.
Detail and file:line cites: `evidence/audit-parts/*.md` (four reports). Claims marked
**verified** were re-checked by the lead; all others are agent findings pending verification.

## 1. Package vs. authority
- The package is a design brief, not evidence. Invariant 37 (reservations expire on absence of
  observable progress, never elapsed duration) overrides package 03 "TTL". Package lease/TTL
  wording is read as *progress-based expiry*; any wall-clock value is only a watchdog bound.
- Oct 9 Architecture Consolidation and Oct 10 Federated Provisioning master specs are not in the
  repo; spec 62 + `docs/federated-provisioning-audit.md` stand in. Recorded, not invented.
- Package 06 message names differ from the delivered `provision.*` wire; the wire wins.
- Spec 64 (specs PR #279; inferweave PRs #1014-1016) is unmerged and overlaps. Resolve first.

## 2. Existing-versus-missing matrix
| Capability | Status | Decision |
|---|---|---|
| VRAM + KV accounting (iw-core/capacity.rs) | complete | reuse |
| CPU / RAM / NUMA accounting | missing | extend capacity.rs |
| Unified memory (Apple) single pool | missing (enum labels only) | new, inside capacity.rs |
| CPU-only node (zero GPU) | **broken**: capacity.rs:259 rejects vram==0 (verified); node_advert.rs:257 same (verified) | fix, extend |
| Transactional reservations (federated) | partial: provision_controller.rs; offers not subtracted (multi-parent double-spend), revoke not owner-bound/fenced, lease tick has no production caller (likely) | extend, fix |
| Rebalancer as sole accelerator authority | present in Rust; **Go pool loop is a second actuator** (`warmFloorOnce`, gateway main.go:3274 verified; acquires Slurm jobs) | consolidate: gate Go behind Rust |
| Runtime adapter (12 verbs) | mock only; `hardware_requirements()` has no callers (verified) | consolidate two runtime stacks |
| Backends | llama.cpp, vLLM real; ComfyUI/diffusers partial; TEI/ONNX/whisper/Piper/XGBoost stubs; SGLang/TensorRT/PyTorch/video missing | extend per adapter |
| Hot swap | stop-then-start, no peak reserve/cutover | extend (spec 50) |
| Artifact cache digest | non-cryptographic, no real I/O | fix (security) |
| Profile schema CPU/GPU/hybrid | missing; code refuses CPU fallback by design | extend schema, policy change |
| Aliases / routing | complete | reuse, no change |
| Federation modes/wire/fencing | partial: no production PhaseExecutor, no release msg, no schemas/vectors | extend |
| Slurm/Apptainer | SchedulerAdapter test-fake only; states/wait reasons missing | extend |
| Benchmarking | iw-runtime-bench orphan, duplicates iw-core/iw-cli | consolidate |
| Auto-optimization, regression detection | missing / spec only | new on consolidated bench |
| Dead in production | reservation_policy, cache_registry, cache_key, fed_multi_parent, context_admission, hot_swap, runtime_manager, iw-scheduling capacity/demand/placement | wire up, do not rewrite |
| Duplicated controllers | iw_core::autoscaler vs gateway autoscale*; adaptive::Controller; hysteresis configured 3x | consolidate |
| Gateway UI | nav, tokens, API client, SSE, stale handling, a11y, VRAM page exist | extend |
| UI gaps | unified mem, NUMA, deployment stages, leases, Slurm wait reasons missing; benchmark evidence only in apps/web; no calls to Rust provision/profiles/occupancy/demand | new views on existing shell |
| UI tests | 41 Playwright scripts not in CI; no screenshot baselines | add CI + baselines |
| SDKs | no SDK repos; only generated TS/Rust bindings | compatibility = generated clients |

## 3. The 15 hardening items
Reuse spec: context-aware capacity, transactional reservations, crash recovery, regression
detection, forecasting, dry-run, placement recommendations (46 §9, 61, 62).
Extend: predictive pressure (46 §6), compatibility validation, prewarming (32), adaptive CPU/GPU
benchmarking, profile optimization. New (need spec first): unified-memory accounting,
energy-aware scheduling, compatible cache sharing. Spec 46 safe-schedulable VRAM / pressure /
forecast / simulation are wire types or missing (`docs/gpu-memory-observation.md:3-5`).

## 4. Ownership map
- Rust (inferweave): all lifecycle, accounting, placement, rebalancing, reservations,
  federation, Slurm, benchmarking, observability.
- Go gateway: auth, admin, transparent relay, UI. Duplicated authority listed in
  `gateway-ui.md` must defer to Rust; remove only after parity proof (package rule).
- Specs: schemas, contracts, conformance vectors, OPEN_GATES, task cards. Contracts merge first.

## 5. Dependency DAG
```
S0 specs hygiene (resolve spec 64/PR 279, OPEN_GATES stale, validate_specs jsonschema env)
 └─ S1 contracts: profile exec fields, resource/ledger, provision release msg, slurm states,
        unified-memory, wait reasons, conformance vectors      (specs repo)
     ├─ W1 resource accounting + reservations (fix CPU-only, CPU/RAM/NUMA, unified mem,
     │      double-spend, fencing, tick wiring)
     │   ├─ W3 CPU/GPU/hybrid scheduling (needs W1 ledger, W2 hardware_requirements)
     │   └─ W4 federated provisioning + Slurm (needs W1 reservations)
     ├─ W2 universal runtime/adapters (consolidate stacks, sha256 cache, hot-swap)
     │   └─ W5 benchmarking/optimization (needs W2 adapters, W3 modes)
     └─ W6 gateway UI/observability (needs S1 contracts; reads W1/W3/W4 APIs; Go-authority
            demotion needs W3 parity)
W7 integration/security/e2e: continuous; final gate after all.
```
Serialize shared crate edits: iw-core capacity.rs (W1 only until merged), iw-gateway
provision_* (W4 only; W1 supplies a trait), iw-core runtime_family.rs (W2 only).

## 6. Decisions (conservative defaults, recorded)
D1 Go pool loop: a flag, **default on** (revised 2026-10-16; this originally said default off). Default-off would stop demand ever being acted on, which the gateway's own tests document as the failure it once had. Built as `-pool-reconcile on|off`, gateway #565 (merged). Do not delete the loop until Rust parity is proven; shadow mode needs a split of `pool.Reconcile` into plan and apply (gateway #559).
D2 CPU fallback: explicit opt-in per profile; strict-SLO rejects it; never silent.
D3 Artifact digest: SHA-256, with migration reading old digests read-only.
D4 Lease expiry: progress-based per invariant 37.
D5 Unified memory: one physical pool entry; RAM and "VRAM" views derived, never summed.
D6 Hardware claims: only mock/sim evidence unless a labeled runner reports the device.

## 7. Status update (2026-10-16) — supersedes anything above that disagrees

What changed after this audit was written, verified against the code or the PRs:

- **Merged:** inferweave #1056 (offer double-allocation and revoke ownership in the federated
  provisioning controller); inferweave-gateway #565 (D1 flag, default on); inferweave-specs
  #279 (spec 64). Follow-ups from the independent review of #1056 are tracked in inferweave #1061.
- **Lease expiry has no production caller of `tick`, confirmed**, and nothing outside tests
  attaches the provisioning transport at all (`with_provision_transport` is called only in
  `tests/gateway_e2e.rs`). The ledger is dormant in production, so the #1056 bugs were latent.
  Wiring is W4, not a W1 fix.
- **W1(a), the CPU-only fix, is not independent of S1.** `CapacityModel` has one accelerator pool
  that weights, KV and seats all draw from; relaxing the zero-VRAM check alone yields a node
  that advertises and admits nothing. It needs a memory-pool contract (system RAM as the pool;
  meaning of `vram_bytes` for a node with no accelerator). W1(a) and (b) are one change after S1.
- **CI exists and gates merges.** inferweave and inferweave-gateway use Woodpecker
  (`.woodpecker/rust.yaml`, `.woodpecker.yml`), not GitHub Actions; the earlier "no CI" reading
  came from looking only for `.github`. The specs repo has `protocol-ci.yml`, which showed no
  runs. The gateway's branch protection also requires the branch to be current with `main`.
- **jsonschema version split.** `validate_specs.py` and `conformance/runner.py` fail on the
  pinned jsonschema 4.23 (legacy `RefResolver` scoping) and pass on 4.17. The smoke failures seen
  earlier were this version effect, not independent defects. Several `RefResolver` call sites
  remain; see specs #287 and the follow-up issue.
- **Known flake, fixed upstream:** gateway tests failed intermittently with "TempDir RemoveAll
  cleanup: directory not empty" (a background key-usage write racing temp-dir removal); fixed on
  gateway `main` by #560.
- **Still true and unstarted:** the memory-pool contract (spec 65), W2 to W5, and shadow mode.
