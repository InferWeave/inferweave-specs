# Dynamic nodes and gateway-driven model provisioning — 2026-10-15

**Status:** Proposed  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-15  
**Authorizes:** On acceptance: the wire contract of
`specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md` (the `iw.dynamic-node/1` capability, the
`dynamic` register member, the first `assignments` entry shapes, the heartbeat `provisioning`
member) and the reference implementation of it in the Rust gateway and node. It does **not**
authorize deploying it, enabling it on any production gateway, serving production traffic from a
drafted profile, or any change to routing, trust, admission or the autoscaler.  
**Relationship:** Extends `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` §5.1 (`assignments`
was reserved and always empty; this is the later minor release that section promised) and
`specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md` "Gateway-Assigned Deployments" (prose design, now a
wire shape); preserves `specs/43_GPU_PLACEMENT_HOT_SWAP.md` and invariants 15, 28, 36, 42 and
43. Supersedes no record. No resolved decision in `decisions/DECISIONS_REQUIRED.md` is reopened.

## Context

A node today names the model it serves on its command line and the gateway routes to what it
advertises. Adding a model means an operator sizing it, writing a catalogue or a launcher script
on the node, and restarting the node. The operator asked for the next step: start a node with
`--model dynamic`, let it advertise itself to its gateways, and let a gateway download, profile
and configure models onto it over the protocol, and only in that mode. The operator's first use is
two Qwen3.8 deployments (the 27B and Flash-Next, Q8 with vision) on the R9700 hosts, with every
card of one engine on one physical host, at 120k to 260k of context per request, and the highest
aggregate tokens per second a measured profile gives.

Spec 47 reserved `assignments` on the register response for exactly this and defined no entry.
Spec 25 described the exchange in prose for Slurm workers. The reference implementation had a
third mechanism, the executor node, which needs a node-local engine catalogue and a held link and
receives its card assignments on the telemetry acknowledgement, which a hardware-only node may not
file. None of the three let a node that joined with nothing be given something.

## Decisions

1. **The register and heartbeat responses carry the assignments**, as spec 47 reserved, under a
   capability (`iw.dynamic-node/1`) both sides must name. Alternative rejected: the telemetry
   acknowledgement, which a hardware-only node cannot file, and which would have made a dynamic
   node register something it does not serve in order to be told what to serve.
2. **Desired state with explicit withdrawal.** Entries are repeated until the node's status
   agrees; `stop` is its own kind; absence means no change; a restarted gateway adopts what a
   node reports serving. Alternative rejected: absence as withdrawal, which turns every restart of
   a gateway into a fleet-wide unload (`docs/specs/node-unload-and-coresidency.md` NU-3 records
   the same choice for executor nodes).
3. **The profile travels whole on the assignment**, and the node pins the cards by serial. The
   node needs no profile library and runs exactly what the gateway chose. Alternative rejected: a
   profile name the node resolves against its own copy, which lets two nodes run two different
   things under one name.
4. **Only measured profiles serve** (invariants 28 and 42): decode evidence at no less than 90%
   of the desired context floor at the serving slot count, and a quality block when the desired
   model requires one. A candidate without evidence is measured first by a `measure` assignment
   and the measurement becomes a draft profile the next plan may select. Alternative rejected:
   serving from a candidate's published figures, which spec 39 records as assumptions.
5. **All cards of an engine on one node**, by construction: an entry names one node's cards and
   as many as the profile's `match.gpu.count`. Alternative rejected: multi-node tensor
   parallelism, which the autoscaler's `--nodes=1` rule and spec 43 already exclude.
6. **The deployment id is derived** from the model, the profile, the image digest, the command
   and the artifact digests (invariant 15), never typed by an operator.
7. **Artifacts are fetched only on an assignment**, pinned by size and SHA-256, resumable, and
   never published under their path before the digest is verified (spec 20).
8. **A failed placement is not retried into the same hole** on this gateway's lifetime (spec 43
   failure handling); it is recorded and shown.
9. **One engine per dynamic node** in this version, dialled at an operator-named address.
   Link-only dynamic nodes and co-residency are follow-ups, recorded in the specification's
   non-goals.

## Consequences

Positive: a node joins with nothing and is given the best measured profile its host supports; a
gateway's model intent is one configuration file; an unmeasured candidate yields a measurement
on the target placement rather than a guess. Negative: a dynamic node needs docker and an address
the gateway can dial; the first serve of a new model waits on a fetch and a probe; a draft profile
has no quality score. Operational: the desired-model file, the drafts directory and
`GET /iw/v1/dynamic` are new operator surfaces.

## Requirements affected

- IW-DYNNODE-001 (new)
- IW-NODEHW-001 (spec 47 §5.1 amended: `assignments` non-empty under the capability)

## Proof status

The reference implementation carries unit tests (`iw-core::dynamic_node`,
`iw-gateway::dynamic_provisioner`, `iw-cli::dynamic_node`), HTTP tests against the real
handlers on loopback (`iw-gateway/tests/dynamic_nodes.rs`) and a scripted-gateway test of the
node's join loop in dynamic mode (`iw-cli::join`). Each fails when its control is removed. A
dynamic node that fetched real weights, launched a real profile and served through its gateway
has not been observed; that operational proof, and the two Qwen3.8 Q8 vision deployments the
operator asked for, are **owed** by `P5-T35` and recorded in `OPEN_GATES.md`.

## Rollback/revisit trigger

A fleet where the same node must hold two engines (co-residency), or where dynamic nodes sit
behind NAT, revisits decision 9. A measured case where a drafted profile without a quality score
served worse than a rejected shipped one revisits decision 4's default of not requiring a
quality suite.
