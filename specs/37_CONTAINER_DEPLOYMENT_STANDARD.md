# 37 — Docker / Apptainer Deployment Standard

## Binding rule

All InferWeave production services and workloads are container-deployed.

### Persistent / ordinary hosts
Use **Docker Engine + Docker Compose**.

Applies to:
- gateway/control plane;
- Next.js web;
- PostgreSQL and supporting stores;
- persistent GPU node;
- edge/relay;
- site connector;
- local proxy where deployed as a service;
- MCP;
- benchmark/tuning services;
- watchdog/supervisor components.

### Slurm / HPC allocations
Use **Apptainer**.

Applies to:
- ephemeral Slurm GPU worker;
- Slurm-scoped inference runtime;
- Slurm benchmark/evaluation jobs.

Do not require Docker daemon access inside Slurm jobs.

## No alternate production substrate without ADR

Podman, Kubernetes, bare-metal system services, Conda-only runtime deployment and ad-hoc host Python environments are not supported production deployment paths unless a future ADR explicitly adds them.

The host may still use:
- the small `inferweave` bootstrap CLI;
- OS GPU drivers;
- Docker/Apptainer;
- scheduler/client tools;
- required security/network integrations.

Model servers and InferWeave services remain containerized.

## OCI artifact model

Build production images as pinned OCI artifacts.

Track:

```text
source revision
build recipe hash
OCI digest
SBOM
signature/provenance
runtime compatibility
model/runtime deployment fingerprint
```

Slurm/Apptainer deployments should consume the same trusted OCI lineage when practical, producing/using a pinned SIF or OCI-compatible Apptainer execution form with an auditable mapping back to the OCI digest.

## Docker GPU assignment

The bootstrap probe must identify exact GPUs and generate container configuration that exposes only intended devices.

Do not blindly expose every GPU to every service.

Docker Compose GPU reservations/device selection are generated from discovered hardware and operator policy.

## Apptainer GPU assignment

For NVIDIA:
- use Apptainer GPU support such as `--nv` or the current equivalent;
- restrict application-visible devices to the Slurm allocation.

For AMD ROCm:
- use `--rocm` or the current equivalent;
- bind only scheduler/site-approved device/runtime resources;
- respect Slurm visibility/allocation.

InferWeave must re-probe inside the container to confirm what the workload can actually use.

## Host/container compatibility

GPU drivers remain host-side.

The installer validates:
- driver availability;
- container runtime version;
- Docker GPU runtime prerequisites;
- Apptainer version;
- host/container libc/runtime compatibility where applicable;
- ROCm/CUDA compatibility;
- required device nodes/groups;
- shared filesystem bind paths;
- `/dev/shm` / IPC needs.

A failed compatibility probe blocks promotion rather than starting an unstable profile.

## Docker composition

The CLI owns generated deployment composition.

Examples:

Gateway:

```text
gateway
web
postgres
prompt/object storage profile
telemetry/benchmark storage profile
mcp
```

GPU node:

```text
node-agent
runtime/model-server
watchdog
optional local cache
optional restricted runtime-control helper
```

Edge:

```text
edge
relay
cache
mcp
```

Site:

```text
site-connector
site-cache
site-relay
mcp
```

Services are split only when operational isolation provides value.

## Watchdog and container lifecycle

Docker restart policies are a last line of liveness protection, not the entire watchdog.

The InferWeave watchdog:
- detects semantic/runtime/GPU failure;
- drains;
- restarts backend;
- rolls back profile;
- may recreate InferWeave-owned containers through a tightly scoped control path;
- verifies recovery;
- quarantines after bounded failures.

Never expose unrestricted Docker control to model workloads or public MCP/tool execution.

## Apptainer lifecycle

Slurm job wrapper:
1. obtains allocation;
2. stages/pulls verified SIF/OCI artifact;
3. starts worker/runtime under Apptainer;
4. registers with site/gateway;
5. serves or benchmarks;
6. traps scheduler warning/preemption signal;
7. drains and flushes;
8. stops Apptainer process;
9. exits.

Apptainer workers are disposable; stable GPU history is external to the container.

## Persistence

Persistent state never depends on a container writable layer.

Use explicit volumes/binds for:
- PostgreSQL;
- prompt/object store;
- config;
- identity/certificates;
- model cache;
- telemetry queues/outbox;
- benchmark artifacts;
- rollback manifests.

Model/deployment artifacts should be read-only once verified.

## Networking

Generated Docker networks separate:
- public ingress;
- internal control/storage;
- runtime/backend;
- admin/diagnostics.

GPU model-server ports should not become public merely because the container exposes them.

Slurm workers connect outbound.

## Security

- pin image digests;
- verify signatures/provenance;
- scan images;
- generate SBOM;
- drop unnecessary capabilities;
- read-only rootfs when feasible;
- non-root service users where compatible with GPU stack;
- explicit GPU devices;
- secret mounts rather than image-baked secrets;
- no host-wide privileged mode unless an explicit device-recovery helper requires narrowly reviewed privileges;
- keep watchdog/runtime-control authority isolated from inference code.

## Bootstrap CLI

`inferweave doctor` detects Docker or Apptainer based on role.

`inferweave init` generates only the supported substrate:

```text
gateway -> Docker Compose
node    -> Docker Compose
edge    -> Docker Compose
site    -> Docker Compose
proxy   -> Docker Compose
slurm-worker -> Apptainer
dev     -> Docker Compose
```

## Acceptance

- clean gateway install uses Docker Compose only;
- clean persistent GPU-node install uses Docker Compose only;
- Slurm worker runs without Docker daemon;
- Slurm AMD test successfully sees only allocated ROCm GPUs through Apptainer;
- Slurm NVIDIA test successfully sees only allocated CUDA GPUs through Apptainer;
- model/runtime artifacts are pinned and traceable;
- persistent state survives container recreation;
- watchdog can rescue/recreate InferWeave-owned Docker runtime safely;
- no production task requires a bare host model-server install.
