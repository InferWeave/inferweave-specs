# Proposed: the spec 62 operator-audience plan, eviction handles and what a requester may rely on — 2026-10-16

**Status:** Proposed — needs owner acceptance. This record decides and authorizes nothing.  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-16  
**Authorizes:** nothing (design proposal only; not implementation, deployment, an eviction of any
model, a route, or any change to a plan a peer receives).  
**Relationship:** `discloses` the five gaps `OPEN_GATES.md` records for the operator-audience plan
(the "UNSATISFIED / owed" item (2) of the 2026-10-16 spec 62 update); proposes answers without
amending `specs/62_FEDERATED_PROVISIONING_HOSTING_REQUESTS.md`. Preserves D-003, invariant 37 and
spec 61's redaction rule. Not normative specification text.

Code citations are to `InferWeave/inferweave@a54e0398b7faf0842145aab410d358021c618b5f`, read, not run.

## Context

Spec 62 line 177 says `evicts` are "opaque handles to the owner's operator only (the requester
receives only the redacted verdict)", that "the distinction `FITS` versus `FITS_AFTER_EVICTION` itself
reveals other tenants' load", and that "a requester without authorization receives the plan as if no
other tenant's model existed (spec 61 rule)". Lines 182-190 say `fit` comes from the owner's own
measured reports and that `FITS_AFTER_EVICTION` "never evicts anything by itself". Required test 7
(lines 343-344) demands the unauthorized plan equal the plan for a world without the other tenants,
"modulo handles". The text defines none of: the handle's format, its lifetime, who may receive it,
the route that returns it, what an "authorized requester" is, or what a requester told `FITS` may
rely on when the owner would in fact have to unload something. `OPEN_GATES.md` records the same list.

What the code does at the pinned commit:

* **The pure verdict exists and is redacting.** `Audience` has three values, `Operator`,
  `AuthorizedRequester`, `UnauthorizedRequester`
  (`crates/iw-core/src/provision_hosting.rs:451-461`). For the unauthorized audience the verdict uses
  `(free = total, evictable = Some(0))` (`:636`); handles are copied from the resource report only when
  the room needs eviction (`:642`) and are returned only for `Audience::Operator` (`:748`), failing
  closed to `UNKNOWN` above `MAX_EVICTS` (`:756`). The handle strings are not made by this module: it reads
  `ResourceReport.evict_handles` verbatim.
* **Nothing produces a report.** `OwnerResources` is "Injected: this crate ships no probe. Without one
  every resource is `unknown`" (`crates/iw-gateway/src/provision_plan.rs:30-32`); the `None` branch
  makes both reports unknown (`:39-46`, `:121`). The node-side memory reports set `evictable: None` at
  every site (`crates/iw-cli/src/gpu_memory/mod.rs:668`, `:806`, `:975`), so even with a source
  wired, evictability has no producer and `FITS_AFTER_EVICTION` would stay unreachable.
* **The production planner never builds the operator audience.** `build_plan` hard-codes
  `audience: Audience::UnauthorizedRequester` (`provision_plan.rs:148`) and returns
  `plan.for_requester()`.
* **The operator is shown the redacted plan.** The approvals listing serializes
  `r.acquisition.as_ref().and_then(|a| a.plan.as_ref())` (`crates/iw-gateway/src/provision_operator.rs:257`),
  which is the stored plan built above. The operator therefore has no way today to see a handle even
  if one existed.
* **The approval binds no eviction.** `HostingApproval` carries the model reference, approved digests,
  egress hosts, byte bounds and the licence acknowledgement
  (`crates/iw-gateway/src/provision_acquisition.rs:130-147`); there is no eviction set, so an approval
  cannot authorize an unload.
* **Operator authentication is the admin secret.** `/iw/v1/provision/operator/*` answers 401 unless the
  caller presents the admin secret or arrives on loopback, and `hosting/approve`, `hosting/ask` and
  `hosting/discover` require the secret even on loopback because "a same-host reverse proxy makes every
  remote caller look loopback" (`crates/iw-gateway/src/server.rs:3815-3830`).
* **Parent allowlist is not disclosure authority.** `OwnerPolicy.allowlist` decides which parents the
  gateway will talk to at all and "an empty allowlist admits nobody"
  (`crates/iw-core/src/provisioning.rs:29`, `:105`; spec 62 lines 45-46).

Constraints: spec 61's rule that for a principal not authorized to see a candidate every entry, count
and figure "MUST be identical to those of a world in which that candidate does not exist", with handle
values differing "by nonce, never their structure" (`specs/61_ALIAS_PRECISION_ADHOC_SELECTION_AND_RESOLUTION_TREES.md:352-356`); D-003 owner priority
(`decisions/DECISIONS_REQUIRED.md:53-62`); local clients outrank upstream (spec 62 lines 51, 270); a
hot swap keeps the old runtime routable until the new one validates, and a failed swap rolls back
(spec 50 lines 70-77); pins protect active, rollback and operator-required cache entries (spec 50
lines 174-183).

## Options

### A. Eviction handle

1. **A derivation from the model** (a hash of instance and model id). Stable and cheap, but a requester
   who can guess model names confirms what is loaded; it fails the nonce rule. Rejected.
2. **An owner-minted, random, single-use reference with a private mapping.** Unpredictable, scoped,
   expires, cannot be correlated across plans. Costs an owner-side table.
3. **A signed token naming the victim.** Verifiable without a table, but a signed token must contain or
   reference the victim, and anything a requester could hold becomes an oracle if it ever leaks.
   Rejected.

### B. Who may receive handles and how

1. **Operator only, admin secret required, never loopback alone** (as `hosting/approve`).
2. **Operator and a named set of requesters** that hold a plan-disclosure grant.
3. **Requester-visible handles with the victim hidden.** Opaque to the requester, but the count and the
   structure already reveal load; rejected by test 7.

### C. What the requester is told when the owner would have to evict

1. **`UNKNOWN`.** Honest but it differs from the answer for an empty world, so it leaks occupancy and
   breaks the identical-world rule (`specs/61_ALIAS_PRECISION_ADHOC_SELECTION_AND_RESOLUTION_TREES.md:352-356`). Rejected.
2. **`FITS`, with its meaning fixed: fit against the owner's total hardware and policy caps, not an
   availability or entitlement statement.** Keeps the rule; moves the honesty into what `FITS` may be
   relied on for.
3. **A new coarse "may be delayed" member.** Leaks the same bit as `UNKNOWN`. Rejected.

### D. "Authorized requester"

1. **Parent on the allowlist.** Already required to be asked at all; says nothing about what it may
   see. Rejected as a definition.
2. **A separate owner-granted plan-disclosure grant** naming the requesting identity and the scopes
   whose load it may see, revocable, evaluated per candidate as spec 61 does.
3. **No authorized requester in version 1.** The `AuthorizedRequester` audience stays defined and
   unreachable.

## Recommended option

**A2, B1, C2, D3 now with D2 as the named later extension.** The sketch is for later spec text, not a
contract; every number is left to the owner's policy (none measured).

**Handle.** `ev1-` plus 128 bits of fresh randomness from the system generator (the shape spec 63
uses for `ub-` binding ids, `specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md:203`). It is minted when the operator view is computed, per
`(reservation_id, candidate)`, so the same victim has different handles in different plans. The owner
keeps an in-memory map `handle -> (reservation_id, instance_id, generation, node, model, residency
report sequence, policy revision)`. It is never derived from a model or instance name, never logged
beside a name outside the operator's audit entry, and never written into the stored plan, the
provisioning event stream or the ledger.

**Lifetime.** A handle dies at the first of: the approval decision on its reservation; the
reservation reaching `FAILED`, `REVOKED`, `EXPIRED` or `RELEASED`; a change of the victim's
generation (it unloaded, reloaded or was replaced); a residency report newer than the one the handle
was computed from, or a policy revision change; an owner-set maximum age (no default; an owner without
one issues no handles). The map is bounded and lost on restart; a lost handle is simply invalid and
the operator asks again. Fail closed.

**Who receives it and from which route.** Only the owner's operator, over a new route proposed as
`GET /iw/v1/provision/operator/hosting/plan?reservation_id=...`, with the same admin-secret-only rule
as `hosting/approve` (`server.rs:3820-3830`). The route computes the `Operator` audience view on
demand from a fresh resource report and returns the handle plus an operator-only descriptor (model id,
instance, local or upstream traffic class, in-flight count, pin or rollback status). Nothing computed
there is stored. The existing approvals listing keeps serving the requester-audience plan, so the
stored plan can never carry a handle. The Go console may render what this route returns to an
operator already authenticated with the admin secret, and does not mint, derive, rank or store a
handle (spec 62 lines 312-314).

**What an approval binds.** The hosting approval gains an explicit `eviction_set` (possibly empty).
The owner re-resolves each handle at approval time; any invalid or changed handle refuses the approval
rather than shrinking the set. An approval with an empty set cannot cause an unload. The unload itself
is not done by the approval: it is a step of a spec 50 swap, driven through the existing reservation
authority (spec 50 line 187: "only express intent to the existing rebalancer"), and follows the order
of record `decisions/2026-10-16-proposed-hosting-hook-boundary.md`: weights are acquired and verified
first, the swap is transactional, and a failed load rolls back to the known-good victim (spec 50
lines 70-77). Candidate victims exclude instances serving local clients, pinned or rollback entries
and anything in a drain already. Whether an operator may override the local-client exclusion is an open
question; the proposal is no.

**"Authorized requester."** In version 1 there is none: every requester gets the unauthorized view
(`provision_plan.rs:148` already does this), which is the only view that cannot leak. A later grant
(D2) would be a separate owner-held record naming the requester identity, the scopes it may see and an
expiry, evaluated per candidate, and the allowlist alone would never confer it.

**What a requester told `FITS` may rely on.** Only this, and the spec text should say so in these terms:
`FITS` in a requester-audience plan means the model's measured or bounded needs are within the owner's
total capacity and policy caps and the source, licence and runtime gates are satisfied. It is a
statement about hardware and policy, not about availability. It is not a reservation, not an
approval and not an entitlement; the owner may decline at approval, may need to unload something to
honour it, may take longer to reach `READY` because of that, and may still fail the pre-load re-check
with `INSUFFICIENT_VRAM` or `SIZE_BOUND_EXCEEDED` (spec 62 lines 164-166, 206-209). The only commitments
are the reservation states, and even `RESERVED` is preemptible by a local need (spec 62 lines 50-52,
270). The same sentence covers `FITS_AFTER_EVICTION`, which no requester ever sees in version 1.

**Residual leaks, stated rather than hidden.** The time to `READY` and the operator's approval latency
differ when an unload is needed, so occupancy is partly observable by timing; planning is rate-limited
(spec 62 lines 112-113, test 8) which bounds repeated probing but does not remove the channel. A phase
duration is already `null` in the plan ("no duration is measured: none is claimed",
`provision_plan.rs:161`, phases built with `duration: None`), which helps. The owner accepts this residual
risk or rejects the design.

**Rollout.** (1) a real `OwnerResources` source from the gateway's own residency reports, including an
evictability classification the node reports today as `None`; (2) the handle map and the operator
route, read-only, with the approval unchanged; (3) the `eviction_set` binding, still without
execution; (4) execution through the spec 50 path, after the hook boundary record is settled. Each
step has its own test that fails when the control is removed, per spec 62's required tests.

## Consequences

* Positive: a requester can never distinguish a busy owner from an idle one by the plan's content; the
  operator can see and approve exactly which models would go; an eviction cannot happen without an
  approval that names it.
* Negative: `FITS` is a weaker promise than it sounds, and the spec must say so; the handle map is
  volatile; a human operator in the loop makes eviction slow by design; timing remains a residual
  channel.
* Until a resource source exists, `FITS_AFTER_EVICTION` and handles stay unreachable; this record does
  not make them reachable.

## What implementation would follow

Spec 62 text for the handle, the route, the approval member and the meaning of `FITS`; schema and
fixtures for the operator view and the approval; the `OwnerResources` implementation and the node
evictability report (spec 46 vocabulary); the handle map; the route; tests for test 7 with the
operator and requester views side by side. Tasks `A-T05` and `P5-T17`; no task-graph change.

## Open questions for the owner

1. May an operator ever evict an instance that is serving local clients, or is that never allowed?
2. Is the maximum handle age a policy the owner sets, and what is acceptable for the lab?
3. Is a plan-disclosure grant (D2) wanted at all, or is "requesters always see the unauthorized view"
   the permanent answer?
4. Does the owner accept the timing residual channel?
5. Should `FITS` in a requester plan carry a wire flag naming it non-binding, or is the spec sentence
   enough? (A flag is an additive member and a spec change.)

## Not authorized

Any implementation, route, schema or fixture change; minting or storing a handle; evicting or
unloading any model; any change to the plan a peer receives; any deployment; any production traffic.
