# DNS withdrawal and truthful eligible capacity — 2026-11-05

## Scope and observed failure

Feature IDs: `IW-CAP-001`, `IW-ROUTE-001`, `IW-CORE-001`; tasks `P1-T11`,
`P1-T12`, `P1-T13`, `P1-T09`. Recovery remains governed by `IW-NODE-001`,
`IW-DP-001` / `P1-T03`, specs 08 and 47 section 2.3.

Operational investigation found a registered direct-route worker whose endpoint
had been withdrawn as unresolvable. Later endpoint checks succeeded, but its
DNS withdrawal remained latched under the existing recovery policy. Selection
rejected it while the catalogue/admission projection still published positive
capacity from fresh registration/readiness. Thus upstream requests could see a
capacity offer that the serving gateway would not select.

This does not establish a musl/NSS resolver split or justify replacing a hostname
with an IP address. Missing capacity for separately pending scheduler workloads
is a different condition; this correction assigns no models or GPU resources.

## A: capacity correction and proof boundary

The correction filters the canonical catalogue's capacity and currently servable
context projections through the existing generic out-of-routing predicate. It
does not redefine the broad freshness-based inventory predicate. A withdrawn
provider contributes zero eligible/owner capacity while known model/deployment
identity and declared context remain available. Healthy siblings and accepted
work retain their existing capacity/reservation semantics.

The specification defect was silence about applying selection's withdrawal
predicate to catalogue budgeting. Freshness-only budgeting could satisfy the
old text while advertising ghost capacity; future implementers must not repeat
that separation.

Implementation revision:
[`ee84a29ba2981e241bd5818a28ac1187437f4c38`](https://github.com/InferWeave/inferweave/commit/ee84a29ba2981e241bd5818a28ac1187437f4c38),
[Rust PR #1489](https://github.com/InferWeave/inferweave/pull/1489), based on
`2f536121`. The production change adds the existing out-of-routing predicate to
the two canonical catalogue projection loops.
The supplied red/green logs were inspected for
`dns_withdrawal_removes_ghost_capacity_but_preserves_identity_and_active_work`
in Rust `crates/iw-gateway/tests/refused_node.rs`: without the correction the
withdrawn provider's usable-capacity assertion reported `left: 4`, `right: 0`;
with the correction the regression passed. The test's stated scope includes
known identity/context, a healthy sibling and a held lease. This bounded test
is not production qualification or proof of automatic DNS recovery.

The implementation author reports strict Rust 1.91 focused integration,
formatting and Clippy checks passing. Independent source review approved the
correction and independently reran the refused-node suite on Rust 1.91. These
are bounded implementation checks, not a claim that every platform/fixture test
passes: the author's broader macOS run retained platform/database-fixture
failures. Required Linux CI on PR #1489 remains **owed** until its actual result
is available. This specification change still requires its own independent
review before commit; no production rollout qualification is asserted.

## B: engine-preserving recovery remains owed

A does not automatically recover a healthy direct-only worker from a transient
DNS latch. Ordinary heartbeat, successful DNS lookup and unauthenticated endpoint
health do not clear it. Only genuine fresh authenticated producer registration
or an accepted authenticated held Link supplies the existing recovery evidence.

A bounded positive probe that requests fresh producer registration is design
work, not an implemented or proven recovery path. It owes atomic endpoint,
registration/control-connection and stronger-hold fences; finite per-episode
refresh/retry budgets; bounded outstanding DNS work with no abandoned-thread
growth; and proof using the supported producer that exhaustion cannot create a
forget/register loop. It must preserve the credential, canonical deployment,
GPU proof and running engine/job. Do not signal or restart a producer and claim
engine preservation without that proof. A false forgot-connection response while
retaining the connection is not a substitute for a genuine conditional control
transition. No direct DNS restoration or new automatic-restoration gate is
approved here.

Production route recovery, preservation of running engines through producer
refresh, and current-route inference smoke remain **owed**. Accepted requests
must not be replayed. Existing DNS heartbeat, bad-credential Link, stronger
withdrawal and late-result generation fences remain required regressions.
