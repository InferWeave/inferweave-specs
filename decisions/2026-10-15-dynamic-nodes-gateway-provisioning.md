# Dynamic nodes and gateway-driven model provisioning — 2026-10-15

**Status:** Accepted  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-15 (accepted 2026-10-16; operational proof on real R9700 hardware, see `tasks/phase-5/P5-T35.md` and `evidence/dynamic-nodes-r9700-2026-10-16/`)  
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
aggregate tokens per second a measured profile gives. (As configured in the reference
implementation, not as contract: the 27B is `q8_k_xl` on two cards; Flash-Next is served as plain
`q8_0`, in six shards plus the projector, on eight cards, because the upstream repository
publishes no `UD-Q8_K_XL` build and the model needs about 213 GiB across its cards. The model id says
which: `...-quant-q8_0`.)

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
   node reports, and places nothing on a registration until its first `provisioning` report. Alternative rejected: absence as withdrawal, which turns every restart of
   a gateway into a fleet-wide unload (`docs/specs/node-unload-and-coresidency.md` NU-3 records
   the same choice for executor nodes).
3. **The profile travels whole on the assignment**, and the node pins the cards by serial. The
   node needs no profile library and runs exactly what the gateway chose. Alternative rejected: a
   profile name the node resolves against its own copy, which lets two nodes run two different
   things under one name.
4. **Only measured profiles serve** (invariants 28 and 42): decode evidence at no less than 90%
   of the desired context floor at the serving slot count, and a quality block when the desired
   model requires one; this is the qualification gate of this surface for invariant 28. A
   candidate without evidence is measured first by a `measure` assignment and the measurement
   becomes a draft profile the next plan may select; a model with measurement candidates cannot
   require a quality suite, and a candidate whose matrix could not produce a qualified draft is
   refused at load. A draft serves on measured throughput alone, so it is not authorized for
   production traffic by this record. Eligible profiles, drafts among them, are ordered by quality
   tier, then measured decode at the floor, then name and version; the size of the serving group
   is not an ordering key, so an engine over more cards wins only when its evidence says it is
   faster. Alternative rejected: serving from a candidate's published
   figures, which spec 39 records as assumptions.
5. **All cards of an engine on one node**, by construction: an entry names one node's cards and
   as many as the profile's `match.gpu.count`. Alternative rejected: multi-node tensor
   parallelism, which the autoscaler's `--nodes=1` rule and spec 43 already exclude.
6. **The deployment id is derived** from the model, the profile name and version, the whole launch
   block (image, digest, command, environment, privileges, mounts, shm size, engine, backend,
   label), the artifact paths and digests and, for a `serve`, the advert figures, as one SHA-256
   over length-prefixed strings and count-prefixed lists (invariant 15; spec 64 section 5 rule 6),
   never typed by an operator. A node recomputes the id and refuses an entry whose id differs.
   The first draft of this rule hashed fewer fields and did not count its lists, so a command that
   ended in the strings an artifact contributes hashed like that artifact, and two assignments
   that differed only in an environment variable, a mount or an advertised figure shared an
   id; both are corrected before this record was accepted, and the known answers are pinned in
   `conformance/dynamic-node-vectors.json`.
7. **Artifacts are fetched only on an assignment**, pinned by size and SHA-256, resumable, and
   never published under their path before the digest is verified (spec 20).
8. **A failed placement is not retried into the same hole** for the permanent reasons
   (`launch_failed`, `probe_failed`, `measure_failed`) on this gateway's lifetime, extending spec
   43's never-retry rule for out-of-memory and no-fit loads; the reasons that say nothing about the
   profile (`engine_exited`, `artifact_unavailable`, `digest_mismatch`, `disk_full`,
   `runtime_unavailable`) expire after 600 s. A full disk comes back and a stopped docker daemon
   or an unreachable registry says nothing about a profile, so retiring a good placement for the
   gateway's life on them would leave the node idle until a restart (`disk_full` was permanent in
   the first draft of this record and is corrected). `refused` is never recorded as a failure,
   but the same (node, model, profile) is not placed again for 60 s after a refusal, doubling to
   600 s, and the operator view shows it. A holding its node never reports is dropped after 300 s
   as a transient failure, and an engine found beyond a model's `replicas` is stopped. Failures
   are recorded and shown.
9. **One engine per dynamic node** in this version, dialled at an operator-named address.
   Link-only dynamic nodes and co-residency are follow-ups, recorded in the specification's
   non-goals.
10. **Only operator-enrolled credentials are provisioned.** An assignment carries a launch
    command and the sources artifacts are fetched from; an identity that only proved a key
    (spec 47 section 6) is never assigned anything and its `dynamic` and `provisioning` are not
    stored or read. Alternative rejected: provisioning any registered node, which would let any
    holder of a fresh key run the gateway's configured engines on its own host.

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

The deployment-id layout has known answers that the reference implementation's unit test asserts
and `python3 conformance/runner.py` recomputes independently (`conformance/dynamic-node-vectors.json`).
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
quality suite. The quantization of a desired model is read from the `quant` qualifier of the
model id the operator configured, not from a model id a node advertised. Spec 61 (the `quantization`
member of its profile facts, line 40) says a consumer never derives quantization by parsing an id
string; the gateway's configuration is the operator's own statement, not a producer's evidence, so
the reference reads it there, and the tension stays documented here rather than resolved: if spec
61's rule is read to cover configuration, the desired model carries the token as its own member
instead.
