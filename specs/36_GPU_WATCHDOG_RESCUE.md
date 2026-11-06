# 36 — GPU Watchdog, Runtime Rescue and Automatic Rollback

## Goal

InferWeave must make failed or wedged GPU serving nodes easy to rescue without losing the operational safety behavior developed in earlier AutoSpec/InferWeave tuning work.

The watchdog is a first-class node capability, not an optional dashboard script.

It protects:
- physical GPU resources;
- model/runtime processes;
- active deployment profiles;
- node availability;
- prompt/request accounting;
- owner workloads;
- Slurm allocations.

## Principles

1. Detect failure before routing more work to a broken resource.
2. Stop admissions before attempting rescue.
3. Prefer the least destructive recovery action.
4. Preserve the last known-good deployment/profile until recovery succeeds.
5. Never loop endlessly.
6. Record every rescue attempt and outcome.
7. Quarantine repeated severe failures.
8. Slurm remains authoritative for scheduler-owned hardware.
9. GPU owner priority remains absolute.
10. Recovery must not corrupt prompt, telemetry, benchmark, contribution or lease accounting.

## Expected device inventory

The devices a node expects are derived from discovery and versioned with the hardware
fingerprint, never held as a configured constant.

A hard-coded expected device count turns every legitimate hardware change — a card removed,
replaced or added — into a permanent degraded state no recovery action can clear, because
nothing is actually broken.

A change in device count or device identity is a requalification trigger:

- record a new host generation (`26_RESOURCE_IDENTITY_REDISCOVERY.md`);
- re-measure the resource envelope and the published context ceiling;
- re-advertise capability before becoming schedulable again.

A device count below expectation is never resolved by falling back to CPU execution. Silent
CPU fallback presents as a working node serving at a small fraction of expected throughput,
which is harder to detect than an outage.

## Watchdog signals

Monitor, where supported:

```text
backend process liveness
container liveness
node heartbeat
request progress
stream update gap
GPU utilization
GPU temperature / hotspot
GPU power
GPU clocks
VRAM usage
KV usage
GPU error counters
GPU reset events
illegal-memory / Xid / ROCm faults
ECC where exposed
driver/runtime errors
OOM
OOM below admitted envelope
NaN / invalid numerical output
tool/JSON correctness failures
prefix-cache-only corruption
model hash/artifact corruption
profile fingerprint drift
restart frequency
PCIe link degradation
thermal throttling
```

A metric marked unsupported is not interpreted as zero.

## Kernel OOM attribution

For `IW-WATCH-001` / `P1-T20A`, a kernel OOM record is evidence to classify,
not proof that the monitored runtime failed. This implements invariants 34–35
without withdrawing a healthy runtime for a provably unrelated memory limit.

A watchdog may discount a memory-cgroup OOM only when a bounded, complete event
proves all of the following:

- the constraint is explicitly `CONSTRAINT_MEMCG`;
- both the constrained cgroup and victim's cgroup are known, with the victim
  inside the constrained subtree;
- the matching victim record identifies the same PID and task;
- both cgroups are disjoint from the monitored engine and registrar container
  roots, including their ancestors and descendants.

Derive monitored scope from trusted runtime identity and kernel process
membership, not from event text, a configured process name or an unverified PID.
For Docker, bind the actual memory cgroup to the pinned container generation and
running PID, and reject a generation change during capture. Normalize a PID in a
delegated child to the exact container-ID ancestor: an OOM in a sibling child is
still an OOM of the monitored container. Ambiguous or unavailable provenance is
not evidence that an event is unrelated. A stopped registrar has no live scope;
when registration starts, monitoring must include its current trusted scope.

Engine/registrar OOM, their container-root sibling subtrees and ancestor-limit
OOM remain faults. Global OOM and unknown, malformed, truncated or unmatched OOM
events remain fail closed. Bound bytes, line size/count and pending event/victim
correlations; exceeding a bound is a monitor failure, never permission to ignore
records. An unrelated event must not mask a later runtime or GPU fault in the
same batch. Preserve GPU/native fault detection and fail-closed monitor errors.
A successful HTTP health check does not override a genuine runtime fault.

For a false-positive quarantine of the same engine incarnation, preserve the
original quarantine, cursor,
native-log baselines and engine identity. Before an explicitly authorized
acknowledgement, replay the complete saved-cursor kernel interval through the
corrected classifier using independently qualified scope. Missing or truncated
evidence blocks recovery. The corrected normal monitor must process the original
cursor; do not reset cursors, discard native evidence, recapture identity or
restart the engine to make the incident disappear. This rule grants no automatic
engine action or bypass of existing recovery/qualification gates.

### 2026-11-04 Beast incident and bounded proof

At 20:36:14 UTC, unrelated Python processes exhausted a memory-cgroup limit in a
user-session `app.slice/run-*.scope`. At 20:36:15 UTC, the Paiton containment guard
withdrew its registrar and quarantined with `runtime_fault_or_monitor_failure`.
Its implementation matched any host kernel `oom-kill:` / `out of memory:` line,
without cgroup attribution. The engine remained running in a separate Docker
cgroup, with its October 29 generation/start time unchanged and
`OOMKilled=false`; its native fault logs had not advanced.

The implementation defect was a host-wide OOM classifier. This specification's
previous unqualified `OOM` signal and acceptance text did not define attribution,
so an implementer following it could reproduce that false positive. The rules
above repair that omission; they do not relax detection of runtime OOM below the
admitted envelope.

The corrected operational guard's `main.rs` SHA-256 is
`d1af9a287717a3e3e561cc76072a0dad3a35aae645ef9d3bf06ae6738d247342`;
the tested Linux musl ELF SHA-256 is
`f73c9a2b760157b949ec939fbeb96c856a00a11cecf02df0d79752fcab2c2e98`.
Its module is `deploy/beast/paiton-flashnext-131k/guard`, preserved with its CI gate
in [implementation PR 1470](https://github.com/InferWeave/inferweave/pull/1470).
Bounded proof for this correction is:

- **proven, incident regression:** the exact foreign MEMCG/victim fixture first
  failed on the old classifier, then passed with attribution. A second failing
  regression exposed delegated-child scope hiding a sibling OOM; container-root
  normalization made it pass without discounting that fault.
- **proven, standalone Linux guard scope:** all 22 tests passed, including
  engine/registrar ancestry, global/unknown OOM, malformed/truncated input,
  provenance, GPU/native faults and existing containment ordering. Independent
  review accepted the correction after the sibling-scope repair.
- **incident recovery observation:** the preserved 90,046-byte saved-cursor
  journal interval contained eight MEMCG events and replayed clear under the
  corrected classifier. Recovery explicitly acknowledged the original false
  positive; it did not repeatedly clear quarantine or reset evidence. The
  registrar returned while engine generation and the locked three-slot,
  131K-per-slot W3A8 profile remained unchanged. Public chat and automatic tool
  selection passed. Forced structured output was rejected by the backend with
  HTTP 400 and is not recorded as a passing capability.

These observations prove only the scoped OOM classification/containment repair
and the reported recovery path. They do not grant a new Verified qualification,
prove sustained availability, authorize profile changes, or establish the full
automatic rescue/rollback ladder, device reset, or host reboot. Those controls
remain owed to their existing task/production gates; this guard has no automatic
engine actions. Existing `OPEN_GATES.md` restrictions remain binding.

## Owner cold-boot catch-up and epoch adoption

For `IW-WATCH-001` / `P1-T20A` and `IW-WATCH-003` / `P3-T18A`, a supported
owner operation may requalify an externally managed engine after a host reboot.
It is explicit owner recovery, not automatic healing, a new watchdog rescue
tier, or permission to reopen any production gate. The existing guard executable
and serving profile may remain pinned; the recovery helper must implement the
following contract independently of any normal monitor's bounded batch API.

A serving deployment fingerprint and a live engine incarnation are distinct.
Unchanged hashed model/profile/resource/policy/input bytes may retain their
immutable deployment identity; a new start time/boot/process needs a newly
qualified protected engine snapshot. Changed hashed inputs require normal
identity rederivation and qualification. Never relabel the old incarnation's
proof as current or adopt a changed profile through this operation.

### Containment and evidence boundary

- Hold an exclusive owner maintenance/recovery lock. Close ordinary admission,
  prove public active/pending and native active/waiting work are zero, and
  establish local-client quiescence. Keep the registrar stopped/unarmed and
  quarantine present throughout catch-up and local qualification. Preserve
  protected originals of the quarantine, identities, checkpoint files, guard
  package/unit, profile and serving inputs before any state publication.
- Replay the complete saved-cursor interval, including the retained previous-boot
  tail, every intervening retained boot and current-boot history through a fixed
  cutoff. A seekable cursor or a list of retained boots alone does not prove
  continuity. Bind boot IDs, ordered record identities, page boundaries and
  source retention/sequence evidence; detect missing, duplicated, reordered or
  vacuumed ranges. If completeness cannot be established, remain quarantined.
  A current-boot-only query cannot prove a cross-boot interval.
- Preserve OOM/victim correlation across bounded pages within one boot. At a
  boot boundary unresolved events fail closed; never pair records across boots
  or discard pending events to finish a page. Use conservative protected
  historical engine **and registrar** container-root scopes for their relevant
  generations, including stopped historical registrars. Current live scope alone
  cannot establish that an old OOM was foreign. Unavailable or ambiguous scope
  provenance means unknown/fault; preserve all earlier OOM/GPU fault rules.
- Scan every unconsumed native byte through fixed per-file cutoffs, with enough
  carried state/lookbehind to detect patterns split across old offsets, chunks
  or concurrent appends. Bind device/inode lineage and byte offsets; missing
  files, replacement, truncation or unverifiable lineage fail closed. No tail-N,
  sample, discarded prefix, checkpoint deletion, rewind or blind tail baseline
  substitutes for complete replay. Bound records/pages/bytes, total work/time,
  line sizes and pending classifier state; hitting a bound refuses adoption.
- Include the entire local qualification interval in replay. Recheck engine,
  boot, input and log/journal identities before publication. Persist explicit
  watermarks and classifier boundary state. Bytes/records appended after the
  cutoffs remain pending for the normal guard; prove its first read resumes
  without gaps or double-skipped prefixes. If its bounds cannot consume the
  pending handoff, perform another bounded qualified catch-up or refuse; never
  advance past unseen evidence to fit a legacy batch limit.

### Qualification and publication transaction

Before adoption, freshly verify exact hardware binding, image, ordered launch
arguments, input digests, TP/KV/resource limits, context and concurrency geometry
against the unchanged owner-qualified package. Health HTTP 200, idle metrics,
offline digest agreement and prior ready proofs are insufficient. Fresh local
response-integrity, context and concurrent-session qualification must exercise
the retained envelope; the locked Beast case retains TP2 and three public
131072-token sessions without changing native sequence or KV limits.

Publish the engine snapshot, kernel cursor/boot watermarks, native offsets and
registrar-proof disposition as one coherent protected multi-file transaction.
A durable manifest binds old/new file hashes, generations, cutoffs and evidence.
Serialize all checkpoint writers and guard startup; an incomplete transaction
blocks the strict preparation path.
Stage regular private files, fsync their contents and parent directories, then
publish in a documented recoverable order. Keep quarantine until every required
replacement and transaction commit is durable; acknowledging quarantine is the
last publication step. A crash at any earlier step, mixed manifest/file state,
or ambiguous commit must leave registration blocked and quarantine retained or
re-established before any service start. Preserve originals for audit; rollback
must not reinstall an old engine identity as proof of the new process. An old
registrar PID proof cannot authorize a new registrar generation.

Normal startup must use a reviewed strict **no-bootstrap** preparation path:
require the exact already-running engine and reject absent/stopped/changed
engines without starting or restarting them. Passing an ignored flag to an old
hook is not enforcement. The existing guard/owner alone creates the new
registrar proof and arms it; no PATH shim, bypassed prehook, synthetic readiness
or public profile/transport change is permitted.

Keep ordinary traffic closed while fresh authenticated full-path completion,
context and concurrent-session qualification proves the new incarnation through
its real authorization/admission route. Preserve request identity, terminal
stream status, resource accounting and fault monitoring. Do not replay old
interrupted requests. Open ordinary admission only after the unchanged owner's
existing gates and explicit operational approval pass. On any failure or new
fault, contain/quarantine and preserve pending evidence; do not restart/retune
the engine, erase history or loop acknowledgements.

### Proof status and required failure tests

All cold-boot controls above are **owed** until executable removal-sensitive
proof, independent review and applicable repository checks pass. In particular:

- split/interleaved OOM across pages, historical registrar/ancestor OOM, and GPU
  faults cannot be hidden by foreign MEMCG events; cross-boot pairing fails;
- missing/duplicate/reordered records/pages, absent boots, vacuum/loss, oversized
  events and exhausted bounds refuse adoption;
- split native faults across offset/chunk/append boundaries, inode replacement,
  truncation and missing rank logs refuse adoption;
- concurrent engine/boot/input changes, append-at-cutoff and monitor handoff
  demonstrate no evidence gap; unseen events remain pending;
- fault injection at every file/manifest/quarantine publication and restart
  boundary proves crash containment and rejection of mixed epochs;
- stopped-engine strict startup cannot bootstrap; old identity/PID/ready proofs
  cannot arm a new generation; failed qualification cannot reopen admission;
- fresh local and authenticated context/session tests preserve the locked
  profile and accepted-request/replay semantics.

See [the operational correction and open proof boundary](../evidence/owner-coldboot-epoch-adoption-2026-11-06/README.md).

## Failure classification

```text
REQUEST_STUCK
BACKEND_HUNG
BACKEND_CRASHED
CONTAINER_UNHEALTHY
GPU_MEMORY_PRESSURE
GPU_OOM
GPU_OOM_BELOW_ADMISSION
GPU_RESET
GPU_ILLEGAL_MEMORY
GPU_DRIVER_ERROR
GPU_THERMAL
GPU_POWER_THROTTLE
GPU_PCIE_DEGRADED
OUTPUT_CORRUPTION
PROFILE_DRIFT
ARTIFACT_CORRUPTION
RESTART_LOOP
UNKNOWN
```

## Rescue state machine

```text
HEALTHY
  ↓
SUSPECT
  ↓
DRAINING
  ↓
SOFT_RESCUE
  ↓
VERIFYING
  ├── success → HEALTHY
  └── fail
       ↓
PROFILE_ROLLBACK
       ↓
VERIFYING
       ├── success → RECOVERING → HEALTHY
       └── fail
            ↓
RUNTIME_RECREATE
            ↓
VERIFYING
            ├── success → RECOVERING → HEALTHY
            └── fail
                 ↓
DEVICE_RECOVERY
                 ↓
VERIFYING
                 ├── success → RECOVERING → HEALTHY
                 └── fail → QUARANTINED
```

A watchdog policy may skip unsafe/unavailable stages.

## Rescue tier 0 — request/lease cleanup

For a single stuck request:
- stop new work only if resource health is uncertain;
- cancel the backend request;
- fence/release the lease;
- clear request-local resources;
- preserve unrelated healthy sessions if the runtime proves safe;
- verify progress before restoring admission.

## Rescue tier 1 — backend soft restart

Restart the model-serving child process/runtime while keeping the node control agent alive.

Use for:
- hung backend;
- backend crash;
- isolated memory leak;
- repeated request timeout.

After restart:
- reload exact active deployment;
- run health probe;
- verify GPU memory returned to expected envelope;
- verify one small inference;
- resume only after passing.

## Rescue tier 2 — automatic deployment/profile rollback

The historical AutoSpec/InferWeave behavior is mandatory.

Automatic rollback triggers include:
- GPU reset or illegal-memory error;
- OOM below the admitted envelope;
- deterministic equivalence failure;
- tool/structured-output failure above policy threshold;
- prefix-hit-only corruption;
- server restart loop;
- streaming p99/update-gap SLO violation;
- speculative acceptance below configured break-even threshold;
- deployment/profile fingerprint drift.

Before activating a candidate profile, retain:
- previous container image digest;
- previous deployment/model manifest;
- previous model mounts/artifact digests;
- previous environment/arguments;
- previous cache namespace;
- previous resource envelope.

Do not delete these until rollback verification succeeds.

## Rescue tier 3 — runtime container recreation

For persistent Docker nodes:
- stop/drain InferWeave-owned runtime container;
- recreate it from pinned digest/config;
- remount immutable model artifacts;
- restore known-good profile;
- re-probe hardware;
- run smoke/equivalence/health gates.

Container lifecycle control must be narrowly scoped to InferWeave-owned resources. Do not grant arbitrary untrusted code access to the Docker socket.

## Rescue tier 4 — GPU/device recovery

Device reset is more destructive and vendor/platform dependent.

It is allowed automatically only when policy proves:
- the node is dedicated/managed for InferWeave or owner explicitly enabled it;
- no owner workload is active;
- no unrelated container/process owns the GPU;
- no other Slurm allocation shares the device;
- reset capability is supported and verified;
- bounded cooldown/retry count remains.

Possible vendor-specific implementations can use the supported host management stack, but the watchdog contract is vendor-neutral.

After reset:
- full hardware/software probe;
- driver/device availability check;
- container/backend recreation;
- deployment rollback to known-good profile;
- benchmark smoke;
- mark RECOVERING before normal traffic.

## Rescue tier 5 — host reboot

Host reboot is **never automatic by default**.

It can only be enabled by explicit node-operator policy on a dedicated managed node.

Otherwise InferWeave:
- quarantines the GPU/node;
- reports a recommended reboot;
- exposes a one-click/CLI/MCP operator action where authorized.

## Slurm / Apptainer behavior

Slurm workers cannot take ownership of the host.

Inside an allocation the watchdog may:
- cancel a request;
- restart the model process;
- restart/re-exec the Apptainer workload within the allocation;
- rollback to an already available known-good SIF/profile;
- drain;
- flush results;
- exit with a diagnostic reason.

It must not:
- reset a GPU outside site policy;
- reboot the compute host;
- manipulate other allocations;
- start Docker;
- bypass Slurm.

Severe device failure is reported to the site connector/control plane. The allocation is drained/exited and the stable GPU resource can be marked DEGRADED/QUARANTINED pending future rediscovery or site action.

## Restart-loop protection

Track attempts per:
- deployment;
- backend;
- container;
- GPU;
- node.

Example bounded policy:

```text
soft restart:      max 2 / 10 min
profile rollback:  max 1 / activation incident
runtime recreate:  max 2 / 30 min
device reset:      max 1 / cooldown window
```

After the bound:
- stop attempts;
- quarantine;
- alert operator.

No unbounded watchdog loop.

## Health probes

Recovery verification includes:
- GPU enumeration;
- expected PCIe/topology;
- expected VRAM;
- temperature/power sanity;
- driver/runtime query;
- backend API health;
- exact deployment fingerprint;
- tiny deterministic inference;
- structured-output/tool smoke when deployment declares it;
- memory returned near baseline;
- no immediate reset/error.

A candidate production profile additionally requires its normal qualification/soak gates.

## Production qualification preservation

Production candidates must retain the earlier safety expectations:
- no GPU reset during required soak;
- no restart loop;
- rollback succeeds;
- OOM/preemption boundaries validated;
- cancellation/restart behavior validated.

## Telemetry

Emit counters/events such as:

```text
inferweave_watchdog_incidents_total{gpu,reason}
inferweave_watchdog_rescue_attempts_total{gpu,tier}
inferweave_watchdog_rescue_success_total{gpu,tier}
inferweave_watchdog_rescue_failures_total{gpu,tier}
inferweave_profile_rollbacks_total{gpu,reason}
inferweave_gpu_resets_observed_total{gpu}
inferweave_runtime_restarts_total{gpu,deployment}
inferweave_watchdog_quarantines_total{gpu,reason}
```

Every event links to:
- stable GPU ID;
- host generation;
- worker/allocation ID;
- deployment fingerprint;
- runtime/container digest;
- request IDs affected;
- timestamps;
- before/after health state.

## Dashboard / MCP / CLI

Dashboard:
- current watchdog state;
- incident timeline;
- rescue tier/current step;
- restart counts;
- active/rollback profile;
- last known-good profile;
- GPU errors/thermal/power;
- recovery verification;
- quarantine reason.

CLI:

```text
inferweave watchdog status
inferweave watchdog diagnose
inferweave watchdog rescue --gpu <id>
inferweave watchdog rollback --gpu <id>
inferweave watchdog quarantine --gpu <id>
inferweave watchdog recover --gpu <id>
```

MCP typed tools:

```text
get_watchdog_status
get_gpu_incidents
run_gpu_diagnostics
request_soft_rescue
request_profile_rollback
request_runtime_recreate
request_gpu_recovery
quarantine_gpu
```

Destructive operations require strong authorization and audit.

## Acceptance

- GPU reset removes the GPU from routing before more work is admitted.
- OOM below admitted envelope trips rollback/health policy.
- Complete provably unrelated MEMCG/victim pairs do not withdraw the monitored
  runtime; engine/registrar ancestor and sibling-container-subtree OOM do.
- Global/unknown OOM, incomplete attribution and monitor failure remain fail
  closed, including when an unrelated event appears in the same input batch.
- False-positive recovery preserves and replays the original cursor before an
  explicit quarantine acknowledgement; no engine action or qualification claim
  is inferred from a clear replay.
- backend restart loop is bounded and ends in quarantine.
- previous deployment/image/environment/cache remain available until rollback succeeds.
- successful soft rescue returns resource through RECOVERING before HEALTHY.
- failed rescue never loops indefinitely.
- Docker node can recreate InferWeave runtime container safely.
- Slurm/Apptainer worker drains instead of attempting host takeover.
- operator can inspect/rescue a GPU through CLI/dashboard/MCP.
