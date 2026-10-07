# InferWeave Protocol v1 — architecture

The authoritative protocol definition is `specs/45_PROTOCOL_V1.md`. This document explains the
architecture for implementers.

## Planes

- **Data plane** — inference workloads; stays compatible with industry APIs (OpenAI-compatible
  primary).
- **Control plane** — registration, federation, topology, capability negotiation, model/runtime
  lifecycle, placement, capacity, autoscaling, draining, rebalancing, aliases, artifacts, admin.
- **Observability plane** — health, telemetry, events, routing explanations, accounting.

## Recursive federation

```text
Gateway
├── Gateway ── Node ── Device ── RuntimeInstance ── ModelResidency
├── Node
└── RelayNode
```

The upstream never assumes how downstream capacity is physically orchestrated. Bare metal,
Docker, Apptainer, Slurm, Kubernetes, cloud VM, remote gateway, and edge devices all present
identically through the generic protocol.

## Dependency direction

```text
inferweave-specs  →  inferweave (reference impl)  →  consumers  →  gateway (consumer/UI)
```

The protocol is specified first; no consumer defines protocol behavior.

## Key rules

- Stable identity, never physical address (invariants 17/18).
- Desired state separated from observed state.
- Unknown/0/null/false/not_reported/unsupported are distinct and preserved.
- Extension namespace for organization-specific metadata.
- Transport-independent object model; HTTP+JSON is the v1 transport.
