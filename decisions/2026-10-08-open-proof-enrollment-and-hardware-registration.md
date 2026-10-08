# Open proof enrollment and hardware-only node registration — 2026-10-08

**Status:** Proposed  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-08  
**Authorizes:** On acceptance: the wire contract of `specs/47_NODE_JOIN_AND_HARDWARE_REGISTRATION.md`
and implementations of it in the Rust and Go gateways. It does **not** authorize deploying either
gateway, enabling the open enrollment policy on any deployment, or any change to routing, trust or
placement.  
**Relationship:** Extends `specs/03_NODE_BOOTSTRAP_DEPLOYMENTS.md` ("Token-free proof enrollment",
unchanged) and `specs/45_PROTOCOL_V1.md` (minor release 1.1.0); supersedes no record. No resolved
decision in `decisions/DECISIONS_REQUIRED.md` is reopened.

## Context

Both gateways need to learn what hardware a host has before any model is deployed to it, so that
an operator can see the machine and later instruct it. Today a node can register only with models
and an endpoint. Separately, tokenless proof enrollment is specified in prose only, so the two
gateways could implement different wire shapes and different signed bytes, and a node would work
against one and fail against the other without any error pointing at the cause.

## Decisions

1. **One optional `hardware` member** on `POST /v1/node/register`: a versioned JSON object the
   gateway stores verbatim and never uses for routing or authentication. The gateway validates
   only "object with an integer `version`, at most 65536 compact bytes". Alternative rejected:
   a strictly typed schema enforced by the gateway, which would refuse a newer node's report at an
   older gateway and make a probe bug into a registration failure.
2. **Hardware-only registration is valid**: empty `models`, `endpoint` and `deployment`. It is
   recorded and listed, never routable, never dialled. Alternative rejected: a separate endpoint,
   which would need its own authentication, freshness and heartbeat and would double the surface.
3. **`assignments: []`** reserved in the response so the later gateway-to-node instruction channel
   needs no breaking change. Alternative rejected: adding the member when first needed, which
   leaves old nodes unable to tell "no instructions" from "gateway does not support them".
4. **Tokenless enrollment is mandatory protocol** with the transcript pinned byte for byte and
   known answers, because a transcript is the one part where two correct-looking implementations
   silently disagree.
5. **Open registration is permitted**, not required: a gateway MAY accept proof enrollment from
   any key, at the lowest trust tier, and only for the role `node`. A challenge for any other role
   (`gateway`, `edge`, ...) is `400 bad_request`; privileged roles stay operator-issued. Alternative
   rejected: letting a proof earn any well-formed role, which would let a free identity register
   as a gateway.

6. **A tokenless credential cannot make a node routable.** A node whose credential was earned only
   by proof may register hardware-only and heartbeat; a non-empty endpoint or any models is
   `403 forbidden`, and a proof never replaces an operator-issued credential (`403`). Routability
   requires operator-issued enrollment. Rationale: a routable node receives other people's
   prompts, so open registration must not let a stranger choose where traffic goes. Alternative
   rejected: relying on the lowest trust tier alone, which limits weight but still lets a stranger
   receive traffic.

## Consequences and the tension recorded

Open enrollment makes a node identity free to mint. The peer-trust design in the reference
repository relies on identity scarcity for bans and quarantine to bite. This record does not
resolve that: it permits the policy for the in-house lab deployment and names the mitigations
(section 6 of spec 47). The decision owner should confirm the lab-only scope before any
internet-reachable gateway enables it.

## Measured basis

- The reference implementation was read at InferWeave/inferweave `2c98035`
  (`crates/iw-core/src/signature.rs`, `proof_enrollment.rs`, `crates/iw-gateway/src/server.rs`,
  `node_control.rs`).
- The known answers were computed with a dependency-free Ed25519 in `conformance/node_join.py`,
  checked with OpenSSL 3.0.13, and reproduced by a throwaway binary calling the reference
  implementation's `proof_transcript` and `ed25519-dalek`; all three agree for both cases.
- Reading `server.rs` shows `/v1/node/proof` minting its credential in a store that
  `/v1/node/register` does not consult, `deployment: ""` refused at deserialization, and the proof
  store held in memory. None of these was exercised by running the gateway.

## Proof status

Every required test is `owed` by `P5-T33` and `P5-T34`.
