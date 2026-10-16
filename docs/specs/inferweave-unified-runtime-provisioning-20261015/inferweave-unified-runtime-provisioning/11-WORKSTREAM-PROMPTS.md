# 11 — Claude cloud session prompts

Sessions cannot talk to each other. Coordinate only through committed docs, issues, branches,
PRs and CI artifacts. Every session: read AGENTS.md of its repo, specs/00_INVARIANTS.md,
OPEN_GATES.md, `10-AUDIT-SYNTHESIS.md` and its audit part; re-verify any audit claim it relies on
before changing code (audit was static); run tests serially with timeouts; record proof as
`proven` only if a test fails when the control is removed, else `owed`; never claim hardware
validation from mocks; open a draft PR with audit evidence, test output and rollback steps;
no production deploys, no destructive migrations; do not touch paths outside "Allowed".

## S0/S1 — Specs hygiene and contracts (start first)
Repo: inferweave-specs. Allowed: schemas/, contracts/, openapi/, conformance/, fixtures/,
specs/ (new numbered spec only for unified memory, energy, cache sharing), OPEN_GATES.md,
tasks/, this package dir. Depends: none. Tasks: resolve spec 64/PR #279 overlap; refresh stale
OPEN_GATES per inferweave PR #1041; fix validate_specs.py jsonschema env; add profile
`execution.*` fields, CPU/RAM/NUMA/unified-memory resource schema, provision release message,
Slurm state + wait-reason vocabulary (frozen data, invariant 41), conformance vectors.
Accept: validate_specs passes; vectors fail when a field is removed. PR: one per contract area.

## W1 — Resource accounting and reservations
Repo: inferweave. Allowed: crates/iw-core/src/capacity.rs, node_advert.rs, reservation_policy*,
crates/iw-gateway/src/provision_controller.rs (ledger/CAS only), related tests. Depends: S1.
Tasks: accept zero-VRAM CPU-only nodes (capacity.rs:259, node_advert.rs:257); add CPU/RAM/NUMA
and single-pool unified memory; subtract outstanding offers (multi-parent double-spend);
owner-bound, epoch-fenced, idempotent revoke/renew/release; wire lease progress expiry into a
production caller; crash-recovery reconcile. Accept: concurrent-admission and overcommit tests,
Apple-unified no-double-count test, stale-offer, node-loss, lease-expiry/fencing tests, each
shown failing with the guard removed. PRs: (a)+(b) CPU-only and CPU/RAM/unified together, after S1
(a zero-VRAM relaxation alone does not make a CPU-only node admit anything; see 10 section 7), (c) ledger
(first slice merged: inferweave #1056; remainder in inferweave #1061).

## W2 — Universal runtime and adapters
Repo: inferweave. Allowed: iw-core/runtime_family.rs, iw-node runtime_manager/hot_swap/SwapDriver,
artifact cache, iw-embedding-runtime, iw-diffusion*. Depends: S1. Tasks: consolidate the mock
12-verb adapter and the real SwapDriver path into one; call hardware_requirements()/validate
before load; SHA-256 artifact digests with real I/O; hot swap with peak reserve, health check,
cutover, rollback. Backends added one per PR, only real or clearly marked stub.
Accept: adapter conformance suite; swap rollback tests; compat-validation rejects bad hw/runtime.

## W3 — CPU/GPU/hybrid scheduling
Repo: inferweave. Allowed: iw-scheduling, rebalancer integration, profile loader. Depends: W1,
W2, S1. Tasks: profile execution.preference; wire dead iw-scheduling placement/capacity and
context_admission into production; explicit-opt-in CPU fallback with SLO check; hysteresis
consolidated to one config; consolidate autoscaler duplicates; shadow-mode decisions.
Accept: simulation matrix (CPU-only, GPU-only, hybrid, strict-SLO rejects CPU), no silent downgrade.

## W4 — Federated provisioning and Slurm
Repo: inferweave. Allowed: iw-federation, iw-gateway/provision_* (executor/transport),
Slurm/Apptainer adapters. Depends: W1, S1. Tasks: production PhaseExecutor; release message;
real SchedulerAdapter (sinfo/sbatch/scancel) with queued/wait-reason/staging/downloading/
loading/warming/draining/preempted states and real job IDs; fault tests (partition, duplicate
commit, preemption, revocation, crash). Remote provisioning stays off by default.

## W5 — Benchmarking and optimization
Repo: inferweave. Allowed: iw-runtime-bench, iw-cli bench code. Depends: W2, W3. Tasks: fold
orphan crate and duplicated logic into one; benchmark key (digest+quant+runtime+hw+context+
batch+concurrency+mode) with staleness; regression detection; closed-loop profile suggestions
(recommend, never auto-apply without approval). Accept: reproducible measured figures only.

## W6 — Gateway UI and observability
Repo: inferweave-gateway (+ apps/web only for ported benchmark views). Allowed: web/, typed Rust
API client. Depends: S1; data from W1/W3/W4. Tasks: pool loop flag is DONE and defaults ON (D1,
gateway #565); shadow mode needs `pool.Reconcile` split into plan and apply first (gateway #559);
call Rust provision/profiles/occupancy/demand; add
unified-memory, NUMA, stages, leases, Slurm wait reasons, placement history on the existing
shell; run Playwright in CI with screenshot baselines; stale/redaction states.
Accept: existing UI unchanged; a11y checks pass; no new Go routing logic.

## W7 — Integration, security, e2e
Repos: all (tests/CI only). Continuous; final gate. Tasks: serial e2e, chaos (restart gateway/
node), multi-parent contention, SDK/generated-client compatibility, security review of cache
digest, fencing, revoke ownership, remote-provisioning defaults. Report physical-hardware runs
only where a labeled runner exists.
