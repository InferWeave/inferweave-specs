# 65 — InferWeave Storage: content-addressed model store, signed grants and S3 front end

## Status

**SPECIFICATION — PROPOSED; BLOCKED for production use.** This document defines a distributed,
content-addressed model store: the `store` role and the `iw.store/1` capability, the signed
`iwg1` read grant, the store's native data plane and its read-only S3-compatible front end, the
network exposure and abuse controls of a store, the single-writer rule for shared filesystems, the
control-plane messages and digest index, the multi-source staging client, and the integrity and
quarantine rules. It is additive to InferWeave Protocol 1.1.0 and changes nothing for a peer that
did not negotiate `iw.store/1`.

Phase 1 is **implemented in part** in the reference implementation (`InferWeave/inferweave`, branch
`feat/inferweave-storage`, read at commit `c92fb073`, **not merged**). Phase 2 is specified and
not built. Section 1.3 marks every part as implemented or not; where this text and the
implementation disagree, this text is the contract and the difference is a defect to be recorded in
`OPEN_GATES.md`. Every required test is recorded `owed` by canonical tasks `P5-T36` (feature
`IW-STORE-001`, Phase 1) and `P5-T37` (feature `IW-STORE-002`, Phase 2); see `OPEN_GATES.md`.
The decision record is `decisions/2026-10-16-inferweave-storage.md` (Proposed). The items needing
an operator decision are collected in section 12.

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

## 1. Purpose and scope

Nodes pull 10 to 100 GiB model blobs from Hugging Face one node at a time (about 20 minutes for
30 GiB per farm node). This is slow, subject to rate limits and gating, and repeated per node.

InferWeave Storage lets **store** nodes, placed next to cluster storage, hold the catalog once.
Any node pulls a blob from whichever holders give the best *measured* path, using the existing
gateway trust fabric, with **no open public HTTP endpoint**.

Non-goals: serving inference traffic; storing anything not pinned by sha256; replacing
`artifact_cache.rs` (the client reuses it); a general object store.

### 1.1 Architecture rule: control plane on the link, data plane off it

1. The gateway link (`crates/iw-core/src/control_connection.rs`, `crates/iw-gateway/src/node_link.rs`)
   carries **control messages only**: advertisements, index queries, grant issuing, ingest
   leases, replication orders. It MUST NOT carry blob bytes. Reasons, each measurable:
   base64 in `token` frames costs +33 percent; the credit window counts frames, not bytes;
   bulk frames share the socket with heartbeats and live inference streams, so a 100 GiB pull
   would stall them.
2. Blob bytes flow on a separate **data connection**: node to store, HTTP/1.1 (section 5),
   authenticated per request by a signed grant (section 4).
3. A node that cannot reach any store directly MAY use a relayed path on its **own**
   rate-limited connection, never on the inference link (Phase 2, section 10, open item O6).

"No public HTTP server" is read as: no open or unauthenticated endpoint. A store MAY listen on
a port; it serves only requests carrying a valid grant (open item O2).

### 1.2 Relationship to other specifications

| Document | What it covers | What this document adds |
| --- | --- | --- |
| `specs/20_NODE_AUTOCONFIG_DISCOVERY.md` "Model fetch" | acquisition is resumable, checksum pinned and authorized by deployment intent | a second source for the same pinned blob (a store holding it), tried before the origin; the origin stays the fallback (7.7) |
| `specs/27_SITE_CONNECTOR_ARTIFACT_CACHE.md` | the site-connector cache tiers | a holder tier that any node can reach by grant; this document does not change the tier order of spec 27 and the two are not integrated (open item O18) |
| `specs/40_NETWORK_TOPOLOGY_GRAPH.md` | the topology graph and its export contract | the optional, capability-gated `store` field and its carrier vertices (6.3); the topology schemas of this repository are not yet amended (`OPEN_GATES.md`) |
| `specs/45_PROTOCOL_V1.md` | capability negotiation by exact string `iw.<name>/<major>` | the capability `iw.store/1` (6.1) |
| `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` | hardware-only registration, operator-enrolled credentials | the `store` role registers hardware-only, operator-approved, and carries an optional `store` object on register and heartbeat (6.2); spec 47's role list is not yet amended |
| `specs/21_FEDERATION_ROLES.md`, `specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md` | parent and child gateways; authenticated gateway links | presence-only reporting of a child's stores to its parent and the rule that the signer of a grant is the gateway the store trusts (3.1, 6.3, 6.5) |
| `specs/64_DYNAMIC_NODES_AND_GATEWAY_PROVISIONING.md` | an assignment's artifacts carry ordered sources and are fetched on assignment | nothing yet: a store is not a source kind of an assignment (open item O18) |
| `specs/00_INVARIANTS.md`, invariant 15 | a deployment is an immutable fingerprint | a blob is identified by its sha256 and size; a store never changes what a pin means |

**Where the specification was silent.** Nodes pulled 10 to 100 GiB model blobs from the origin one
node at a time (about 20 minutes for 30 GiB per farm node), repeated per node, subject to the
origin's rate limits and gating. Specs 20 and 27 specify resumable pinned fetch and a per-site
cache but no way for one site's copy to serve another node over a verified path, and spec 40
carries topology and no content presence. This document fills that gap without opening a public
endpoint and without putting blob bytes on the gateway link.

### 1.3 Implemented and proposed

"Implemented" means present in the reference implementation at `c92fb073` and exercised by the
tests that implementation names; it does not mean `proven` (section 15).

| Part | Status |
| --- | --- |
| Grant primitive, token, transcript, verification order (3, 4) | Implemented (`iw-core` `store_grant`). Presenter binding (O5) not built. |
| Native data plane `/v1/blob`, `/healthz`, limits, keep-alive (5) | Implemented (`iw-store`). Plain HTTP only; TLS is not built (5.6, 5B.11 H1). |
| S3 front end, read-only (5A) | Implemented. Virtual-hosted addressing, any write verb, `STREAMING-*` payloads are not (5A.8). |
| Bind policy, allow-list, lockout, ceilings, audit (5B.1 to 5B.9) | Implemented, with the gaps listed in 5B.11 (H1 to H7). |
| Rendezvous with no inbound port (5B.10) | Proposed (Phase 2). |
| Single-writer rule for the serving daemon (5C.1 to 5C.5, 5C.7) | Implemented. |
| Ingestion, epoch and no-replace publish (5C.6, 6.6) | Proposed (Phase 2). |
| Capability, role, advertisement, leave notice, digest index (6.1, 6.2, 6.4) | Implemented. |
| Topology `store` field, one hop (6.3) | Implemented. Grandchild reporting is not. |
| Grant request, `who-has`, `report` over HTTP (6.5) | Implemented. Forwarding a grant request to a child gateway is not (O4). |
| Multi-source client in `deploy/farm/artifacts/stage.py` (7) | Implemented through source ranking, range plan, resume, failure table, origin fallback and final verification; hedging beyond throughput shifting is not (10.2). The Rust client through `artifact_cache.rs` is not. |
| Reputation, quarantine, operator clear (8) | Implemented. The production value of the corroboration threshold is open (O8). |
| Scope tags (9) | Specified; per-blob scope on a store and per-listener enforcement are not built (H6, O3). |
| Replication, repair, quota, eviction, relayed path (10.1) | Proposed (Phase 2). |

## 2. Glossary

| Term | Meaning |
|---|---|
| blob | One immutable file (typically a GGUF shard), identified by its sha256. |
| digest | Lowercase hex sha256 of the blob, 64 chars, no `sha256:` prefix on the wire (the prefix is allowed only in human-readable text, as in `sha256:X`). |
| catalog | The sha256-pinned manifest of wanted blobs. Schema follows `deploy/farm/artifacts/models.json` (`files[].{name,size,sha256}`) plus a `scope` (section 9). The catalog is the source of truth ("pins are truth"). |
| store | A process with role `Role::Store` (`--kind store`) that holds blobs on a local or shared filesystem and serves them over the data plane. |
| holder | A store that currently has a blob in state `complete`, as advertised. |
| gateway | An InferWeave gateway. Authority that issues grants and keeps the digest index. |
| node | Any consumer (GPU node, farm node, hive staging script) that wants a blob. |
| client | The fetching code on a node (Python `stage.py` first, Rust via `artifact_cache.rs` later). |
| grant | A signed, stateless authorization to read a digest and byte range (section 4). |
| issuer | The gateway key that signed a grant. |
| ingest lease | A time-limited right, granted by the gateway to exactly one store, to download a digest from the origin (Hugging Face). |
| shared-fs hit | The blob is already readable at a local path (for example hive Quobyte); distance zero, no transfer. |

## 3. Trust model

### 3.1 Principals and keys

* Every gateway has an Ed25519 keypair (`crates/iw-core/src/signature.rs`, `NodeKeypair`). Its
  public key (64 lowercase hex chars) is the gateway's **grant issuer key**.
* A store holds **no signing key for grants** and never issues grants. Its enrollment identity
  (as `--kind store`, operator-approved like a node) is separate and is used only on the
  control link.
* A store holds a set of **trusted issuer public keys** (`trusted_gateway_keys`). A grant whose
  `issuer` is not in that set MUST be rejected (`UntrustedKey`) before the signature is
  evaluated. The set is the union of two sources:
  1. **Home gateway keys, learned.** A store is enrolled with one or more gateways (its *home*
     gateways). Each returns its grant-signing public key(s) in the `grantIssuerKeys` field of the
     registration reply and of every heartbeat reply sent to a store that negotiated `iw.store/1`
     (3.3). The store replaces that gateway's previous set with each reply, so no manual key
     configuration is needed for a home gateway and a rotation reaches the store within one
     heartbeat.
  2. **Operator extras.** Keys the operator lists explicitly (flag or file). A store trusts no
     other key.
  A store enrolled with two gateways therefore trusts both. Rotation: the gateway replies
  `[new, old]` for at least one max lifetime (300 s) plus the heartbeat interval, then `[new]`.
  The store MUST apply a changed set without restart (a restart discards in-flight work); extras
  are re-read on SIGHUP or file change.
* **Grants are issued only by the gateway the node is enrolled with.** Access rule: any node that
  is currently enrolled with, and has a fresh registration (link or heartbeat) at, THIS gateway
  may be granted reads of digests that are in the catalog and in the node's scope (public by
  default; section 9). A node that is not enrolled, whose credential is revoked or denied, or
  whose registration has lapsed, gets no grant. Because a grant lives at most 300 s, revocation
  takes effect within one lifetime.
* Federation (**open item O4**, now resolved for Phase 1 as follows): a store trusts only its home
  gateways (learned, above) plus the operator's explicit extras. It never auto-trusts keys it
  sees in topology, because topology is itself a claim made by peers. A node enrolled with a
  gateway other than the store's home gateway is served by asking that gateway for a grant
  (6.5); the store then must list that gateway's key as an extra, or the grant is rejected
  `UntrustedKey`.

Remote holders reported through topology (6.3, 6.4) do not change this rule: they are hints to
ask the child gateway, and no grant is issued for them by the parent.

### 3.2 What a grant proves, and what it does not

A valid grant proves: a trusted gateway decided, no longer than `max_lifetime` ago, that node
`node_id` may read the stated digest and range from the stated store (or any store).
It does not prove: that the node is currently enrolled, that the blob is sound, or that the
presenter is the named node (see replay stance, 4.6).

Pins are truth: a store's *claim* to hold a digest is a hint. Correctness is established only
by the client verifying size and sha256 of what it received (section 7.8).

### 3.3 `grantIssuerKeys`

Present on the registration reply and each heartbeat reply to a store that negotiated
`iw.store/1`; absent otherwise (absent means none, and a heartbeat reply that omits it leaves the
store's current set unchanged):

```json
{"status": "ok", "grantIssuerKeys": ["<64 lowercase hex, current>", "<64 lowercase hex, previous>"]}
```

* A JSON array of 0 to 4 distinct strings of 64 lowercase hex characters, current key first. The
  reader is strict: a field that is not such an array is ignored as a whole (never half applied)
  and the previous set stays.
* The same keys are readable unauthenticated at `GET /v1/store/issuer` (a public key is not a
  secret), as `{"version":1,"grantIssuerKeys":[...]}`, for an operator who lists a key as an extra.
* The gateway holds the signing seed in a file (`--store-grant-key-file`, 64 hex characters, mode
  0600, created when absent); the previous public key during a rotation is
  `--store-grant-previous-key`.

## 4. The grant

### 4.1 Fields

| Field | JSON type | Rule |
|---|---|---|
| `version` | integer | MUST be `1`. Any other value: `UnknownVersion`. |
| `issuer` | string | Issuer public key, 64 lowercase hex. Selects the verification key; MUST be in the store's trusted set. |
| `digest` | string | 64 lowercase hex chars. |
| `range` | object or null | `{"start": u64, "end": u64}`, **inclusive** both ends, `start <= end`. `null` means the grant covers the whole blob and any sub-range of it. |
| `node_id` | string | The node permitted to present the grant. 1 to 128 chars, ASCII graphic (0x21 to 0x7e). |
| `store_id` | string or null | Optional audience: if non-null the grant is valid only at that store. Same charset and length as `node_id`. |
| `not_before` | integer | Unix seconds, UTC. |
| `expires_at` | integer | Unix seconds, UTC, exclusive. `expires_at > not_before`. |
| `grant_id` | string | Unique per grant, 1 to 64 chars, ASCII graphic. Used for audit and optional deny-listing; not for replay protection (4.6). |

All integers are in `0 .. 2^63`. Issuers SHOULD keep them under `2^53` so JavaScript and
Python-with-float consumers round-trip them.

The lifetime is `expires_at - not_before` and MUST be `<= 300` seconds by default; a verifier
MUST reject a larger window (`LifetimeTooLong`). The limit is verifier policy, default 300, so a
verifier can be stricter but a grant cannot make itself longer-lived.

A byte range in a `range` grant is a *ceiling*. A request for a sub-range is allowed; a request
for one byte beyond `end` is not. A request for the whole blob (no `Range` header) is allowed
only when `range` is `null`.

### 4.2 Token encoding

```
Authorization: Bearer iwg1.<payload>.<signature>
```

* `iwg1` is the token version marker and equals the `version` field. A different marker of the
  shape `iwg<digits>` (`iwg2`, ...) is `UnknownVersion`; any other prefix is `BadEncoding`.
* `<payload>` = base64url (RFC 4648 section 5), **no padding**, of the UTF-8 JSON object of 4.1.
* `<signature>` = base64url, no padding, of the 64 raw Ed25519 signature bytes.
* Decoders MUST be strict: alphabet `A-Za-z0-9-_` only; no `=`; no whitespace; trailing bits of
  the last symbol MUST be zero (canonical). Exactly three dot-separated segments.
* Total token length MUST NOT exceed **2048** bytes. A verifier MUST check this before decoding
  anything. A decoded payload larger than 1536 bytes is `BadEncoding`.

Producers MUST emit these keys exactly once each, in this order, with `null` for absent
optionals:
`version, issuer, digest, range, node_id, store_id, not_before, expires_at, grant_id`.
Consumers MUST reject duplicate keys and unknown keys (`BadEncoding`) and MUST accept an absent
`range` or `store_id` as `null`.

The JSON is **not** what is signed (4.3), so JSON whitespace or key-order differences between
implementations cannot create a verification mismatch; they are only a parsing concern. The
corollary is that the token bytes are not an identifier: identify a grant by `grant_id`.

### 4.3 Signed transcript

The signature is Ed25519 (`NodeKeypair::sign_bytes`, verified with `verify_bytes`, i.e.
`verify_strict`) over the byte string `T` built from the **parsed fields**, in this order, in the
style of `proof_transcript` in `signature.rs`:

```
T = field("iw-store-grant-v1")        // domain separation tag
 || u8(version)                       // 1
 || field(issuer)                     // the 64 hex chars, ASCII
 || field(digest)                     // the 64 hex chars, ASCII
 || range_enc
 || field(node_id)
 || optional(store_id)
 || u64be(not_before)
 || u64be(expires_at)
 || field(grant_id)

field(b)       = u32be(len(b)) || b
optional(s)    = 0x00                       if s is null
               | 0x01 || field(s)           otherwise
range_enc      = 0x00                       if range is null
               | 0x01 || u64be(start) || u64be(end)
```

* `u32be`/`u64be` are big-endian fixed width. Strings are their UTF-8 (here ASCII) bytes.
* The domain tag `iw-store-grant-v1` is a protocol version: changing it invalidates every grant.
  A key that signs grants MUST NOT sign any other material without a different domain tag.
* Length prefixes and presence bytes make the encoding unambiguous: shifting a boundary
  between `node_id` and `store_id`, or turning an absent `store_id` into an empty one, changes
  `T`.
* `verify_bytes` takes hex: the verifier passes the lowercase hex of the 64 signature bytes
  decoded from the token.

### 4.4 Verification procedure

A verifier is given: the token, the trusted issuer key set, `now` (unix seconds, injected, never
read from a global clock inside the function), the expected `node_id`, the verifier's own
`store_id`, the requested digest, the requested range (or none = whole blob), and policy
(`skew` default 30 s, `max_lifetime` default 300 s). It MUST evaluate in this order and return the
first failure:

1. token length cap, three segments, marker `iwg1` (`BadEncoding` / `UnknownVersion`);
2. strict base64url decode of both segments, JSON parse, field validation (`BadEncoding`);
3. `version == 1` (`UnknownVersion`), read before the strict field check so a future version
   with new fields is reported as `UnknownVersion`, not `BadEncoding`;
4. `issuer` in trusted set (`UntrustedKey`);
5. signature over `T` (`BadSignature`);
6. window shape: `expires_at > not_before` (`BadWindow`) and
   `expires_at - not_before <= max_lifetime` (`LifetimeTooLong`);
7. time: `now + skew < not_before` is `NotYetValid`; `now >= expires_at + skew` is `Expired`
   (expiry is exclusive: with zero skew, `now == expires_at` is expired);
8. `digest` equals the requested digest (`WrongDigest`);
9. requested range inside grant range (`RangeOutsideGrant`); an inverted requested range is
   also `RangeOutsideGrant`;
10. `node_id` equals expected node (`WrongNode`);
11. if `store_id` is non-null it equals the verifier's own store id (`WrongStore`); a null
    `store_id` is accepted by any store that trusts the issuer.

Signature before any semantic check, so a forged token cannot probe which semantic check failed.
Comparisons of identifiers and digests SHOULD be constant-time; they are not secret, but the
signature check is the only gate and equal-cost comparison costs nothing.

The skew tolerance widens both edges by `skew`. Skew MUST be configurable and SHOULD NOT exceed
60 s. Because the window is at most 300 s, the effective ceiling is `300 + skew`.

### 4.5 Issuing

A gateway issues a grant only to a node it currently considers enrolled and only for a digest in
the catalog and in the node's scope (section 9). It SHOULD set `not_before = now` and
`expires_at = now + 300` (or less), SHOULD narrow `range` to what was asked when the node asked
for a range, and SHOULD set `store_id` when it names a specific store. `grant_id` MUST be unique
(128 random bits, hex or base64url).

### 4.6 Replay stance

Grants are **reusable** within their lifetime and range scope. There is no per-use nonce and no
store-side state keyed on `grant_id`.

Why this is acceptable:

* The grant gates *reads of sha256-pinned, immutable content that is public by default*, with a
  bounded lifetime. A replayed grant lets an eavesdropper read what the node was already
  allowed to read, for at most 300 s. It cannot write, list, or read another digest or range.
* A use-once rule would force every store to keep shared state (or call the issuer), which
  defeats stateless verification at a remote site, and would break resumable ranged fetches that
  legitimately present one grant many times.
* Exposure is further reduced by the `node_id` and optional `store_id` binding, the short
  lifetime, the narrow range, and (open item O2) a TLS or tunneled transport that keeps the
  token off the wire in clear.

Where scope is `restricted` (section 9), the gateway SHOULD set `store_id` and `range` and a
lifetime of 60 s or less, and the transport MUST be confidential.
Stores MAY keep an operator-supplied deny-list of `grant_id` values for incident response;
this is optional and not required for correctness.

Binding the presenter to `node_id` cryptographically (proof of possession) is not in Phase 1; it
is open item O5.

## 5. Store data-plane API (HTTP/1.1)

Base path `/v1`. No other path exists on this listener (the optional S3 listener of 5A is a separate socket). Responses MUST NOT reveal blob names, directory
structure, or the set of held digests beyond what a valid grant already names.

### 5.1 `GET /v1/blob/<digest>`

* `<digest>` is 64 lowercase hex. Anything else is treated as an unknown path (`404`).
* `Authorization: Bearer iwg1....` is REQUIRED.
* `Range: bytes=<start>-<end>` or `bytes=<start>-` is the supported form. A store MUST
  support single ranges and MUST reject multi-range requests with `416`. Suffix ranges
  (`bytes=-N`) MUST be rejected with `416`: a grant range is explicit and a suffix needs the size.
* Success is **`206 Partial Content`** with:
  * `Content-Range: bytes <first>-<last>/<total>` matching `bytes (\d+)-(\d+)/(\d+)`, where
    `<first>` is the requested start, `<last>` the requested end (or `total-1` when open-ended,
    or the capped end, see below), and `<total>` the blob size.
  * `Content-Length: <last - first + 1>`.
  * `Accept-Ranges: bytes`, `Content-Type: application/octet-stream`, `Cache-Control: no-store`,
    and no `Content-Encoding` (clients send `Accept-Encoding: identity`).
  * `ETag: "sha256-<digest>"` is informative; clients MUST NOT rely on it for integrity.
* This is what `deploy/farm/artifacts/stage.py` `fetch_range` already requires: status `206`
  and `Content-Range` equal to `(offset, end, total)` for the range it asked for. A response that
  does not match MUST be treated by the client as a failure of that source (7.6).
* A request **without** `Range` is answered `416` (never `200` with the whole blob), unless the
  grant range is `null`, in which case the store MAY answer `200` with the whole blob.
  Rationale: the client never appends a `200`, and 100 GiB in one response is not a supported mode.
* A store MAY cap the bytes sent per request (`max_request_bytes`, default 1 GiB). If it caps,
  `<last>` in `Content-Range` is the capped last byte and the client re-requests the rest. A
  client asking for `bytes=<start>-<end>` therefore MUST accept a `<last>` smaller than `<end>`
  only when `<first>` equals the requested start and the total matches; this is an extension to
  what `stage.py` accepts today and the Phase 1 client MAY request no more than the cap.

### 5.2 `HEAD /v1/blob/<digest>`

Same authentication. Returns `200` with `Content-Length: <total>`, `Accept-Ranges: bytes`, and
no body. A range grant is accepted for HEAD as long as the digest matches. Use: size discovery
and a cheap latency probe. The catalog size is authoritative; a mismatch is a source failure.

### 5.3 `GET /healthz`

The only unauthenticated endpoint, answered only to peers that pass the allow-list of 5B.3. Returns `200`, `Content-Type: application/json`, body exactly
`{"status":"ok"}`. It MUST NOT include version, hostname, free space, blob counts, or any other
field.

### 5.4 Status codes

| Condition | Status | Notes |
|---|---|---|
| No `Authorization`, wrong scheme, malformed token, unknown version, bad signature, untrusted issuer, bad window, expired, not yet valid | `401` | `WWW-Authenticate: Bearer realm="iw-store"`. One generic body `{"error":"unauthorized"}`; the specific cause goes to the store log, not the client. |
| Valid grant but wrong digest, range outside grant, wrong node, wrong store | `403` | Body `{"error":"forbidden"}`. |
| Valid grant for this digest, blob not held or held only `partial` | `404` | Body `{"error":"not_found"}`. |
| Range unsatisfiable, malformed, multi-range, suffix, beyond blob end, or no `Range` on a range grant | `416` | `Content-Range: bytes */<total>` when the total is known. |
| Unknown path | `404` | No directory listing, no index page. |
| Method other than GET/HEAD on a known path | `405` | `Allow: GET, HEAD`. |
| Request line or headers over 16 KiB, or more than 64 headers | `431` | |
| Store overloaded (concurrency cap) | `503` | With `Retry-After`. Client treats it as a slow source, not misbehaviour. |

Ordering: authenticate (`401`) before anything about the digest is evaluated, except `/healthz`.
Existence (`404`) is only revealed after all grant checks pass, so a valid-but-narrow grant
cannot enumerate other digests.

### 5.5 Resource limits

Stores MUST bound: concurrent connections (default 256), concurrent range streams per `node_id`
(default 32), idle time between bytes (a slow-loris client is cut after 30 s without progress),
request header size (5.4). A store MUST resolve the blob by digest only (`<root>/<digest[0:2]>/<digest>`
or a configured index), never by a client-supplied path component, and MUST NOT follow symlinks
out of the configured blob directory.

### 5.6 Transport

Plain HTTP/1.1, TLS, or an SSH tunnel: open item O2. Network exposure is constrained by 5B regardless of the choice. Whichever is chosen, the API above is
unchanged. Over plain HTTP the grant is visible to the network path (4.6 applies).

Connection reuse is opt-in. By default every response carries `Connection: close`. A client that
sends `Connection: keep-alive` on an HTTP/1.1 request without a body may reuse the connection
after a complete `200`/`206` answer (GET or HEAD); the store then answers `Connection: keep-alive`.
Every request on the connection is parsed, authenticated and authorized on its own (a grant is
never remembered per connection), every error answer closes the connection, a request with a body
or with pipelined bytes is answered and closed, the idle wait between requests is bounded by the
head deadline, and a connection serves at most 1000 requests. The connection and per-node stream
caps of 5.5 apply unchanged. This saves the TCP handshake, the thread spawn and the close per
request, which matters for ranges of 1 MiB and below, not for 256 MiB ranges.

## 5A. S3-compatible API (second front end, read-only in Phase 1)

A store MAY also expose an S3-compatible HTTP API so that any S3 client (`aws`, `mc`, `s3cmd`,
`rclone`, `boto3`, llama.cpp-style downloaders) can read models from it. It is a **second front
end on the same digest index and blob directory** as section 5. It is off unless `--s3-listen` is
given, it listens on its own socket, and it does not change section 5 in any way: `/v1/blob`,
signed grants and their status codes are exactly as specified there. Section 1.1 still applies:
the S3 listener carries blob bytes to operators and tools, never over the gateway link.

### 5A.1 Why authentication differs from the native plane

The native plane is stateless for the store: a grant is verified with the gateway's *public* key
(section 4). S3 clients sign requests with a **shared secret** (AWS Signature Version 4), so the
verifier must hold the secret. That is the opposite of the grant design, which deliberately keeps
every secret off the store. The consequence is a deliberate split of audience:

* **Nodes** pull with grants on section 5. This is the path the fabric uses and it is unchanged.
* **Operators and tools** pull over S3 with **store-local access keys**, created by the store's
  operator, scoped to buckets and key prefixes (5A.4), and revocable by editing a file. S3 access
  never reaches the gateway, never appears in the digest index and is not a way for a node to
  bypass the gateway's scope decisions (section 9): over S3 a store serves only what its local
  operator chose to publish through `--s3-catalog` and the `blobs` bucket.

An S3 key is a long-lived credential for a read-only view. It is not a grant and is not issued by
a gateway. Open item O13 records the alternative (gateway-issued, short-lived S3 credentials).

### 5A.2 Namespaces

Path-style addressing only: `/{bucket}/{key}`. Virtual-hosted style (`{bucket}.host`) is a
Phase 1 non-goal; a request using it resolves the first path segment as a bucket and normally
answers `NoSuchBucket` or `AccessDenied`. The `Host` header is signed by the client but its value
is not interpreted.

Two kinds of bucket, configured on the daemon:

1. **`blobs`** (always present). Key = a 64-lowercase-hex sha256; the object is that blob. The
   bucket lists every held digest. Anything that is not 64 lowercase hex is `NoSuchKey`.
2. **Catalog bucket** (default name `models`, `--s3-catalog-bucket`; present when `--s3-catalog
   FILE` is given). Built from a catalog manifest in the farm schema
   (`deploy/farm/artifacts/models.json`): for each entry under `models`, for each element of
   `files` (`path`, `size`, `sha256`), the object key is `<model_id>/<path>`, where `<model_id>` is
   the entry's key in the manifest and `<path>` the pinned flat path. An object exists **only if**
   the store holds that sha256 in its index **and** the held size equals the manifest size;
   otherwise the key is absent (`NoSuchKey`, and not listed). Pins are truth: bytes that do not
   hash to the pin cannot be in the index under that digest. Manifest entries whose id or path is
   empty, contains `..` as a component, a NUL or a control character, or whose digest is not 64
   lowercase hex, are skipped and counted in the log.

The manifest is re-read on `SIGHUP` and when its (mtime, length) changes (checked per request);
a manifest that fails to parse leaves the previous catalog in force. Keys are never resolved to
filesystem paths: the object is found by digest through the index (5.5), so a key such as `../x`
is merely a key that does not exist.

### 5A.3 Operations

| Operation | HTTP | Status |
|---|---|---|
| ListBuckets | `GET /` | Supported. Lists only the buckets the key may see. |
| HeadBucket | `HEAD /{bucket}` | Supported. |
| GetBucketLocation | `GET /{bucket}?location` | Supported. |
| ListObjectsV2 | `GET /{bucket}?list-type=2` | Supported: `prefix`, `delimiter`, `max-keys` (default and cap 1000), `continuation-token`, `start-after`, `encoding-type=url`. |
| ListObjects (v1) | `GET /{bucket}` | Supported minimally: `prefix`, `delimiter`, `max-keys`, `marker`, `encoding-type`. |
| HeadObject | `HEAD /{bucket}/{key}` | Supported. |
| GetObject | `GET /{bucket}/{key}` | Supported: whole object (`200`) or one `Range` (`206`); `If-Match`, `If-None-Match`, `If-Modified-Since`, `If-Unmodified-Since`. |
| PutObject, DeleteObject, DeleteObjects, CopyObject, CreateBucket, DeleteBucket, multipart, PutObjectAcl, PutObjectTagging, PutBucketVersioning: every request using `PUT`, `POST` or `DELETE` | | `403 AccessDenied`, message `this store is read-only`. Never succeeds, never reads the body. |
| GetObjectAcl, GetObjectTagging, GetBucketVersioning, ListObjectVersions, ListMultipartUploads, GetObjectAttributes, SelectObjectContent, policy, lifecycle, CORS, encryption, website, logging, replication, object-lock and any other sub-resource query | `GET`/`HEAD` with that sub-resource | `501 NotImplemented`. |
| Any other method (`OPTIONS`, `PATCH`, `TRACE`, ...) | | `405 MethodNotAllowed`, `Allow: GET, HEAD`. |

Authentication is evaluated before the operation is classified, so an unauthenticated client
learns nothing, not even which operations exist. `x-amz-request-id` is present on every response.

**Range.** A single range `bytes=a-b`, `bytes=a-` or `bytes=-n` yields `206` with `Content-Range:
bytes first-last/total` and `Content-Length: last-first+1`, byte-exact (`last` is clamped to
`total-1`). A range that starts at or beyond the object size, or `bytes=-0`, yields `416
InvalidRange` with `Content-Range: bytes */total`. An invalid or multi-range header is ignored and
the whole object returned (`200`), as S3 does. The `max_request_bytes` cap of 5.1 does **not**
apply to this front end: an S3 client cannot tell that a `206` was shortened, and a silently
truncated download of an object it believes it received completely is worse than a long one. The
other bounds of 5.5 (connections, header limits, idle time) apply unchanged; the range-stream cap
applies per access key instead of per node.

**Conditional requests** follow RFC 9110 precedence: `If-Match` (mismatch: `412
PreconditionFailed`), else `If-Unmodified-Since` (modified since: `412`); then `If-None-Match`
(match: `304`), else `If-Modified-Since` (not modified: `304`). `304` has no body and carries `ETag`
and `Last-Modified`.

### 5A.4 Authentication and authorization

AWS Signature Version 4, service `s3`, region configurable (`--s3-region`, default `us-east-1`),
in both the `Authorization` header form and the presigned query form (`X-Amz-Algorithm`,
`X-Amz-Credential`, `X-Amz-Date`, `X-Amz-Expires`, `X-Amz-SignedHeaders`, `X-Amz-Signature`).
**There is no anonymous access.** A request with neither form is `403 AccessDenied`.

* The canonical request, string to sign and signing key are exactly as in the AWS documentation
  (path URI-encoded once, never double-encoded, as S3 requires). The signature is compared in
  constant time. `host` MUST be a signed header, as MUST `x-amz-date` and `x-amz-content-sha256`
  when sent as headers. A duplicated signed header is refused (`400`).
* Payload: `x-amz-content-sha256` MUST be `UNSIGNED-PAYLOAD` or the empty-body hash
  (`e3b0c442...b855`) for `GET`/`HEAD`; `STREAMING-*` modes answer `501 NotImplemented` (the store
  accepts no request bodies). Presigned requests use `UNSIGNED-PAYLOAD`. These payload rules
  apply to `GET`/`HEAD`; a signed write verb is answered `403` read-only whatever payload mode
  it used, so an uploader sees the real reason.
* Clock: a header-signed request whose `x-amz-date` differs from the store clock by more than 15
  minutes is `403 RequestTimeTooSkewed`. A presigned request is valid from `X-Amz-Date` (with the
  same 15 minutes of tolerance into the future) until `X-Amz-Date + X-Amz-Expires`;
  `X-Amz-Expires` MUST be 1 to 604800 (7 days); afterwards `403 AccessDenied`, message `Request
  has expired`.
* The credential scope MUST name the configured region, service `s3`, `aws4_request` and the date
  of `X-Amz-Date`, else `400 AuthorizationHeaderMalformed` (`AuthorizationQueryParametersError`
  for the query form).
* Header caps are those of 5.4 (16 KiB, 64 headers).
* Neither the secret, the `Authorization` header nor the presigned `X-Amz-Signature` is logged.
  The access key id (not secret) is.

**Access keys** come from a local JSON file (`--s3-keys-file`, re-read on `SIGHUP`; an invalid
file leaves the previous set in force):

```json
{"keys":[{"access_key_id":"AKIA...","secret_access_key":"...","buckets":["models"],
          "prefixes":["qwen3.8-27b-"],"enabled":true}]}
```

`buckets` lists the buckets the key may use (empty: none). `prefixes` optionally restricts the
object keys (empty: the whole bucket). Unknown fields are an error so a misspelt restriction
cannot widen access. The file holds plaintext secrets and SHOULD be mode `0600`; the daemon warns
otherwise.

**Scope rules.** A key sees only its buckets and prefixes. A bucket outside the key's list is
`AccessDenied` whether or not it exists, so bucket names are not an oracle. An object outside the
key's prefixes is `AccessDenied` for `GET`/`HEAD`. `ListBuckets` returns only the key's buckets.
`ListObjectsV2` returns only keys inside the key's prefixes, **and** `CommonPrefixes` and
`NextContinuationToken` are derived only from those keys, so a listing never discloses a name, a
size or the existence of anything outside the scope (a requested `prefix` outside the scope
simply yields an empty listing). A disabled key is indistinguishable from an unknown one
(`InvalidAccessKeyId`).

### 5A.5 Object metadata and ETag

* `ETag`: the quoted lowercase sha256, e.g. `"af36...e0"`. It is **not** an MD5. Why this is safe:
  S3 clients treat a non-multipart ETag as an opaque equality token (`If-Match`, `If-None-Match`,
  change detection in sync tools). A client that compares an ETag to an MD5 of the data (some sync
  tools do, as a heuristic) sees a mismatch and skips that check or re-downloads; none can be made
  to accept wrong bytes by it. A multipart-style ETag (`...-N`), which makes clients switch to
  part-wise verification, is never emitted.
* `x-amz-meta-sha256`: the hex sha256. `x-amz-checksum-sha256`: base64 of the 32 digest bytes, the
  S3 checksum header format, so clients that verify checksums can. Both are the digest the index
  computed over the bytes, not a value trusted from a name.
  `x-amz-checksum-sha256` describes the whole object and is therefore sent on `200` and `HEAD`
  responses only, never on a `206` (clients verify it against the body they received).
* `Content-Length`, `Accept-Ranges: bytes`, `Content-Type: application/octet-stream`,
  `Last-Modified` = the file's mtime (whole seconds, HTTP date).

### 5A.6 Error shape

Every error is S3 XML with `Content-Type: application/xml`; `HEAD` errors and `304` carry no body:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>NoSuchKey</Code><Message>...</Message><Resource>/models/x</Resource>
<RequestId>...</RequestId></Error>
```

| Condition | Status | Code |
|---|---|---|
| No credentials, or a write verb (`this store is read-only`), or a scope violation, or an expired presign | `403` | `AccessDenied` |
| Unknown or disabled access key | `403` | `InvalidAccessKeyId` |
| Signature mismatch (wrong secret, tampered path, query, signed header or method) | `403` | `SignatureDoesNotMatch` |
| Clock differs by more than 15 minutes | `403` | `RequestTimeTooSkewed` |
| Malformed `Authorization`, credential scope or algorithm | `400` | `AuthorizationHeaderMalformed` |
| Malformed presign parameters | `400` | `AuthorizationQueryParametersError` |
| Bad `max-keys`, `list-type`, `encoding-type`, `X-Amz-Expires` | `400` | `InvalidArgument` |
| Missing or inconsistent payload hash header, malformed request | `400` | `InvalidRequest` / `XAmzContentSHA256Mismatch` |
| Request line or headers over limit | `431` | `InvalidRequest` |
| Unknown bucket the key may use | `404` | `NoSuchBucket` |
| Unknown key, or catalog entry not held or size mismatch | `404` | `NoSuchKey` |
| Range not satisfiable | `416` | `InvalidRange` |
| `If-Match` / `If-Unmodified-Since` failed | `412` | `PreconditionFailed` |
| `If-None-Match` / `If-Modified-Since` matched | `304` | (no body) |
| Unsupported operation, `STREAMING-*` payload | `501` | `NotImplemented` |
| Method not served | `405` | `MethodNotAllowed` |
| Concurrency cap | `503` | `SlowDown` (`Retry-After`) |

### 5A.7 Security considerations

* **Shared secret at the store.** Anyone who reads the keys file can mint requests as that key.
  The store refuses a keys file accessible to group or other (5B.7); keep it `0600`, give each tool its own key, revoke with `enabled: false` plus `SIGHUP`.
* **Replay.** SigV4 binds no nonce. A captured header-signed request can be replayed for 15
  minutes, a presigned URL until its `X-Amz-Expires` (up to 7 days). Impact is limited to
  re-reading the same object (the front end is read-only), but operators SHOULD use short
  expiries. Unsigned `Range` and `If-*` headers can be altered by an on-path attacker only to
  change which bytes of an already authorized object come back; use TLS (O2) on untrusted paths.
* **No anonymous access, no public listing.** With scope-limited listings this keeps the "no open
  endpoint" reading of 1.1.
* **Listing leaks.** Prefix scope is applied before delimiter grouping and paging, and the
  continuation token is a bare position re-filtered on every request; a forged token cannot reach
  outside the scope.
* **Enumeration of the digest space.** The `blobs` bucket names every held digest to a key allowed
  it. Give it only to operators.
* **Index vs catalog.** A catalog entry never makes the store read or serve anything not in the
  index; a manifest naming a digest with the wrong size is hidden, not served.
* **Timing.** Signature comparison is constant time. Key lookup is not (the access key id is not
  secret).

### 5A.8 Phase 2 (specified, not built)

* **PutObject as the ingestion path**, allowed only for keys that map in the catalog to a pinned
  digest. The body is streamed to a `.part` file and published by atomic rename only after its
  sha256 and size equal the pin; otherwise the part file is deleted and the request fails. Pins
  are truth. The access key must also be granted `write` in the keys file.
* **Multipart upload** under the same rule: parts accumulate in one `.part` file, the rename
  happens at `CompleteMultipartUpload` after the whole-object hash matches the pin.
* **No `DeleteObject`** by default; eviction stays an operator action (10.1).
* Virtual-hosted addressing and `STREAMING-AWS4-HMAC-SHA256-PAYLOAD` (used by the AWS CLI for
  uploads) are Phase 2 items.

## 5B. Network exposure and hardening

Sections 4 and 5A authenticate every request. This section adds the network-level controls
and the abuse resistance that keep an instance which is exposed by mistake from revealing
anything or being worn down. The requirement is: **public external access is bad**. Neither
listener may reach the public internet by accident, and authentication is the second line,
not the only one.

### 5B.1 Threat model

| Threat | Scenario | Controls |
|---|---|---|
| Exposed instance | A port forward, a wildcard bind or a cloud security group puts a listener on the internet | Bind policy (5B.2), peer allow-list (5B.3), no unauthenticated endpoint reachable by an outsider (5B.4) |
| Credential stuffing | A remote party tries stolen or guessed grants and access keys | Failed-authentication lockout (5B.5), per-key network pinning (5B.7), key-file hygiene (5B.7) |
| Enumeration | Probing digests, buckets, paths or `/healthz` to learn what is held | Allow-list closes before any byte is read; `404` only after authorization (5.4); S3 has no open endpoint |
| Resource exhaustion | Connection floods, request floods, address cycling to fill tables | Per-IP connection cap, global request ceiling, bounded lockout table (5B.5), audit-log rate limit (5B.8) |
| Header injection | A client forges `X-Forwarded-For`, `Forwarded` or `X-Real-IP` to claim an allowed address | The peer address is the TCP peer, never a header (5B.3) |

Many unrelated users share each remote cluster's single egress address, so the allow-list only
keeps the rest of the internet out. Grants (4) and SigV4 (5A.4) remain the real access control,
and the abuse controls are keyed so one noisy tenant cannot lock out a whole NAT address
(5B.5).

Out of scope here: an attacker already inside an allowed network with a valid credential
(sections 4.6 and 5A.7 apply), and on-path attackers on a private network (transport, O2).

### 5B.2 Bind policy (normative)

1. Each configured listen address (native and S3) is classified as one of: **loopback**
   (`127.0.0.0/8`, `::1`), **private** (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`,
   link-local `169.254.0.0/16` and `fe80::/10`, CGNAT `100.64.0.0/10`, unique-local `fc00::/7`),
   **unspecified** (`0.0.0.0`, `::`) or **public** (anything else, including multicast,
   broadcast, `0.0.0.0/8` other than the unspecified address, and documentation ranges).
   An IPv4-mapped IPv6 address (`::ffff:a.b.c.d`) is classified as the IPv4 address it maps.
2. The default listen address is loopback.
3. A store MUST refuse to start, with a message naming the address and the reason, when a
   listen address is unspecified (`0.0.0.0`, `::`). There is no override: a wildcard bind is
   refused even when a firewall is believed to be present, because a mistake in the firewall
   must not matter.
4. A store MUST refuse to start when a listen address is not loopback and no allowed network is
   configured (5B.3).
5. A bind to a specific publicly routable address is allowed only if ALL hold: (a) the operator
   passes `--allow-public-bind`; (b) the allow-list is non-empty; (c) the allow-list contains
   no default route and no overly broad range (IPv4 shorter than /16, IPv6 shorter than /48),
   unless `--allow-broad-cidr` is also passed, which logs a loud warning; (d) startup prints
   the effective listen addresses and the allow-list. The reason this exists: other clusters
   reach the store from one fixed egress address each (for example farm `128.120.146.1`, hive
   `169.237.233.14`), so the list is typically a few `/32` entries.
6. A public bind is plain HTTP (TLS is not provided in Phase 1, O2, H1). Until TLS exists a
   publicly bound store MUST serve only public-scope blobs: gated-scope blobs (section 9)
   require TLS over any non-private network. The store prints a warning at startup when a
   listener is public. (Enforcement of scope per listener is owed; see H6.)

### 5B.3 Peer allow-list (normative)

1. `--allow-cidr CIDR` (repeatable) and `--allow-cidrs-file FILE` (one CIDR per line, `#`
   comments, strict parsing: a bad line is a startup error) define the allowed networks, IPv4
   and IPv6. One list serves both listeners.
2. On a loopback bind the list is optional. When a list is configured it is enforced on every
   bind, loopback included, so a list that excludes `127.0.0.1` closes loopback peers too.
3. The peer is the address of the accepted TCP connection. An IPv4-mapped IPv6 peer is
   normalised to IPv4 before matching, and a mapped CIDR (`::ffff:10.0.0.0/104`) is normalised
   the same way. The store MUST NOT consult `X-Forwarded-For`, `Forwarded`, `X-Real-IP` or any
   other header for the peer address, for any control in this section.
4. A connection from a peer outside the list is closed immediately after accept, before any
   byte is read and without any response. It is counted and audited (`outside_allowlist`).

### 5B.4 Health endpoint

`GET /healthz` (5.3) is answered only to peers that pass 5B.3 (on a loopback bind with no
list, every peer is loopback). Any other peer is closed at accept. The S3 listener has no
unauthenticated endpoint: every path, including `/healthz` and `/`, requires a verified
signature and otherwise returns `AccessDenied`.

### 5B.5 Abuse resistance (normative; both fronts)

Applied at accept, in this order, so that refused connections cost no hashing and no
filesystem work:

1. **Allow-list** (5B.3).
2. **Lockout.** The store tracks failed authentication. A failure is any `401` or `403`
   produced by the grant verifier (including a missing credential) or the SigV4 verifier,
   plus a key presented outside its pinned networks (5B.7). A failure is charged to a key:
   * **(address, identity)** when it carries a *trusted* identity: on the native front, a
     failure after the grant signature verified against a trusted issuer (wrong digest, node,
     store, window, expiry) with a valid-looking `X-IW-Node` (1 to 128 of `[A-Za-z0-9_.:-]`);
     on the S3 front, a failed signature or a pinned-network violation for an access key id
     that exists. Default 5 failures within 60 s.
   * **address alone** for everything else: unparseable or untrusted tokens, missing
     credentials, unknown access key ids. Default 50 failures within 60 s, higher because many
     tenants may sit behind one address. Garbage never counts against an identity, so
     forging a victim's node id in a header cannot lock the victim.

   Locking lasts 60 s; each further lockout of the same key doubles the duration up to 3600 s;
   the doubling resets after the key has been quiet for 3600 s. A locked *address* is answered
   `429` with `Retry-After: <seconds>` at accept, before the request is read; a locked
   *(address, identity)* is answered `429` as soon as the head is read and the claimed identity
   extracted, before any verification, hashing or filesystem work. A successful authentication
   does not shorten or clear a lockout. The table is bounded
   (default 4096 addresses): when full, the least recently seen unlocked address is evicted
   first, so an attacker cycling source addresses cannot grow memory and cannot evict a lock
   held on another address while unlocked entries exist. Time comes from an injectable clock.
3. **Global request ceiling per front** (default 200 per second, fixed one-second window):
   over it the front answers `503` with `Retry-After` before reading the request.
4. **Per-IP concurrent connection cap** (default 16), answered `503` with `Retry-After`, on
   top of the global cap of 5.5.

Scope denials on the S3 front after a valid signature (a bucket or prefix outside the key's
scope, write verbs) are audited but do not count towards lockout: the caller already holds a
valid key and a typo must not lock out a shared address.

### 5B.6 Counters

SIGUSR1 prints, besides the counters of 5.5, denials by front and cause.

### 5B.7 Credential file hygiene and key pinning

1. The trusted-keys file (3.1) and the S3 keys file (5A.4) MUST NOT be accessible to group or
   other (`mode & 0077 == 0`). A store refuses to start otherwise, and a reload of a file that
   became accessible fails and keeps the previous set. `--insecure-key-file-permissions`
   downgrades this to a warning. This replaces the warning of 5A.7.
2. The sidecar index is written with mode `0600`, in the node-local state directory (5C).
3. An S3 access key entry MAY carry `allowed_cidrs` (array of CIDR strings; the schema stays
   strict). A request signed by that key from a peer outside those networks is refused as
   `AccessDenied` after the signature verifies (so an outsider cannot learn that a key is
   pinned), and it counts as a failed authentication. An empty or absent list means any peer
   that passed 5B.3.

### 5B.8 Audit logging

Every denial writes one structured line `iw-store: audit front=<native|s3> peer=<ip>
cause=<cause>` where cause is one of `outside_allowlist`, `locked_out`, `no_credentials`,
`bad_grant`, `bad_signature`, `out_of_scope`, `key_network`, `conn_cap_ip`, `rate_shed`. Lines
are rate-limited per cause and front (default 20 per minute; the next line after a burst
reports `suppressed=<n>`), so a flood cannot fill the disk; the counters of 5B.6 still count
every denial. Tokens, Authorization headers, query strings, secrets and client-supplied
identifiers are never logged.

### 5B.9 Deployment guidance

* Bind to the cluster-private interface address, or to loopback behind a tunnel
  (`ssh -L`, or the relay tunnel of `iw-tunnel`).
* Set `--allow-cidr` to the narrowest networks that need the store, and pin S3 keys with
  `allowed_cidrs`.
* Firewall in depth: add a host firewall rule that restricts the store port to the same CIDRs
  as `--allow-cidr` and drops everything else. The store's own controls are a second line, not
  a replacement.
* For another cluster that appears as one fixed public address, bind the store's public
  address with `--allow-public-bind` and `--allow-cidr <that address>/32`. That serves
  public-scope blobs only until TLS exists (5B.2); gated-scope blobs need TLS or a tunnel.
* Never forward the port to the internet, never run it behind a public reverse proxy (the peer
  address would then be the proxy), and never expose it on a login node's public interface.
* Cross-site traffic goes through a tunnel, not through an opened port.

### 5B.10 Phase 2: no inbound port at all

The store dials out to a rendezvous (the relay of
`docs/superpowers/specs/2026-10-06-relay-ssh-tunnel-design.md` (an implementation-repository draft, not canonical)), and the node meets it there. The store then listens on
nothing but loopback, or on nothing at all, and the allow-list controls become defence in
depth. The grant and SigV4 checks are unchanged. Not built.

### 5B.11 Open items for this section

* H1 - TLS listener (`--tls-cert/--tls-key`): the workspace has rustls and ring, but the
  fronts are written against `TcpStream`; a generic stream is a refactor. Until then no
  non-private bind exists.
* H2 - Lockout is per exact IP. An IPv6 attacker with a `/64` can cycle addresses; keying by
  `/64` is likely right and untested against shared-prefix clients.
* H3 - The allow-list is read at start; a reload on SIGHUP is not implemented.
* H4 - The ceiling is a fixed one-second window; a token bucket would smooth bursts.
* H6 - Per-listener blob scope: a public bind must serve only public-scope blobs, but the
  store has no scope tag per blob yet (O3, section 9). Until then the operator must keep
  gated blobs out of a publicly bound store's directory and catalog; the store only warns.
* H7 - A native client holding one valid grant can rotate `X-IW-Node` values to dodge the
  identity lock; it gains nothing beyond that grant, and the 403s still count in the audit
  log and counters. No address-wide backstop counter exists.
* H8 - `--gateway-ca-file <pem>` (daemon): a PEM bundle of an internal CA is ADDED to the
  public roots for an `https` gateway (verification is never off; the file must hold a
  CERTIFICATE block and the gateway URL must be https, both checked at start). Tested against a
  real TLS server with a locally generated CA (`crates/iw-store/tests/gateway_tls.rs`). Not
  reloaded on SIGHUP.
* H5 - Behind a trusted proxy (not recommended) the peer address is the proxy's; a PROXY
  protocol option is deliberately absent.

## 5C. Single-writer invariant on shared filesystems

On a shared cluster filesystem (Quobyte in the incident that motivates this section), concurrent
writes to the same file can hang the filesystem for every client. The rule is therefore
absolute: **one writer per file, always**. Blob directories are expected to live on such
filesystems (BeeGFS, Quobyte, NFS), and several store daemons may serve one directory.

### 5C.1 A serving daemon is read-only on blob directories (normative)

* The daemon MUST NOT create, open for writing, truncate, append to, rename, or remove anything
  under `--blob-dir`. Every blob open uses read-only flags through one helper. A sidecar,
  temp file, lock, log or counter inside the blob directory is a defect.
* The daemon refuses to start when its state directory or index file is inside the blob
  directory, and the library refuses to build a store whose sidecar would be.
* Two daemons serving one blob directory need no coordination: they never write there.

### 5C.2 Node-local state directory

Everything the daemon writes (the sidecar index, anything added later) lives in the state
directory, `--state-dir`, default `${IW_STORE_STATE_DIR:-/var/tmp/inferweave-store-<uid>}/<store-id>`
(store id characters outside `[A-Za-z0-9_-]` become `_`), created mode `0700`. `--index-file`
remains as an override of the sidecar path and is subject to 5C.1 and 5C.4. The library, as
opposed to the daemon, writes nothing unless a state directory or index path is given.

### 5C.3 Temp files

Every temp file the daemon creates has a name unique to the process and the attempt (process id,
a per-process sequence number and 64 random bits), is created with `create_new` (`O_EXCL`),
written, fsynced, and renamed over its target. On any failure the temp file is removed. A fixed
temp name is forbidden: two daemons would write the same file. Only the process that created a
temp file removes it; start-up never deletes temp files it does not own.

### 5C.4 Shared-filesystem guard

The daemon reads `/proc/self/mountinfo`, finds the mount containing each write location
(longest mount-point prefix; the later line wins for an over-mount; a bind mount takes the type
of the mount at its target) and its filesystem type. These types are shared: `nfs`, `nfs4`,
`cifs`, `smb3`, `smbfs`, `quobyte`, `fuse.quobyte`, `beegfs`, `lustre`, `gpfs`, `ceph`,
`cephfs`, `fuse.ceph`, `glusterfs`, `fuse.glusterfs`, `fuse.sshfs`. The daemon REFUSES to start
if its state directory, index file directory or any other write location is on a shared
filesystem, unless `--allow-shared-state` is passed, which prints a loud warning naming the
hazard. If the mount table cannot be read the daemon fails closed (refuses) for writes. Reading
the blob directory from a shared filesystem is the intended case and is not checked.

### 5C.5 One daemon per state directory

The daemon takes an exclusive `flock` on `<state-dir>/lock` and refuses to start if another
process holds it. The lock is only meaningful on a node-local filesystem, which 5C.4 guarantees;
when `--allow-shared-state` puts the state directory on a shared mount the lock is skipped,
because `flock`/`fcntl` locks MUST NOT be used on a shared filesystem.

### 5C.6 Phase 2: ingestion and replication (specified, not built)

* Exactly one writer per final file, enforced by the ingest lease (6.6) carrying a
  monotonically increasing **epoch**.
* The writer builds on node-local fast storage, then performs one sequential copy plus fsync
  into a temp name containing the epoch and the writer id, then publishes with a no-replace
  rename (`link()` then `unlink()`, or `renameat2(RENAME_NOREPLACE)`). A take-over after lease
  expiry therefore never writes the same file as the old writer, and publication never replaces
  a file being read. Publishing a digest that already exists is idempotent: the loser discards
  its temp file.
* Never append to a shared file.
* Forbidden on shared filesystems: lock files opened by several nodes, shared sidecars, shared
  logs or counters, shared temp names, and reliance on `flock`/`fcntl` across nodes. Per-writer
  logs go to node-local directories.
* Readers never block writers: publication is an atomic rename, and a reader keeps the inode it
  opened.
* A hung shared-filesystem read MUST NOT wedge the daemon: every blob read is bounded by the
  existing deadlines (5.5), each connection has its own thread, and the accept loop and the
  allow-list and lockout gates (5B) do no blob I/O.

### 5C.7 Failure modes

| # | Failure | Effect | Mitigation | Test |
|---|---|---|---|---|
| F19 | Lease take-over overlaps the old writer (Phase 2) | Two writers on one path | Temp names include epoch and writer id; no-replace publish; the old writer's rename loses | owed (Phase 2) |
| F20 | Stale temp file after a crash | Clutter, never served (dotfile, `.tmp`) | Names are unique, so a stale file blocks nothing; only the owning pid/epoch removes its own | `concurrent_atomic_writes_to_one_target_never_collide` |
| F21 | Shared mount hangs | Blob reads stall | Per-connection threads, 30 s progress timeout, accept loop independent of blob I/O; the daemon writes nothing there | owed: stalled-read fixture |
| F22 | Operator points state at a shared mount | Concurrent writers if two daemons | Start-up refusal (5C.4) | `prepare_refuses_a_shared_state_dir_unless_overridden` |
| F23 | Two daemons, one state dir | Shared sidecar writes | Exclusive lock (5C.5) | `the_daemon_keeps_state_node_local_and_one_instance_per_state_dir` |

## 6. Control-plane messages

All messages ride the existing gateway link as control frames under capability `iw.store/1`.
They carry no blob bytes. Bodies are JSON; field names are normative. Readers MUST ignore unknown
fields in these messages (forward compatibility); grants are the exception (section 4).

### 6.1 Capability and role

* New capability constant `STORE_V1 = "iw.store/1"` in `crates/iw-core/src/fed_capabilities.rs`,
  grammar `iw.<name>/<major>`, exact-string negotiation like the others.
* New role `Role::Store` and CLI `--kind store` (`crates/iw-cli/src/commands.rs`); registration
  through the node control path (`crates/iw-gateway/src/node_control.rs`) with operator approval.
* The offer/support lists (`join.rs`, `node_control.rs`) gain `iw.store/1`. A peer that did not
  negotiate `iw.store/1` MUST NOT be sent any message in this section and MUST NOT see the new
  topology field (6.3).

### 6.2 Store advertisement

A store sends `store.advertise` after registration, after any change, and as a periodic
refresh (default every 60 s, which doubles as liveness for the index):

```json
{
  "type": "store.advertise",
  "store_id": "whiteale-store-1",
  "endpoints": [
    {"url": "http://10.10.0.5:8744", "kind": "direct", "site": "whiteale", "region": "eu-west"}
  ],
  "fs_id": "beegfs:whiteale",
  "epoch": 17,
  "full": true,
  "entries": [
    {"digest": "<64 hex>", "size": 41234567890, "state": "complete", "scope": ["public"]},
    {"digest": "<64 hex>", "size": 9876543210, "state": "partial", "have": 4294967296, "scope": ["public"]}
  ]
}
```

* `state` is `complete` or `partial`. Only `complete` entries make a store a *holder*.
  `partial` is informational (repair, resume) and MUST NOT be returned as a source.
* `scope` is a list of scope tags (section 9). Absent or empty means `["public"]`.
* `fs_id` identifies a shared filesystem. A node whose configured `fs_id` equals a holder's can
  read the blob in place: distance zero (7.2). It is operator-assigned and compared as an exact
  string; it is a hint, and the client still verifies size and sha256 of the local file.
* `epoch` is a store-local monotonic counter. `full: true` replaces the store's whole entry set;
  `full: false` (delta) adds/updates entries and MAY carry `"removed": ["<digest>", ...]`.
  A gateway that sees an epoch gap on a delta MUST request a full advertisement.
* A store MUST advertise a digest `complete` only after it has verified size and sha256 of the
  stored file itself.

**How the advertisement travels (Phase 1).** The `store.advertise` body rides the store's
`POST /v1/node/register` and `POST /v1/node/heartbeat` as the optional `store` object (a store is a
hardware-only registration, so it holds no link). The reply carries `store`:
`{"accepted":true,"epoch":N}`, `{"accepted":true,"need_full":true}` (epoch gap, 6.2),
`{"accepted":true,"page_pending":{"have":h,"pages":n}}`, or `{"accepted":false,"reason":R}` with R
one of `not_a_store`, `malformed`, `store_id_taken`, `too_many_stores`, `too_many_entries`,
`incoherent`. A refused advertisement never fails the beat. A full set of more than 1,000 entries is
sent as pages: `full:true` with `page` and `pages` (at most 100); the previous set stays live until
the last page arrives. Only a node enrolled with role `store` that negotiated `iw.store/1` may
advertise, and a `store_id` is owned by the first node to advertise it while that node's entries
are live.

**Leave notice (graceful shutdown).** On SIGTERM or SIGINT the daemon sends, once, on its
heartbeat, `{"store": {"type": "store.leave", "store_id": "..."}}` (bounded wait of 5 s) and the
reply is `{"accepted": true, "left": true|false}`. The gateway drops that store from its index at
once, but only if the caller owns the `store_id` (a store or a plain node cannot remove another's);
its standing (section 8) is kept, so a quarantined store that leaves and comes back is still
excluded. A lost or refused notice costs nothing: the entries age out after 3 refresh intervals
exactly as for a crash. `Link::leave` in `crates/iw-store/src/gateway.rs`.

### 6.3 Topology v2 field, capability-gated and paged

The digest advertisement is carried on the topology v2 vertex (`crates/iw-core/src/topology_v2.rs`)
in a **new** field `store` (not in `models`, which is reserved for model identities), emitted
only to peers that negotiated `iw.store/1`:

```json
"store": {"store_id": "...", "epoch": 17, "count": 2500, "page": 0, "pages": 3, "digests": ["<64 hex>", "..."]}
```

* Topology v2 messages are limited to 512 KiB. A digest costs about 68 bytes with quoting and
  comma, so the limit admits roughly 7,000 in theory and about 3,000 once the rest of the vertex
  and sibling vertices are counted. The writer MUST therefore page: at most **1,000 digests per
  page** (about 68 KiB), pages numbered from 0, `pages` the total.
  A reader MUST keep the previous complete set until all `pages` of one `epoch` have arrived and
  MUST ignore a page whose `epoch` differs from the set it is assembling.
* Topology carries digest *presence* (complete holders only). Sizes, scope detail and endpoints
  are not in topology; they come from `store.advertise` to the owning gateway and from the
  `store.holders` answer (6.4).
* A parent gateway that wants to send a node to a child's store asks the child (6.5), because
  grants are issued by the gateway that owns the store's trust relationship.

**As built (Phase 1).**

* *Carrier vertices.* A vertex carries one page, so a gateway reports each page as a vertex of
  its own, `store-<store_id>` for page 0 and `store-<store_id>#<page>` after it (kind `provider`,
  `registeredWith` edge to the root). Only complete digests of live, non-quarantined LOCAL stores
  are reported, sorted and paged at 1,000, at most 60 pages in all. A quarantined store is not
  advertised upward. Remote (child) stores are not re-exported: one hop only.
* *Emission.* `GET /iw/v1/topology?store=1` with the operator credential appends the pages after
  the cached graph is taken, so rotating pages never become last-known vertices or bump the graph
  version; without the query the document is byte for byte unchanged. At most 3 pages (about
  204 KB) ride one document, further capped so the document stays 16 KiB under the 512 KiB limit;
  the window advances every 30 s (`TOPOLOGY_WINDOW_SECS`), so a larger index rotates its pages
  through successive documents. If the budget leaves no room for a page, none is sent (best
  effort; a document already near the limit starves the store pages, never the rest).
* *Capability gating, child side.* A gateway whose local gateway has storage (unauthenticated
  `GET /v1/store/issuer` answers 200) offers `iw.store/1` to its parent
  (`offered_capabilities_for_role_with`). The held-link topology publisher fetches with
  `?store=1` and applies `Graph::for_peer(negotiated)` before every heartbeat; `for_peer(false)`
  drops the carrier vertices and their edges and clears the field on the root, so a parent that
  did not negotiate `iw.store/1` receives the pre-storage document. The "negotiated" bit is
  process-wide (set at each register), which assumes one parent per process.
* *Ingestion, parent side.* The `store` pages of a heartbeat's `status.topology`, on the held link
  or the HTTP heartbeat, are read only from a node enrolled as a `gateway` whose CURRENT
  registration negotiated `iw.store/1`. Pages are assembled per (child, store) by epoch
  (`PageAssembler`); the previous complete set stays until the new one is whole; only digests the
  catalog pins are kept; a malformed page, or a document that fails `Graph::validate`, is dropped.
  Limits: 32 stores per child, 256 in all, 1,000,000 announced digests in all
  (`MAX_REMOTE_DIGESTS`), 16 pages per document.
* *Liveness.* Any valid page refreshes the store; a remote entry lives 900 s from its last page
  (`REMOTE_TTL_SECS`), longer than the 180 s local TTL on purpose: at the 60-page cap a full
  rotation takes 20 windows (600 s), so the local TTL would flap a large child's holders in and
  out. A child dropped by the stale sweep takes its remote stores with it.
* *Not built.* The parent does not forward a node's grant request to the child (6.5, "or the
  parent forwards"); it names the remote holder and the node asks that gateway. Transitive
  (grandchild) reporting, and per-page integrity beyond the pin filter, are not implemented.

### 6.4 Digest index and `who has`

Each gateway keeps `digest -> [holder]` from: (a) its directly registered stores
(`store.advertise`); (b) child gateways' topology `store` fields (presence only, tagged with the
child). Entries expire when the store's last refresh is older than 3 refresh intervals, or on
disconnect.

Query ("who has sha256:X"):

```json
{"type": "store.lookup", "digest": "<64 hex>"}
```

Answer:

```json
{
  "type": "store.holders", "digest": "<64 hex>", "size": 41234567890,
  "holders": [
    {"store_id": "whiteale-store-1", "site": "whiteale", "region": "eu-west",
     "fs_id": "beegfs:whiteale", "via": "local"},
    {"store_id": "hive-store-1", "site": "hive", "region": "eu-central", "via": "child:hive-gw"}
  ]
}
```

A holder behind a child gateway is `{"store_id", "via": "child:<child node id>", "remote": true}`
with no site, region or fs_id (topology carries presence only, so size and scope cannot be
checked against the pin here; the node verifies the bytes as always). Remote holders are listed in
`GET /v1/store/who-has` but are NEVER a source for a grant: when no local holder exists,
`POST /v1/store/grants` answers `sources: []`, `reason: "no_holder"` plus `remote: [...]` naming
whom to ask, and no grant is signed (the grant is signed by the store's home gateway, 3.1).
Local reputation does not apply to remote holders; the home gateway's standing decides, and it
omits a quarantined store from its topology.

An empty `holders` means no known holder: the client falls back to the origin (7.7). The answer
MUST NOT include grants; grants are issued separately (6.5). `size` is the catalog pin when the
gateway has one, otherwise the holders' size; holders disagreeing with the pin are ineligible and
logged.

### 6.5 Grant-issuing request

Node to its gateway:

```json
{"type": "store.grants.request", "digest": "<64 hex>", "ranges": [[0, 268435455]], "want": 3}
```

* `ranges` is optional (inclusive pairs); absent means a whole-blob grant, which the gateway MAY
  refuse in favour of range grants (open item O11).
* `want` is the maximum number of sources wanted (default 3, gateway cap 8).

Gateway answer:

```json
{
  "type": "store.grants",
  "digest": "<64 hex>", "size": 41234567890,
  "sources": [
    {"store_id": "whiteale-store-1",
     "endpoints": [{"url": "http://10.10.0.5:8744", "kind": "direct"},
                   {"url": "https://store1.example.net:8744", "kind": "direct"}],
     "fs_id": "beegfs:whiteale",
     "grant": "iwg1.<payload>.<signature>"}
  ],
  "grant_expires_at": 1760000300
}
```

* `endpoints` are candidates in the gateway's **preference order**; the client tries them in
  order and keeps the first that answers `HEAD` quickly.
* One grant per source, bound to that source's `store_id`, to the requesting `node_id` (taken
  from the authenticated link, never from the request body), and to the requested range union.
  When `ranges` has several entries the source carries a `grants` list instead of `grant`, one
  per range.
* If the digest is unknown, out of scope for the node, or has no holder, `sources` is empty and
  `reason` is one of `unknown`, `out_of_scope`, `no_holder`.
* The gateway MUST rate-limit grant requests per node (default 30 per minute) and count issued
  grants in its metrics. The client SHOULD renew when 30 s of lifetime remain.
* Grants are issued only by the gateway the node is enrolled with (3.1). For a holder behind a
  child gateway (`via: child:*`), the node is told so by `store.holders` and asks THAT gateway, or
  the parent forwards the request over the link and the child signs; either way the signer is the
  gateway the store trusts, never the asking node's gateway on the child's behalf.
* Phase 1 HTTP form: `POST /v1/store/grants` (body as above, plus optional `prefer`: store ids
  tried first), `GET /v1/store/who-has/<digest>`, `POST /v1/store/report`
  (`{"digest","store_id","kind":"digest_mismatch|short_read|unreachable"}`). The caller sends
  `X-InferWeave-Node: <node id>` and `Authorization: Bearer <node credential>`. Besides `unknown`,
  `out_of_scope` and `no_holder`, `reason` may be `range_required`: a digest whose scope is not
  only `public` is granted by range only, for at most 60 s (4.6, O11). Holders whose advertised
  size or scope differs from the catalog pin are ineligible (F12, F14).

### 6.6 Ingest leases (Phase 2)

Defined here so Phase 1 does not paint into a corner; not implemented in Phase 1.

* `store.ingest.acquire {digest, size, store_id}`: a store asks to download `digest` from the
  origin. The gateway grants it to at most one store per digest:
  `store.ingest.granted {digest, lease_id, expires_at}` (default lease 900 s) or
  `store.ingest.denied {digest, owner}` telling the store to replicate from holders instead.
* `store.ingest.renew {lease_id, bytes_done}` extends `expires_at` by the default lease while
  progress is made. No progress over 2 renew intervals: the gateway MAY let the lease lapse.
* `store.ingest.expire {lease_id}` gateway to store when a lease is revoked or lapsed; the store
  stops new origin requests but keeps its `.part` range files.
* **Take-over:** after expiry the next `acquire` for the digest is granted to the requester. A
  store on the same `fs_id` as the dead owner MAY resume that owner's range files; a store that
  cannot read them starts over. Resumed ranges are trusted only after the final sha256 verifies.
* `store.ingest.done {lease_id, digest}` after verification releases the lease; the store then
  advertises `complete`.

The lease is a liveness device, not a trust one.

## 7. Client algorithm

The client is given a pin `{name, size, sha256}` from the catalog. It never learns size or
digest from a store.

### 7.1 Order of operations

1. If the destination exists and its size and sha256 verify: done (cache hit).
2. If a shared-fs path for the digest is configured and verifies size and sha256: use it in
   place (or link/copy per configuration); done (distance zero, no transfer).
3. Ask the gateway `store.grants.request` (6.5). No sources: go to 7.7.
4. Rank sources (7.2), plan ranges (7.3), fetch (7.4 to 7.6), assemble, verify (7.8).
5. On unrecoverable failure, fall back to Hugging Face (7.7).

### 7.2 Source ranking (seed only)

1. **Distance zero:** the shared-fs hit of step 2 above. No network source ranks above it.
2. **Static order:** same site, then same region, then other, comparing the answer's `site` and
   `region` with the node's configuration. Ties by the gateway's endpoint preference order.
3. **Measured:** once bytes have moved, the exponentially weighted throughput (7.4) replaces the
   static order. Static order MUST NOT override a measurement taken within the last 60 s.

A source with no measurement is probed: its first assignment is one range, and it gets no second
until that one has produced a sample.

### 7.3 Range plan

* Range size defaults to **256 MiB** (as `stage.py`: 8 ranges of 256 MiB for 2 GiB), clamped so
  a blob of at least 1 GiB has at least 4 ranges. The last range is shorter.
* Each range is stored as `<destination>.ranges/<start>-<end>.part` (inclusive end), the layout
  `stage.py` uses, so existing partial downloads resume. `.part` files are `fsync`ed on
  completion and are the only resume state.
* Concurrency: global cap 8 workers (as `stage.py`), per-source cap 4.

### 7.4 Scheduling and reassignment

* Workers pull the next unfinished range from a shared queue, so a faster source takes more.
  Each completed or interrupted read updates the source estimate
  `ewma = 0.7 * ewma + 0.3 * sample`, sample = bytes / seconds over the last `max(2 s, 8 MiB)`.
  The first sample sets `ewma`.
* **Assignment:** an idle worker takes the next range and a source chosen with probability
  proportional to `ewma` among sources below their per-source cap; 10 percent of picks are
  uniform so a recovering source is re-measured. Before any measurement: round robin in static
  order.
* **Hedging at the tail:** when the queue is empty and ranges remain, an idle worker MAY duplicate
  the slowest in-flight range on a faster source (one duplicate per range, duplicate bytes under
  10 percent of the blob). The first to finish wins; the other is cancelled and its `.part`
  deleted.
* **Re-assignment:** a source whose `ewma` is below `0.25 *` the best source for 2 consecutive
  10 s intervals keeps its in-flight ranges but receives no new ones until re-measured.
* A `401` on a range triggers one grant renewal, then a source failure.

### 7.5 Resume

Per range: `saved` = size of its `.part`; if `saved == length` the range is done; if
`saved > length` delete and restart; else request `Range: bytes=<start+saved>-<end>`. This is
`stage.py` behaviour. A process restart resumes from the `.part` files with no coordination.

### 7.6 Failure handling

| Event | Detection | Action |
|---|---|---|
| Holder dies mid-range | reset / EOF before range complete | Keep bytes already in `.part`; resume that range on another source from the saved offset. Mark source failed for 60 s, doubling, max 15 min. |
| Wrong status or `Content-Range` | `status != 206` or `Content-Range` not equal to `(offset, end, total)` | Discard response, do not append; source failure; adverse observation (non-severe). |
| Extra bytes | received more than range length | Delete `.part`; source failure; adverse observation. |
| Wrong bytes | final size/sha256 mismatch (7.8) | Severe (section 8). |
| Slow loris | no progress for 30 s, or `ewma` under 1 MiB/s for 60 s | Abort stream, resume the range elsewhere; source demoted by measurement. |
| `401` | grant rejected | Renew once; if still `401`, source failed (trust or clock mismatch; log it). |
| `403` | grant mismatch | Source failed for this grant; never retry the same grant. |
| `404` | store lost the blob | Source failed for this digest; re-ask the gateway later. |
| `416` | range outside actual blob | Size disagreement; source failed; adverse observation. |
| `503` | overload | Slow source; honour `Retry-After`. |
| No sources left | all failed or empty | Fall back (7.7). |
| `ENOSPC`/`EDQUOT` | local write | Fatal, no fallback (as `stage.py`). |

Bounded retries: at most 4 attempts per range per source and 12 per range overall, after which
the failure is global and the client falls back.

### 7.7 Fallback to Hugging Face

If no source can complete the blob, the client MUST fall back to the existing Hugging Face path
(`repo`/`revision`/`file` from the catalog), keeping the same `.ranges` layout and final
verification. Fallback applies when: no holders, scope forbids stores, all sources failed, or the
store fabric is unavailable (gateway unreachable, `iw.store/1` not negotiated). The store fabric
MUST NOT make staging less reliable than today. A model whose license or privacy forbids the
origin fails closed with no fallback.

### 7.8 Final verification

After assembly, and before the file is made visible under its final name, the client MUST verify
size equals the pin and sha256 equals the pin (`verified()` in `stage.py`; resumable
fetch/verify in `crates/iw-core/src/artifact_cache.rs`). Assembly writes `<name>.part`, then an
atomic rename. On mismatch the client deletes the assembly and retries once from a single source
different from the one that supplied most bytes; if that also mismatches it falls back to the
origin. The pin is the arbiter in every case.

Without per-range hashes, a corrupt assembly cannot be attributed to one source except by the
single-source retry above. Per-range hashes are not in Phase 1 (open item O7).

## 8. Integrity and reputation

* The catalog pin (sha256 and size) is truth. Advertisements, topology and `store.holders` are
  hints.
* A store MUST verify sha256 and size before advertising `complete`, and SHOULD re-verify on a
  schedule (default weekly) and after any storage error.
* A client MUST verify the final blob (7.8). It never trusts a store's `ETag`, `Content-Range`
  total or advertised digest in place of the pin.
* On a mismatch attributable to a source (single-source retry mismatch), the client reports to its
  gateway, which records `Observation::severe("store served bytes not matching pinned sha256")`
  against that store in `crates/iw-core/src/peer_reputation.rs`. This is a **new input**: today
  that module tracks model-output drift only. Severe evidence recommends revocation and never
  performs it (existing module contract).
* Lesser misbehaviour (wrong status or `Content-Range`, extra bytes, inconsistent size, `416` on
  an in-range request, repeated 5xx) is `Observation::adverse(...)`, non-severe.
* A store with a severe observation is excluded from `store.holders` and grant issuing until an
  operator clears it. The gateway MUST log `grant_id`, `store_id` and `digest`.
* A client report is a claim from a node: the gateway SHOULD require two independent nodes'
  severe reports, or one report plus its own verification, before exclusion, so a malicious node
  cannot knock out a good store (open item O8).
* **Corroboration is a gateway flag.** `--store-quarantine-reporters <n>` (1..16, default 1) is the
  number of DISTINCT enrolled nodes whose attributable `digest_mismatch` reports quarantine a
  store. With 2 or more, the first report records adverse evidence only (the store becomes
  `suspect`, stays a holder and keeps being granted); the n-th distinct reporter quarantines. One
  node repeating itself counts once, and a store cannot report itself (`400`). An unattributable
  mismatch (`attributable: false`) never quarantines.
* **Operator clear.** `POST /v1/store/quarantine/clear` with `{"storeId": "..."}` (also accepts
  `store_id`) and the admin secret (`x-inferweave-admin` or Bearer) restores a store to `trusted`,
  forgets the reports that quarantined it (a fresh quarantine needs fresh reporters), and logs
  `store quarantine cleared by operator store=... was=...`. No or wrong secret: `401`; unknown
  store: `404`; a revoked store: `409` (revocation is permanent and is not undone by a clear).
  `GET /v1/admin/store` shows the standing.

## 9. Scope: gated and private models

* Each catalog entry carries `scope`, a list of tags. Absent means `["public"]`.
  `restricted:<name>` marks gated or licensed models; `private:<name>` marks private weights.
* A store is configured with the tags it may hold (`replicates`, default `["public"]`). It
  replicates and advertises only digests whose tags are all within that set. A restricted blob
  MUST NOT be placed on a store not configured for its tag.
* A node is entitled to a set of tags at the gateway. The gateway issues grants only for digests
  whose tags are within the node's set (6.5); otherwise `reason: out_of_scope`.
* Adding a tag to an existing entry is a catalog change that stores MUST act on (stop serving)
  within one refresh interval.
* Licensing and privacy are hard constraints (`docs/specs/routing-preference.md`); nothing here
  weakens them for speed. Fallback to the origin (7.7) for a restricted model uses the node's own
  origin credentials; the store fabric never holds origin tokens for other nodes.
* Which models are restricted is open item O3.

## 10. Replication and repair (Phase 2) and what Phase 1 omits

### 10.1 Phase 2 outline

* **Full replica per store** (decided): every store replicates every digest in its scope.
* A store missing a catalog entry acts as a client: ask for holders, fetch ranges multi-source,
  verify, advertise. Each finished copy becomes a source, so fan-out is a tree.
* **Download once:** one ingest lease per digest (6.6) with take-over on expiry; only the lease
  holder contacts the origin, all other stores replicate from holders.
* **Repair:** a failed periodic verify deletes the blob, drops it from the advertisement and
  re-replicates. The gateway index reports under-replication (fewer holders than stores in scope).
* **Quota and eviction:** per-store quota; evict first blobs removed from the catalog, then least
  recently granted; never the only complete copy; never a blob under an active ingest lease.
* **Relayed path** for nodes with no direct route, via the `iw-tunnel` design in
  `docs/superpowers/specs/2026-10-06-relay-ssh-tunnel-design.md` (an untracked draft at the time
  of writing; confirm its status before any dependency on it).
* Shared catalog for hive (needs sha256 pins, which `models.tsv` lacks).

### 10.2 Phase 1 deliberately omits

Replication, repair, ingest leases, per-range hashes, relayed path, proof of possession of
`node_id`, hive pins, eviction, hedging beyond simple throughput shifting. Phase 1 is: a
read-only store daemon over a configured directory with a sha256 index; the grant primitive in
`iw-core` (section 4); `iw.store/1`, the digest index and the grant endpoint in the gateway; a
multi-source client in `stage.py` with Hugging Face as fallback. Phase 1 changes no behaviour for
peers that did not negotiate `iw.store/1`.

## 11. Failure modes

| # | Failure | Effect | Mitigation | Test |
|---|---|---|---|---|
| F1 | Store dies mid-range | Range incomplete | Resume offset on another source (7.5, 7.6) | owed: two fake stores, kill one mid-transfer |
| F2 | Store serves wrong bytes | Corrupt blob | Final sha256 (7.8), severe observation (8) | owed: flipped-byte store rejected and reported |
| F3 | Store sends more or fewer bytes than the range | Truncation or overrun | Per-range length check, delete `.part` | owed |
| F4 | Slow loris | Stalled range | 30 s progress timeout, re-assign (7.4) | owed: throttled source |
| F5 | Gateway unreachable | No grants or index | Cached grants run to expiry, then fall back (7.7) | owed |
| F6 | Grant expires mid-transfer | `401` | Renew at 30 s left (7.4) | owed; expiry boundary covered by `store_grant` tests |
| F7 | Clock skew gateway vs store | Valid grants rejected or expired ones accepted | Skew tolerance (30 s default); NTP on stores; log both clocks | `store_grant` boundary tests |
| F8 | Stolen grant | Read of that digest/range within 300 s | Short lifetime, node/store binding, TLS (O2), narrowing (4.6) | accepted risk |
| F9 | Issuer key rotated or untrusted | `401` fleet-wide | Config-driven key set with overlap (3.1) | `store_grant` untrusted-key test |
| F10 | Topology digest set too large | Peer drops the message | Paging at 1,000 digests (6.3) | owed: 512 KiB budget |
| F11 | Index stale (store gone) | Grants to a dead store | Expiry after 3 refresh intervals; connect failure is a source failure | owed |
| F12 | Sizes disagree | Wrong plan | Catalog size wins; disagreeing holders ineligible (6.4) | owed |
| F13 | Ingest lease holder dies (Phase 2) | Blob not ingested | Lease lapses, next store takes over (6.6) | owed |
| F14 | Scope violation | Restricted blob on wrong store | Store-side and gateway-side filter (9) | owed |
| F15 | Client disk full | Cannot stage | Fatal `ENOSPC`, no fallback | existing `stage.py` behaviour |
| F16 | Malicious node flags a good store | Good store excluded | Corroboration (8, O8); `--store-quarantine-reporters`, operator clear | built, default 1 |
| F17 | Hostile token sent to a store | Panic or DoS | Size cap before decode; no panic on any input; connection caps (5.5) | `store_grant` garbage/oversize tests |
| F18 | Whole-store loss | Fewer holders | Other full replicas serve; Phase 2 repair | owed |

## 12. Open items for review

* **O1 - First store location.** Whiteale compute nodes are private; a daemon on a login node
  may break cluster policy. Options: (a) a Slurm job running the store, published through a
  tunnel or relay; (b) login node with operator approval; (c) a dedicated host outside the
  cluster mounting BeeGFS. Needs the site operator's decision.
* **O2 - Data-connection transport.** Plain HTTP on a private network, TLS (needs certificate
  provisioning and a client trust path), or SSH-tunneled. Also confirm the reading of "no public
  HTTP server" as "no open endpoint" (1.1).
* **O3 - Restricted models.** Which catalog entries are gated, licensed or private, and who sets
  the tags (section 9).
* **O4 - Trust anchor across federated gateways.** Phase 1 (3.1): a store trusts its home
  gateways' keys, learned from `grantIssuerKeys`, plus explicit operator extras; no auto-trust from
  topology. Alternatives still open: a root key certifying gateway issuer keys (adds a chain to the
  grant), or per-store listing only.
* **O5 - Presenter binding.** Grants are bearer within `node_id`. Whether to require proof of
  possession (the node signs a per-request challenge with its enrollment key) is deferred.
* **O6 - Relayed path.** Via the `iw-tunnel` design
  (`docs/superpowers/specs/2026-10-06-relay-ssh-tunnel-design.md`, untracked draft, may be absent
  from a given checkout): whether bulk reads may use a relay data path, and its rate limits.
* **O7 - Per-range hashes** in the catalog, to attribute corruption to one source and avoid a
  full-blob retry.
* **O8 - Exclusion corroboration** thresholds (section 8). Mechanism built: `--store-quarantine-reporters`
  and the operator clear; the default stays 1 and the right production value is still open.
* **O9 - Version coupling.** The token marker `iwg1`, the `version` field and the domain tag
  `iw-store-grant-v1` move together; confirm a future incompatible change bumps all three.
* **O10 - `issuer` field.** The proposal carries the issuer public key in the token so the
  verifier selects the key and the key is bound into the signature. Alternative: a short key id,
  which needs a key-id registry.
* **O11 - Whole-blob grants.** Whether the gateway may ever issue `range: null` for a 100 GiB
  blob (wider replay exposure) or must always issue per-range grants.
* **O12 - `max_request_bytes` cap.** The 5.1 behaviour of answering a shorter range than asked
  differs from `stage.py` today (strict equality); confirm or drop the cap.
* **O13 - S3 credential model.** Phase 1 uses store-local long-lived keys (5A.1). Alternative:
  the gateway issues short-lived, per-operator S3 key pairs (a store still needs the secret, so
  the gateway would have to hand it to the store over the control plane).
* **O14 - S3 transport.** Same decision as O2; SigV4 over plain HTTP exposes object bytes and the
  signed request to the path (5A.7).
* **O15 - Virtual-hosted addressing** (needs a wildcard name and a configured base domain).
* **O16 - ETag as sha256.** Confirm no required client depends on an MD5 ETag; if one does, an
  MD5 would have to be computed and stored in the index (a second hash pass over every blob).
* **O17 - S3 request cap.** 5A.3 exempts the S3 front end from `max_request_bytes`; confirm, or
  accept that clients must handle shortened `206` responses.
* **O18 - Integration with specs 27 and 64.** Whether a store is a tier of the site-connector cache
  and a source kind of a dynamic-node artifact (spec 64 section 5) is undecided; this version
  integrates with neither.

## 13. Compatibility

Additive and capability-gated. A peer that did not negotiate `iw.store/1` is sent no message of
section 6, never sees the topology `store` field or `grantIssuerKeys`, and behaves as before. A
gateway without storage answers the register and heartbeat without the `store` member and offers
no store role. The `iwg1` marker, the `version` field and the domain tag `iw-store-grant-v1` move
together (O9); an incompatible change names a new capability major, `iw.store/2`. Forward
compatibility inside `iw.store/1`: readers ignore unknown members of the control messages of
section 6; a grant is the exception and is read strictly (4.2). The staging client falls back to
the origin whenever the fabric is unavailable, so adopting a store cannot make staging less
reliable than it was (7.7).

## 14. Security, privacy and deployment impact

- **No open endpoint.** Every store request carries a gateway-signed grant or a store-local S3
  signature; a listener is loopback by default, never a wildcard bind, and closes peers outside its
  allow-list before reading a byte (5B). The reading of "no public HTTP server" as "no open
  endpoint" is open item O2.
- **No secret on the data plane for nodes.** A store holds only public keys for grants. Its S3
  access keys are long-lived store-local secrets (O13).
- **Prompt privacy and the inference path.** Nothing here carries a prompt, a completion or an
  inference byte; the gateway link carries control messages only (1.1), and the gateway does not
  become a byte path for blobs.
- **Deployment.** The store daemon is a persistent service and follows the repository's rules:
  Docker Engine and Docker Compose for a persistent store, Apptainer inside a Slurm allocation. No
  deployment substrate is added.
- **Shared filesystems.** The daemon is read-only on blob directories and keeps all state
  node-local (5C), because concurrent writers on a cluster filesystem hang it for every client.
- **Not weakened:** owner priority, the GPU watchdog and rescue, quarantine and recovery (a store
  quarantine is a new instance of the same pattern, section 8) and Slurm scheduler authority.

## 15. Required tests

Recorded `owed` by `P5-T36` (Phase 1) and `P5-T37` (Phase 2); see the task cards and
`contracts/canonical-task-graph.json`. The reference implementation carries tests for the
following controls, named here so a reviewer can find them; none has had independent review and
none is recorded `proven`:

- `iw-core` `store_grant`: transcript known answers, the verification order, the boundaries of
  skew and expiry, untrusted key, garbage and oversize tokens;
- `iw-store` `data_plane`, `hardening`, `s3`, `gateway_link`, `gateway_tls` and the shell
  interoperability script `s3_interop.sh` (a real S3 client against the front end);
- the unit tests of the topology paging, the page assembler and the quarantine standing;
- `deploy/farm/artifacts` `test_stage.py`, `test_stage_sharedfs.py`, `test_stage_inplace.py`
  and the end-to-end `e2e_store.py` and `e2e_stage_runner.py`;
- the failure-mode tests of sections 5C.7 and 11 that name a test; every row that says `owed`
  has none.

What no test has done: moved a real 100 GiB blob across two clusters through a store; served a
production workload; run against a shared filesystem under fault (F21 is owed); exercised
corroborated quarantine with more than one real reporter; or been reviewed by anyone other than
the author. Operational measurement is pending: the farm staging figure quoted in section 1 is the
motivating observation, not a measurement of this system.
