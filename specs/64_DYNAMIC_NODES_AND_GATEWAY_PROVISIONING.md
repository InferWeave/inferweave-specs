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
| `specs/43_GPU_PLACEMENT_HOT_SWAP.md` "Failure handling"; invariant 43 | per-GPU placement; an out-of-memory or no-fit load is never retried into the same placement; the availability floor (invariant 43, not applied here, section 8) | the one-node rule for a placement's cards, and the extension of the never-retry rule to the permanent failure reasons of section 7 rule 8 (`launch_failed`, `probe_failed`, `measure_failed`) |
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
- **Draft:** a profile the gateway wrote from a measurement; it has no quality block and is
  experimental (section 8).
- **Transient** and **permanent** failure reasons: the reasons of section 6 rule 2 that expire
  after 600 s (`artifact_unavailable`, `digest_mismatch`, `disk_full`, `runtime_unavailable`,
  `engine_exited`) and the three that last until the gateway restarts (`launch_failed`,
  `probe_failed`, `measure_failed`). `refused` is neither (section 7 rule 8).

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

A gateway MAY list the capability without a provisioner configured. It then validates the
`dynamic` member like any other (a malformed one is still `400 bad_request`) but records nothing
about the node: not its facts, not its `provisioning`. It assigns nothing and answers
`assignments: []` on every register and heartbeat answer for which the capability is in force.
Its operator view answers `{"schema": "iw.dynamic-nodes/1", "configured": false, "models": [],
"nodes": []}`. A node reads `assignments: []` from such a gateway as "nothing to do", never as a
withdrawal.

## 4. The `dynamic` register member

`schemas/v1/requests/node-dynamic-facts.json`. Sent on every register of a dynamic node, whether
hardware-only or routable. Rules:

1. A gateway MUST validate it before authentication, whether or not the capability is offered,
   and refuse a malformed member with `400 bad_request`, minting nothing. `null` counts as
   absent. Otherwise it MUST be an object carrying every required member of the schema, with
   these types and values:
   - `version`: the integer `1`;
   - `host`: an object with `gpuVendor` (`amd` or `nvidia`), `gpuModel` (a string that is not
     empty or blank, at most 256 characters), and `ramGib`, `shmGib` and `pcieGen` (non-negative
     integers; `pcieGen` at most 255);
   - `gpus`: at least one card and at most 256, each an object with a `gpuId` and a `serial` that
     are not empty or blank and at most 256 characters, `vramMib` (a non-negative integer) and
     optionally `busy` (a boolean), and no `gpuId` twice;
   - `artifactRoot`: a string that is not empty or blank, at most 4096 characters;
     `containerRuntime`: a string that is not blank, at most 64 characters; optionally
     `freeBytes`, a non-negative integer;
   - the member **as the node sent it** at most 65536 bytes. The bound is measured on the
     compact serialization of the parsed member, unknown members included, before it is read
     into the typed form: a member padded with a large unknown member is refused, which a bound
     measured on the typed form (that has dropped what it does not know) would let through.
     (The measure is the compact serialization, not the byte count on the wire, so insignificant
     whitespace is not counted.)

   Unknown members are ignored. A gateway MUST enforce every bound above, those of the schema
   (`schemas/v1/requests/node-dynamic-facts.json`) as well as the total size, and refuse a member
   that exceeds one with `400 bad_request`. The message of that refusal is cut to 200 characters:
   it is returned to the node and logged, and a parser's error quotes the input it choked on.
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
   active for a desired model as held; one of a model no longer desired is stopped, and so is
   one beyond the model's `replicas` (section 7 rule 7).
3. **Unknown entries are skipped; invalid ones are refused.** The schemas describe the entries a
   gateway of this version emits, and a node validates entry by entry. A node MUST ignore an
   entry whose `kind` or `version` it does not know and MUST NOT fail a registration or a beat
   because of one (spec 47 §5.1). A node SHOULD count what it skipped and say so once. An entry
   of a known `kind` and `version` that fails validation (it does not parse, names a card the
   node does not hold, carries a `deployment` that its payload does not derive (rule 6), or
   breaks a bound or rule of this section) is not acted on: the node reports it
   once as `failed` with reason `refused` when its `id` is a plain id (`^[a-z0-9._-]+$`, at
   most 128 characters), and otherwise skips it. The other entries of the answer are still
   acted on. A node ignores members it does not know in an entry and in its `advert` (a newer
   gateway may add a figure); it reads the profile, the artifacts and the matrix strictly, so a
   member those do not know makes the entry unparseable and therefore refused.
4. **Bounded.** At most 8 entries per answer (the gateway holds at most 8 for a node); a node
   reads the first 8 and skips the rest. The answer has no byte bound of its own: it is bounded
   by that count and by the 64 artifacts and 8 sources per artifact an entry may name.
5. **One node, all cards.** `gpuIds` of one entry name cards of the receiving node only, and
   their count equals the profile's `match.gpu.count`. A placement is never split across nodes.
6. **The deployment id is derived**, never typed, and a node checks it. It is `dep_` followed by
   the lowercase hex SHA-256 of one byte string. In the layout below `S(x)` is the length of the
   string `x` in bytes as an unsigned 64-bit big-endian integer followed by the UTF-8 bytes of
   `x`; `N(n)` is the integer `n` as an unsigned 64-bit big-endian integer (a count, or an advert
   figure); `B(b)` is one byte, `01` for true and `00` for false. Everything is appended in this
   order, with no tag or separator between the parts:

   ```text
   S(model id)
   S(profile name)
   S(profile version, as decimal digits without padding, e.g. "1")
   S(launch image)
   S(launch digest, as written: sha256:<64 hex>; "" when absent)
   N(command count)     S(command[0]) S(command[1]) ...                       in listed order
   N(artifact count)    { S(path) S(sha256) } ...                             in listed order
   N(env count)         { S(key) S(value) } ...                               ascending by key
   N(privilege count)   S(privilege) ...                                      in listed order
   N(mount count)       { S(host) S(container) B(readOnly) } ...              in listed order
   shm size             N(0) when absent, else N(1) S(shmSize)
   S(launch engine) S(launch backend) S(launch label)
   advert               B(0) for a measure, else
                        B(1) N(slots) N(contextSupported) N(maxContextTokens) N(kvBytesPerToken)
   ```

   `env` keys are sorted by the bytes of their UTF-8 encoding; a mount's `readOnly` is true when
   the profile omits it. Every list is count-prefixed, so the elements of one list can never be
   read as the head of the next: a command `["x","p","s"]` with no artifact hashes differently
   from the command `["x"]` with the artifact whose path is `p` and digest `s`.

   Not hashed, because they do not change what runs: the artifacts' `bytes` and `sources`, the
   advert's `tools` and `structuredOutput`, the profile's `match` rules, `evidence`, `quality`,
   `quantization`, `kvOffload` and `probe`. Hashed, so that they distinguish deployments: the
   model id, the profile `name` and `version`, every launch member listed above (image, digest,
   command, environment, privileges, mounts, shm size, engine, backend, label), the artifacts'
   paths and digests and, for a `serve`, the advert figures. A different profile, image, flag,
   environment, mount, weight file or advertised figure is a different deployment (invariant
   15). For a `measure` entry the profile is the `candidate` and there is no advert (`B(0)`), so
   a measurement and a serve never share an id.

   **A gateway MUST derive the id this way. A node MUST recompute it from the entry's own
   payload and MUST NOT act on an entry whose `deployment` differs**: it treats the entry as
   invalid (rule 3) and reports it `refused`. An id that is not the one its payload hashes to
   names a deployment directory the entry did not earn.

   Test vectors. The model id is `qwen3.8-27b-modality-vision-quant-q8_k_xl`; the profile is
   `r9700-q8-one` version 1 with launch image `ghcr.io/ggml-org/llama.cpp`, digest `sha256:`
   followed by 64 times `a`, command `--model` and `/models/m.gguf`, engine `llama.cpp`, backend
   `rocm`, label `r9700-q8-one`, no environment, privileges, mounts or shm size; one artifact,
   path `m.gguf`, sha256 64 times `b`; and the advert 1, 262144, 262144, 65536.

   | vector | result |
   | --- | --- |
   | a `serve` with that advert | `dep_2dbde03f1caf05686818da3ade04a6ced7853aedea6ac3021d76e27d38c94e44` |
   | a `measure` (no advert, `B(0)` last) | `dep_6866ef335f03f489914a99313941c3b16b2be92b8cad743439c2f851aa26019e` |
   | the `serve`, with `env` `HSA_OVERRIDE=1` and `A=x` (hashed `A` first), privilege `--device=/dev/kfd`, mounts (`/models`, `/models`, read-only) and (`/cache`, `/c`, read-write) and `shmSize` `64g` | `dep_6c0ec71feede12a8789bccda8a8d345b7ec27547af8c074e5bef58987b8c615f` |

   All three were computed from the layout above with Python `hashlib` run as `python3 -I`, and
   they equal the three values the reference implementation's unit test
   `the_deployment_id_known_answer_vectors` (`iw_core::dynamic_node`) asserts, so the layout
   here and the code agree byte for byte. The vectors, with relations that two inputs must or
   must not hash alike, are `conformance/dynamic-node-vectors.json`; `conformance/runner.py`
   recomputes them, and the fixtures' `deployment` members are their real derived ids.

   The node registers its engine under this id and keeps the deployment's artifacts under
   `<artifactRoot>/<deployment>/`. The assignment `id` is a plain id the gateway mints as
   `dyn-<boot>-<sequence>-<node>`: `<boot>` is a token fixed for the life of the gateway process,
   1 to 12 lowercase base-36 characters; `<sequence>` is a counter of at least six digits (at most
   20) that restarts with the process; and `<node>` is the first 12 ASCII letters and digits of
   the node id, lowercased. An id minted by this version is at most 50 characters. The boot token
   is the hash of three inputs, the clock in nanoseconds, the process id and a random 32-bit
   value, so a restart mints a different token, and so do two gateway processes that start in
   the same second or the same clock tick. It is a hash cut to 12 characters, not a counter: a
   collision between two processes is possible in principle and negligible in practice. The
   token's one job is to keep a fresh id from equalling a status a node retains from the
   previous process or the name of a draft file already on disk. A node treats the `id` as
   opaque.

7. **Artifacts.** Each names, as members, a plain relative `path` (no `.` or `..` or empty
   segment, so no leading or trailing `/`), its exact size `bytes` (at least 1), its lowercase hex
   `sha256` and 1 to 8 `sources`; an entry names at most 64 artifacts. The sources are tried in
   the order listed; each is a `file://`, `http://` or `https://` URL. A node MUST verify size and
   digest before a file is published under its path, MUST keep a partial HTTP download and resume
   it with a `Range` request, MUST refuse to publish a file whose digest differs
   (`digest_mismatch`), and MUST check free space before fetching (`disk_full`). Only an
   assignment authorizes a fetch (spec 20).

   The artifacts of one entry must sit side by side in one directory and have their sizes added.
   A gateway MUST NOT emit, and a node refuses (rule 3), an entry whose artifacts break either
   rule, because a node keeps `<path>.part` while a file downloads and `<path>.sha256` once it
   is verified:
   - a path listed twice; two paths where one is the other followed by `/` and more (`a` and
     `a/b`: one would have to be both a file and a directory); or two paths where one is the
     other followed by `.part` or `.sha256` (`x` and `x.part`, `m.gguf` and `m.gguf.sha256`);
   - sizes that add up to more than 2^64 - 1 bytes (the disk check could not be sized).

   An artifact whose `path`, `sha256` or any source contains the text `SET_` is refused: an
   example configuration marks a value the operator must fill in that way (`SET_REVISION`), and a
   value that still carries one was never filled in, wherever in the artifact it hides.

   What a node does with a source (the reference node; it does not change the wire):
   - A `file://` source is honoured only for a file under an operator-configured source root
     (`--source-root`); without one, or outside it, the source is skipped with the generic
     message "source not permitted" and the next source is tried. An assignment, which a gateway
     sends, never widens what a node may read from its own disk.
   - An HTTP(S) source never targets a loopback or link-local address, follows at most 3
     redirects, and never follows a redirect from `https` to `http`.
   - A node MAY reuse a file it has already verified, with the same size and SHA-256, from
     another deployment's directory (a content store) instead of fetching it again; a `measure`
     followed by the `serve` of its draft therefore downloads once.
8. **`serve`** carries the whole `RuntimeProfile` (the node needs no profile library), the
   artifacts, and the `advert` figures the gateway decided for it: `slots` (1 to 4294967295),
   `contextSupported` (the native context), `maxContextTokens` (the context per slot, 1 to
   `contextSupported`), `kvBytesPerToken` (at least 1), and the optional `tools` and
   `structuredOutput` claims. A node ignores an `advert` member it does not know, so a newer
   gateway can add a figure. The node substitutes its own `<artifactRoot>/<deployment>` for the
   `$ARTIFACTS` prefix of a profile mount's host path; such a mount is always bound read-only,
   whatever the profile's `readOnly` says, and is confined to the deployment's own directory. It
   pins the cards by serial (profiles never name a card), launches, probes
   readiness and one long prompt, and only then re-registers as a routable node with that advert,
   the engine's endpoint and the deployment id. Its VRAM pool is the assigned cards' memory; its
   KV pool is `kvBytesPerToken × maxContextTokens × slots`.
9. **`measure`** carries a `candidate` profile with no evidence and a `matrix` whose members are
   `contexts` (1 to 8 depths, tokens), `concurrency` (1 to 8 stream counts, each at most 256) and
   `maxTokens` (the output cap per request, 2 to 4096: one output token is no decode rate);
   every depth is measured at every concurrency. Every depth MUST be at least `10 × (maxTokens +
   16)`: the node fills the prompt to 90% of the depth and keeps the other 10% for the answer
   and a template margin of 16 tokens, so a shallower depth cannot hold both and the node
   refuses the entry (rule 3). A gateway MUST NOT emit an entry that breaks these matrix rules;
   a gateway that loads a desired model refuses one whose candidate's matrix breaks them. The
   node launches, probes readiness, runs every cell, reports one evidence row per cell and
   stops the engine. A row's `decodeTps` is the
   aggregate decode rate across the cell's concurrent streams, `prefillTps` the mean prompt rate
   and `ttftP50Ms` the median time to first token; a cell's prompts are distinct so no cached
   prefix serves another.
10. **One engine per dynamic node** in this version: a `serve` or `measure` that arrives while
    one runs is refused (`refused`), never queued. A `stop` for an assignment the node is still
    carrying out (fetching, launching, probing or measuring) cancels it promptly; the node does
    not wait for the fetch, the launch or the measurement to finish.

## 6. The `provisioning` heartbeat member

`schemas/v1/requests/node-provisioning-status.json`. A top-level member of the JSON body of
`POST /v1/node/heartbeat`, an array sent on every beat while the capability is in force (`[]`
when the node has acted on nothing): one entry per assignment the node has acted on, each with
`id`, `model`, `gpuIds`, `updatedAt` (Unix seconds of its last change) and `phase` one of `pending`,
`fetching` (with `bytesDone`/`bytesTotal`), `launching`, `probing`, `serving` (with `endpoint`
and `deployment`), `measuring` (with `cellsDone`/`cellsTotal`), `measured` (with `evidence` and
`readySec`), `failed` (with a closed `reason` and a message) or `stopped`. Rules:

1. A gateway reads it leniently after the beat is accepted and never refuses a beat for it.
   - A member that is not an array, or whose compact serialization is over 65536 bytes, is not a
     report: it changes nothing the gateway holds and does not count as the first report of
     section 7 rule 6. An empty array is a report.
   - Within a report an entry is dropped when it does not parse, when its `id` is not a plain id
     (`^[a-z0-9._-]+$`, at most 128 characters), or when its `model` is empty or longer than 256
     characters. A `gpuIds` list is cut to its first 64 and a `failed` message to 512
     characters. Two entries of one `id` collapse to the one with the later `updatedAt`.
   - At most 64 entries are read, in report order; later ones are ignored. A report of 64 KiB
     could otherwise carry about a thousand distinct ids for the planner to adopt.

   A gateway that caps the body of a hardware-only registration's heartbeat more tightly than
   other beats MUST raise the cap by 65536 bytes for a beat that carries `provisioning` under a
   registration that negotiated the capability (the reference caps such beats at 16 KiB, so
   16 KiB + 64 KiB).
2. `reason` is closed: `refused` (the entry was invalid, named a card the node does not hold, or
   arrived while the node already runs an engine), `artifact_unavailable` (no source served an
   artifact), `digest_mismatch` (a fetched file differs from its pinned size or digest),
   `disk_full` (not enough room under the artifact root), `runtime_unavailable` (the node's
   container runtime could not do its job: the daemon is down, an image could not be pulled from
   its registry, a container name collided, or a local filesystem call failed for a reason that
   is not lack of space), `launch_failed` (the container started and died, was misconfigured or
   did not become ready), `probe_failed` (the engine answered and failed the probe),
   `engine_exited` (a serving engine stopped answering, or the executor stopped) and
   `measure_failed` (the measurement could not complete). What failed is reported, never the
   bytes that failed it. Which reasons are permanent and which expire is section 7 rule 8.
3. A serving engine that stops answering `/health` for three consecutive beats is stopped and
   reported `failed` with `engine_exited`; its cards are released. A node sends a `message` of
   at most 512 characters (it cuts a longer one); the gateway keeps at most 256 characters of
   it on a recorded failure or refusal. A terminal status (`failed`, `stopped`, `measured`) is
   reported for at least ten minutes after its last change and MAY be dropped after, so the list
   stays bounded. A node keeps the member within 65536 bytes by dropping its oldest terminal
   statuses first; it never drops an active status. (The gateway does not trim a report: it
   reads what is within the bounds of rule 1.)
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
matrix. A configuration member the reference does not know is refused (a misspelt
`requireQualitysuite` would otherwise load as the default and serve a model the operator meant to
gate); the `advert` is read strictly in the configuration, unlike on the wire.

The gateway MUST refuse to start on a desired model it could never serve or could only
measure for ever, namely one whose id has no `quant` qualifier; whose `advert.slots` differs
from `serves.slots` or whose `advert.maxContextTokens` is below `serves.contextPerSlotMin`; whose
`artifacts` break the rules of section 5 rule 7 (the set, the `SET_` placeholder); that
sets `requireQualitySuite` and names any candidate (a draft never carries a quality block, so it
could never be selected); or that names a candidate which is not a valid profile, whose matrix
breaks the rules of section 5 rule 9, whose name is not a plain id, that matches another model or
is not admitted by rule 2, or whose matrix cannot produce a qualified draft: its `concurrency`
MUST contain `serves.slots`, its `contexts` MUST contain a depth of at least 90% of the context
floor, and no `concurrency` may exceed the candidate's own `match.serves.slots`.

**A candidate's name MUST leave room for its draft's.** A draft is named
`<candidate>-draft-<assignment id>` (rule 1), a profile `name` is at most 128 characters (the
schema; a longer one is also a file name the drafts directory must hold), and an id this version
mints is at most 50, so a candidate's name is at most 128 - 7 - 50 = 71 characters. The gateway
refuses to start on a candidate whose name is longer (the check is against the longest id this
version mints, so no id this gateway mints later can make the draft's name too long).

The plan is deterministic in its inputs and runs on every register and beat:

1. **Reconcile.** A node that left, or that registered without the capability, the facts or an
   operator-enrolled credential, takes its holdings with it. For each node's report against
   what is held:
   - `failed` drops the holding and, for the reasons of rule 8, records a failure for (node,
     model, profile) or counts a refusal; `stopped` drops it;
   - `measured` drops the holding and settles the measurement: only the evidence rows at a
     (`context`, `concurrency`) cell of the assignment's matrix are kept, one per cell, each with
     a finite `decodeTps` above zero and a `prefillTps` and `ttftP50Ms`, when present, that are
     finite and not negative (a row that breaks this is dropped; a zero `prefillTps` or
     `ttftP50Ms` reads as not measured and is left out of the row). The candidate and those rows
     become a draft profile, which is validated like any profile, MUST be admitted for the
     desired model like any profile (rule 2) and MUST itself be qualified for it, or a
     `measure_failed` failure is recorded for the candidate instead and no draft is made. A
     draft name over 128 characters (the assignment id of a measurement this gateway did not mint
     can be as long as the node chose) is such a failure;
   - a held `serve` or `measure` that the node, while it keeps reporting other things, does not
     name in a report for 300 s (`HELD_REPORT_SECS` in the reference; the time since it was held,
     or last named) is dropped: the node skipped the entry or cut it from its own report, and
     the holding would keep the cards, the replica and the measurement slot for ever. It is
     recorded as a failure of (node, model, profile) with the reason `artifact_unavailable`
     (a transient reason, so tried again after 600 s) and the message "the node reported
     nothing of <id> for <n> s". An adopted holding (no known profile) is dropped without a
     record. A node that has not reported at all is not "reporting": its holdings wait;
   - a model removed from the configuration is stopped wherever it serves. A `stop` entry is done
     when the node no longer reports its id, or reports it `stopped` or `failed`.

   The draft is named `<candidate>-draft-<assignment id>` (the whole id), has version 1, no
   `quality` block, evidence rows stamped with the assignment id as `run` and the UTC date, and
   is matched to the measured host: its GPU vendor and model, the number of cards, the smallest
   assigned card's memory as `vramMibMin`, and the lesser of the candidate's and the host's RAM
   and PCIe generation. The host is the node's facts **as they were when the `measure` was
   assigned**, not whatever the node says by the time the evidence arrives (a re-registration in
   between may have changed its cards or RAM); for a measurement the gateway lost track of (a
   restart in between) it is the node's current facts. The draft is written to the drafts
   directory as `<name>.yaml` (staged and renamed so a reader sees all of it or none, its
   temporary file removed if the write or the rename fails, retried after 60 s when the write
   fails) for an operator to promote, and a draft file that no longer parses is skipped at start.
2. **Qualify.** For each desired model, in priority order (ties by model id), and each node
   with no holding, in `nodeId` order:
   - *Admitted*: a profile whose `quantization` equals the desired model's quantization token
     (a profile with none is never admitted: an MXFP4 profile never serves a Q8 id, whatever
     its family and name say), and which is on the model's `profilesAllow` list when one is
     configured. A draft is admitted with its candidate: when `profilesAllow` is set, a profile
     named `<allowed>-draft-` followed by a non-empty measurement id is on the list when
     `<allowed>` is (a configuration with `profilesAllow` must name every candidate, so the
     draft of an allowed candidate must be admitted, or the model would be measured, drafted and
     measured again for ever). The token is the model's configured quantization, not a value
     read from an id a node advertised; in the reference it is the `quant` qualifier of the
     model id the operator configured (validated at load, above).
   - *Matching*: the node's free cards (not `busy`) in `gpuId` order are tried as serving groups
     of every size from all of them down to one (the first *k* cards, with the smallest card's
     memory and the host's facts); an admitted profile matches the size equal to its
     `match.gpu.count` when the family and name, GPU vendor, GPU model (one of those listed),
     memory per card, host RAM and PCIe generation match, and its `match.serves.slots` and
     `contextPerSlotMin` are no less than the desired model's. The size of the group is not an
     ordering key.
   - *Kept only if qualified* (section 2): a profile with a measured decode at the floor and,
     when `requireQualitySuite`, a `quality` block.
   - *Ordered* by **quality tier, then measured decode at the floor (higher first), then
     profile `name` (ascending), then `version` (descending)**. Group size is not a key: an
     engine over more cards wins only when its measured decode says it is faster. The
     quality tiers are those of the shared profile ranking
     (`docs/specs/runtime-profile-autoselect.md`, `profile_select::rank_all`): the *best score*
     is the highest `quality.score` among the qualified profiles that have one, compared in
     thousandths, and the *tolerance* is the `quality.toleranceAbs` of the profile that holds
     it (**the smaller on a tie** in score: a tighter claim of the same score sets the tighter
     tier). Tier 0 is a profile with a quality block whose score is at least the best score minus
     the tolerance (within the tolerance counts as one tier); tier 1 the other profiles with a
     quality block, higher score first; tier 2 the profiles with none.
   - A profile with a recorded failure (rule 8) for this node and model is skipped. This extends
     spec 43's never-retry rule for out-of-memory and no-fit loads to the permanent reasons of
     rule 8; the transient reasons expire after 600 s. A profile this node refused a moment ago
     (rule 8) is skipped until its backoff ends.
3. **Serve** the first eligible profile on the first `match.gpu.count` free cards of the node,
   until the model's replicas are met. A node holds one assignment, so a node that holds one is
   not considered for another model.
4. **Measure** when no profile matches the node or none is qualified: the first measurement
   candidate (in configured order) that matches the node's host on its first `match.gpu.count`
   free cards and has no recorded failure there and is not backing off after a refusal, one
   measurement per model fleet-wide at a time. When every qualified profile has failed on the
   node, it is not measured but left idle.
5. **Explain.** Why each idle node holds nothing for each model is recorded with a reason from
   a closed set of eight and shown on the operator view:

   | reason | the node holds nothing for the model because |
   | --- | --- |
   | `occupied` | it holds an assignment already (one engine per node), or has no free card |
   | `no_matching_profile` | no profile matches it for the model and no candidate matches either |
   | `no_qualified_profile` | profiles match but none has a measured decode at the floor (or a quality block, where required) and no candidate matches |
   | `failed_before` | every matching profile or candidate failed on this node before |
   | `measuring_elsewhere` | a measurement of the model is running on another node (one at a time) |
   | `replicas_met` | the model's replicas are placed |
   | `awaiting_status` | it has registered but not yet reported what it holds (rule 6) |
   | `refused_recently` | every otherwise placeable profile or candidate was refused by this node a moment ago and is backing off (rule 8) |

   `awaiting_status` takes precedence over `replicas_met`; `refused_recently` over `failed_before`
   when both apply, because a refusal lapses by itself and a failure may not.
6. **A registration places nothing.** A node is placed on only after the first `provisioning`
   report of its current registration (section 6 rule 1; an empty array counts). Until then it
   may be serving an engine the gateway cannot see (a gateway restart, a forgotten record, a
   swap), and a second `serve` would be refused as occupied. A node with the capability in force
   sends `provisioning` on every beat, `[]` when idle. The register response carries only the
   entries already held for the node, so it is `assignments: []` for a node the gateway holds
   nothing for; the first report unlocks placement and the next answer carries it. A
   re-registration starts that wait again.
7. **Adoption and excess.** A gateway that restarted holds nothing and adopts what nodes report.
   For each model a node reports an active status for under an id the gateway does not hold for
   that node, **at most one** is adopted: the one with the latest `updatedAt` (on a tie the
   lower id), and none when the node already holds something for that model. One engine runs per
   node, so a second active id for a model is stale or invented, and adopted it would count as a
   replica, occupy the node and (for a model nobody wants) be stopped again on every pass.
   - an active phase (any but `failed`, `stopped`, `measured`) of a desired model becomes a
     holding with no entry to repeat and no known profile: `measuring` as a measurement, any
     other phase (`serving` among them) as a serving engine. It counts toward the model's
     replicas and occupies the node's cards;
   - an active phase of a model that is not desired becomes a `stop` entry for that id,
     repeated until the node stops reporting it;
   - `measured` for a desired model is settled as in rule 1 (the newest such status per model)
     when the model has exactly one measurement candidate for that many cards, and otherwise
     drafts nothing;
   - other phases change nothing.

   **Excess is stopped.** After reconciliation and before placing, for each desired model the
   serving holdings (adopted or not) are ordered by node id, then by the time they were held
   (earliest first), then by assignment id. The first `replicas` are kept and **every later one is
   sent a `stop` entry**, repeated like any `stop` until the node no longer reports it. Adoption
   after a restart, or two nodes reporting one model, can leave more engines serving than wanted;
   without this the `replicas` limit would only stop further placement and the extra engine
   would run for ever. The order is a total one, so every pass keeps the same engines.

   A re-registration of the same `nodeId` with the capability, the facts and an enrolled
   credential replaces the stored facts and keeps the node's holdings and its last reported
   statuses (a dynamic node re-registers as a routable node when its engine answers, and keeps
   the holding that produced it); placement waits for the next report (rule 6). A registration
   without them forgets the node and its holdings are released on the next plan.
8. **Failure classes.** A reported `failed` on a held assignment is recorded as a failure of
   (node, model, profile) by its `reason`, and the holding is dropped either way:
   - `refused` is a disagreement between node and gateway and says nothing about a profile: it
     is never recorded as a failure. It is **counted**, and the same (node, model, profile) is
     **not placed again for 60 s after a refusal, then 120 s, 240 s, ... up to 600 s** for each
     further refusal in a row (`REFUSAL_BACKOFF_SECS` and `REFUSAL_BACKOFF_MAX_SECS` in the
     reference), so a node that keeps refusing is not handed a new id on every beat. The count is
     forgotten 600 s after its backoff ends, or when the placement reaches `serving`. The gateway
     keeps at most 1024 of them, the oldest dropped first. While a profile or candidate backs
     off, the node's idle reason is `refused_recently` (rule 5);
   - **transient**, the pair suppressed for 600 s and then tried again: `engine_exited`,
     `artifact_unavailable`, `digest_mismatch`, `disk_full` and `runtime_unavailable`. They say
     nothing lasting about the profile: a dead mirror, a short file, a full disk (space comes
     back), a stopped docker daemon or an unreachable registry, an engine that died after
     serving. Retiring a good profile on one of them would leave the node idle until the gateway
     restarts;
   - **permanent**, the pair suppressed until the gateway restarts: `launch_failed`,
     `probe_failed` and `measure_failed`. They are verdicts on the profile (the engine started
     and died or was misconfigured, the engine failed the probe, the measurement could not
     complete);
   - a failure on an adopted holding (no known profile) is not recorded.

   The gateway keeps at most 1024 failures, the oldest dropped first, and shows them on the
   operator view with a message cut to 256 characters.

The operator view is `GET /iw/v1/dynamic` (admin secret only; a held assignment carries a
launch command): desired models with how many serve, every dynamic node with its facts, last
statuses, holdings and idle reasons, the profiles, the drafts, the failures and the `refusals`
(each with `nodeId`, `model`, `profile`, `count`, `message`, `at` and `retryAt`). Each draft and
each holding served from a draft carries `"experimental": true` (section 8).

## 8. What this does not do

- No link-only dynamic node: the engine's port is published on the address the operator names
  on the node (`--endpoint-host`, required, an address without port or scheme; the node neither
  detects it nor takes it from an assignment) and the node advertises `<endpoint-host>:<port>`
  for the gateway to dial. A dynamic node behind NAT is a follow-up that carries the engine
  over the held link.
- No co-residency: one engine per dynamic node (§5 rule 10).
- No availability floor or dwell: a desired model's replicas are counted and an engine beyond
  them is stopped (§7 rule 7), but nothing is drained first; spec 43's swap lifecycle does not
  apply to a dynamic node's single engine.
- No promotion of a draft to a shipped profile: a draft serves where its evidence qualifies it
  and the desired model does not require a quality suite; promotion to
  `docs/specs/runtime-profiles` with a measured quality score is an operator's act.

**Qualification.** The qualification of section 2 is this surface's gate for invariant 28
(experimental profiles are not selected by ordinary production routing until qualification gates
pass): only a profile with measured decode at the context floor, and a quality block where the
desired model requires one, is ever assigned to serve. A draft has the decode evidence and no
quality block, so it is serving on measured throughput alone. The reference gateway's operator
view marks each draft, and each holding served from one, `"experimental": true`; a gateway that
serves from drafts SHOULD mark them the same way. The decision record does not authorize
production traffic from a draft.

## 9. Compatibility

Additive and capability-gated. An older node never offers the capability, sends no `dynamic`,
reads `assignments: []` as before and never sees `provisioning`. An older gateway lists nothing,
so a dynamic node registered to it stays hardware-only and acts on nothing. A gateway that
negotiates the capability but has no provisioner answers `[]` and records nothing (section 3).
Forward compatibility within `iw.dynamic-node/1`: a node ignores an entry whose `kind` or
`version` it does not know, an unknown member of an entry or of its `advert`, and a gateway
ignores a member of the facts it does not know (section 4).

## 10. Required tests

Recorded `owed` by `P5-T35`; see the task card and `contracts/canonical-task-graph.json`.
The reference implementation's unit and HTTP tests (`iw-core::dynamic_node`,
`iw-gateway::dynamic_provisioner`, `iw-gateway/tests/dynamic_nodes.rs`,
`iw-cli::dynamic_node`, `iw-cli::join` dynamic mode) exercise every rule above against
loopback engines and scripted gateways; a dynamic node that fetched real weights, launched a
real profile and served real requests through its gateway is the operational proof this gate
waits on. The deployment-id vectors of section 5 rule 6 are known-answer tests every
implementation MUST pass; they are `conformance/dynamic-node-vectors.json`, recomputed by
`conformance/runner.py`, together with the valid and invalid fixtures for the assignment rules a
schema cannot express (the derived id, the matrix floor, artifact collisions and size overflow,
the card count), which `conformance/dynamic_nodes.py` checks.

## Nibbler observability rollout scope (2026-10-20)

The operator's observability approval authorizes qualification work on the
already registered Nibbler, not a claim of serving readiness. A Go root without
this spec's provisioner leaves it hardware-only. Dynamic serving requires the
Rust owner/executor, profile evidence on the actual placement, a real full
admission-path request and the watchdog/rollback safety gates. A read-only
capacity report can expose inventory and unknown serving capacity meanwhile;
it cannot fabricate assignments or advertise an unqualified runtime as ready.
See the observability ADR and AC-OBS-09. All new operational proof is owed.
