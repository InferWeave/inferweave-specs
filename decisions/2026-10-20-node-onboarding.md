# Managed persistent node onboarding — 2026-10-20

**Status:** Accepted design; implementation and operational proof owed.
**Decision owner:** InferWeave operator.
**Scope:** The operator authorized automatic onboarding/reconciliation implementation, independent review and normal merge, and installation/reset/qualification/restart tests on disposable Nibbler. This authorizes the bounded work, not a claim that the capability is deployed or production-ready.
**Contract:** `iw.node-reconcile/1`, defined in spec 64 section 11 and `contracts/node-reconcile.json`.
**Traceability:** `IW-DYNNODE-002`, canonical task `P5-T38`, acceptance ONB-01 through ONB-12, all implementation/operational proof `owed`.
**Relationship:** Additive to `iw.dynamic-node/1` and the accepted 2026-10-15 decision. P5-T35's Beast evidence retains its original scope. Neither that evidence nor the earlier Nibbler observability authorization proves this new capability.

## Why a separate negotiated extension

The existing dynamic facts contain one GPU model for a whole host, the executor permits one
engine, and a throughput-only draft can enter its serving candidate set. That cannot describe
mixed Pascal/Turing cards or the stronger qualification policy needed for automatically managed
onboarding. Reinterpreting the existing fields would let older peers execute a group or publish
a deployment under weaker assumptions.

Both parties therefore negotiate `iw.dynamic-node/1` and `iw.node-reconcile/1` on the existing
HTTP node-control registration. New versioned `reconcile` members carry register facts,
heartbeat recovery/attestation status, and owner-response qualification records/permits.
Existing `DynamicFacts`, assignment and provisioning-status schemas stay unchanged. There is
no new public administration API and no automatic fleet-wide activation.

## Decisions and implementation boundaries

1. **Facts are per physical card.** Model/vendor, serial, memory and PCIe facts are retained for
   every stable GPU identity. Measured NVIDIA compute capability is optional; absence is
   unknown. Only homogeneous compatible groups are selected. Owner use, RAM and storage budgets
   remain hard placement constraints. Inventory and control connectivity never imply serving
   capacity.
2. **One live instance per deployment per node.** Distinct deployments may occupy disjoint
   groups. A same-deployment second assignment is refused before conversion to card assignments;
   it cannot become an accidental multi-card span. An explicit span is one assignment with an
   exact qualified group. Identical-profile singleton replicas wait for a separately propagated
   instance identity. Changing immutable deployment IDs merely to manufacture instances is
   rejected: the existing engine set/router are keyed by deployment, and `NodeExecutor::apply`
   currently groups equal deployment IDs into one engine.
3. **One persistent Rust owner.** Linux Docker Compose owns enrollment, claims, telemetry,
   executor and bounded watchdog supervision. The first increment uses host networking because
   the existing router dials loopback ports published by sibling containers on the host. Prove
   that path before GPU qualification; do not widen engine binds to compensate. Apptainer remains
   for Slurm workers and is not required for this persistent-host setup.
4. **Adoption is ownership, not publication.** Attested containers may be adopted after process
   restart, but both initial adoption and subsequent executor settling require current
   qualification, fresh control observations, active watchdog supervision and no quarantine
   before publication. A healthy HTTP endpoint is insufficient, including after restart.
5. **Suspension differs from retirement.** Managed SIGTERM, SIGINT and graceful owner drop
   persist claims, withdraw readiness and detach attested engines for subsequent adoption.
   Explicit retirement withdraws admission, drains, unloads the owned engine and releases claims.
   Existing destructive paths are dynamic `Executor::drop`, `ContainerEngine::drop`, SIGTERM
   leaving cleanup and dynamic SIGINT cleanup. The startup `clear_leftovers` sweep is already
   restricted to owned exited/created/dead containers; it does not remove running containers.
   Real subprocess signal/drop tests are required. Legacy transient cleanup remains unchanged.
6. **Automatic qualification is policy-bounded.** The installed owner policy fixes allowed
   artifacts/profiles, scope, groups, resource budgets, checks and retry bounds. An opaque,
   short-lived owner-issued qualification permit allows a real request through the existing
   authorization/admission path while ordinary routing stays closed. It is bound to enrolled
   identity, owner epoch, policy, scope, assignment, immutable deployment, exact GPU set and
   environment. A throughput draft or node-supplied readiness claim cannot grant serving scope.
7. **Evidence and recovery survive restarts.** Stable identity, claims, failure suppression,
   bounded rescue attempts and known-good artifacts persist. A changed owner epoch invalidates
   old authorization permits; preserved evidence must be revalidated against actual residency
   and a fresh authorization/admission probe before a new readiness record is issued. With no
   known-good deployment, failed first qualification ends in bounded failure/quarantine, not a
   fabricated rollback. Elective changes honor healthy floors; severe faults withdraw unsafe
   capacity even when the resulting deficit needs replenishment.

## Authorized hardware work and limits

Nibbler is the disposable test host identified by the operator. Its reported inventory is one
RTX 2080 Ti plus two GTX 1080 Ti cards, approximately 11 GiB each, 16 logical CPUs and approximately
64 GiB RAM. These are unverified planning inputs, not new measurements in this decision. The
implementation must reproduce inventory, pin a runtime actually compatible with Pascal/Turing,
prove actual GPU execution, and record exact application/runtime/artifact identities.

Required new operational evidence includes clean installation, idempotent rerun, both node
signals and graceful drop, host reboot, gateway restart, full-path inference and cancellation,
failed qualification exclusion, bounded rescue/rollback and durable quarantine. All are owed.
No unrelated host reset, global catalogue activation or production approval is implied.

## Evidence and integration

The standalone checker is `python3 conformance/node_reconcile.py`; regression tests are
`python3 -m unittest discover -s tests/smoke -p test_node_reconcile.py`. They exercise synthetic
wire/owner-state examples only. They do not execute containers, authenticate live peers, verify
kernel compatibility, run watchdog recovery or staff independent release review.

The shared feature/task coverage, runner/validator hooks, bundle metadata and `OPEN_GATES.md`
trace this extension through `IW-DYNNODE-002` / `P5-T38`. These contract checks do not close the
operational gate. The new acceptance IDs are ONB-01 through ONB-12, all `owed`.
