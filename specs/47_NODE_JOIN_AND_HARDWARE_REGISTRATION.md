# 47 — Node join wire contract: hardware-only registration and tokenless enrollment

## Status

**SPECIFICATION ONLY — PROPOSED; BLOCKED for production use.** This document defines additions to
the node control surface (`/v1/node/*`) of InferWeave Protocol 1.1.0 and pins the wire shape of
the tokenless enrollment endpoints that `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md` describes only in
prose. It is the shared contract that the Rust gateway (`InferWeave/inferweave`) and the in-house
Go gateway (`metabolomics-us/inferweave-gateway`) implement concurrently. Every required test is
recorded `owed` by canonical tasks `P5-T33` and `P5-T34` (feature `IW-NODEHW-001`); see
`OPEN_GATES.md`. The decision record is
`decisions/2026-10-08-open-proof-enrollment-and-hardware-registration.md` (Proposed).

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

## 1. Relationship to other specifications

| Document | What it covers | What this document adds |
| --- | --- | --- |
| `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md` "Token-free proof enrollment" | the design: persistent keypair, challenge, proof, credential bound to exactly what was challenged | the wire shapes, error mapping and the signed transcript (section 5) |
| `specs/45_PROTOCOL_V1.md` "Registration" | the generic registration envelope (`identity`, `protocol`, `features`, ...) validated by `schemas/v1/requests/registration.json` | nothing; that envelope is not the `/v1/node/register` body |
| `specs/16_SECURITY_PRIVACY_TRUST.md` | "node enrollment + rotating short-lived credentials", API keys | the open enrollment policy (section 6) |
| `specs/25`, `specs/28`, `specs/42` | Slurm nodes, init client, site gateway conformance | nothing |

**Where the specification was silent.** Before this document the repository did not define the
`POST /v1/node/register`, `/key`, `/challenge` or `/proof` request and response bodies, the
byte-level proof transcript, the error mapping or any hardware reporting. Section 2 records the
baseline register body as it is implemented by the reference gateway; it is informative, not
normative, because the repository had no authority for it. Sections 3 to 7 are normative.

## 2. Baseline register wire (informative)

All bodies are JSON with camelCase members. The reference gateway
(`crates/iw-gateway/src/node_control.rs`, `RegisterRequest`, `RegisterResponse`) accepts, per
`POST /v1/node/register`:

```json
{
  "nodeId": "node_lab-gpu-07",
  "role": "node",
  "credential": "<the credential the node holds>",
  "endpoint": "127.0.0.1:9101",
  "models": [ { "model": "qwen3-8b-modality-text-quant-q4_k_m", "contextSupported": 131072,
                "maxContextTokens": 32768, "engine": "llama.cpp", "backend": "cuda",
                "slots": 1, "vramBytes": 100 } ],
  "deployment": "dep_9f8e7d6c",
  "vramBytes": 100000000, "kvBytes": 10000000, "kvBytesPerToken": 10,
  "gpuIds": ["iw-gpu-0"]
}
```

plus optional members an older node omits (`card`, `schedulerJobId`, `capabilities`, `linkOnly`,
`declaredWeightsMib`, `declaredBudgetMib`). Except for `capabilities`, which section 2.1 makes
normative, those optional members are outside this contract; a conforming gateway need not
implement them. The common response members are
`{ nodeId, connectionId, freshnessTtlSecs, capabilities, assignments }`; implementations may add
the optional members already described elsewhere in this specification. For
`iw.link-native-request/1`, this `connectionId` is also the authenticated registration-incarnation
value copied into Link Hello `registration_connection_id`; see `specs/45_PROTOCOL_V1.md`. It must
not be replaced by node id, process `session`, or a separately inferred current registration. Errors are
`{"error": {"code": "...", "message": "..."}}`; the codes used here are `bad_request` (400),
`control_auth_failed` (401) and `node_id_conflict` (409). `message` is for humans and is not
normative.

A registration is authenticated by `nodeId`, `role` and `credential`. That is unchanged by this
document: a hardware-only registration (section 4) is authenticated exactly like any other.

### 2.1 Capability offer and negotiated response (normative)

The actual `/v1/node/register` request and response producer shapes are
`schemas/v1/requests/node-register.json` and `node-register-response.json`. They use the existing
camelCase wire. The request's optional `capabilities` member is an array of at most 32 unique
strings. Each is at most 128 bytes and has grammar `iw.<name>/<major>`, where `name` contains only
lowercase ASCII letters, digits, or `-`, and `major` is `0` or a decimal integer without a leading
zero. This array is the capability offer used by both the Rust and Go gateways. It is not the
generic Protocol registration `features` level map in `schemas/v1/requests/registration.json`.

The schema always requires the authentication/routing discriminator members `nodeId`, `role`,
`credential`, `endpoint`, and `models`. A routable registration (non-empty endpoint and models)
also requires `deployment`, `vramBytes`, `kvBytes`, `kvBytesPerToken`, and `gpuIds`. A hardware-only
registration has empty endpoint and models; it may omit those deployment/capacity members because
the gateway supplies their existing empty/zero defaults and must not route from them. Mixed shapes
(for example a non-empty endpoint with no models) are invalid.

The response always carries `connectionId` as lowercase `c-` followed by 16 hexadecimal digits,
the volatile format minted by both current gateway implementations, and carries `capabilities` as
an array. That array contains only the exact string
intersection of the first 32 well-formed request entries and gateway support for this newly minted
`connectionId`, de-duplicated in deterministic gateway-supported order. A capability is in force
only when it appears in both arrays. Absence, `null`, a non-array, or an empty request array
negotiates nothing. For compatibility, a gateway ignores malformed entries and entries beyond 32
rather than refusing an otherwise valid legacy registration; such a request is not a conforming
producer of the schema. Unknown well-formed capabilities are ignored unless supported.

A node that wants native Link v1 includes `iw.link-native-request/1` in the request array and may
send the native Link v1 Hello fields only when that exact string is present in the response array.
The response `connectionId` is copied byte-for-byte into Hello `registration_connection_id`. A
legacy registration without `capabilities` succeeds as before, receives an empty response array
from a new gateway, and cannot enable native dispatch. No feature is inferred from protocol
version, node id, model, or a generic features map.

## 3. The `hardware` member

### 3.1 Gateway rules

`POST /v1/node/register` gains ONE optional request member, `hardware`.

1. A gateway MUST treat an absent `hardware` as today (older nodes keep joining) and MUST treat
   JSON `null` as absent.
2. A present, non-null `hardware` MUST be a JSON object with an integer `version`. A gateway MUST
   refuse the registration with HTTP 400 and error code `bad_request` when `hardware` is:
   - not a JSON object (array, string, number, boolean);
   - an object with no `version`, or a `version` that is not a JSON integer. A number written with
     a fraction or exponent (`1.0`, `1e0`) is not an integer; neither are `null`, strings, booleans
     and objects. A value outside the signed 64-bit range is refused;
   - larger than **65536 bytes**.
3. Size is measured on the **compact serialization**: the JSON text of the `hardware` value with no
   insignificant whitespace, UTF-8 encoded. A gateway that cannot recover the compact form from the
   received text MAY measure the raw received bytes of the `hardware` value instead and so refuse
   some inputs between the two measures. The vectors avoid that band (exactly 65536 compact bytes
   is accepted; 65537 is refused; both are written compactly).
4. Any integer `version` is accepted (`0`, `2`, `99`): the gateway MUST NOT refuse a report because
   it does not recognise the layout version.
5. A gateway MUST NOT validate any other member. A `hardware` object whose `cpu.threads` is a
   string is stored, not refused; typing is the producer's contract (section 3.2).
6. A gateway MUST store the accepted object **verbatim**: unknown top-level and nested members are
   kept, so a newer node's report survives an older gateway. "Verbatim" means equal as JSON values
   (key order, whitespace and number formatting are not preserved or required).
7. A refusal is transactional: a registration refused for `hardware` admits nothing, and an
   existing registration of the same `nodeId` is unchanged.
8. `hardware` is informational. It MUST NOT be used for routing, admission, placement, trust or
   authentication. A re-registration replaces the stored object, and **clears it when the new request
   carries none** (a gateway MUST NOT keep the previous value). Stored hardware is also dropped
   when its registration is reaped as stale, forgotten, withdrawn or replaced by a promotion
   (section 6.2). A conformance divergence is recorded in `OPEN_GATES.md`.
9. When both an authentication failure and an invalid `hardware` apply, the gateway MAY report
   either 401 or 400.
10. `hardware` contains stable host identifiers (`hostname`, `machineId`, GPU `uuid`). A gateway
    MUST show it only to operators (the admin surface) and MUST NOT include it in `/v1/models`,
    public status or any unauthenticated response.

Machine-readable form: `schemas/v1/requests/node-hardware.json` (deliberately minimal: object with
integer `version`, everything else open).

### 3.2 Producer layout, version 1

A node SHOULD send:

```json
{
  "version": 1,
  "hostname": "lab-gpu-07",
  "machineId": "3f1c0a9e5b7d4c2e8a6f1d0b9c8e7a65",
  "role": "node",
  "kernel": "6.8.0-138-generic",
  "os": "Ubuntu 24.04.2 LTS",
  "cpu": { "model": "AMD EPYC 7413 24-Core Processor", "threads": 48 },
  "memBytes": 270582939648,
  "disks": [ { "name": "nvme0n1", "sizeBytes": 1920383410176, "rotational": false } ],
  "nics": [ { "name": "eno1", "speedMbps": 10000 }, { "name": "ib0", "speedMbps": null } ],
  "gpus": [ { "vendor": "nvidia", "index": 0, "uuid": "GPU-0f4c2b1a-1111-2222-3333-444455556666",
              "model": "NVIDIA GeForce RTX 4090", "vramBytes": 25757220864,
              "driver": "570.133.20", "pciId": "0000:41:00.0" } ],
  "notes": [ "no container runtime found" ]
}
```

Members: byte counts are integers in bytes; `speedMbps` is `null` when the link speed is unknown
(never `0` for unknown); `notes` is an array of free-form strings the node uses to say what it
could not detect. A member the node cannot determine is omitted rather than invented.
`schemas/v1/requests/node-hardware-report.json` is the producer schema. It is a SHOULD: a gateway
never enforces it (section 3.1 rule 5).

## 4. Hardware-only registration

1. A registration whose `models` is `[]`, `endpoint` is `""` **and** `deployment` is `""` is a
   **hardware-only registration** and is VALID. Any other combination (including an empty `models`
   with a non-empty `endpoint`, or a non-empty `models` with an empty `endpoint`) is not
   hardware-only and keeps every existing check unchanged, so a gateway that previously refused
   such a body still refuses it.
2. A hardware-only body MAY omit `deployment`, `vramBytes`, `kvBytes`, `kvBytesPerToken`, and
   `gpuIds`; the existing gateway defaults are respectively empty, zero, zero, zero, and empty. If
   sent, they SHOULD carry those values. A gateway MUST NOT derive routability or capacity from
   them for a hardware-only node. A non-hardware-only registration still requires every member.
3. A hardware-only node is **recorded**: it is authenticated, receives a `connectionId`, is
   subject to the normal freshness window and heartbeats normally, and appears in operator node
   listings together with its stored `hardware` (member name `hardware`; the listing endpoint
   itself is implementation-specific, spec 45 "Discovery, control, ...").
4. A hardware-only node MUST NOT be routable, MUST NOT appear in `/v1/models` or any model list,
   MUST NOT receive demand, and its `endpoint` MUST never be dialled (it is empty, and a gateway
   MUST NOT substitute a guess from the connection's peer address). An operator listing SHOULD
   make the not-routable state visible.
5. A node MAY later re-register with models and an endpoint on the same `nodeId` and credential; it
   then becomes routable under the existing rules. The reverse (a routable node re-registering
   hardware-only) withdraws its routing entries.
6. Authentication is unchanged (section 2): hardware-only is not a way to skip it.

## 5. Register response and tokenless enrollment

### 5.1 `assignments`

The register response gains an **always-present** member `assignments`: an array reserved for
future gateway-to-node instructions (images to pull, a profile to run). In this version it MUST be
`[]`. A node MUST ignore entries it does not understand and MUST NOT fail a registration because of
one. No entry shape is defined yet; the first one will be added by a later minor release together
with a capability name.

### 5.2 Endpoints

Every conforming gateway MUST implement the three endpoints below. Bodies are JSON, members
camelCase. Hex is **lowercase ASCII** hexadecimal; a gateway SHOULD also accept uppercase when
parsing, and MUST reject non-ASCII input without failing the request handler (the reference
gateway slices hex by byte offsets and should be hardened against a multi-byte character).

**`POST /v1/node/key`** — publish the public half of the node's persistent Ed25519 keypair.
Unauthenticated: publishing a key grants nothing.

```json
{ "nodeId": "node_lab-gpu-07", "publicKey": "<64 lowercase hex chars = 32 bytes>" }
```

- `200 {"status":"ok"}`; re-publishing the same key is idempotent.
- A different key for a `nodeId` that already has one: `400 bad_request`. The first publisher owns
  the id; a later impostor cannot replace it.
- **On the tokenless path the `nodeId` MUST be derived from the key:** `"node_"` followed by the
  first 16 lowercase hexadecimal digits of the SHA-256 of the **raw** public key bytes (the 32
  bytes the hex `publicKey` decodes to). `/key` with any other id (including the same digits in
  uppercase) is `400 bad_request`. This makes an identity cost a key, stops a caller from choosing
  or squatting a human-readable id, and ties the id to the key that will sign. Operator-issued
  enrollment (`/v1/node/enroll`) still takes any id. Example: the RFC 8032 public key of the known
  answers, `d75a98...511a`, derives `node_21fe31dfa154a261`. The known-id `403` of section 6.4 is
  evaluated first, before this rule, at `/challenge` and `/proof`.
- `nodeId`: non-empty, at most 128 bytes, no whitespace or control characters. `publicKey`:
  non-empty, at most 512 bytes, no whitespace or control characters. A gateway MUST accept any
  well-formed 64-hex key. The reference does not check the key encoding at publication (a malformed
  key simply never verifies a proof); a gateway MAY refuse it earlier with `400 bad_request`.

**`POST /v1/node/challenge`** — ask to be challenged for a role. Unauthenticated.

```json
{ "nodeId": "node_lab-gpu-07", "role": "node" }
```

- `200`:

```json
{ "challengeId": "<32 lowercase hex>", "nonce": 17375808098319191535,
  "claim": { "role": "node", "model": null, "contextClass": null, "resourceClaim": null },
  "expiresAt": 1791500000 }
```

  `challengeId` carries at least 128 bits of entropy and is opaque: the node signs the exact string
  it received. `nonce` is a uniformly random **unsigned 64-bit integer** and a client MUST parse it
  as one (never as a binary64 float; values above 2^53 are normal). `claim` is the exact claim the
  proof must repeat; the four members are always present, absent members as explicit `null`.
  `expiresAt` is Unix seconds; the challenge lifetime is 900 seconds.
- **Tokenless enrollment grants only the role `node`.** A challenge request whose `role` is
  anything else (for example `gateway`, `edge`, or an empty or malformed value) MUST be refused
  with `400 bad_request`, and no challenge is issued. Privileged roles continue to require
  operator-issued enrollment (the one-time code path of `/v1/node/enroll`); no proof can earn them.
  The reference gateway currently accepts any well-formed role here and must be tightened.
- **`/challenge` is idempotent.** If the id already has an unexpired pending challenge (for the
  same claim), the gateway MUST return that same challenge again (same `challengeId`, `nonce` and
  `expiresAt`) and MUST NOT replace it; a challenge is replaced only once it has expired. Rationale:
  `/challenge` needs only the node id, so a gateway that replaced the pending challenge on every
  request would let anyone invalidate the challenge a real agent is about to answer, and so grief
  its proof indefinitely.
- A node with no published key or a revoked node: `400 bad_request`.
- Only the role claim is reachable over HTTP. The model-execution claim (model, context class,
  measured resource claim) has a defined transcript (section 5.4) but **no wire surface yet**; the
  spec was silent and this document does not invent one.

**`POST /v1/node/proof`** — answer a challenge and earn a credential. Unauthenticated.

```json
{ "nodeId": "node_lab-gpu-07", "challengeId": "<as issued>",
  "claim": { "role": "node", "model": null, "contextClass": null, "resourceClaim": null },
  "signature": "<128 lowercase hex chars = 64 bytes>" }
```

- `200 { "nodeId": ..., "role": "node", "credential": "<secret>", "expiresAt": ... }`. The
  credential is revealed exactly once. Its lifetime is 90 days.
- A malformed body: `400 bad_request`.
- A proof for a `nodeId` whose credential was issued by operator enrollment (the one-time code
  path) is `403 forbidden`, checked before the signature: a proof MUST NOT replace or take over an
  operator-issued credential, because anyone may publish a key under any unclaimed-looking id.
- Every other proof failure is `401 control_auth_failed`: unknown, expired or already-used challenge, a
  challenge issued to another node, a `claim` that differs from the challenged claim in any member,
  a node with no key, a signature that does not verify, a revoked node, and a node that already
  holds a role credential.
- A challenge is **single use**. Every failure after the challenge is found consumes it, so a
  claim mismatch cannot be used to probe the challenged scope and a proof cannot be replayed.
- The signature is verified against the public key published for `nodeId`, over the transcript of
  section 5.4, with **strict** Ed25519 verification (RFC 8032, plus rejection of small-order public
  keys and of non-canonical encodings of the key, `R` and `S`). A library verifier that is more permissive (a general-purpose Ed25519 verifier such as Go's
  `crypto/ed25519` is not specified to reject small-order keys or non-canonical point encodings;
  this specification has not tested it) MUST be hardened to the same rules, or a signature the
  reference refuses can be accepted by another gateway.

### 5.3 Using the credential

The credential returned by `/proof` is the `credential` a node presents in
`POST /v1/node/register` with `role` equal to the proven role. A gateway that issues it MUST
accept it there and for the heartbeat for its lifetime, until revoked or replaced (section 6.2).
It is **not** accepted for link authentication (section 6.3): holding a link is a routing
privilege, so a link hello presenting a proof-only credential is refused. (An earlier revision
recorded that the Rust reference minted the proof credential in a store `register` never consulted;
that was fixed before release and no longer applies.) Renewal and re-proof for a
node that already holds a credential have no wire surface in the reference (a second proof is
`401`); a gateway MAY let a fresh valid proof by the bound key supersede the earlier credential,
which invalidates it, and MUST NOT leave two valid credentials for one `nodeId` and role.

### 5.4 The signed transcript

`proof_transcript(challengeId, nonce, claim)` is the byte string below. The domain tag is a
protocol version: changing it invalidates every signature.

```text
field(s)     = u32 big-endian byte length of s, then the UTF-8 bytes of s
optional(v)  = 0x00                      when v is absent (null)
             = 0x01 || field(v)          when v is present (an empty string is present)

transcript   = field("iw-proof-enrollment-v1")
            || field(challengeId)          -- the string exactly as issued
            || nonce                       -- 8 bytes, unsigned 64-bit big-endian, no length prefix
            || field(claim.role)
            || optional(claim.model)
            || optional(claim.contextClass)
            || optional(claim.resourceClaim)
```

The signature is Ed25519 (PureEdDSA, no pre-hash, no context) over the transcript bytes,
hex-encoded. The public key is **not** part of the transcript (a comment in the reference's
`ProofRequest` says it is; the code, `crates/iw-core/src/signature.rs`, is authoritative).
Length-prefixing makes field boundaries unambiguous; the presence byte keeps an absent member and
an empty one distinct.

**Known answers** (`conformance/node-join-vectors.json`, `enrollmentKnownAnswers`). Seed
`9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60` (RFC 8032 section 7.1 test 1),
public key `d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a`, challenge id
`00112233445566778899aabbccddeeff`, nonce `17375808098319191535` (`0xf123456789abcdef`), claim
`{role: "node", model/contextClass/resourceClaim: null}`:

```text
transcript 0000001669772d70726f6f662d656e726f6c6c6d656e742d7631000000203030313132323333343435353636
           373738383939616162626363646465656666f123456789abcdef000000046e6f6465000000
signature  171688ee458955d37f5ae88c19ee007d6ef1e770021e87a3093c5b52bb02283800488d4058ce97a27c2b80b
           e1b39dab0f6e68c873e814caf693dfbb692403a0b
```

A second known answer covers a model claim (`0x01` tags). Both were generated by a throwaway
script, verified with OpenSSL and reproduced by the reference implementation; the commands are in
the vector file, and `conformance/runner.py` recomputes them on every run.

## 6. Open registration policy

A gateway MAY accept tokenless proof enrollment from **any** key; it is not required to keep an
operator-issued token gate in front of it. The in-house lab deployment does exactly that. A
gateway that does so:

- MUST start every newly enrolled node at the lowest trust tier of whatever trust ladder it runs;
  a proof of key possession proves identity continuity, not honesty or capability;
- MUST grant only the role `node` (section 5.2); a gateway, edge or other privileged role is never
  earned by proof, so open enrollment cannot mint a node that is allowed to act as a gateway;
- MUST NOT treat a role credential as proof of any model or context capability (spec 03: a
  capability claim that has not been challenged does not license serving it);
- SHOULD bound what unauthenticated callers can make it store (published keys, pending
  challenges), because `/key` and `/challenge` need no credential. Such limits are permitted
  implementation limits and are not part of the conformance vectors; the in-house Go gateway caps
  pending challenges at 1024 and published keys at 10000 and answers `429` when a cap is hit. A
  gateway MAY use `429` for this (it is not otherwise in this contract), and a node SHOULD retry
  with backoff. The reference gateway keeps both
  maps in memory without a bound, and loses the key-to-id binding at restart, so "the first
  publisher owns the id" holds for one process lifetime only;
- SHOULD rate limit the three endpoints per source.

**Documented tension, not a prohibition.** The peer-trust design in the reference repository rests
on identity scarcity: a ban, quarantine or reputation attaches to an identity, and that only works
if identities are costly to mint. Open enrollment makes a node identity free (a fresh keypair and
a fresh `nodeId`), so a misbehaving node can re-enter under a new key and the ladder's cost model
weakens for nodes. Mitigations a deployment may combine: keep the lowest tier non-routable for
shared traffic until a gateway-run challenge passes; key quarantine by source and key rather than
by `nodeId`; cap enrollments per source and per time window; and keep an operator allow-list for
anything above the lowest tier. This repository does not define the tier names or the peer-trust
ladder (the specification is silent; the design lives in `InferWeave/inferweave`), and this
document does not constrain a deployment that chooses the open policy.

### 6.1 What a tokenless credential may do

A credential earned **only** through tokenless proof enrollment (a *proved* credential) is
limited to hardware-only use. A rationale first: a routable node receives other people's prompts,
so open registration must not let a stranger choose where traffic goes.

1. A node holding a proved credential MAY register **hardware-only** (section 4) and MAY heartbeat.
2. Such a node MUST NOT register a non-empty `endpoint` or any `models`. Every registration that
   is not hardware-only (including an endpoint with no models, or models with no endpoint) is
   refused `403 forbidden`, after authentication succeeds, and admits nothing. This is a different
   outcome from 401 (credential not accepted) and 400 (malformed).
3. A proof MUST NOT replace or take over an operator-issued credential (section 5.2: `403`). The
   operator's credential keeps working. A second proof for an id that already holds a proved
   credential does not replace it either (the reference answers `401`, section 5.3).
4. A node becomes routable **only** through operator-issued enrollment (a one-time code or secret
   issued on the admin surface and spent on `/v1/node/enroll`). Whether a node already enrolled
   by code may register an endpoint and models is unchanged from today.
5. Origin is per `nodeId`: *proof-only* (earned by `/v1/node/proof` and never replaced) or
   *operator-issued*. A gateway MUST remember it for as long as the credential is valid. Section
   6.2 supersedes "first issued wins" for the proof-only case: an operator-issued credential
   replaces a proof-only one; the reverse never happens.

### 6.2 Promotion: operator enrollment replaces a proof-only credential

Anyone may publish a key and prove it under any free-looking id, so a stranger can squat on the id
of a node an operator is about to enroll. Therefore:

1. An operator-issued enrollment (a valid one-time code, or the fleet secret) for an id whose
   credential is proof-only MUST **replace** that credential. The old credential then fails
   authentication (`401 control_auth_failed`). No tombstone is kept: the id is not poisoned.
2. At the same moment the gateway MUST drop the proof-only node's registration and connection (a
   heartbeat naming the old `connectionId` is `401`), its stored `hardware`, and MUST close every
   link it holds.
3. An unredeemable or invalid operator code (unknown, expired, already used, wrong id) MUST NOT
   unseat anyone: the proof-only credential, registration and hardware are unchanged.
4. The reverse is never allowed: a proof never replaces an operator-issued credential
   (`403 forbidden`, section 5.2).

### 6.3 Links

A link is a routing privilege (routing prefers a held link). Therefore a gateway MUST refuse a
link hello (the link authentication step) from (a) a node whose credential is proof-only and (b)
any node whose current registration is hardware-only, even with an operator-issued credential.
Registering hardware-only on a node that holds a link MUST release that link. The link wire is not
HTTP and is outside the conformance vectors; both are owed tests (`P5-T33`, `P5-T34`).

### 6.4 Known ids

A gateway MUST refuse a tokenless `/v1/node/challenge` and `/v1/node/proof` with `403 forbidden`
for a `nodeId` it already knows or routes to: a static-catalog node, a node in the live fleet, a
joined node, a link-only node, a controller-managed instance id, and an id that holds an
operator-issued credential. The check runs at `/challenge` **and again at `/proof`**, because an id
can become known between the two. `/key` SHOULD also be refused with `403 forbidden` for a known
id (both reference gateways do), and MUST NOT overwrite or reveal anything about a known id: a key
bound to an id the gateway already routes to would otherwise sit there waiting for that id to be
released.

### 6.5 Bounded state

State created by unauthenticated callers is an exhaustion target. A gateway MUST bound pending
challenges, published keys, proof-only credentials/nodes and stored hardware. When a bound is
reached the request is refused `429`; clients MUST key on the status. The code SHOULD be
`too_many_requests` (a bound) or `rate_limited` (a rate, with a `Retry-After` header). Operator
enrollment MUST NOT be blocked by exhaustion of any of these bounds. Expired proof state (expired
challenges, keys that never proved, consumed-challenge records) SHOULD be purged. An implementation
MAY add per-source rate limiting (`429 rate_limited`, `Retry-After`).

The bounds are implementation limits, not contract values; these are permitted:

| Gateway | Limits |
| --- | --- |
| Rust | 1024 pending challenges; 10000 published keys; 10000 proved nodes; hardware stored in compact form |
| Go | one outstanding challenge per node id (a new one replaces it); 1024 global; 10000 published keys, with a 1 h expiry for a key that never completes a proof; 2000 proof-only credentials; per-source limiter, burst 60 then 1 per second |

They are not vectors. A deployment may choose other values but MUST have a bound.

### 6.6 Request size

An unauthenticated body is parsed only after its size is known to be acceptable. A gateway SHOULD
refuse a body larger than **256 KiB** on `/v1/node/register` and **16 KiB** on `/v1/node/key`,
`/challenge` and `/proof`, before parsing it, with `400 bad_request` or `413`. (Rust: 256 KiB and
16 KiB, 400. Go: 128 KiB on register, which is stricter and permitted; the 65536-byte `hardware`
limit of section 3.1 still applies.) A body at or under the cap is parsed normally.

### 6.7 Hardware lifecycle

Stored hardware lives exactly as long as the registration that sent it: it is replaced by a
re-registration, cleared by one that omits it, and dropped when the registration is reaped,
forgotten, withdrawn or replaced by a promotion (section 3.1 rule 8, 6.2).

### 6.8 Rollback safety

A gateway SHOULD persist the origin (proof-only or operator-issued) of every credential together
with the credential, using a form an older binary does not accept as operator-issued (for example
a role an older binary rejects), so that rolling back to a binary that predates section 6.1 fails
**closed** (the proof-only credential does not authenticate) rather than treating it as
operator-issued and letting it register an endpoint. The Go gateway does this; the Rust proof
store is in memory (`OPEN_GATES.md`).

### 6.9 Hardware-only nodes contribute no capacity

Heartbeats and telemetry from a node whose current registration is hardware-only are accepted for
liveness, but MUST NOT contribute devices or GPU-memory reports (spec 46) to fleet capacity,
placement or any snapshot that routing or the rebalancer reads.

### 6.10 Release of proof-only nodes

A node that holds only a proved credential is released (its credential and registration dropped) by
a gateway only after a **long silence**. The control freshness window (30 s in the reference) MUST
NOT release it, because that window is meant for routable nodes and would force an honest agent to
re-prove every time it paused. Permitted range: the Rust gateway releases after 1 hour of silence
(or if it never registers within an hour of proving); the Go gateway persists proof-only
credentials with a longer TTL. A gateway SHOULD NOT release earlier than one hour and MUST have an
upper bound (section 6.5).

### 6.11 Per-source live-state caps and rate limits

Per-source caps on live state are **permitted and RECOMMENDED** in addition to the global bounds of
section 6.5. The reference values (not contract values): each source holds at most 16 unproved
keys, 8 outstanding challenges and 4 proved credentials, with IPv6 sources grouped by /64; a full
key table evicts the **oldest unproved** key rather than refusing; a repeat of a held key or of an
outstanding challenge is free. The token-free routes `/key`, `/challenge` and `/proof` use a token
bucket of burst 30 then 10 per second per source; register and heartbeat of proved credentials draw
from a separate bucket; operator-issued credentials are never charged. A cap or bucket that
refuses answers `429` (section 6.5). Reverse-proxy caveat: the source is the TCP peer address, so
behind a reverse proxy every caller shares the proxy's address and these limits then apply to the
proxy as a whole; a deployment behind a proxy should either trust a forwarded-address header from
that proxy only or accept the shared limit.

### 6.12 Telemetry and body bounds

A connection whose registration is hardware-only, or whose credential is proof-only, MUST NOT be
allowed to file telemetry: `POST /v1/node/telemetry` is `403 forbidden`. Its heartbeat is accepted
for liveness but keeps only `busySlots`, `queueDepth` and `leaving`; everything else in the status
(devices, residency, GPU memory) is discarded (section 6.9). Heartbeat and telemetry bodies SHOULD be
size-capped before parsing (Rust: 1 MiB).

## 7. Compatibility

- Additive and capability-free: an older node never sends `hardware`; an older gateway that
  ignores unknown request members registers such a node as a normal one (if its body also names an
  endpoint and models) or refuses a hardware-only body under its existing checks. A node that wants
  hardware-only registration against an unknown gateway cannot tell the difference between
  "refused" and "unsupported" except by the 400; it SHOULD fall back to its previous behavior and
  say so.
- A newer node ignores unknown `assignments` entries, and an older node ignores the member.
- Mixed fleets: both gateways store `hardware` verbatim, so an operator listing is comparable
  across them.

## 8. Conformance

`conformance/node-join-vectors.json` defines the HTTP-level register cases and the enrollment known
answers; each gateway replays them in its own suite against a credential it obtained itself
(`${CREDENTIAL}` is substituted). The scenarios are `hardware_registration` and `node_enrollment`
in `conformance/manifest.yaml` (the `registration` and `backwards_compatibility` scenarios also
apply to the older-node vector).

| Vector id | Requirement |
| --- | --- |
| `hw-only-with-hardware`, `hw-only-without-hardware`, `hw-only-null-hardware` | (a) hardware-only is accepted; response has `connectionId` and `assignments: []`; not routable |
| `hw-oversize`, `hw-oversize-by-one` (`hw-at-limit` is accepted) | (b) oversize `hardware` is `400 bad_request`; nothing admitted |
| `hw-not-object-*` | (c) `hardware` not an object is `400 bad_request` |
| `hw-version-*` | (d) missing or non-integer `version` is `400 bad_request`; any integer accepted |
| `older-node-no-hardware` | (e) a node without `hardware` registers as before; `assignments: []` added |
| `hw-unknown-keys-kept` | unknown members are stored verbatim |
| `enrollmentIdCases` | tokenless `/key` accepts only the derived id (`node_` + 16 hex of SHA-256 of the raw key); any other id or uppercase is 400; operator enrollment takes any id |
| `enrollmentLifecycleCases` | promotion evicts a proof-only squatter (old credential and connectionId `401`, hardware gone); a bad operator code unseats nobody; known ids get `403` at `/challenge` and `/proof`; a repeated `/challenge` returns the same challenge until it expires; hardware-only and proved connections cannot file telemetry; omitting `hardware` clears it |
| `requestSizeCases` | oversize bodies are refused before parsing (SHOULD) |
| `enrollmentTrustCases` | tokenless + endpoint is 403; tokenless + models is 403; tokenless hardware-only is 200; code-enrolled with an endpoint is 200; a proof over an operator-enrolled id is 403 |
| `enrollmentRoleCases` | tokenless challenge for role `node` is 200; for `gateway` (and other roles) is `400 bad_request` |
| `enrollmentKnownAnswers` | (f) transcript and signature for fixed seed, challenge, nonce and claim |

The reference gateway replays the vectors in addition to its own `conformance/MANIFEST.json`; that
manifest is not updated by this repository (it lives in `InferWeave/inferweave`).

## 9. Required tests

Recorded `owed` by `P5-T33` (Rust gateway) and `P5-T34` (Go gateway); see the task cards and
`contracts/canonical-task-graph.json`. A passing schema fixture or runner check does not close the
gate: only a running gateway replaying the vectors does.
