# Proposed answers to the open decisions of the link upstream role record — 2026-10-16

**Status:** Proposed — needs owner acceptance. This record decides and authorizes nothing.  
**Decision owner:** InferWeave operator  
**Date:** 2026-10-16  
**Authorizes:** nothing (design proposal only; not a registry edit, a task-graph edit, an acceptor in
any gateway, deployment, key issuance or traffic).  
**Relationship:** `discloses` a recommendation for each decision `decisions/2026-10-15-link-upstream-role.md`
left open ("Open decisions (none made here)": Go acceptor side, feature ID, invariant 11). It does not
amend that record, whose status stays Proposed. Premise, stated by the owner for this proposal: **the
Go gateway is a lab-only relay and renderer, and the Rust gateway owns aliases and the protocol.**
That premise is consistent with, and not read from, D-001/D-002 as amended on 2026-10-12
(`decisions/DECISIONS_REQUIRED.md:5-52`) and `decisions/2026-10-12-dynamic-alias-authority.md`; this
record does not amend them.

Code and registry citations are to `InferWeave/inferweave@a54e0398b7faf0842145aab410d358021c618b5f`
and to this repository at `5b97ed9`, read, not run.

## Context

Spec 63 adds the `upstream` link role: the dialer submits exact-model requests up a held link to an
acceptor that "executes from its own capacity" (`specs/63_LINK_UPSTREAM_ROLE_AND_AUTHENTICATED_GATEWAYS.md:50`).
The acceptor stores only a salted hash of each key, applies per-key allow-lists, concurrency and token
budgets, deduplicates by request id, appends itself to the federation path and enforces a hop limit
(lines 63-107, 174-187), and "admits the request exactly as it admits a local client" (line 155). The
Rust gateway implements the acceptor and the dialer, default off (spec 63 lines 378-392;
`OPEN_GATES.md` section "Link upstream role and authenticated gateways", and the latest 2026-10-16
update). Spec 63 lines 334-339 say "Whether a Go site gateway implements the acceptor side is **not
decided here**" and that it "touches the D-002 amendment of 2026-10-12: spec 54 limits the Go gateway
to consuming, rendering and relaying". The ownership paragraph (lines 326-332) says `IW-DP-002` is "the
closest existing feature" and a new ID "may" be warranted.

Registry facts: `IW-DP-002` is "Regional relay/direct path/rendezvous", phase 3, priority P1, status
`required_later`, canonical tasks `P1-T16`, `P1-T18`, `P3-T08`, `P5-T03`, contract
`contracts/protocol-v1/link-upstream.json` (`contracts/feature-registry.json`;
`implementation/FEATURE_TASK_COVERAGE.md:20`). Task `P1-T18` is "Regional/gateway relay fallback" with
features `IW-DP-001` and `IW-DP-002` (`tasks/phase-1/P1-T18.md`). The validator requires every feature
to have a canonical task that exists and a row in `implementation/FEATURE_TASK_COVERAGE.md`
(`scripts/validate_specs.py`, `guard_feature_mappings` and `guard_coverage_tables_match`). Precedent for
a feature split off a workstream: `IW-DYNNODE-001`, phase 5, one task `P5-T35`, created with its spec
and decision record.

## Decision 1 — does the Go gateway implement the acceptor side?

### Options

1. **No: Go is neither acceptor nor dialer.** The Rust gateway is the only acceptor and dialer. Go may
   display what Rust projects (its keys' labels, counts, refusal reasons, link state) and may carry
   no `upstream` Hello.
2. **Yes, a full Go acceptor.** Go gains a key store, per-key budgets, deduplication, path/hop
   handling, traffic-class reading and an executor for admitted requests.
3. **Go as a transparent, protocol-blind forwarder** of the TCP/TLS stream to a Rust acceptor.
   Unverified feasibility: spec 63's channel binding is tied to the TLS exporter of the link
   (spec 63 lines 202-203, 378-380; the exact derivation was not read for this record), so anything
   that terminates TLS at the forwarder breaks it. A layer-4 pass-through would not need any Go
   protocol logic and would be infrastructure, not a gateway feature.

### Duties spec 63 places on each side (read, not assumed)

The acceptor executes and accounts: key store, budgets, admission, deduplication, the appended federation
path and hop limit, traffic-class handling (lines 63-107, 148-194). The dialer chooses and accounts:
reads the catalog, treats an upstream's models "as remote capacity with the upstream as a trust domain"
(line 229), picks among N upstreams by "dialer-local policy" with bounded failover (lines 236-262),
records its client's use against the client's quota and the upstream's as `reported` (lines 253-258),
mints a fresh request id per dispatch (line 177) and runs the relay circuit breaker and byte accounting
(line 262 onward). Selection, admission and accounting are exactly the functions spec 54 and the
2026-10-12 decision keep out of Go ("No Go alias database, model selector, ..." spec 54 lines 34-36;
"Rust remains the only alias persistence, resolution and admission authority").

### Recommendation

**Option 1.** Reasoning: under the stated premise both halves of the role are Rust-owned functions.
An acceptor in Go would be a second admission and accounting authority, which is the failure mode the
2026-10-12 decision rejected ("independent Go alias engine (two authorities)"), and it would make the
Go gateway "execute and account requests" which the old record says spec 54 and the D-002 amendment limit Go away from. A Go
dialer would make Go a selector. Option 2 is rejected on the same ground. Option 3 stays available as
a deployment choice, outside this decision.

### Consequences

* Spec 63 "Conformance scope" would read: the Rust gateway is the only conformant acceptor and dialer;
  a Go site gateway offers no `upstream` role. This is a spec 63 edit for the owner to authorize, not
  made here.
* A conformant Go site gateway does not need the role: spec 42 lists the held link as checked
  "afterward and reported separately" and "a missing link cannot create model reachability"
  (`specs/42_SITE_GATEWAY_CONFORMANCE.md:82-87`), and nothing in the capability list makes `upstream`
  mandatory (as read; not a code audit of the Go gateway).
* A dialer that meets a Go gateway gets no `upstream_ack` and closes (spec 63 lines 114, 129), the same
  outcome as a bad key. How a Go gateway reacts to an unknown Hello role was not audited and should
  have a test in the Rust dialer's interop set.
* Operator surfaces for upstream keys and counters, if wanted in the lab console, are Rust projections
  rendered by Go under the D-002 amendment.
* Revisit trigger: the owner decides Go carries more than render and relay.

## Decision 2 — does the upstream role get its own feature ID?

### Options

1. **Extend `IW-DP-002`.** No registry change.
2. **A new feature ID**, for example `IW-LINKUP-001` (the registry's IDs are `IW-<WORD>-<NNN>`) (naming is the owner's), with canonical task
   `P1-T18` (which would list it beside `IW-DP-001` and `IW-DP-002`), its own coverage row and its
   own contract entry, carrying spec 63's proof status.
3. **A new ID and a new task**, separating the upstream work from `P1-T18`'s relay-fallback outcome.

### Trade-offs

* `IW-DP-002` is a phase-3 `required_later` feature spanning rendezvous and relay with three other
  tasks; spec 63 is implemented in the Rust gateway today (default off) with its own OPEN_GATES section,
  its own required-test list (spec 63 lines 341-376), a different trust surface (an API-key principal,
  budgets, byte relay under invariant 11) and its own security review. Folding it into `IW-DP-002`
  makes that feature's status mean two things: closing `IW-DP-002` would need `P3-T08` and `P5-T03` and
  the upstream proof together, or would silently exclude one of them.
* A separate ID costs a registry entry, a `FEATURE_TASK_COVERAGE.md` row, `P1-T18`'s feature list and
  the regenerated bundle metadata; the validator already demands each of those and would catch an
  omission. It makes the feature's proof status trackable in `OPEN_GATES.md` without editing an
  unrelated feature.
* A new task (option 3) is more churn than the evidence supports: `P1-T18` already owns the tests
  (spec 63 line 330-331).

### Recommendation

**Option 2.** It follows the `IW-DYNNODE-001` precedent, keeps `IW-DP-002` closable on its own terms,
and the Rust-only ownership of Decision 1 gives the feature a single `owner_component`. Do not touch
the registry in this change; the entry, the `P1-T18` card edit, the coverage row, the task-graph
`features` list for `P1-T18` and `OPEN_GATES.md` would be one separate PR after acceptance.

### Consequences

Positive: clean proof accounting; the spec 63 acceptance can be reported without implying relay or
rendezvous coverage. Negative: one more feature in a registry the validator already guards; existing
references that say "link upstream role: spec 63" under `IW-DP-002` (`FEATURE_TASK_COVERAGE.md:20`,
`CHANGELOG.md`) would be re-pointed. Revisit trigger: the role is folded into a larger relay design.

## Decision 3 — invariant 11 (the third item of the old record)

The old record lists "The role is admitted only where direct transport is unavailable or forbidden" as
a third open decision. Spec 63 lines 32-39 already says so as drafted, and says the dialer "that can
reach the node through the normal direct path MUST use it". **Recommendation: accept the sentence as
drafted, with one candour added to the spec when it is next edited:** an acceptor cannot observe whether
a dialer could have gone direct, so this is enforced by who is issued an upstream key, not by the
protocol. The operator issues `upstream` keys only to dialers whose policy forbids a direct path, and
the byte accounting and circuit breaker spec 63 owes (line 39-40, 262 onward) are the runtime evidence.
Consequence: a misissued key is a policy failure the protocol cannot detect. This stays an owner
decision and is not an enforcement claim.

## What implementation would follow

* Accepted Decision 1: a spec 63 edit to "Conformance scope"; an interop test that a Rust dialer
  meeting a gateway that does not grant `upstream` closes without a binding; no Go work.
* Accepted Decision 2: the registry, card, coverage and task-graph edit named above, run through
  `scripts/validate_specs.py` and the metadata generator.
* Accepted Decision 3: one sentence in spec 63.

## Open questions for the owner

1. Is "Go neither acceptor nor dialer" also true for the lab, or does the lab console need to dial
   an upstream itself?
2. May an L4 pass-through in front of a Rust acceptor be used, and does it need its own record?
3. The feature ID: the name, and phase 1 (the task's phase) or 3 (`IW-DP-002`'s)?
4. Is the invariant 11 enforcement-by-issuance acceptable, or should the acceptor require an
   operator-set `no_direct_path` attestation on each key?

## Not authorized

Any registry, task-graph, card or spec 63 edit; an acceptor or dialer in any gateway; issuing a key;
opening a link; any deployment; any production traffic.
