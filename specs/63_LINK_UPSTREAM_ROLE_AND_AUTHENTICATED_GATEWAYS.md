# 63 — Link Upstream Role: Authenticated Upstream Gateways, N Parents and Siblings

## Purpose

Feature `IW-DP-002` (extension); task `P1-T18` (see Ownership). Status: **proposed**. Nothing here
is `proven`; see Proof status. Decision record: `decisions/2026-10-15-link-upstream-role.md`.

Spec 45 lets a gateway register with another gateway to arbitrary depth, and spec 21 lets a node
keep backup operational parents. In both, registration makes the **parent route work down to the
child** (`registered_with` runs child to parent, `routes_to` runs parent to child, spec 40).
Parent-to-child gateway relay exists in the Rust gateway (deadline, queue-hop and overload budgets
in `crates/iw-gateway/src/forward_budget.rs`, upstream handling in `crates/iw-core/src/upstream.rs`)
and this text reuses those hop and budget semantics. What no specification defines is a gateway
that **uses another gateway's models without being routed to by it**, over the held link, with an
API key and no registration. A read of `origin/main` found no `link_roles`, no such role and no
dialer-to-parent inference path using an API key; that is a reading, not a code audit. The only
alternative today is the public HTTPS client API, which has none of the held link's negotiation,
incarnation binding, liveness, loop prevention or provenance.

This text adds an **additive link role**, `upstream`: the dialer treats the acceptor as one of its
upstreams and submits exact-model requests up the link. It adds no scheduler, no new frame kind
beyond what is named below, and no authority beyond what the key grants. Where this text and spec
45, 59, 57, 21, 16 or the invariants disagree, those win.

The word *consume* is **not** used for this role: `ConsumeDispatch` and the
`link-consume-dispatch` schemas already name something else (spec 57).

## Invariant 11

Invariant 11 makes gateway byte proxying a last resort. An `upstream` link **is** gateway byte
relay, so it is admitted only where direct transport is not available or not permitted: the
dialer is a site gateway whose policy forbids a direct client-to-node path (for example a private
developer fabric that must not hold routes into the lab). A dialer that can reach the node through
the normal direct path MUST use it. This text does not make the upstream link a normal path, and
it adds byte accounting and a circuit breaker obligation (spec 08) that are owed with the tests.

## Roles on a held link

Today a held link carries one thing: the dialer registered as a node or peer and the acceptor
dispatches down it. This text names that role **`serve`** (unchanged; the default for every
legacy Hello) and adds **`upstream`**:

| Role | Dialer | Acceptor | Direction of requests |
|---|---|---|---|
| `serve` | offers capacity (registered) | dispatches work | acceptor → dialer |
| `upstream` | submits work (not registered) | executes from its own capacity | dialer → acceptor |

A dialer may request both roles on one link or hold separate links. Each granted role has its own
credential type, authorization, accounting and revocation; granting one never grants the other.

## Credentials are typed

Spec 45's Hello authenticates a **registration credential** and binds to a current registration.
An `upstream` link has no registration, so it uses a **different, typed credential**:

* The Hello carries `credential_type`: `registration` (the existing, default when absent) or
  `api_key`. The acceptor validates the secret **only against the store for the declared type**.
  A registration credential presented as an `api_key`, or a key as a registration credential, is
  refused, and an `api_key` **never yields `serve`**: the acceptor, not the dialer, decides the
  roles, and checks the credential type on every dispatch decision.
* The key identifies a **principal** (a tenant or project), not a node. It confers no node
  identity, no registration and no approval; enrolling a node remains a separate act (spec 47).
* The acceptor stores only a salted hash of the key. The dialer stores the key in a `0600` file
  and reads it from there; it is never in argv, a URL, a log, a receipt, an error or the ledger.
* The key is presented only over an authenticated, encrypted transport (TLS, or a transport spec
  16 admits as private).
* A key carries, set by the acceptor's operator: an optional model allow-list, a concurrency
  bound, a request-rate bound, an optional token budget, an expiry, and a traffic-class ceiling.
  A bound that is absent means the acceptor's default applies; an acceptor with no default
  **denies**. The defaults and numbers are owed measurements.
* Rotation is two overlapping keys. The key is the **same principal** whether presented on the
  link or as a bearer credential to the public API, with the same allow-list and bounds, and this
  must be reconciled with the current standalone principal-key surface of the Rust gateway
  (`INFERWEAVE_PRINCIPALS_FILE`, `cli.rs`); the reconciliation is owed.
* An upstream credential MUST NOT be forwarded downstream or to any further upstream
  (spec 45, trust and authentication): the `transit` grant below does not relax this; a transiting
  gateway uses its own credential for the next hop.

## Negotiation and binding

* Capability `iw.link-upstream/1`; the Hello gains the optional `link_roles`, a subset of
  `["serve","upstream"]` (absence means `["serve"]`), and `credential_type`. Spec 45's Hello
  schema is open (`additionalProperties: true`), so an old peer ignores both and grants nothing.
* Because there is no registration to intersect, the binding is a **separate upstream binding**:
  the acceptor authenticates the key, creates an unpredictable `upstream_binding_id`, and returns
  a bound acknowledgement echoing the Hello's `link_incarnation_id` and the binding id, listing
  the **granted** roles and the principal's pseudonymous label. The dialer enables `upstream`
  only on an acknowledgement that echoes both ids **from the same socket**. An acknowledgement
  from another dial, an old acknowledgement and a replayed Hello are refused: the Hello carries a
  fresh `link_incarnation_id` per dial and the acceptor rejects a reused one.
* The binding is also bound to the transport channel (TLS exporter or equivalent), so a key
  observed on one channel cannot be replayed on another.
* Selection of the link, check of the binding, the key's validity and the negotiated role, and
  enqueue are one atomic transition, as in spec 45. Key revocation, expiry, socket close and
  replacement revoke the binding for **new** requests immediately.
* A role not granted is absent. A dialer that asked for `upstream` and was not granted it closes
  that role and **never falls back** to `serve`, to an unauthenticated path or to the HTTPS API.

## What an upstream link may carry

* Only the spec 59 transport: exact-model JSON chat completions and completions with the existing
  request and response proof. The request names an **exact** model id the key permits. No alias is
  resolved on the link; level-2 alias execution, owner permits and `meta.native` together with
  `meta.http` remain invalid (spec 57, spec 59). An alias reaches an upstream only as the exact
  model the dialer's own resolution chose.
* The acceptor admits the request exactly as it admits a local client (admission, exact model
  identity, privacy, quota, spec 07 fairshare and owner priority); the link is a transport, not an
  admission authority. An upstream request is treated as a request of the key's principal, not as
  owner traffic.
* **Traffic class.** The dialer's declared class is **untrusted input**. The request's class is
  the more restrictive of the declared class and the key's ceiling, with the order taken from the
  class vocabulary of spec 44; an undeclared class is `private`. A request restricted to owned
  machines is never routed to volunteer or peer hardware (the acceptor's tier rules apply).
* **Idempotency.** Each request carries the dialer's request id. The acceptor deduplicates by
  `(principal, request id)` across reconnects, so a request repeated after a reconnect is not
  executed twice; a request that may already have produced output is never re-executed.
* **Hop and path.** Every upstream request carries the federation path of spec 45. The
  **acceptor appends itself** and rejects a path containing itself; the dialer-asserted path is
  never trusted alone. A hop limit (the bound used for spec 62 provisioning, 8, until measured
  otherwise) and the deadline and queue-hop budgets of `forward_budget.rs` apply, and a request
  past either is refused.
* **Streams.** Dialer-initiated streams use an identifier space disjoint from acceptor-initiated
  ones. The exact rule and the closed schema of the Hello and acknowledgement members are owed.

## Catalog and discovery

The acceptor offers, over the link, the **bounded list of exact model ids the key may use**, each
with the provenance of spec 45 (`reported`; passing through a gateway never makes it `verified`).
The dialer treats an upstream's models as **remote capacity with the upstream as a trust domain**:
two upstreams advertising one `model_id` keep independent deployments, capacity, health and
performance. A disconnected upstream's models are stale and never advertised live. Catalog bounds
are owed. The catalog, the receipt returned to the dialer and every response header show **the
key's view only**: no acceptor topology, queue-hop detail, other tenant, node identity or free
capacity (spec 61 redaction rule).

## N parents and siblings

* A gateway MAY hold any number of upstream links, each with its own key, role set, trust domain
  and lifecycle. "Parent" and "sibling" differ only in whether a registration (`serve`) also
  exists.
* **No transit by default.** A request that arrives over an upstream link is served from the
  acceptor's **own** capacity only. Forwarding it to a further upstream requires an explicit
  `transit` grant on the key and is bounded by the hop limit; the grant is owed and, until
  defined, no acceptor offers it. Loop safety does not depend on the default alone: the
  acceptor-appended path and the hop limit hold with or without transit.
* **Accounting.** Spec 21's single accounting lineage is stated there for development accounting
  (spec 18). This text applies the same discipline to production use: the gateway that
  **executes** a request records usage against the key's principal and charges the key's budget.
  The dialer records its own client's use against the **client's** quota and the upstream
  consumption as `reported`. The dialer's quota is authoritative for its client, the upstream's
  budget for the key; a client is therefore charged once at each boundary, never twice at one.
  Multi-parent connectivity never duplicates entitlement.
* **Selection among upstreams** is a dialer-local policy. Failover for one request is bounded and
  never retries a request that may already have produced output.

## Privacy and trust

* A prompt sent up an upstream link is visible to the acceptor in plaintext. The dialer declares a
  **trust domain per upstream** (spec 45 vocabulary) and never sends a request whose class its
  own policy restricts to a domain the upstream is not in.
* The acceptor's retention of the dialer's prompts and outputs follows its own prompt ledger and
  store rules (specs 22, 34) for the key's principal; the dialer is told in the acknowledgement
  whether the acceptor records prompt content for this principal, and MUST NOT send private
  content to an upstream that does.
* The dialer shares its gateway id and the path; it shares no node identity behind it.

## Revocation, abuse bounds

* Revocation stops **new** requests at once. Requests already streaming continue to completion
  only up to a bounded drain window, after which the acceptor aborts them with a terminal error;
  accepted requests with no output yet are aborted at once. The window is an owed measurement.
* Pre-authentication Hello rate, per-link stream caps, per-principal and per-gateway caps, and
  interaction with spec 07 are required controls whose numbers are owed.

## Relation to the public HTTPS client API

A dialer that does not implement this role MAY use the HTTPS API with its key as an interim path;
that has none of the negotiation, incarnation binding, liveness or loop prevention above, and
this text does not claim it does. The link role adds those; it does not replace the API.

## Ownership

Feature `IW-DP-002` is the closest existing feature; a new role, credential type, accounting rule
and trust surface may warrant its own feature ID, which is recorded as an open decision in
`decisions/2026-10-15-link-upstream-role.md`. Task `P1-T18` owns the required tests below in the
task card until a later task is chosen; spec 59 is the precedent for a link capability added to
it.

## Conformance scope

The first conformant acceptor and dialer are specified for the Rust gateway. Whether a Go site
gateway implements the acceptor side is **not decided here** and is recorded as an open decision
in the decision record (it touches the D-002 amendment of 2026-10-12: spec 54 limits the Go
gateway to consuming, rendering and relaying).

## Required tests

All **owed**; none is `proven`. Each must fail if its control is removed.

1. Negotiation and binding: no `upstream` role without the typed credential, an acceptor-created
   binding and a same-socket bound acknowledgement; an acknowledgement from another dial, a
   replayed Hello and a key replayed on another channel are refused; a legacy Hello is unchanged;
   a refused role never becomes `serve`.
2. Credential: a registration credential as `api_key` (and the reverse) is refused; a wrong,
   expired, revoked or over-budget key is refused before any request; the key never appears in
   argv, logs, receipts, errors or the ledger; only a hash is stored; a key never enrols or
   approves a node; an upstream credential is never forwarded.
3. Authorization: allow-list, concurrency and rate bounds hold per key; an unlisted model is
   refused; an alias is never resolved on the link; `meta.native` with `meta.http` is refused.
4. Class and privacy: the more restrictive class wins and an undeclared class is `private`; an
   owned-only request is not routed to peer hardware; a dialer never sends a restricted class to
   an out-of-domain upstream; catalog, receipt and headers show only the key's view.
5. Topology: no transit by default; the acceptor appends itself; a path containing the receiver
   and a request past the hop limit are rejected; mutual upstream cannot loop; two upstreams with
   one model id stay independent; a disconnected upstream goes stale.
6. Accounting and idempotency: the executing gateway charges the principal; the dialer's record is
   `reported`; a request repeated after reconnect is not executed twice; no duplicate entitlement.
7. Revocation and failure: revocation stops new requests at once; streaming requests end within
   the drain window; failover never retries a request that may have produced output.
8. Invariant 11: a dialer that can use the direct path does; byte accounting and the relay circuit
   breaker apply to upstream links.
9. Interop: the Rust dialer against the HTTPS-only fallback uses the same principal and bounds.

## Proof status

Everything here is **proposed** and **owed**: no schema, fixture, sender, acceptor, dialer or test
exists. Statements about today's behaviour come from specs 21, 40, 45 and 59 and a read of the
Rust repository's `origin/main`, not from a code audit. The evidence note in
`evidence/link-upstream-key-probe-2026-10-15/` is a single **unreproduced observation** (a key
needed to reproduce it is not recorded). All bounds and timings are deliberately unspecified
because none has been measured. Nothing here opens a production gate.

## Out of scope

* Registration of nodes (spec 47), alias resolution (spec 54, 61), provisioning (spec 62).
* Pricing, billing and quota between organizations.
* Changing the `serve` role, the Hello of legacy peers, or the exact-model transport of spec 59.
