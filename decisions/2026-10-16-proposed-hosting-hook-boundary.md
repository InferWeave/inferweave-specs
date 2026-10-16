# Proposed: the spec 62 profile and load hook boundary with the spec 50 lifecycle — 2026-10-16

**Status:** Proposed — needs owner acceptance. This record decides and authorizes nothing.  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-16  
**Authorizes:** nothing (design proposal only; not implementation, a loader, a node assignment, a
deployment, a model load or an eviction).  
**Relationship:** `discloses` that spec 62 names the runtime lifecycle as the authority on loading
without saying what crosses the boundary; proposes the boundary without amending
`specs/50_TRANSACTIONAL_RUNTIME_LIFECYCLE.md`, `specs/62_FEDERATED_PROVISIONING_HOSTING_REQUESTS.md` or
`specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md`. Reads
`decisions/2026-10-15-dynamic-nodes-gateway-provisioning.md` (Accepted) as given. Not normative
specification text.

Code citations are to `InferWeave/inferweave@a54e0398b7faf0842145aab410d358021c618b5f`, read, not run.

## Context

Spec 62 puts five phases inside `ACTIVATING`: `acquiring`, `verifying`, `profiling`, `loading`,
`validating` (lines 196-199) and says "The owner's internal runtime lifecycle (spec 50: `DOWNLOADING`,
`LOADING`, `WARMING`, `VALIDATING`) is the implementation of these phases and remains the authority on
loading" (lines 198-199). `READY` is entered only after `validating` succeeded, "the model loaded,
answered a validation request, and its profile facts were recorded", and `verified` confidence comes
"only by the owner's own qualification" (lines 201-204). Loading "follows spec 50's transactional
lifecycle and the rebalancer; this text adds no loader" (lines 267-269). A failed phase has closed
reasons, among them `PROFILE_FAILED`, `VALIDATION_FAILED`, `INSUFFICIENT_VRAM` (lines 206-209).

The delivered seam, at the pinned commit:

* **`PhaseHooks`** has three methods the executor calls inside the gateway process:
  `profile(ctx, dir) -> ProfileFacts { vram_bytes }`, `load(ctx, dir)` and `validate(ctx) -> bool`
  (`crates/iw-gateway/src/provision_executor.rs:39-52`). The default `NoHooks` fails closed: `profile`
  returns `PROFILE_FAILED`; `load` and `validate` return `VALIDATION_FAILED` (`:56-71`; the two returns at `:67` and `:70`), so a load
  failure and a validation failure are already conflated. The hooks are one `Arc<Mutex<Box<dyn
  PhaseHooks>>>` shared by every reservation (`:134`, locked at `:500`, `:514`, `:526`), so one long
  hook call serializes the others'; the owner's default is one concurrent job
  (`provision_acquisition.rs:340`).
* **What a hook receives**: the reservation id, the approved `ModelRef`, egress hosts, digests, byte
  bounds, a per-phase deadline and a cooperative cancel flag (`OwnedPhaseContext`,
  `provision_acquisition.rs:376-395`), plus the reservation-scoped staging directory `dir`
  (`provision_executor.rs:503`, `:517`). It reports `PhaseReport`
  (`provision_acquisition.rs:407-428`): progress `done`, measured bytes, `profile_recorded`,
  `validated`.
* **Spec 50's loader is not in the gateway.** The node-side swap is `SwapDriver` with `drain`,
  `unload`, `load`, `warm` and `span` (`crates/iw-core/src/swap_executor.rs:55-83`), driven by
  `run_swap` (`:193`) with per-phase budgets and rollback rules, and implemented on the node by
  `EngineDriver` (`crates/iw-cli/src/engine_driver.rs`), which refuses any deployment that has no
  advert template: "join was not started with a --model or --models-dir naming it"
  (`engine_driver.rs:435`). A gateway-side hook therefore cannot call a loader. It can only hand
  intent across a control channel.
* **A second, accepted node path already exists.** Spec 64 / the accepted dynamic-nodes record let a
  gateway hand an enrolled dynamic node a `serve`, `measure` or `stop` assignment that carries the
  whole profile, artifacts pinned by size and SHA-256 fetched by the node only on an assignment, and
  reads progress back on the heartbeat (`provisioning` phases `fetching`, `launching`, `probing`,
  `serving`, `measuring` with `cellsDone`/`cellsTotal`, `measured` with `evidence`; spec 64 section 6).
  Its closed failure reasons are `artifact_unavailable`, `digest_mismatch`, `disk_full`,
  `runtime_unavailable`, `launch_failed`, `probe_failed`, `engine_exited`, `measure_failed`, `refused`
  (spec 64 section 6 rule 2). But spec 64 section 8 says it has "no co-residency", "no availability
  floor or dwell", and that "spec 43's swap lifecycle does not apply to a dynamic node's single
  engine"; it does not mention spec 50's reservation contract.
* **Evidence rows carry no VRAM.** A spec 64 evidence row is `context`, `concurrency`, `decodeTps`,
  optionally `prefillTps` and `ttftP50Ms` (spec 64 line 52). Spec 62's `ProfileFacts.vram_bytes`
  ("measured peak VRAM") therefore has no producer in either path as specified.
* **Three deployment identities exist.** Spec 50's `deployment_key`, `sha256:` over a canonical
  manifest recomputed by the receiver (spec 50 lines 78-99); spec 64's `dep_<hex>` derived from
  length-prefixed launch, artifact and advert fields (spec 64 section 5 rule 6; accepted decision item
  6); and the `dep_` id a node registers under, which the spec 56 producer reports as
  `deployment_fingerprint` (`crates/iw-cli/src/runtime_observation_report.rs:672`).
* **Two acquisition paths.** The gateway's `DownloadExecutor` fetches weights into a `0700`
  reservation-scoped staging directory (`provision_executor.rs`; spec 62 `acquiring` and `verifying`).
  A spec 64 node fetches for itself, only on an assignment (decision item 7). Spec 50 requires model
  bytes to enter a transactional cache: streamed into bounded staging, fully digest-verified, then
  published atomically, with pins for active and rollback entries (spec 50 lines 174-183).

Constraints: the rebalancer is the sole reservation authority and the lifecycle only expresses intent
(spec 50 lines 61-69, 100-102, invariant 1 at line 187); `READY` is never advertised without a
successful `VALIDATING` probe (invariant 3, line 193); the old runtime stays routable until the new one
validates, otherwise an explicit drain-and-swap or cross-node replacement, and a failed step rolls
back to the known-good deployment (lines 70-77); loads coalesce only by `deployment_key` and a waiter
detaching cancels nothing shared (lines 78-99); leases expire on absence of progress and accepted
progress can sustain a load for ever (spec 50 lines 135-146; invariant 37, `00_INVARIANTS.md:45`);
`READY` and its advertisement are one event with the spec 54 advertisement generation (spec 62
lines 218-219); probes are not verification (spec 56 lines 181-186).

## Options

### 1. Keep `PhaseHooks` as the loader seam

Implement `profile`, `load` and `validate` in the gateway by running a runtime directly.

* For: smallest change; the seam exists.
* Against: it is a second loader inside the gateway, which spec 62 line 269 and spec 50 invariant 1
  forbid; the process boundary makes it impossible for executor nodes (the node owns the engines);
  the shared mutex serializes unrelated reservations; and it would bypass drain-before-unload,
  rollback and the watchdog. Rejected.

### 2. Make the hook a thin adapter that submits intent to the owner's existing placement path

The hosting executor never loads. For each phase that needs a runtime it submits an intent to a target
adapter and waits for the target's reported progress:

* **2a, dynamic-node target:** `profiling` is a spec 64 `measure` assignment, `loading` plus
  `validating` is a `serve` assignment on a node that holds nothing else.
* **2b, spec 50 target:** the intent is a spec 50 manifest handed to the reservation authority
  (`RESERVING`), then the existing `SwapDriver` flow on an executor node.

* For: honors "adds no loader"; reuses two proven node paths; keeps one allocation authority.
* Against: two targets with different guarantees (2a has no reservation contract, no co-residency and
  no drain; 2b has all of them but needs an advert template the node does not have for a model it has
  never served); the three identities must be reconciled; VRAM measurement has no producer.

### 3. Collapse profiling into loading

Skip a separate profiling load: load the candidate once, validate, and record the measured facts of
that load as the profile.

* For: one load instead of two; spec 62's order (profiling, then loading) is awkward because
  `ProfileFacts` is measured peak VRAM, which needs the model resident.
* Against: spec 62 lines 187-188 and 201-204 and invariants 28/42 want facts measured on the target
  placement before serving; loading first and serving whatever it measured weakens that gate; spec 64
  already separates `measure` from `serve` for exactly this reason (decision item 4).

## Recommended option

**Option 2, adopted as a boundary rule rather than an implementation choice, with 2a as the first
target and 2b specified but gated behind spec 50's reservation contract.** Profiling stays a separate
step (against option 3), which on 2a is a spec 64 `measure`. The sketch below is for later spec text.

**What the hosting executor hands to spec 50 (or to a target that claims to implement it):**

1. A **manifest** from which the receiver recomputes `deployment_key` (spec 50 lines 90-99). The
   executor's stated key is never trusted. The record also carries the target's own derived id
   (spec 64 `dep_` or the registered id) so the mapping between identities is explicit, not assumed.
2. **Staged, verified artifacts by content digest**, not a path into a reservation directory. The
   `acquiring` and `verifying` phases end by publishing into the transactional cache (spec 50 lines
   174-183) or by naming a source the node can fetch from with the pinned size and digest (spec 64
   decision item 7). A reservation-scoped staging directory is never the runtime's model path, because
   release deletes it (spec 62 lines 209-211) and it is not a pinned, verified, atomically published
   entry.
3. The **approved bounds and the safe-peak request** as spec 50's `Quantity` shape with `basis`,
   `source` and `confidence`; an estimated VRAM figure is admitted as `estimated`, low confidence
   (spec 50 lines 107-113), and is re-requested after measurement before `loading` (spec 62 lines
   164-166).
4. A **cancel and a deadline**, mapped to waiter detach, not load cancel (spec 50 lines 94-99); the
   shared load stops only after the final waiter or a revoked reservation.

**What the hosting executor must not do:**

* load, start, stop or unload a runtime in the gateway process, or call `SwapDriver`/`EngineDriver`
  directly;
* choose the GPUs, create or extend a reservation outside the rebalancer, or run a scheduler of its own;
* publish an artifact from its staging directory into a serving path, or mark anything `READY`
  or advertise it (the controller does that, as one event with the new instance generation, after the
  target reports a validated, served state);
* run its own synthetic validation: `validate` reports the target's `VALIDATING`/`WARMING` result,
  which uses the real admission path (`swap_executor.rs`, `SwapDriver::warm` doc);
* evict a model, except as a step of a spec 50 swap named by an approved eviction set (see
  `decisions/2026-10-16-proposed-hosting-operator-audience.md`), and never before the weights are
  acquired and verified;
* retry into a hole a permanent failure already marked (spec 64 section 7 rule 8; spec 43);
* claim `verified`: a profile it records is `probed` at best (spec 62 lines 201-203; spec 56 lines
  181-186); `verified` needs the qualification record of
  `decisions/2026-10-16-proposed-qualification-verifier.md`;
* bypass the watchdog, rescue, quarantine, restart-loop protection or Slurm authority (spec 62 lines
  267-269);
* hold the controller lock across a runtime call.

**Progress, two leases.** The provision lease (invariant 37, spec 62 lines 212-218) and the spec 50
runtime reservation (own fence, `progressTimeoutMs`, authority-tick deadline; spec 50 lines 135-146)
stay separate. The hook forwards a target's progress, such as bytes fetched, `cellsDone`, a phase
transition, only when it strictly advances, and never synthesizes it: a heartbeat with unchanged `done`
is not progress (spec 62 lines 214-215). Neither lease extends the other. If either expires the
reservation is released and the other is released with it (spec 62 lines 209-211; spec 50 lines 144-146).
The runtime reservation is requested when the first GPU-needing phase begins and renewed with measured
figures before `loading`.

**Failure mapping (to be confirmed by the owner; spec 62's list is closed).** `measure_failed` to
`PROFILE_FAILED`; `probe_failed` and a failed validation to `VALIDATION_FAILED`; `digest_mismatch` to
`DIGEST_MISMATCH`; `disk_full` to `INSUFFICIENT_DISK`; an out-of-memory load to `INSUFFICIENT_VRAM`;
`artifact_unavailable` to `DOWNLOAD_FAILED`; `refused`, `runtime_unavailable`, `launch_failed` and
`engine_exited` have no clean spec 62 reason, and the delivered code maps load failure to
`VALIDATION_FAILED` already (`provision_executor.rs:67`, `:70`). Whether spec 62 needs a closed `LOAD_FAILED`
reason is an owner question.

**Rollback.** On a failed load, warm or validation the hook reports the failure and releases; the
target performs the rollback to the known-good deployment under spec 50 lines 70-77 (2b) or stops its
single engine (2a). The hook never rolls routing back itself.

**Rollout.** (1) A `PhaseTarget` trait in the gateway whose only operations are submit-intent, read
progress, cancel, and release, with a fake target and the existing `NoHooks` behaviour preserved as the
failing default; (2) the 2a adapter on dynamic nodes with one hosting reservation per node, proven on the
lab hardware that already ran the dynamic-node proof; (3) a VRAM measurement source (an owner decision:
extend the spec 64 evidence row, or take the figure from the spec 46 memory report taken during
`measure`); (4) the 2b adapter after the owner decides how a model with no advert template reaches an
executor node.

## Consequences

* Positive: the gateway keeps no loader and no second scheduler; the same boundary serves both node
  paths; every unsafe action is named and testable; a hosted model's confidence cannot be inflated.
* Negative: two loads (a measurement then a serve) on 2a; 2a has no reservation contract and no drain,
  so it can host only onto idle cards and cannot be the eviction path; the three deployment
  identities stay unreconciled; the shared hook mutex must be replaced by per-target state if more than
  one hosting reservation runs.
* The delivered `PhaseHooks` trait becomes legacy: the new trait replaces it, and `NoHooks` stays as the
  default so nothing reaches `READY` without a target.

## What implementation would follow

Spec 62 text for the boundary rules and the failure mapping; a spec 50 note stating how a hosting
reservation maps to `RESERVING`; a Rust `PhaseTarget` trait and fake; the 2a adapter; tests that fail
when each "must not" is removed (no in-process load, no `READY` before the target's validated report,
no staging path as model path, progress never synthesized, cancel detaches a waiter only). Tasks
`A-T05` and `P5-T17`, with `P5-T35` for the dynamic-node side. No task-graph change.

## Open questions for the owner

1. Is 2a (dynamic node, one engine, no drain) an acceptable first target, given it cannot evict?
2. Which deployment identity does a hosted model carry, and may the three be unified later?
3. Where does measured peak VRAM come from: a new spec 64 evidence member or the spec 46 report?
4. Should spec 62 gain a closed `LOAD_FAILED` reason, or is `VALIDATION_FAILED` kept?
5. How does a model no executor node has an advert template for get one: a new node assignment kind, or
   not at all for executor nodes?
6. Are acquisition by the gateway (staging) and acquisition by the node (spec 64) to be one path, for
   example both reading from the owner's store (`specs/65_INFERWEAVE_STORAGE.md`, still Proposed)?

## Not authorized

Any implementation, trait or adapter; any assignment to any node; loading, unloading or evicting any
model; changing the delivered hooks' behaviour; any deployment; any production traffic.
