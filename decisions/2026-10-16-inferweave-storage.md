# InferWeave Storage: a distributed content-addressed model store — 2026-10-16

**Status:** Proposed  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-16  
**Authorizes:** On acceptance: the contract of `specs/65_INFERWEAVE_STORAGE.md` Phase 1 (the
`store` role, the `iw.store/1` capability, the signed `iwg1` grant, the native and S3 read-only
front ends, the digest index, quarantine and the multi-source stager) and its reference
implementation in the Rust gateway, the `iw-store` daemon and the staging client. It does **not**
authorize deploying a store on any cluster, exposing any listener beyond a private network or
loopback, running a store on a login node, using the S3 front end for production tooling, or any
Phase 2 behaviour (ingest, replication, TLS, grant forwarding across federation).  
**Relationship:** Extends `specs/20_NODE_AUTOCONFIG_DISCOVERY.md` "Model fetch" with a second
source, `specs/40_NETWORK_TOPOLOGY_GRAPH.md` with a presence-only `store` field and
`specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md` with a hardware-only role. Preserves the rule
that the gateway link carries control only and is never the byte path for blobs. Supersedes no
record. No resolved decision in `decisions/DECISIONS_REQUIRED.md` is reopened.

## Context

Nodes pull 10 to 100 GiB model blobs from the origin one node at a time, about 20 minutes for
30 GiB per farm node, repeated per node and subject to the origin's rate limits and gating
(an observation of the farm cluster, not a measurement of the proposed system). Clusters differ
in what they can expose: the compute nodes are private, a shared filesystem (BeeGFS, Quobyte) holds
the catalog once, and another cluster reaches the first only through one fixed egress address. A
shared cluster filesystem has also hung for every client when two processes wrote one file, so the
store must be able to sit on one without ever being a second writer.

## Decisions

1. **Control on the link, data off it.** The gateway link carries advertisements, index queries,
   grants and (Phase 2) leases. Blob bytes flow on a separate node-to-store HTTP connection.
   Alternative rejected: bulk frames on the link, which cost +33 percent as base64, are counted by
   frame not byte, and stall heartbeats and live inference streams.
2. **Stateless signed grants.** A gateway signs a short-lived (at most 300 s), digest-, range-,
   node- and optionally store-bound Ed25519 grant over a length-prefixed transcript with a domain
   tag; a store holds public keys only. Alternative rejected: a per-use nonce or a store calling the
   issuer, which would make every remote store stateful. Replay within the lifetime is accepted
   and stated (spec 65 section 4.6).
3. **A store trusts its home gateways' keys, learned, plus operator extras**, and never keys seen
   in topology, which is itself a peer's claim. Alternatives (a root key certifying gateway keys;
   per-store listing only) stay open (O4).
4. **Pins are truth.** The catalog's size and SHA-256 decide; advertisements, topology and holders
   are hints; the client verifies before a file is visible and falls back to the origin. A store
   advertises `complete` only after verifying the file itself.
5. **Network exposure is refused by construction.** A listener is loopback by default; a wildcard
   bind has no override; a non-loopback bind requires an allow-list; a public bind requires explicit
   flags and serves public-scope blobs only; peers outside the list are closed before a byte is
   read; the peer is the TCP peer, never a header. Authentication is the second line, not the only
   one. Alternative rejected: relying on grants alone, because a firewall or forwarding mistake must
   not matter.
6. **A serving daemon is read-only on blob directories** and keeps all state node-local, refusing a
   shared filesystem for its own writes (spec 65 section 5C). Alternative rejected: a shared sidecar
   index or lock file, which is the hazard the rule exists to prevent.
7. **An S3 front end is a second, read-only front end** with store-local long-lived access keys,
   scoped to buckets and prefixes. It never reaches the gateway and is not how a node bypasses
   scope. The ETag is the SHA-256, not an MD5 (O16). Alternative recorded: gateway-issued
   short-lived S3 credentials (O13).
8. **Quarantine is evidence-based.** A client's digest-mismatch report is a claim; the number of
   distinct enrolled reporters needed to quarantine is a gateway flag (default 1), severe evidence
   excludes a store from holders and grants until an operator clears it, and revocation stays
   permanent. The right production threshold is open (O8).
9. **Phase 2 is specified, not built:** ingest leases with an epoch and no-replace publication,
   replication and repair, quota and eviction, a write path that publishes only a pinned blob, a
   rendezvous with no inbound port, TLS, and grant forwarding across federation.

## Consequences

Positive: a catalog is held once per site and any node pulls from the best measured holder; no
public endpoint exists; a stolen grant reads one public, immutable blob for at most 300 s.
Negative: until TLS exists a non-private bind serves public blobs over plain HTTP and the grant is
visible to the path; the S3 keys file holds plaintext secrets; a parent cannot yet obtain a grant
for a child's store on a node's behalf. Operational: a store daemon, a grant-signing key file on
the gateway, an allow-list per store and a keys file are new operator surfaces.

## Requirements affected

- IW-STORE-001 (new)
- IW-STORE-002 (new, required later)

## Proof status

The reference implementation carries unit, loopback HTTP, TLS-gateway, S3 client interoperability
and end-to-end stager tests (spec 65 section 15). None has had independent review; no blob has
moved between two real clusters through a store. Every required test is **owed** by `P5-T36` and
`P5-T37` and recorded in `OPEN_GATES.md`.

## Rollback/revisit trigger

A measured case where a gateway-signed grant is too weak (a stolen grant read a gated blob) revisits
decision 2 and brings forward presenter binding (O5). A deployment that must expose a store on a
public address before TLS exists revisits decision 5. A site that cannot allow any inbound port
brings forward the Phase 2 rendezvous. A required S3 client that depends on an MD5 ETag revisits
decision 7 (O16).
