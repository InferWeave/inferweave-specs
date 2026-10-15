# 63 — Link Consume Role: Authenticated Upstream Gateways, N Parents and Siblings

## Purpose

Feature `IW-DP-002` (extension); task `P1-T18`. Status: **proposed**. Nothing here is `proven`;
see Proof status.

Spec 45 lets a gateway register with another gateway to arbitrary depth, and spec 21 lets a node
keep backup operational parents. In both, registration makes the **parent route work down to the
child** (`registered_with` runs child to parent, `routes_to` runs parent to child, spec 40). No
specification lets a gateway **use another gateway's models without being routed to by it**. A site
gateway that wants a partner's models (for example a developer-fabric gateway that wants the lab
gateway's models, and does not want to be routable from the lab) has only the public HTTPS client
API, which carries none of the held link's negotiation, incarnation binding, liveness, loop
prevention or provenance.

This text adds an **additive link role**: a gateway that holds a credential (an API key) dials an
upstream gateway, negotiates the role `consume` on the held link, and submits exact-model requests
up that link. It adds no scheduler, no new frame kind that is not named below, and no authority
beyond what the key grants. Where this text and spec 45, 59, 57, 21 or 16 disagree, those win.

## Roles on a held link

Today a held link carries one thing: the dialer registered as a node/peer and the acceptor
dispatches down it. This text names that role **`serve`** (unchanged, the default for every
legacy Hello) and adds **`consume`**:

| Role | Dialer | Acceptor | Direction of requests |
|---|---|---|---|
| `serve` | offers capacity | dispatches work | acceptor → dialer |
| `consume` | submits work | executes work from its own capacity | dialer → acceptor |

A dialer may request both roles on one link or hold separate links. Each negotiated role has its
own authorization, accounting and revocation; granting one never grants the other.

## Negotiation

* New capability `iw.link-consume/1`, negotiated exactly as the other native link capabilities
  (spec 45 *Native Link v1 incarnation binding*: Hello offer, registration/Hello/gateway
  intersection, same-socket bound acknowledgement echoing both ids). The Hello gains the optional
  member `link_roles`, a subset of `["serve","consume"]`; its absence means `["serve"]`.
* The acknowledgement lists the **granted** roles. A role not granted is absent; the dialer MUST
  NOT assume it. A dialer that asked for `consume` and was not granted it closes that role and
  **never falls back to `serve`** or to an unauthenticated path.
* Mixed versions: a peer that does not understand `iw.link-consume/1` ignores `link_roles` and
  treats the link as a legacy Hello; it grants no `consume`. Metadata-free legacy behaviour is
  unchanged.
* The Hello carries **no credential in the clear**: the key is presented only over an
  authenticated, encrypted transport (TLS, or a transport spec 16 admits as private), in the
  existing authentication field of the Hello, never in a URL, argv or a log.

## Credential: the API key

* The key identifies a **principal** (a tenant or project), **not a node**. A consume link confers
  no node identity, no registration, no `serve` role, and no approval; enrolling a node remains a
  separate act (spec 47).
* The acceptor stores only a salted hash of the key, never the key. The dialer stores the key in a
  file with mode `0600` and reads it from that file; it is never passed in argv, and never sent to
  the ledger, telemetry, receipts or errors.
* A key carries, set by the acceptor's operator: an optional **model allow-list**, a **concurrency
  bound**, a **request-rate bound**, an optional **token budget**, an **expiry**, and a
  **traffic-class ceiling** (below). A bound that is absent means the acceptor's own default
  applies, and an acceptor with no default **denies**.
* Rotation is two overlapping keys; revocation takes effect for **new** requests immediately and
  aborts accepted requests that have produced no output within a bounded drain window. The
  numbers are owed measurements, not set here.

## What a consume link may carry

* Only the transport of spec 59: exact-model JSON chat completions and completions, with the
  existing request and response proof. The request names an **exact** model id the key's
  allow-list permits. No alias is resolved on a consume link: level-2 alias execution, owner
  permits and `meta.native` together with `meta.http` remain invalid (spec 57, spec 59).
  An alias reaches an upstream only as the exact model the dialer's own resolution chose.
* The acceptor admits the request exactly as it admits a local client request (admission, exact
  model identity, privacy, quota); the link is a transport, not an admission authority.
* Requests the dialer originates carry the dialer's traffic class and an end-to-end trace id
  (spec 09). The acceptor treats the **lower of the dialer's declared class and the key's
  ceiling** as the class of the request. A request whose class the acceptor's policy restricts to
  owned machines is not routed to volunteer or peer hardware (the acceptor's existing tier rules
  apply unchanged).

### Frames and streams

No new frame kind is introduced beyond what the exact wire form needs. The dialer-initiated
streams use a stream identifier space **disjoint** from acceptor-initiated ones, so the two
directions cannot collide. The exact identifier rule, the schema of the optional `consume` member
of the Hello and acknowledgement, and the reuse of Request/Token/End are **owed** to a closed
schema; this text fixes the properties, not the bytes.

## Catalog and discovery

The acceptor offers, over the consume link, the **bounded list of exact model ids the key may
use**, each with the provenance of spec 45 (`reported`, never `verified` by passing through a
gateway). The dialer treats an upstream's models as **remote capacity with the upstream as a
trust domain**: two upstreams advertising the same `model_id` keep independent deployments,
capacity, health and performance (spec 45). A disconnected upstream's models become stale and are
never advertised live. The catalog is bounded in entries and bytes; the bounds are owed.

## N parents and siblings

* A gateway MAY hold any number of upstream links, each with its own key, role set, trust domain
  and lifecycle. There is no distinguished parent for `consume`; a "parent" and a "sibling" differ
  only in whether a registration (`serve`) also exists.
* **No transit by default.** A request that arrives over a consume link is served from the
  acceptor's **own** capacity only. Forwarding it onward to a further upstream requires an
  explicit `transit` grant on the key, which this text does not define a bound for (owed). This
  keeps the default topology a star, not a chain.
* **Loops.** Every consumed request carries the spec 45 federation path. A gateway rejects a
  request whose path contains itself and never selects an upstream whose id is already in the
  path. A mutual `consume` between two gateways is legal and, with no transit, cannot loop.
* **Accounting.** One request has one authoritative accounting lineage (spec 21): the gateway
  that **executed** it records usage against the key's principal; the dialer records its own
  client's use and the upstream cost as `reported`, not as a second entitlement. Multi-parent
  connectivity MUST NOT duplicate entitlement.
* **Selection among upstreams** is a dialer-local policy. Failover between upstreams for one
  request is bounded and never retries a request that may already have produced output.

## Privacy and trust

* A prompt sent up a consume link is visible to the acceptor in plaintext. The dialer therefore
  declares a **trust domain per upstream** (spec 45 vocabulary) and never sends a request whose
  class its own policy restricts to a domain the upstream is not in.
* The acceptor must not learn more of the dialer's topology than the dialer chooses to state: the
  dialer's gateway id and the path are shared; node identities behind the dialer are not.
* A consume link never reveals the acceptor's other tenants, nodes or free capacity to the
  dialer; the catalog is the key's view only (spec 61 redaction rule).

## Relation to the public HTTPS client API

The key is the **same principal** whether presented on the link or as an HTTP bearer credential
to the public API, with the same allow-list, bounds and accounting. A dialer that does not
implement this role MAY use the HTTPS API with its key as an interim path; that carries none of
the negotiation, incarnation binding, liveness or loop prevention above, and this text does not
claim it does. The link role adds those; it does not replace the API.

## Conformance scope

* The first conformant acceptor and dialer are specified for the Rust gateway.
* Whether a Go site gateway implements the acceptor side is **not decided here**: spec 54 limits
  the Go gateway to consuming, rendering and relaying, and this text neither extends nor
  contradicts that. Recorded in `OPEN_GATES.md` as an open decision.

## Required tests

All **owed**; none is `proven`. Each must fail if its control is removed.

1. Negotiation: no `consume` without Hello offer, registration/gateway intersection and a bound
   acknowledgement on the same socket; an acknowledgement from another dial is ignored; a legacy
   Hello is unchanged; a refused `consume` never becomes `serve`.
2. Credential: a wrong, expired, revoked or over-budget key is refused before any request; the key
   never appears in argv, logs, receipts, errors or the ledger; only a hash is stored; a key does
   not enrol or approve a node.
3. Authorization: allow-list, concurrency and rate bounds hold per key; an unlisted model is
   refused; an alias is never resolved on the link; `meta.native` with `meta.http` is refused.
4. Class and privacy: the lower of dialer class and key ceiling applies; an owned-only request is
   not routed to peer hardware; a dialer never sends a restricted class to an out-of-domain
   upstream; the catalog shows only the key's view.
5. Topology: a star by default (no transit); a path containing the receiver is rejected; mutual
   consume cannot loop; two upstreams with one model id stay independent; a disconnected upstream
   goes stale.
6. Accounting: the executing gateway records usage against the principal; the dialer's record is
   `reported`; multi-parent use never duplicates entitlement.
7. Revocation and failure: revocation stops new requests at once and aborts silent accepted ones
   within the drain window; failover never retries a request that may have produced output.
8. Interop: the Rust dialer against the HTTPS-only fallback uses the same key and bounds.

## Proof status

Everything here is **proposed** and **owed**: no schema, fixture, sender, acceptor, dialer or test
exists. The claims about today's behaviour (registration routes down; no gateway-to-gateway
request path with a key) are read from specs 21, 40, 45 and 59, not from a code audit. The
evidence note in `evidence/link-consume-key-probe-2026-10-15/` records one measurement: that the
public HTTPS API accepts a key on a read. All bounds and timings are deliberately unspecified
because none has been measured. Nothing here opens a production gate.

## Out of scope

* Registration of nodes (spec 47), alias resolution (spec 54, 61), provisioning (spec 62).
* Pricing, billing and quota between organizations.
* Changing the `serve` role, the Hello of legacy peers, or the exact-model transport of spec 59.
