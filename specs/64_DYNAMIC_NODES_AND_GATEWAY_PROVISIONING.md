# 64 — Dynamic nodes and gateway-driven model provisioning

## Status

**SPECIFICATION — PROPOSED; BLOCKED for production use.** This document defines the first
non-empty entry shape of the `assignments` member that
`specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` §5.1 reserved, the capability that puts it in
force, the facts a node sends to earn one, and the status it reports while carrying one out. It is
additive to InferWeave Protocol 1.1.0. Every required test is recorded `owed` by canonical task
`P5-T35` (feature `IW-DYNNODE-001`); see `OPEN_GATES.md`. The decision record is
`decisions/2026-10-15-dynamic-nodes-gateway-provisioning.md` (Proposed).

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

## 1. Relationship to other specifications

| Document | What it covers | What this document adds |
| --- | --- | --- |
| `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` | hardware-only registration; `assignments` reserved and always `[]` | the capability `iw.dynamic-node/1`, the `dynamic` register member, the first `assignments` entry shapes, the heartbeat `provisioning` member |
| `specs/25_SLURM_EPHEMERAL_PROVIDER_NODES.md` "Gateway-Assigned Deployments" | the design: a worker asks what to run and the gateway answers with desired deployments carrying pinned artifacts | the wire shape of that answer on the node control surface, for any node, Slurm or not |
| `specs/20_NODE_AUTOCONFIG_DISCOVERY.md` "Model fetch" | acquisition is resumable, checksum pinned, and authorized by deployment intent | the artifact entry (size, SHA-256, ordered sources) and the rule that only an assignment authorizes a fetch |
| `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md`, invariant 15 | a deployment is an immutable fingerprint | how the gateway derives the `dep_` id an assigned engine registers under |
| `specs/39_INFERENCE_RUNTIME_TUNING.md`, invariants 28 and 42 | a throughput figure names its depth; configuration is measured on the target placement | which runtime profiles may be assigned to serve, and how an unmeasured candidate is measured first |
| `specs/43_GPU_PLACEMENT_HOT_SWAP.md`, invariant 43 | per-GPU placement, failed loads, availability floors | the one-node rule for a placement's cards and the no-retry rule for a failed placement |
| `docs/specs/runtime-profile-autoselect.md` (implementation repository) | the `RuntimeProfile` document and its selection | the profile is carried whole on the assignment; selection moves to the gateway |

**Where the specification was silent.** Spec 47 reserved `assignments` for "images to pull, a
profile to run" and defined no entry. Spec 25 described the exchange in prose for Slurm workers
only, and the reference implementation grew a different mechanism: an executor node started
with a node-local engine catalogue, reached only over a link, told which deployment to put on
which card on the telemetry acknowledgement. That mechanism cannot provision a node that has no
catalogue, and a hardware-only node cannot file telemetry, so a node that joins with nothing to
serve had no path to serving anything. This document closes that gap on the surface spec 47
reserved for it.

## 2. Terms

- **Dynamic node:** a node that joins naming no model (`inferweave join --model dynamic`),
  registers hardware-only, offers `iw.dynamic-node/1` and serves what its gateway assigns.
- **Facts:** the `dynamic` register member: the node's cards by stable identity and serial, its
  host as the profile selector reads it, and its artifact root.
- **Assignment:** one entry of `assignments` on a register or heartbeat response: `serve`,
  `measure` or `stop`.
- **Status:** one entry of the heartbeat `provisioning` member: where an assignment is.
- **Desired model:** a gateway's configured intent to have a model served by its dynamic nodes.
- **Profile:** a `RuntimeProfile` document: match rules, a digest-pinned launch block, evidence.
- **Qualified profile:** a profile with decode evidence at no less than 90% of the desired
  model's context floor, at the slot count the model will serve, and with a quality block when
  the desired model requires one.
- **Draft:** a profile the gateway wrote from a measurement; it has no quality block.

## 3. Capability

A dynamic node includes `iw.dynamic-node/1` in its register `capabilities` offer (spec 47 §2.1).
A gateway that provisions dynamic nodes lists it in its response. The capability is in force for
a registration only when both arrays carry it, and a new registration renegotiates it (FA-10).

While it is NOT in force for the node's current registration:

- the gateway MUST NOT act on `dynamic` and MUST answer `assignments: []`;
- the node MUST ignore any `assignments` it receives and MUST NOT send `provisioning`;
- whatever the gateway held for the node is released on its next plan.

A gateway MAY list the capability without a provisioner configured; it then records the node
and assigns nothing. A node reads `assignments: []` from such a gateway as "nothing to do",
never as a withdrawal.

## 4. The `dynamic` register member

`schemas/v1/requests/node-dynamic-facts.json`. Sent on every register of a dynamic node, whether
hardware-only or routable. Rules:

1. A gateway MUST validate it before authentication and refuse a malformed member with
   `400 bad_request`, minting nothing: it MUST be an object; `version` MUST be `1`; `gpus` MUST
   name at least one card, each with a non-empty `gpuId` and `serial` and no `gpuId` twice;
   `artifactRoot` and `host.gpuModel` MUST be non-empty; the compact serialization MUST be at
   most 65536 bytes. `null` counts as absent.
2. `gpus[].gpuId` are the node's stable card identities, and the same registration lists them
   in `gpuIds` even when hardware-only. Spec 47 §4 rule 2 prefers an empty `gpuIds` on a
   hardware-only body; a dynamic node sends them so the inventory the gateway places on and the
   one the node later registers routable are one list. A gateway still derives no routability or
   capacity from them (spec 47 §4 rule 2 stands). A card marked `busy` is held by an engine the
   node did not start and is never assigned.
3. `serial` is what a launch pins the card by: sysfs `unique_id` on AMD, `GPU-<uuid>` on NVIDIA.
4. The member is stored only for a registration with the capability in force; a registration
   without it releases the node's holdings.

## 5. Assignments

`schemas/v1/requests/node-assignment.json`. The register response's `assignments` and the
heartbeat response's `assignments` carry the same entries. Rules:

1. **Desired state.** The gateway repeats every entry on every answer until the node's status
   agrees; a lost answer costs one interval and a duplicated one costs nothing. A node MUST
   treat a repeated id as already acted on.
2. **Withdrawal is explicit.** A `stop` entry names the id to stop; the gateway repeats it until
   the node no longer reports the id as active. The ABSENCE of an entry means no change: a
   gateway that restarted and holds no state answers `[]` and MUST NOT thereby stop a serving
   engine. On a node's first status after a restart the gateway adopts a reported `serving`
   engine of a desired model as held; one of a model no longer desired is stopped.
3. **Unknown entries are skipped.** A node MUST ignore an entry whose `kind` or `version` it does
   not know and MUST NOT fail a registration or a beat because of one (spec 47 §5.1). A node
   SHOULD count what it skipped and say so once.
4. **Bounded.** At most 8 entries per answer; a node reads no more.
5. **One node, all cards.** `gpuIds` of one entry name cards of the receiving node only, and
   their count equals the profile's `match.gpu.count`. A placement is never split across nodes.
6. **The deployment id is derived**, never typed: `dep_` and the lowercase hex SHA-256 over the
   length-prefixed sequence of the model id, the profile name, the profile version, the image,
   the image digest, every command argument in order, and every artifact's path and digest in
   order. A different profile, image, flag or weight file is a different deployment (invariant
   15). The node registers its engine under this id and keeps the deployment's artifacts under
   `<artifactRoot>/<deployment>/`.
7. **Artifacts.** Each names a plain relative path (no `..`, no leading `/`), its exact size, its
   lowercase hex SHA-256 and 1 to 8 sources tried in order (`file://`, then `http://` or
   `https://`). A node MUST verify size and digest before a file is published under its path,
   MUST keep a partial HTTP download and resume it with a `Range` request, MUST refuse to
   publish a file whose digest differs (`digest_mismatch`), and MUST check free space before
   fetching (`disk_full`). Only an assignment authorizes a fetch (spec 20).
8. **`serve`** carries the whole `RuntimeProfile` (the node needs no profile library), the
   artifacts, and the advert figures the gateway decided for it: slots, native context, context
   per slot, KV bytes per token, and the optional tool and structured-output claims. The node
   substitutes its own `<artifactRoot>/<deployment>` for the `$ARTIFACTS` prefix of a profile
   mount's host path, pins the cards by serial (profiles never name a card), launches, probes
   readiness and one long prompt, and only then re-registers as a routable node with that advert,
   the engine's endpoint and the deployment id. Its VRAM pool is the assigned cards' memory; its
   KV pool is `kvBytesPerToken × maxContextTokens × slots`.
9. **`measure`** carries a candidate profile with no evidence and a matrix of context depths (1
   to 8) and concurrencies (1 to 8) with an output cap. The node launches, probes readiness, runs
   every cell, reports one evidence row per cell and stops the engine. A row's `decodeTps` is the
   aggregate decode rate across the cell's concurrent streams, `prefillTps` the mean prompt rate
   and `ttftP50Ms` the median time to first token; a cell's prompts are distinct so no cached
   prefix serves another.
10. **One engine per dynamic node** in this version: a `serve` or `measure` that arrives while
    one runs is refused (`refused`), never queued.

## 6. The `provisioning` heartbeat member

`schemas/v1/requests/node-provisioning-status.json`. Sent on every beat while the capability is
in force: one entry per assignment the node has acted on, with `phase` one of `pending`,
`fetching` (with `bytesDone`/`bytesTotal`), `launching`, `probing`, `serving` (with `endpoint`
and `deployment`), `measuring` (with `cellsDone`/`cellsTotal`), `measured` (with `evidence` and
`readySec`), `failed` (with a closed `reason` and a message) or `stopped`. Rules:

1. A gateway reads it leniently after the beat is accepted: a malformed entry is dropped, never a
   refused beat; a member over 65536 bytes is read as empty.
2. `reason` is closed: `refused`, `artifact_unavailable`, `digest_mismatch`, `disk_full`,
   `launch_failed`, `probe_failed`, `engine_exited`, `measure_failed`. What failed is reported,
   never the bytes that failed it.
3. A serving engine that stops answering `/health` for three consecutive beats is stopped and
   reported `failed` with `engine_exited`; its cards are released. A `message` is at most 512
   characters. A terminal status (`failed`, `stopped`, `measured`) is reported for at least ten
   minutes after its last change and MAY be dropped after, so the list stays bounded.
4. A hardware-only dynamic node files no telemetry (spec 47 §4); its status rides the beat.

## 7. The gateway's plan

The gateway's desired models (`IW_DYNAMIC_MODELS` in the reference: model id, profile family and
name, replicas, priority, the slots and context per slot each engine serves, a context floor,
whether a quality suite is required, the artifacts, the advert figures, and measurement
candidates) and its runtime profiles (the shipped set plus drafts) decide what each dynamic node
is told. The plan is deterministic in its inputs and runs on every register and beat:

1. **Reconcile.** A node that left takes its holdings with it. A reported `failed` records a
   failure for (node, model, profile) and drops the holding; `stopped` drops it; `measured`
   turns the candidate and the evidence into a draft profile, named
   `<candidate>-draft-<assignment>`, matched to the measured host and written to the drafts
   directory as YAML for an operator to promote. A model removed from the configuration is
   stopped wherever it serves.
2. **Qualify.** For each desired model, in priority order, and each node with no holding, only
   profiles whose `quantization` equals the model id's `quant` qualifier are considered (an
   MXFP4 profile never serves a Q8 id, whatever its family and name say), narrowed further by
   the model's profile allowlist when one is configured; of those, the profiles that match the
   node's host at any group size (largest first) are kept only if qualified (§2). They are ordered by quality tier (within the best score's tolerance is one
   tier), then measured decode rate at the context floor, then name and version. A profile that
   failed on this node for this model is skipped (spec 43: a failed load is never retried into
   the same placement).
3. **Serve** the first eligible profile on the first `match.gpu.count` free cards of the node,
   until the model's replicas are met.
4. **Measure** when nothing is qualified: the first measurement candidate matching the node's
   host that has not failed there, one measurement per model fleet-wide at a time.
5. **Explain.** Why each idle node holds nothing for each model is recorded with a closed reason
   (`occupied`, `no_matching_profile`, `no_qualified_profile`, `failed_before`,
   `measuring_elsewhere`, `replicas_met`) and shown on the operator view.

The operator view is `GET /iw/v1/dynamic` (admin secret only; a held assignment carries a
launch command): desired models with how many serve, every dynamic node with its facts, last
statuses, holdings and idle reasons, the profiles, the drafts and the failures.

## 8. What this does not do

- No link-only dynamic node: the engine's port is published on an interface address and the
  node advertises `<endpoint-host>:<port>` for the gateway to dial. A dynamic node behind NAT
  is a follow-up that carries the engine over the held link.
- No co-residency: one engine per dynamic node (§5 rule 10).
- No availability floor or dwell: a desired model's replicas are counted, not drained; spec 43's
  swap lifecycle does not apply to a dynamic node's single engine.
- No promotion of a draft to a shipped profile: a draft serves where its evidence qualifies it
  and the desired model does not require a quality suite; promotion to
  `docs/specs/runtime-profiles` with a measured quality score is an operator's act.

## 9. Compatibility

Additive and capability-gated. An older node never offers the capability, sends no `dynamic`,
reads `assignments: []` as before and never sees `provisioning`. An older gateway lists nothing,
so a dynamic node registered to it stays hardware-only and acts on nothing. A gateway that
negotiates the capability but has no provisioner answers `[]`.

## 10. Required tests

Recorded `owed` by `P5-T35`; see the task card and `contracts/canonical-task-graph.json`.
The reference implementation's unit and HTTP tests (`iw-core::dynamic_node`,
`iw-gateway::dynamic_provisioner`, `iw-gateway/tests/dynamic_nodes.rs`,
`iw-cli::dynamic_node`, `iw-cli::join` dynamic mode) exercise every rule above against
loopback engines and scripted gateways; a dynamic node that fetched real weights, launched a
real profile and served real requests through its gateway is the operational proof this gate
waits on.
