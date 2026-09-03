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
- backend restart loop is bounded and ends in quarantine.
- previous deployment/image/environment/cache remain available until rollback succeeds.
- successful soft rescue returns resource through RECOVERING before HEALTHY.
- failed rescue never loops indefinitely.
- Docker node can recreate InferWeave runtime container safely.
- Slurm/Apptainer worker drains instead of attempting host takeover.
- operator can inspect/rescue a GPU through CLI/dashboard/MCP.
