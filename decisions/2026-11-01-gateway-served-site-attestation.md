# The gateway serves a paid site its own attestation — 2026-11-01

**Status:** Accepted for implementation (Option 2, with the six answers below and the Rust gateway as
issuer). Accepted by the decision owner on 2026-11-01, the same day it was proposed. Option 1 (a
scheduled renewer) was withdrawn the same day.  
**Decision owner:** InferWeave operator  
**Date:** 2026-11-01  
**Authorizes:** building `iw.site-attestation/1` in the Rust gateway and node (`specs/67_SITE_ATTESTATION.md`,
task `P5-T39`, feature `IW-SITEATT-001`). It does **not** authorize: any deployment, enrollment, key
issuance, spending or production traffic; retiring the Go gateway's existing paid-policy path; or
making `any` a default trusted-gateway setting.  
**Relationship:** `discloses` an operational fact no specification states (below). It amends no
record and no invariant. It decides one change of mechanism (Option 2) and amends no invariant.

Code citations are to `InferWeave/inferweave@5ff5c633` (`deploy/whiteale/jev/`) and
`metabolomics-us/inferweave-gateway@6c22b6db`, read in this change; the incident figures in
"Measured basis" are from the production logs of 2026-11-01 and were read, not reconstructed.

## What exists and no specification describes

A paid System One model ("Jev") is served from a Slurm job on Whiteale and advertised through the
public gateway on zapp. Searching this repository (`jev`, `paid-systemone`, `owner grant`,
`default_deny_paid`, `policy-ready`) finds no specification of it; the only hit for "owner grant" is
spec 56 line 44, which says an observation carries none. What runs today is therefore **an
implementation choice made where the specifications are silent**, and is recorded here as such.

As built (`install_public_policy.py`, `validate_attestation.py`, `run-job.sh`, `peer-loop.sh`):

1. The public gateway loads a private policy file that maps a paid model to exactly one permitted
   subject and answers **default-deny for paid models**. It reports its loaded state on a
   loopback-only administrative endpoint (`/v1/admin/paid-systemone-policy`, pinned to
   `127.0.0.1:8292`, bearer credential).
2. An **attestation** is a small file `{version, rollout, model, source_sha256, policy_sha256,
   expires_at}` made by `install_public_policy.py attest` **on the gateway host**. It is produced
   only when the running gateway reports `loaded`, a `policy_sha256` equal to the digest of the
   policy file, `default_deny_paid`, the model present, and exactly one subject for it. It expires
   3600 s after it is made.
3. The Whiteale job refuses to start, refuses to advertise and refuses to (re)join the parent unless
   `validate_attestation.py` accepts that file for its rollout, model and source digest. The check
   runs at job start, before advertising, and **at the top of every join attempt in the supervisor
   loop; it is not repeated while a link is held** (`peer-loop.sh`, loop head). An expired file
   therefore never drops an established link; it prevents the *next* join.
4. The file reaches Whiteale only by an operator copying it. Neither direct path between zapp and
   Whiteale is usable today: from Whiteale to zapp, SSH on port 22 timed out; from zapp to Whiteale,
   strict host-key checking refused for want of a pinned key (not shown to be unreachable). A third
   host with verified access to both is the only path in use.

The attestation is thus an operator's assertion, re-made by hand or by a scheduled job, that the
gateway currently enforces the owner grant.

## Measured basis

Incident, 2026-11-01, gateway restarted at about 17:22 UTC to deploy `510cfef`:

| time (UTC) | event (Whiteale peer log) |
| --- | --- |
| 17:22:15 | link to the parent dropped (status 1): `502 internal_error: unspecified control error` |
| 17:22:17 | `not being advertised: public policy attestation is expired or implausibly long-lived; waiting` |
| ~17:23 | a fresh attestation was installed, but it named rollout `r2` (see below) and was refused |
| 17:28:17 | `attestation valid again; joining the parent` after a file for the running rollout `r5` |
| 17:28:18 | the parent registered `node_iw-whiteale-jev`, 1 model: **6 min 3 s from drop to serving** |

Cause of the second row's delay: the gateway host kept a copy of the rollout request that named an
earlier rollout (`r2`); `attest` accepted it because it only checks the gateway's policy, and the
site correctly refused a file for the wrong rollout. A deploy after the fix (`deploy-gateway.sh`,
`renew_attestation.py`, which takes the request from Whiteale) re-attested in 7 s (19:11:29 to
19:11:36) and the link was held again within the verification window.

No figure here is quoted from another document.

## Context

The attestation is a fail-safe and should stay one: the paid model must not be advertised on a
stale belief about what the gateway enforces. The cost is operational: every gateway restart
requires a person or a scheduled job on a third host to remake and copy the file, or the site
waits. The trust relationship is also inverted from the natural one: the party whose state is being
attested (the gateway) is the one that does nothing, while an operator copies its report to the
party that checks it.

## Options

1. **Status quo, operated.** Keep the operator-copied file. Add a scheduled renewer on the host that
   reaches both (cron, a systemd timer, or a Compose service with a restart policy). Needs no
   gateway or node change. Keeps a standing job and a standing credential on a third host.
2. **Gateway serves the attestation to the site (Option B).** The site asks its parent for a fresh
   attestation over the authenticated channel it already uses to join (spec 63/64 identity). The
   gateway answers with the same document **only if** (a) the requesting identity is the one the
   owner grant binds to the model, (b) the policy is loaded, default-deny and has exactly one
   subject for the model, and (c) the request's rollout and source digest are well formed; it sets
   `expires_at` at most 3600 s ahead and logs the issuance. The supervisor's check fetches a new
   file when the current one is near expiry. No third host, no copy, no schedule.
3. **Lengthen the expiry.** Rejected: it widens the staleness window the check exists to bound and
   removes none of the copying.

## Decision

Accepted by the decision owner on 2026-11-01:

1. **Option 1 was adopted, then withdrawn by the owner the same day** ("we will not be doing the cron
   line ... this needs to be a built in support of the protocol"). No scheduler is to be installed.
   The renewer (`renew_attestation.py`) and `deploy-gateway.sh` remain as tools an operator may run;
   they are not the intended mechanism. Until Option 2 exists, an unplanned link drop with an expired
   attestation leaves the site waiting until someone renews, and a planned gateway deploy re-attests as
   part of the deploy. This interim exposure is accepted by the owner.
2. **Option 2 is accepted for implementation** with the six answers below as written, and with **the
   Rust gateway as the sole issuer and enforcer** (owner decision, 2026-11-01: "all to rust"). `D-002`
   is not amended and no exception is granted to the Go gateway. The Go gateway's existing paid-policy
   path stays as it is, as the legacy path the file attestation serves, until a separate decision
   retires it. Implementation is `P5-T39`; deployment is not authorized by this record and needs the
   proofs in `OPEN_GATES.md`.
3. **Option 3 (a longer expiry) is not adopted.**

## Open questions Option 2 must answer before it can be accepted for implementation (answered below, revised for the owner's any-gateway requirement, and accepted)

1. **Binding.** The policy today maps a model to a permitted *subject* (an owner identity). The
   requesting party is a *node* with a node credential. What binds the node to the grant (a node id
   in the policy, or the owner's subject on the node's enrollment)? Without an explicit binding any
   enrolled gateway-role node could request it.
2. **Does the site's own request influence the answer?** It must not: rollout and source digest are
   echoed for the site to compare, never used to decide what is true.
3. **Replay and scope.** Whether the attestation is bound to the requesting node id and the request
   digest, so a copied file is useless elsewhere.
4. **Failure behaviour.** If the gateway cannot answer (policy not loaded, endpoint down), the site
   must keep waiting and say why, as it does today; it must never fall back to an older file
   (invariant 7).
5. **Unauthenticated parents.** A site joining a parent that is not the policy-bearing gateway must
   not accept an attestation from it.

## Consequences

Positive: a restart no longer needs an operator or a third host; the trust direction matches the
state being reported; one fewer standing credential. Negative: new surface on the gateway and a
binding between node identity and owner grant that does not exist today; the site now depends on the
parent to start (it already does, to be reachable at all). Migration: the file path remains
accepted until the new path is proven, so Option 1 stays available as the fallback.

## Requirements affected

- Invariant 7 (fallback never silently weakens a hard constraint): a failed fetch must not fall back
  to a stale or absent check.
- Invariant 40 (a control is proven only by a test that fails when the control is removed): see
  `OPEN_GATES.md`; every control below is owed.
- A new feature ID and canonical task are required before implementation (the validator requires
  both); none is proposed here.

## Rollback/revisit trigger

Revisit if issuance under Option 2 is ever requested by an identity the grant does not name, if a
restart still leaves the site waiting longer than the time to re-register its node, or if the
binding in open question 1 cannot be stated without enumerating nodes.

## Requirement added by the owner, 2026-11-01

A paid runtime must be able to join **any** gateway, not one named gateway. A gateway that schedules
nodes (a Slurm gateway under spec 64) may start any number of instances of it and keep them alive,
and a container supervisor may spawn and restart them and have them join any other gateway. Such
instances have per-instance, short-lived node ids (spec 64: an id is minted per boot, at most 50
characters) and are enrolled by whichever operator runs the gateway they join. Consequences for this
record: no stable node id can be a binding; "exactly one node per paid model" is wrong; the site
cannot pin one parent; and nothing may need a person or a third host to keep a restarted instance
attested. The answers below replace the first draft, which assumed one parent and one named node.

## Answers and protocol shape (accepted by the owner, 2026-11-01; normative text is `specs/67_SITE_ATTESTATION.md`)

These use the mechanisms the protocol already has: the negotiated capability offer of spec 47
section 2.1, registration authenticated by `nodeId`, `role`, `credential` and `connectionId`, the
heartbeat as the node's periodic authenticated request, and the operator enrollment of spec 64
section 3 (only an operator-enrolled credential is provisioned or trusted with a grant).

**What is attested.** Not "this node", but "this gateway enforces *this grant* for this model". A
**grant** is the owner's statement of who may use the paid model: `{model, permitted subject}`. Its
digest, `grant_sha256`, is computed over a canonical form and is configured on the site by its owner.
Any gateway that hosts the site must carry an entry whose digest is the same, and the attestation says
so. Instance ids, replica counts and restarts do not change the grant.

**Shape.** A capability, `iw.site-attestation/1`. A node offers it at registration; a gateway puts it
in force only when it can evaluate a grant. While in force, the node may send
`siteAttestation: {rollout, model, grant_sha256}` in its heartbeat request, and the response carries
either `siteAttestation: {version, rollout, model, grant_sha256, policy_sha256, node_id, gateway_id,
issued_at, expires_at}` or `siteAttestationRefused: <code>` from a fixed list (`policy_not_loaded`,
`grant_not_enforced`, `model_not_granted`, `not_default_deny`, `not_enrolled`, `malformed_request`). A
refusal is never an empty success. Absent the capability, nothing changes on the wire.

**Order of operations.** The paid advert is added to the registration only **after** an attestation
has been received, and is kept current by re-requesting before `expires_at` while the link is held.
This closes a gap in the as-built design, which checks only at join. A restarted or newly scheduled
instance repeats the sequence by itself; nobody renews anything.

1. **Binding.** By grant and enrollment, not by node id. The gateway issues only to a registration
   whose credential an operator of that gateway enrolled (so a key-only identity earns nothing, as in
   spec 64), and only if the gateway's own policy entry for the model has the same `grant_sha256`
   the node presented. Any number of enrolled instances may carry the same grant. What stays "exactly
   one" is the permitted subject per grant, as today. The first draft's node id in the policy is
   withdrawn because a scheduled replica cannot have a stable id.
2. **The request does not influence the answer.** `rollout`, `model` and `grant_sha256` are validated
   for format (a bounded token, a bounded token, 64 lowercase hex) and compared against what the
   gateway enforces; they are never an input to whether the policy is loaded or default-deny. The
   gateway echoes what it enforces and the site compares.
3. **Replay and scope.** The attestation carries `node_id` (the instance), `gateway_id` and
   `grant_sha256`; the site accepts it only if all three match its own instance id, a gateway it
   trusts (answer 5) and its own grant. It is issued only to a live registration and lasts at most
   3600 s, so a copy is useless to another instance, another gateway, another grant or later.
4. **Failure behaviour.** On refusal or no answer the site keeps the paid model unadvertised and says
   why, as now. It never falls back to an older attestation or to a file while the capability is in
   force (invariant 7). The file path stays only for a parent that does not offer the capability, for
   migration, and goes when the owner declares migration complete.
5. **Which gateways the site trusts.** The owner configures the site with the gateways whose
   attestations it accepts: by default the parent its identity file pins, or an explicit list of
   authenticated gateway ids (spec 63), or an explicit "any". The record states the limit plainly: an
   attestation is a gateway reporting its own state, so it protects the owner against a *mistake* or a
   stale policy on a trusted gateway, never against a gateway that lies. "Any" therefore means the
   owner accepts every gateway's word, and should be a deliberate choice, not a default.
6. **(New) The paid credential.** A gateway that schedules or spawns a paid runtime must not be able to
   read the owner's vendor credential. How a replica obtains it (an owner-held secret mounted into the
   instance, or fetched with the grant) is **not decided here**; this record only requires that the
   attestation path never carry it.

**Who issues it.** The Rust gateway, alone (owner decision, 2026-11-01). Spec 47 says the capability offer
is "used by both the Rust and Go gateways", and the capability stays gateway-neutral on the wire, but only
the Rust gateway evaluates a grant, enforces it and issues the attestation. The Go gateway does not
negotiate `iw.site-attestation/1`, so a paid runtime that joins a Go gateway keeps the file path. This is
consistent with `D-002` as amended on 2026-10-12 and creates no exception.

**Done in this change:** the feature ID `IW-SITEATT-001`, the canonical task `P5-T39`, and the normative
contract in `specs/67_SITE_ATTESTATION.md` (capability, grant digest canonical form, refusal codes,
issuance order, site rules). **Still owed (invariant 40):** the implementation and every proof in
spec 67 section 10 and `OPEN_GATES.md`, each of which must fail when its control is removed.
