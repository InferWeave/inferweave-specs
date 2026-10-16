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
| `specs/39_INFERENCE_RUNTIME_TUNING.md`; invariants 28 and 42 | a throughput figure names its depth; configuration is measured on the target placement; an experimental profile is not selected by ordinary production routing until its qualification gates pass | which runtime profiles may be assigned to serve (section 2, the qualification gate of this surface), and how an unmeasured candidate is measured first |
| `specs/43_GPU_PLACEMENT_HOT_SWAP.md` "Failure handling"; invariant 43 | per-GPU placement; an out-of-memory or no-fit load is never retried into the same placement; the availability floor (invariant 43, not applied here, section 8) | the one-node rule for a placement's cards, and the extension of the never-retry rule to the permanent failure reasons of section 7 rule 8 |
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
  Its configuration names the canonical model id (which MUST carry a `quant` qualifier), the
  profile family and name it selects by, the slot count and context per slot each engine serves
  (`serves.slots`, `serves.contextPerSlotMin`), and the other members listed in section 7.
- **Context floor:** the context depth a desired model's evidence must reach: its configured
  `contextFloor`, by default `serves.contextPerSlotMin`.
- **Profile:** a `RuntimeProfile` document: match rules, a digest-pinned launch block, evidence.
- **Evidence row:** one entry of a profile's `evidence`: `context` (the depth measured at),
  `concurrency` (the streams), `decodeTps` and optionally `prefillTps` and `ttftP50Ms`.
- **Measured decode at the floor:** for a desired model, the largest `decodeTps` among a
  profile's evidence rows whose `concurrency` equals the model's slot count and whose `context`
  is at least 90% of the context floor (`context * 10 >= floor * 9`; a deeper row counts). It is
  absent when no row qualifies.
- **Qualified profile:** a profile with a measured decode at the floor (a row at the slot count
  the model will serve and at no less than 90% of the context floor) and, when the desired
  model requires a quality suite, a `quality` block. This is the qualification gate of this
  surface (section 8).
- **Draft:** a profile the gateway wrote from a measurement; it has no quality block.

## 3. Capability

A dynamic node includes `iw.dynamic-node/1` in its register `capabilities` offer (spec 47 §2.1).
A gateway that provisions dynamic nodes lists it in its response. The capability is in force for
a registration only when both arrays carry it, and a new registration renegotiates it (spec 47
section 2.1).

On the wire, while the capability is in force: `assignments` is a top-level member of the
register response and of the heartbeat response (`POST /v1/node/heartbeat`), present on every
answer, `[]` when there is nothing to do; and `provisioning` is a top-level member of the JSON
body of `POST /v1/node/heartbeat` (section 6).

While it is NOT in force for the node's current registration:

- the gateway MUST NOT act on `dynamic` and MUST answer `assignments: []` (the register response
  always carries the member; the heartbeat response then omits it);
- the node MUST ignore any `assignments` it receives and MUST NOT send `provisioning`;
- whatever the gateway held for the node is released on its next plan.

The same holds for a registration that offers the capability and has it in force but carries no
`dynamic` member (or `null`): the gateway acts on nothing, answers `assignments: []` and
releases whatever it held for the node.

**Only operator-enrolled credentials are provisioned.** A credential that only proved a key (spec
47 section 6) is never assigned anything, because an assignment carries a launch command and the
sources artifacts are fetched from. For such a registration the gateway stores no `dynamic`,
answers `assignments: []`, reads no `provisioning`, and releases whatever an earlier
registration of the id held.

A gateway MAY list the capability without a provisioner configured; it then records the node
and assigns nothing. A node reads `assignments: []` from such a gateway as "nothing to do",
never as a withdrawal.

## 4. The `dynamic` register member

`schemas/v1/requests/node-dynamic-facts.json`. Sent on every register of a dynamic node, whether
hardware-only or routable. Rules:

1. A gateway MUST validate it before authentication, whether or not the capability is offered,
   and refuse a malformed member with `400 bad_request`, minting nothing. `null` counts as
   absent. Otherwise it MUST be an object carrying every required member of the schema, with
   these types and values:
   - `version`: the integer `1`;
   - `host`: an object with `gpuVendor` (`amd` or `nvidia`), `gpuModel` (a string that is not
     empty or blank), and `ramGib`, `shmGib` and `pcieGen` (non-negative integers; `pcieGen` at
     most 255);
   - `gpus`: at least one card, each an object with a `gpuId` and a `serial` that are not empty
     or blank, `vramMib` (a non-negative integer) and optionally `busy` (a boolean), and no
     `gpuId` twice;
   - `artifactRoot`: a string that is not empty or blank; `containerRuntime`: a string;
     optionally `freeBytes`, a non-negative integer;
   - the compact serialization at most 65536 bytes.

   Unknown members are ignored. A node MUST also keep to the bounds of the schema: at most 256
   cards; `gpuId`, `serial` and `gpuModel` at most 256 characters; `artifactRoot` at most 4096;
   `containerRuntime` non-empty and at most 64. A gateway MAY refuse a member that exceeds them;
   the reference gateway enforces only the total size above.
2. `gpus[].gpuId` are the node's stable card identities, and the same registration lists them
   in `gpuIds` even when hardware-only. Spec 47 §4 rule 2 prefers an empty `gpuIds` on a
   hardware-only body; a dynamic node sends them so the inventory the gateway places on and the
   one the node later registers routable are one list. A gateway still derives no routability or
   capacity from them (spec 47 §4 rule 2 stands). A card marked `busy` is held by an engine the
   node did not start and is never assigned.
3. `serial` is what a launch pins the card by: sysfs `unique_id` on AMD, `GPU-<uuid>` on NVIDIA.
4. The member is stored only for a registration with the capability in force whose credential
   an operator enrolled (section 3); a registration without either, or without the member,
   releases the node's holdings. A re-registration of the same `nodeId` that has all of them
   replaces the stored facts and keeps the node's holdings (section 7 rule 7).

## 5. Assignments

`schemas/v1/requests/node-assignment.json`. The register response's `assignments` and the
heartbeat response's `assignments` carry the same entries. Rules:

1. **Desired state.** The gateway repeats every entry on every answer until the node's status
   agrees; a lost answer costs one interval and a duplicated one costs nothing. A node MUST
   treat a repeated id as already acted on.
2. **Withdrawal is explicit.** A `stop` entry names the id to stop; the gateway repeats it until
   the node no longer reports the id as active. The ABSENCE of an entry means no change: a
   gateway that restarted and holds no state answers `[]` and MUST NOT thereby stop a serving
   engine. On a node's first status after a restart the gateway adopts an engine the node reports
   active for a desired model as held; one of a model no longer desired is stopped (section 7
   rule 7).
3. **Unknown entries are skipped; invalid ones are refused.** The schemas describe the entries a
   gateway of this version emits, and a node validates entry by entry. A node MUST ignore an
   entry whose `kind` or `version` it does not know and MUST NOT fail a registration or a beat
   because of one (spec 47 §5.1). A node SHOULD count what it skipped and say so once. An entry
   of a known `kind` and `version` that fails validation (it does not parse, names a card the
   node does not hold, or breaks a bound of this section) is not acted on: the node reports it
   once as `failed` with reason `refused` when its `id` is a plain id (`^[a-z0-9._-]+$`, at
   most 128 characters), and otherwise skips it. The other entries of the answer are still
   acted on.
4. **Bounded.** At most 8 entries per answer (the gateway holds at most 8 for a node); a node
   reads the first 8 and skips the rest.
5. **One node, all cards.** `gpuIds` of one entry name cards of the receiving node only, and
   their count equals the profile's `match.gpu.count`. A placement is never split across nodes.
6. **The deployment id is derived**, never typed: `dep_` followed by the lowercase hex SHA-256
   of one byte string, built by appending *strings* in this order, each string encoded as its
   length in bytes as an unsigned 64-bit big-endian integer followed by its UTF-8 bytes:
   1. the model id;
   2. the profile `name`;
   3. the profile `version` as decimal digits without padding (`1`);
   4. the launch `image`;
   5. the launch `digest` (`sha256:<64 hex>`, as written; the empty string when absent);
   6. each element of the launch `command`, in order, one string each;
   7. for each artifact, in the order listed: its `path`, then its `sha256` (two strings).

   No count, tag or separator is written between or after the sections. Nothing else is hashed:
   not the artifacts' `bytes` or `sources`, the launch `label`, `engine`, `backend`, `env`,
   `privileges`, `mounts` or `shmSize`, the match rules, the evidence, nor the advert, so a
   profile is distinguished by its `name` and `version` together with the fields above. A
   different profile, image, flag or weight file is a different deployment (invariant 15). For a
   `measure` entry the profile is the `candidate`.

   Test vector (the preimage is nine strings: the model id, `r9700-q8-one`, `1`, the image, the
   digest, two command elements, `m.gguf` and the artifact digest):

   | input | value |
   | --- | --- |
   | model id | `qwen3.8-27b-modality-vision-quant-q8_k_xl` |
   | profile name, version | `r9700-q8-one`, `1` |
   | image | `ghcr.io/ggml-org/llama.cpp` |
   | digest | `sha256:` followed by 64 times `a` |
   | command | `--model`, `/models/m.gguf` |
   | artifact path, sha256 | `m.gguf`, 64 times `b` |
   | result | `dep_e5f4ad0bf3442ecc7c65ac599ada066faabd2aa6b22d2928180130d5f98c765a` |

   The value was computed from the encoding above (Python `hashlib`) from the reference
   implementation's `iw_core::dynamic_node::deployment_id`; it has not been checked by running
   that code. A caveat of the encoding: the `command` and artifact sections are not
   count-prefixed, so a deployment whose command ends in the strings an artifact would
   contribute hashes like one that lists that artifact; a later version is expected to count
   them.

   The node registers its engine under this id and keeps the deployment's artifacts under
   `<artifactRoot>/<deployment>/`. The assignment `id` is a plain id the gateway mints as
   `dyn-<boot>-<sequence>-<node>`: `<boot>` is a token fixed for the life of the gateway process
   (its start time in Unix seconds in base 36), `<sequence>` a counter of at least six digits
   that restarts with the process, and `<node>` the first 12 ASCII letters and digits of the
   node id, lowercased; an id minted by this version is at most 50 characters. A restart
   therefore mints different ids (unless two gateway processes start in the same second), and a
   fresh id never equals a status a node retains from the previous process or the name of a
   draft file already on disk. A node treats the `id` as opaque.
7. **Artifacts.** Each names, as members, a plain relative `path` (no `..` or empty segment, no
   leading `/`), its exact size `bytes`, its lowercase hex `sha256` and 1 to 8 `sources`. The
   sources are tried in the order listed; each is a `file://`, `http://` or `https://` URL. A
   node MUST verify size and digest before a file is published under its path,
   MUST keep a partial HTTP download and resume it with a `Range` request, MUST refuse to
   publish a file whose digest differs (`digest_mismatch`), and MUST check free space before
   fetching (`disk_full`). Only an assignment authorizes a fetch (spec 20).
8. **`serve`** carries the whole `RuntimeProfile` (the node needs no profile library), the
   artifacts, and the `advert` figures the gateway decided for it: `slots`, `contextSupported`
   (the native context), `maxContextTokens` (the context per slot, at most `contextSupported`),
   `kvBytesPerToken`, and the optional `tools` and `structuredOutput` claims. The node
   substitutes its own `<artifactRoot>/<deployment>` for the `$ARTIFACTS` prefix of a profile
   mount's host path, pins the cards by serial (profiles never name a card), launches, probes
   readiness and one long prompt, and only then re-registers as a routable node with that advert,
   the engine's endpoint and the deployment id. Its VRAM pool is the assigned cards' memory; its
   KV pool is `kvBytesPerToken × maxContextTokens × slots`.
9. **`measure`** carries a `candidate` profile with no evidence and a `matrix` whose members are
   `contexts` (1 to 8 depths, tokens), `concurrency` (1 to 8 stream counts) and `maxTokens` (the
   output cap per request, 1 to 4096); every depth is measured at every concurrency. The node
   launches, probes readiness, runs
   every cell, reports one evidence row per cell and stops the engine. A row's `decodeTps` is the
   aggregate decode rate across the cell's concurrent streams, `prefillTps` the mean prompt rate
   and `ttftP50Ms` the median time to first token; a cell's prompts are distinct so no cached
   prefix serves another.
10. **One engine per dynamic node** in this version: a `serve` or `measure` that arrives while
    one runs is refused (`refused`), never queued.

## 6. The `provisioning` heartbeat member

`schemas/v1/requests/node-provisioning-status.json`. A top-level member of the JSON body of
`POST /v1/node/heartbeat`, an array sent on every beat while the capability is in force (`[]`
when the node has acted on nothing): one entry per assignment the node has acted on, each with
`id`, `model`, `gpuIds`, `updatedAt` (Unix seconds of its last change) and `phase` one of `pending`,
`fetching` (with `bytesDone`/`bytesTotal`), `launching`, `probing`, `serving` (with `endpoint`
and `deployment`), `measuring` (with `cellsDone`/`cellsTotal`), `measured` (with `evidence` and
`readySec`), `failed` (with a closed `reason` and a message) or `stopped`. Rules:

1. A gateway reads it leniently after the beat is accepted: a malformed entry (or one with an
   empty `id`) is dropped, never a refused beat. A member that is not an array, or is over 65536
   bytes, is not a report: it changes nothing the gateway holds and does not count as the first
   report of section 7 rule 6. An empty array is a report. A gateway that caps the body of a
   hardware-only registration's heartbeat more tightly than other beats MUST raise the cap by
   65536 bytes for a beat that carries `provisioning` under a registration that negotiated the
   capability (the reference caps such beats at 16 KiB).
2. `reason` is closed: `refused` (the entry was invalid, named a card the node does not hold, or
   arrived while the node already runs an engine), `artifact_unavailable` (no source served an
   artifact), `digest_mismatch` (a fetched file differs from its pinned size or digest),
   `disk_full`, `launch_failed` (the container did not start or become ready), `probe_failed`
   (the engine answered and failed the probe), `engine_exited` (a serving engine stopped
   answering, or the executor stopped) and `measure_failed` (the measurement could not
   complete). What failed is reported, never the bytes that failed it.
3. A serving engine that stops answering `/health` for three consecutive beats is stopped and
   reported `failed` with `engine_exited`; its cards are released. A node sends a `message` of
   at most 512 characters (it cuts a longer one); the gateway keeps at most 256 characters of
   it on a recorded failure. A terminal status (`failed`, `stopped`, `measured`) is reported for
   at least ten minutes after its last change and MAY be dropped after, so the list stays
   bounded; when the member would exceed 65536 bytes the oldest terminal statuses go first, and
   an active status is never dropped.
4. A hardware-only dynamic node files no telemetry (spec 47 §4); its status rides the beat.
   Spec 47 §6.12 keeps a hardware-only registration's heartbeat to `busySlots`, `queueDepth` and
   `leaving`; `provisioning` on a registration that negotiated this capability is the one
   exception, and it contributes no devices, GPU memory or capacity (spec 47 §6.9).

## 7. The gateway's plan

The gateway's desired models (`IW_DYNAMIC_MODELS` in the reference) and its runtime profiles (the
shipped set plus drafts) decide what each dynamic node is told. A desired model is configured
with: the canonical model id; the profile `family` and `name` it selects by; `replicas` (default
1); `priority` (higher is placed first); `serves` (`slots` and `contextPerSlotMin`, the slots and
context per slot each engine serves); an optional `contextFloor`; `requireQualitySuite`
(default `false`); an optional `profilesAllow` list of profile names; the `artifacts`; the
`advert` figures; and measurement `measure` candidates, each a profile with no evidence and a
matrix. The gateway MUST refuse to start on a desired model it could never serve or could only
measure for ever, namely one whose id has no `quant` qualifier; whose `advert.slots` differs
from `serves.slots` or whose `advert.maxContextTokens` is below `serves.contextPerSlotMin`; that
sets `requireQualitySuite` and names any candidate (a draft never carries a quality block, so it
could never be selected); or that names a candidate which is not a valid profile, whose name is
not a plain id, that matches another model or is not admitted by rule 2, or whose matrix cannot
produce a qualified draft: its `concurrency` MUST contain `serves.slots`, its `contexts` MUST
contain a depth of at least 90% of the context floor, and no `concurrency` may exceed the
candidate's own `match.serves.slots`.

The plan is deterministic in its inputs and runs on every register and beat:

1. **Reconcile.** A node that left, or that registered without the capability, the facts or an
   operator-enrolled credential, takes its holdings with it. A reported `failed` drops the
   holding and, for the reasons of rule 8, records a failure for (node, model, profile);
   `stopped` drops it. `measured` drops the holding and settles the measurement: only the
   evidence rows at a (`context`, `concurrency`) cell of the assignment's matrix are kept, one
   per cell, each with a finite `decodeTps` above zero (a zero `prefillTps` or `ttftP50Ms` reads
   as not measured); the candidate and those rows become a draft profile, which is validated
   like any profile and MUST itself be qualified for the desired model (rule 2), or a
   `measure_failed` failure is recorded for the candidate instead and no draft is made. The
   draft is named `<candidate>-draft-<assignment id>` (the whole id), has version 1, no
   `quality` block, evidence rows stamped with the assignment id as `run` and the UTC date, and
   is matched to the measured host (its GPU vendor and model, the number of cards, the smallest
   assigned card's memory as `vramMibMin`, and the lesser of the candidate's and the host's RAM
   and PCIe generation); it is written to the drafts directory as `<name>.yaml` (staged and
   renamed so a reader sees all of it or none, retried after 60 s when the write fails) for an
   operator to promote, and a draft file that no longer parses is skipped at start. The
   draft's name is itself a profile `name`, which the schema bounds at 128 characters, so a
   configuration SHOULD keep a candidate's name at most 128 - 7 - 50 = 71 characters; the
   reference checks that a candidate name is a plain id of at most 128 characters, not this sum.
   A model removed from the configuration is stopped wherever it serves. A `stop` entry is done
   when the node no longer reports its id, or reports it `stopped` or `failed`.
2. **Qualify.** For each desired model, in priority order (ties by model id), and each node
   with no holding, in `nodeId` order:
   - *Admitted*: a profile whose `quantization` equals the desired model's quantization token
     (a profile with none is never admitted: an MXFP4 profile never serves a Q8 id, whatever
     its family and name say), and which is on the model's `profilesAllow` list when one is
     configured. The token is the model's configured quantization, not a value read from an id
     a node advertised; in the reference it is the `quant` qualifier of the model id the
     operator configured (validated at load, above).
   - *Matching*: the node's free cards (not `busy`) in `gpuId` order are tried as serving groups
     of every size from all of them down to one (the first *k* cards, with the smallest card's
     memory and the host's facts); an admitted profile matches the size equal to its
     `match.gpu.count` when the family and name, GPU vendor, GPU model (one of those listed),
     memory per card, host RAM and PCIe generation match, and its `match.serves.slots` and
     `contextPerSlotMin` are no less than the desired model's. The size of the group is not an
     ordering key.
   - *Kept only if qualified* (section 2): a profile with a measured decode at the floor and,
     when `requireQualitySuite`, a `quality` block.
   - *Ordered* by quality tier, then measured decode at the floor (higher first), then profile
     `name` (ascending), then `version` (descending). The *best score* is the highest
     `quality.score` among the qualified profiles that have one, compared in thousandths, and
     the *tolerance* is the `quality.toleranceAbs` of the profile that holds it (the larger on a
     tie). Tier 0 is a profile with a quality block whose score is at least the best score
     minus the tolerance (within the tolerance counts as one tier); tier 1 the other profiles
     with a quality block, higher score first; tier 2 the profiles with none.
   - A profile with a recorded failure (rule 8) for this node and model is skipped. This extends
     spec 43's never-retry rule for out-of-memory and no-fit loads to the permanent reasons of
     rule 8; the transient reasons expire after 600 s.
3. **Serve** the first eligible profile on the first `match.gpu.count` free cards of the node,
   until the model's replicas are met. A node holds one assignment, so a node that holds one is
   not considered for another model.
4. **Measure** when no profile matches the node or none is qualified: the first measurement
   candidate (in configured order) that matches the node's host on its first `match.gpu.count`
   free cards and has no recorded failure there, one measurement per model fleet-wide at a time.
   When every qualified profile has failed on the node, it is not measured but left idle.
5. **Explain.** Why each idle node holds nothing for each model is recorded with a closed reason
   (`occupied`, `no_matching_profile`, `no_qualified_profile`, `failed_before`,
   `measuring_elsewhere`, `replicas_met`, `awaiting_status`) and shown on the operator view.
6. **A registration places nothing.** A node is placed on only after the first `provisioning`
   report of its current registration (section 6 rule 1; an empty array counts). Until then it
   may be serving an engine the gateway cannot see (a gateway restart, a forgotten record, a
   swap), and a second `serve` would be refused as occupied. A node with the capability in force
   sends `provisioning` on every beat, `[]` when idle. The register response carries only the
   entries already held for the node, so it is `assignments: []` for a node the gateway holds
   nothing for; the first report unlocks placement and the next answer carries it. A
   re-registration starts that wait again.
7. **Adoption.** A gateway that restarted holds nothing and adopts what nodes report. For each
   status in a report whose id the gateway does not hold for that node:
   - an active phase (any but `failed`, `stopped`, `measured`) of a desired model becomes a
     holding with no entry to repeat and no known profile: `measuring` as a measurement, any
     other phase (`serving` among them) as a serving engine. It counts toward the model's
     replicas and occupies the node's cards. Replicas only limit further placement: a gateway
     does not stop a serving engine because more serve than `replicas`;
   - an active phase of a model that is not desired becomes a `stop` entry for that id,
     repeated until the node stops reporting it;
   - `measured` for a desired model is settled as in rule 1 when the model has exactly one
     measurement candidate for that many cards, and otherwise drafts nothing;
   - other phases change nothing.

   A re-registration of the same `nodeId` with the capability, the facts and an enrolled
   credential replaces the stored facts and keeps the node's holdings and its last reported
   statuses (a dynamic node re-registers as a routable node when its engine answers, and keeps
   the holding that produced it); placement waits for the next report (rule 6). A registration
   without them forgets the node and its holdings are released on the next plan.
8. **Failure classes.** A reported `failed` on a held assignment is recorded as a failure of
   (node, model, profile) by its `reason`, and the holding is dropped either way:
   - `refused` is a disagreement between node and gateway and says nothing about a profile: it
     is never recorded;
   - `engine_exited`, `artifact_unavailable` and `digest_mismatch` say nothing lasting about the
     profile (a dead mirror, a short file, an engine that died after serving): the pair is
     suppressed for 600 s, then tried again;
   - `launch_failed`, `probe_failed`, `disk_full` and `measure_failed` suppress the pair until
     the gateway restarts;
   - a failure on an adopted holding (no known profile) is not recorded.

   The gateway keeps at most 1024 failures, the oldest dropped first, and shows them on the
   operator view with a message cut to 256 characters.

The operator view is `GET /iw/v1/dynamic` (admin secret only; a held assignment carries a
launch command): desired models with how many serve, every dynamic node with its facts, last
statuses, holdings and idle reasons, the profiles, the drafts and the failures.

## 8. What this does not do

- No link-only dynamic node: the engine's port is published on the address the operator names
  on the node (`--endpoint-host`, required, an address without port or scheme; the node neither
  detects it nor takes it from an assignment) and the node advertises `<endpoint-host>:<port>`
  for the gateway to dial. A dynamic node behind NAT is a follow-up that carries the engine
  over the held link.
- No co-residency: one engine per dynamic node (§5 rule 10).
- No availability floor or dwell: a desired model's replicas are counted, not drained; spec 43's
  swap lifecycle does not apply to a dynamic node's single engine.
- No promotion of a draft to a shipped profile: a draft serves where its evidence qualifies it
  and the desired model does not require a quality suite; promotion to
  `docs/specs/runtime-profiles` with a measured quality score is an operator's act.

**Qualification.** The qualification of section 2 is this surface's gate for invariant 28
(experimental profiles are not selected by ordinary production routing until qualification gates
pass): only a profile with measured decode at the context floor, and a quality block where the
desired model requires one, is ever assigned to serve. A draft has the decode evidence and no
quality block, so it is serving on measured throughput alone. A gateway SHOULD mark a deployment
served from a draft as experimental on the operator view, and the decision record does not
authorize production traffic from one.

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
waits on. The deployment-id vector of section 5 rule 6 is a known-answer test every
implementation MUST pass.
