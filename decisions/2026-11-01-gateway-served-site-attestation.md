# The gateway serves a paid site its own attestation — 2026-11-01

**Status:** Accepted for design (Option 2); Option 1 adopted for operation. Accepted by the decision
owner in conversation on 2026-11-01, after this record was proposed the same day.  
**Decision owner:** InferWeave operator  
**Date:** 2026-11-01  
**Authorizes:** the design of Option 2 only, and the operated status quo of Option 1. It does **not**
authorize: any implementation (no endpoint, gateway change or node change), any deployment,
enrollment, key issuance, spending or production traffic, or a feature ID or task. Those need this
record's open questions answered and a later `Accepted for implementation`.  
**Relationship:** `discloses` an operational fact no specification states (below). It amends no
record and no invariant. It decides one change of mechanism (Option 2) for design only.

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

1. **Option 1 is adopted now**, as an operational measure: a scheduled renewer
   (`renew_attestation.py`) on a host with verified access to both ends. It needs no gateway or node
   change. Until a scheduler is installed, an unplanned link drop with an expired attestation leaves
   the site waiting until someone renews; a planned gateway deploy re-attests as part of the deploy.
2. **Option 2 is accepted for design only.** It may be refined and its open questions answered; it
   may not be implemented or deployed under this record. Moving to `Accepted for implementation`
   needs an answer to each open question below, a feature ID and canonical task, and the proofs
   listed in `OPEN_GATES.md`.
3. **Option 3 (a longer expiry) is not adopted.**

## Open questions Option 2 must answer before it can be accepted for implementation (all still open)

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
