# 67 — Site attestation: a gateway attests the grant it enforces to a paid runtime

## Status

**Accepted for implementation; implementation and operational proof `owed`.** Accepted by the decision
owner on 2026-11-01 in `decisions/2026-11-01-gateway-served-site-attestation.md`, which records the
incident, the options and the six answers this document makes normative. Canonical task `P5-T39`.
Additive to InferWeave Protocol 1.1.0: a registration that does not negotiate `iw.site-attestation/1`
behaves exactly as before. Accepted for implementation does not authorize deployment, enrollment,
key issuance, spending or production traffic. The Rust gateway owns grant evaluation, enforcement and
issuance (owner decision 2026-11-01; `D-002` is not amended and no Go-gateway exception is granted).

The key words MUST, MUST NOT, SHOULD and MAY are used as in RFC 2119.

## 1. Purpose

A **paid runtime** is a node whose model costs its owner money per use (a vendor API behind a System
One runtime). Its owner must be able to start it anywhere: under a Slurm gateway that schedules and
restarts instances, under a container supervisor, or by hand against any other gateway. Whatever
gateway it joins, the runtime must advertise the paid model only while that gateway demonstrably
restricts the model to the owner's grant. This specification defines how the gateway says so, over
the registration the node already holds, so that no operator, third host or schedule is involved.

## 2. Terms

- **Grant**: the owner's statement of who may use a paid model: `{model, subject}` (one permitted
  subject, the owner's identity). **Grant digest** `grant_sha256`: the lowercase hex SHA-256 of the
  UTF-8 bytes of the JSON text `{"model":"<model>","subject":"<subject>"}`: exactly those two keys in
  that order, no whitespace, strings escaped as RFC 8259 requires and nothing else. The owner
  configures the digest on the site; a gateway computes it from its own policy entry.
- **Enforcing a grant**: for the model, the gateway refuses every request whose authenticated subject is
  not the grant's subject, before admission and before any dispatch to a node, and never falls back to
  another path (invariants 5 and 7). A gateway MUST NOT attest a grant it does not enforce.
- **Paid-grant policy**: the gateway's private, operator-supplied table of grants it will enforce. It is
  absent, loaded or invalid; invalid is treated as absent, never as the last good table.
- **Site**: the paid runtime's node process. **Trusted gateways**: the gateways whose attestations the
  site accepts (section 6).

## 3. Capability

`iw.site-attestation/1` is offered by a node in the `capabilities` array of `POST /v1/node/register`
(spec 47 section 2.1). A gateway puts it in force for that registration only when its paid-grant
policy is loaded and at least one grant is present. A gateway that cannot evaluate a grant MUST NOT
list it. Negotiation is per registration and repeated on every re-registration; a capability in an
unrelated registration cannot enable it.

## 4. Wire

**Request.** While the capability is in force, a node MAY add to its heartbeat request

    "siteAttestation": { "rollout": "<token>", "model": "<model>", "grant_sha256": "<64 lowercase hex>" }

`rollout` is a token of 1 to 128 characters from `[A-Za-z0-9._:-]`; `model` is a model name as in the
registration; `grant_sha256` is exactly 64 lowercase hex characters. Any other shape is refused
`malformed_request`. The three values are echoed and compared; they are never an input to whether the
policy is loaded, default-deny or granted.

**Response.** The heartbeat response carries exactly one of:

    "siteAttestation": { "version": 1, "rollout": "...", "model": "...", "grant_sha256": "...",
                         "policy_sha256": "<64 hex>", "node_id": "...", "gateway_id": "...",
                         "issued_at": <unix seconds>, "expires_at": <unix seconds> }
    "siteAttestationRefused": "<code>"

`policy_sha256` is the digest of the gateway's loaded paid-grant policy. `expires_at - issued_at` is at
most 3600. Refusal codes are a closed set: `policy_not_loaded`, `grant_not_enforced`,
`model_not_granted`, `not_default_deny`, `not_enrolled`, `malformed_request`. A refusal is never an
empty success, and a heartbeat that carries no request gets neither member.

## 5. Issuance

A gateway issues an attestation only when every condition holds, and refuses with the first that fails
in this order:

1. the request is well formed (`malformed_request`);
2. the registration has the capability in force and a fresh heartbeat (otherwise nothing is issued);
3. the registration's credential was enrolled by an operator of this gateway; a key-only identity earns
   nothing (`not_enrolled`; spec 64 section 3);
4. the paid-grant policy is loaded (`policy_not_loaded`);
5. the policy has an entry for `model` (`model_not_granted`);
6. that entry's grant digest equals the presented `grant_sha256` (`grant_not_enforced`);
7. the gateway currently enforces default-deny for `model` (`not_default_deny`).

`node_id` is the authenticated registration's id (an instance id; spec 64 mints one per boot) and
`gateway_id` is the gateway's own id. Any number of enrolled instances may be attested for the same
grant. Each issuance is logged with node, model and grant digest and never with a credential.

## 6. The site

The site MUST NOT advertise the paid model in its registration until it holds an attestation, and MUST
withdraw the advert when its attestation expires or is refused. It registers first without the paid
model, requests an attestation in its heartbeat, adds the advert on success, and re-requests before
`expires_at` while the link is held. It accepts an attestation only if all of the following hold:

- it arrived on the registration that negotiated the capability;
- `node_id` equals its own instance id, `grant_sha256` equals the digest its owner configured, and
  `rollout` and `model` equal its own;
- `gateway_id` is a trusted gateway: by default the parent its identity file pins, otherwise a list of
  authenticated gateway ids the owner configured, or an explicit `any`;
- `issued_at <= now < expires_at` and `expires_at - issued_at <= 3600`.

On refusal, silence or an unacceptable attestation the site keeps the model unadvertised and logs the
reason at least every 15 minutes. It MUST NOT fall back to an older attestation or to a file while the
capability is in force. A file attestation remains accepted only from a parent that does not offer the
capability, for migration, until the owner declares migration complete in `OPEN_GATES.md`.

An attestation is a gateway reporting its own state. It protects the owner against a mistake or a
stale policy on a trusted gateway, not against a gateway that lies; `any` makes the owner accept every
gateway's word and MUST be an explicit configuration, never a default.

## 7. Credentials

The attestation path carries no vendor or owner credential. How an instance obtains the credential of
its paid vendor is outside this specification, except that a gateway which schedules or spawns a paid
runtime MUST NOT be able to read it.

## 8. What this does not do

It does not provision or schedule paid runtimes (spec 64), does not price or meter them, does not make
`any` safe, and does not change how a gateway authenticates a node (spec 47). It does not replace the
gateway's own per-key allow-lists (spec 63); it states that, for a paid model, an allow-list of exactly
the grant's subject is in force.

## 9. Compatibility

An older node or gateway ignores the unknown capability and the unknown heartbeat members (spec 47
section 2.1). A site whose parent does not offer the capability keeps the file path until migration is
declared complete.

## 10. Required tests

Each must fail if its control is removed (invariant 40):

- the capability is listed only with a loaded, valid paid-grant policy, and an invalid policy is absent
- every refusal code is produced by exactly its condition, in the stated order, and a refusal is never an
  empty success
- an attestation is issued only to an enrolled, fresh registration; a key-only identity gets `not_enrolled`
- two instances with different node ids are each attested for one grant, and a copy of one is refused by
  the other, by another gateway id and by another grant digest
- the gateway refuses a request for the model from any subject other than the grant's before admission
- the site does not advertise the paid model before an attestation, withdraws it at expiry and on refusal,
  and re-requests before expiry with the link held
- the site never falls back to an older attestation or a file while the capability is in force
- `any` is accepted only when configured explicitly
