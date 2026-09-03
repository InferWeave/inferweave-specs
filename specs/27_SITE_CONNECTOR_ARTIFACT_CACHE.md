# 27 — Persistent Site Connector and Hierarchical Artifact Cache

## Goal

Each HPC/Slurm site may run one or more persistent **site connectors**.

GPU workers are ephemeral. The site connector is the stable InferWeave presence at the site.

It may provide:
- cluster/site identity;
- stable scheduler-node ↔ InferWeave host/GPU reconciliation;
- Slurm integration/control-plane adapter;
- model/artifact cache coordination;
- short-lived worker enrollment credentials;
- preferred site relay;
- connectivity rendezvous;
- site policy enforcement;
- aggregate site telemetry;
- local health/diagnostics;
- MCP diagnostics endpoint.

The site connector survives periods with zero active GPU allocations.

## Runtime role

The site connector is an independently deployable Rust service:

```text
inferweave-site
```

It normally runs as:
- a small VM;
- login/service node;
- Kubernetes/Podman/Docker service;
- another site-approved persistent host.

It should not require a GPU.

## Stable site identity

A site connector owns or has access to:

```text
provider_id
cluster_id
site_connector_id
site enrollment certificate
scheduler adapter configuration
resource identity mappings
site cache inventory
site policy
```

Site identity is authentication-backed and distinct from temporary Slurm worker credentials.

## Worker bootstrap

When a Slurm allocation starts:

1. worker contacts local site connector when available;
2. site connector confirms allocation/resource mapping;
3. worker receives short-lived InferWeave enrollment/connection credentials;
4. worker connects outbound to control plane;
5. stable host/GPU identities are reconciled;
6. worker requests desired deployment;
7. artifact locality is considered.

The worker can fall back to direct gateway enrollment when site policy allows and the connector is unavailable.

## Hierarchical content-addressed cache

Artifact lookup order:

```text
GPU/host local NVMe cache
        ↓
site shared cache / HPC shared filesystem
        ↓
site connector cache/proxy
        ↓
regional InferWeave cache
        ↓
configured upstream artifact/model store
        ↓
gateway artifact relay only as last resort
```

All model/runtime/deployment artifacts use immutable content hashes.

Never identify a deployable artifact only by a mutable model name/tag.

## Cache inventory

Each node/site reports:
- artifact digest;
- artifact type;
- size;
- local path/reference;
- last verified time;
- last used time;
- corruption/verification status;
- eviction priority.

The gateway uses cache locality when selecting deployments.

## Pre-staging

The control plane may ask a persistent site connector to pre-stage likely model/runtime artifacts before Slurm GPUs appear.

Pre-stage selection may use:
- historical demand;
- recommendation engine;
- upcoming scheduled reservations if site exposes them;
- model release/qualification queue;
- cache capacity;
- expected artifact transfer time.

## Cache safety

- verify digest after download;
- atomic publish after complete verification;
- resumable downloads;
- partial files never appear READY;
- quarantine corrupted artifacts;
- no credentials embedded in manifests;
- per-site license/policy checks;
- configurable eviction and disk-pressure limits.

## Site relay

If compute nodes cannot accept direct client traffic, the site connector may expose a relay path.

Preferred data order remains:

```text
direct client/proxy ↔ worker
site connector relay
regional relay
gateway relay
```

## HA

A site can run multiple connectors using the same cluster/site identity with separate connector instance IDs.

Resource identity mappings and site state must tolerate connector restart/failover.
