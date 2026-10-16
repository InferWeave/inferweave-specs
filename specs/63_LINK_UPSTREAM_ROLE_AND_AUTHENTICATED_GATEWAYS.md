# 63 — Link Upstream Role: Authenticated Upstream Gateways, N Parents and Siblings

## Purpose

Feature `IW-DP-002` (extension); task `P1-T18` (see Ownership). Status: **proposed, implemented in
part and default off** in the Rust gateway (see Proof status). Only the controls Proof status names
as proven are proven; everything else here is owed. Decision record: `decisions/2026-10-15-link-upstream-role.md`.

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
45, 59, 57, 21, 16 or the invariants disagree, those win, with exactly two named exceptions that
this text adds to spec 59 and that spec 59 now records: the optional request-`meta` member
`traffic_class` (schema `link-request-meta.json`), and the `refused` frame on an `upstream` link
(see Negotiation and binding).

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

A Hello carries exactly one credential, so one link is granted one role. A dialer that wants both
roles holds two links, each with its own Hello and credential. (An earlier draft allowed both roles
on one link, which one credential cannot express.) Each granted role has its own credential type,
authorization, accounting and revocation; granting one never grants the other.

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
  16 admits as private). The channel binding below stops a recorded Hello from being replayed on
  another channel; it is **not** proof of possession of the key (a holder of the key can compute
  it), so TLS, not the binding, is what protects the key in transit.
* A key carries, set by the acceptor's operator: a model allow-list, a concurrency bound, a
  request-rate bound, an optional token budget, an expiry, and a traffic-class ceiling. The
  allow-list is not optional: an absent or empty allow-list permits **no** model. A bound that is
  absent means the acceptor's default applies; an acceptor with no default **denies**. The
  defaults and numbers are owed measurements.
* **Token budget.** When a key has one, it is a number of tokens (prompt plus completion, as the
  executing engine reports them) per fixed 24-hour window kept by the acceptor. Admission refuses
  a request with the reason `token_budget_exceeded` once the tokens charged in the current window,
  plus the tokens reserved for requests already in flight, reach the budget; the refusal is the
  key-scoped capacity refusal like `rate_limited`: nothing ran, so it is reversible and another
  upstream holding a different key, or local capacity, may serve the request within the bounded
  failover. A request admitted under the budget may
  finish, so the budget can be exceeded by the requests in flight at the moment it is reached,
  bounded by the key's concurrency bound. Each admitted request reserves an estimate of its tokens
  at admission and the reservation is replaced by the engine-reported usage when the request ends;
  a request that ends without a usage report is charged its reservation, never zero. A budget
  whose counters do not survive an acceptor restart is weaker than one that does; whether the
  counters are durable is stated in Proof status, and a restart that resets them is a known
  weakness until they are.
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
  An `api_key` Hello requested for the `upstream` role carries `link_roles: ["upstream"]` only.
* **A refused Hello gets no acknowledgement.** The acceptor closes the socket and does not say
  why, so a peer without a valid key learns nothing about which check failed. Only a granted
  `upstream` role is acknowledged.
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
* **The acknowledgement and the refusal frame.** The acknowledgement names the granted roles, the
  principal's pseudonymous label, the negotiated features and `records_prompt_content` (see
  Privacy). Granting `upstream` is what lets the acceptor send the `refused` frame on this link:
  the frame belongs to the federated-admission link capability `iw.link-refusal/1` (defined in the
  implementation repository's federated-admission design, not in this specification set), which
  an upstream link does not negotiate, and that negotiation does not apply here. On an upstream link every admission refusal is a `refused` frame
  and **never** a response head, so the dialer can tell "this was not executed" from "execution
  produced this"; only the former may be taken back and sent elsewhere. The refusal reasons are a
  closed vocabulary that names no model, key, path or other tenant: `binding_closed`,
  `key_invalid`, `invalid_request`, `model_not_permitted`, `federation_loop`,
  `hop_limit_exceeded`, `deadline_exceeded`, `duplicate_request`, `rate_limited`,
  `concurrency_limited`, `token_budget_exceeded` and `backend_unavailable`. Of these, a dialer
  treats only `rate_limited`, `concurrency_limited`, `token_budget_exceeded` and
  `backend_unavailable` as reversible
  (nothing ran and another upstream or local capacity may serve), and never reports a credential
  or binding refusal to its own client as the client's authentication failure.

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
* **Traffic class.** The dialer's declared class is **untrusted input**. It rides the request's
  `meta` as the optional member `traffic_class`, whose value is one of the two class tokens
  `private` and `shareable` (`private` is the more restrictive: a request restricted to owned
  machines; `shareable` may also be served by vetted volunteer hardware). The vocabulary is the
  Rust gateway's node-tier vocabulary; spec 44 does not define it, and an earlier draft cited
  spec 44 for it in error. The dialer sends it only on a link whose acknowledgement granted
  `upstream`, where the acceptor is known to read it (a reader that predates the member ignores it,
  which reads as undeclared). The request's class is the more restrictive of the declared class
  and the key's ceiling, in the order just stated; an undeclared, absent or unrecognised class is
  `private`. The acceptor never reads the class from anywhere but
  this member, and a dialer's class can only make a request more restrictive than the key's
  ceiling, never less. A request restricted to owned machines is never routed to volunteer or peer
  hardware (the acceptor's tier rules apply).
* **Idempotency.** Each request carries the dialer's request id. The acceptor deduplicates by
  `(principal, request id)` across reconnects, so a request repeated after a reconnect is not
  executed twice; a request that may already have produced output is never re-executed. The
  dialer mints a **fresh, unpredictable request id for every dispatch**: never derived from the
  prompt or from any client-supplied id, so two identical prompts are two requests and cannot be
  refused as duplicates, and one client cannot collide with another on a shared key. The dedupe
  therefore guards only a repeat of the same dispatch, which a dialer makes only when it knows
  nothing could have executed. Whether the dedupe state survives an acceptor restart is stated in
  Proof status.
* **Hop and path.** Every upstream request carries the federation path of spec 45. The
  **acceptor appends itself** and rejects a path containing itself; the dialer-asserted path is
  never trusted alone. A hop limit (set by the acceptor's operator from 1 to a maximum of 8, the bound spec 62
  uses for provisioning; there is no default, and an acceptor without one refuses the role) and the deadline and queue-hop budgets of `forward_budget.rs` apply, and a request
  past either is refused.
* **Streams.** The acceptor never initiates a request on an upstream link (no work flows down it),
  so request ids are minted only by the dialer and a rule making dialer and acceptor identifier
  spaces disjoint has nothing to separate. A request id is scoped to the binding and the principal
  (at most 256 bytes). A frame an acceptor never sends on this role (a request, a Hello) or a
  dialer never sends (tokens, a refusal, an acknowledgement) is a protocol violation that closes
  the link. The closed schema of the Hello and acknowledgement members is owed.

## Catalog and discovery

The acceptor offers, over the link, the **bounded list of exact model ids the key may use**, each
with the provenance of spec 45 (`reported`; passing through a gateway never makes it `verified`).
Each entry is a closed object `{model_id, max_context_tokens, provenance}`: `model_id` is the exact
id, `max_context_tokens` is a positive integer, the context the acceptor serves that model at (a
dialer's router cannot place a request on a route that makes no context claim, so the entry
carries one; an entry the acceptor cannot state a context for is omitted), and `provenance` is
`reported`. A catalog holds at most 256 entries and a dialer drops one that breaks any bound. It
is a frame of this capability: the acceptor pushes it once right after the acknowledgement and
again in answer to the dialer's catalog request (which doubles as the dialer's keep-alive), at
most once per second per link; a catalog replaces the previous one.
The dialer treats an upstream's models as **remote capacity with the upstream as a trust domain**:
two upstreams advertising one `model_id` keep independent deployments, capacity, health and
performance. A disconnected upstream's models are stale and never advertised live. The catalog
bound of 256 entries is a placeholder; a measured bound is owed. The catalog, the receipt returned to the dialer and every response header show **the
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
  The relay path of spec 21 marks rows a gateway records for work it forwarded for a parent and
  excludes them from accounting, because the parent's row is the authoritative one. A request
  executed from the acceptor's own capacity for an upstream link is not such a row: the acceptor
  is the executing, charging gateway, so its row is an ordinary row of the key's principal and key
  id (the source client names the dialer), it MUST NOT carry the relay marker, and accounting MUST
  NOT exclude it. Following the relay path literally would charge nobody.
  The dialer records its own client's use against the **client's** quota and the upstream
  consumption as `reported` (provenance on the dialer's route record, never `verified`). The dialer's quota is authoritative for its client, the upstream's
  budget for the key; a client is therefore charged once at each boundary, never twice at one.
  Multi-parent connectivity never duplicates entitlement.
* **Selection among upstreams** is a dialer-local policy. Failover for one request is bounded
  (three dispatches in all, until measured otherwise) and never retries a request that may already
  have produced output; a request that was written to a link and then lost is never sent again.
* **Relay circuit breaker and byte accounting** (invariant 11, spec 08). The dialer counts the
  request and response bytes that cross each of its upstream links, and keeps for each link a
  breaker with the states **closed**, **open** and **half-open**. Consecutive link failures (a
  link lost while a request was pending, a request that timed out with no output, a dial that
  failed) reaching a threshold open the breaker, and an open breaker removes that upstream's
  models from routing at once; after a cool-down one probe request is allowed (half-open), and
  its success closes the breaker while its failure re-opens it. A refusal the acceptor made
  deliberately (a rate, concurrency, budget or model refusal) is not a failure of the link and
  never opens the breaker. A bandwidth bound per link over a window, past which new requests are
  not sent up that link until the window ends, is the second breaker. The thresholds, cool-down
  and bandwidth bound are unmeasured placeholders and owed measurements; implementations default
  them conservatively and make them operator-settable.

## Privacy and trust

* A prompt sent up an upstream link is visible to the acceptor in plaintext. The dialer declares a
  **trust domain per upstream** (spec 45 vocabulary) and never sends a request whose class its
  own policy restricts to a domain the upstream is not in.
* The acceptor's retention of the dialer's prompts and outputs follows its own prompt ledger and
  store rules (specs 22, 34) for the key's principal; the dialer is told in the acknowledgement
  whether the acceptor records prompt content for this principal, and MUST NOT send private
  content to an upstream that does.
* **`records_prompt_content`.** The member is a boolean in the acknowledgement. A dialer reads an
  absent, malformed or non-boolean value as `true`. An acceptor asserts `false` only when an
  operator has positively configured it to and the executing path then retains neither the prompt
  nor the output content of an upstream request at rest: the content stored by the durable
  submission step (spec 22) is not stored for these requests and response capture is off for
  them, while the metadata accounting needs (token counts, timings, outcome, principal, key id)
  is still recorded. This does not contradict spec 22: ordinary gateway records are best-effort and
  may be discarded without refusing inference, and an explicit durable-ingest call is a different
  contract that an upstream request never makes. An acceptor with no such configuration asserts
  `true`. Without a way to
  assert `false` the rule above would make every private request unreachable over an upstream;
  with it, a private request goes up an upstream only when that upstream is in the dialer's own
  trust domain **and** asserts `false`. The assertion is the acceptor's own statement about its
  own storage, `reported` and not `verified`, and an acceptor that stores content elsewhere (a
  traffic capture, a debug log) falsifies it; which stores an implementation suppresses is
  stated in Proof status. The dialer's trust domain, not the assertion alone, is what admits a
  private request.
* The dialer shares its gateway id and the path; it shares no node identity behind it.

## Revocation, abuse bounds

* Revocation stops **new** requests at once. Requests already streaming continue to completion
  only up to a bounded drain window, after which the acceptor aborts them with a terminal error;
  accepted requests with no output yet are aborted at once. The window is an owed measurement.
  **Output** starts at the first response frame of any kind (the response head counts, even when
  its payload is empty, because the request has then been started and answered in part); a head
  with an empty payload is therefore a request with output, which gets the drain window and not
  an immediate abort.
* **Gateway shutdown.** A draining acceptor refuses new upstream requests with the reversible
  `backend_unavailable` and lets the upstream requests already running finish, counted with the
  gateway's other requests in flight, for the gateway's own bounded drain deadline; a request
  still running at the deadline is cut with a terminal error as a request on any other link is.
  Replacing a gateway must not cut every upstream stream at once.
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

Each must fail if its control is removed. `OPEN_GATES.md` records which are proven and which are
owed; a test is never proven here by being listed.

1. Negotiation and binding: no `upstream` role without the typed credential, an acceptor-created
   binding and a same-socket bound acknowledgement; an acknowledgement from another dial, a
   replayed Hello and a key replayed on another channel are refused; a legacy Hello is unchanged;
   a refused role never becomes `serve`.
2. Credential: a registration credential as `api_key` (and the reverse) is refused; a wrong,
   expired, revoked or over-budget key is refused before any request; the key never appears in
   argv, logs, receipts, errors or the ledger; only a hash is stored; a key never enrols or
   approves a node; an upstream credential is never forwarded.
3. Authorization: allow-list, concurrency, rate and token budget hold per key (a key over its
   budget is refused before the request is executed, and an unlisted or absent allow-list permits
   no model); an unlisted model is refused; an alias is never resolved on the link; `meta.native`
   with `meta.http` is refused.
4. Class and privacy: the more restrictive class wins and an undeclared class is `private`; the
   declared class is read from `meta.traffic_class` only and an unrecognised value is `private`;
   an owned-only request is not routed to peer hardware; a dialer never sends a restricted class
   to an out-of-domain upstream, nor a private one to an upstream that records or does not say it
   does not; an acceptor that asserts `records_prompt_content: false` stores no prompt or output
   content of an upstream request; catalog, receipt and headers show only the key's view.
5. Topology: no transit by default; the acceptor appends itself; a path containing the receiver
   and a request past the hop limit are rejected; mutual upstream cannot loop; two upstreams with
   one model id stay independent; a disconnected upstream goes stale.
6. Accounting and idempotency: the executing gateway charges the principal; the dialer's record is
   `reported`; a request repeated after reconnect is not executed twice; no duplicate entitlement.
7. Revocation and failure: revocation stops new requests at once; streaming requests end within
   the drain window; a response head with an empty payload counts as output; a draining gateway
   waits, boundedly, for upstream requests in flight and refuses new ones reversibly; failover
   never retries a request that may have produced output.
8. Invariant 11: a dialer that can use the direct path does; byte accounting and the relay circuit
   breaker apply to upstream links (consecutive link failures open it, an acceptor's deliberate
   refusal does not, and a half-open probe closes it).
9. Interop: the Rust dialer against the HTTPS-only fallback uses the same principal and bounds.

## Proof status

The Rust gateway implements the acceptor (InferWeave/inferweave #1024), the executor, the TLS
channel-binding exporter and the dialer (#1051) and success-response redaction (#1062), all
default off; the tests that exercise them, and what each is shown to catch by removing the
control, are recorded in `OPEN_GATES.md` (section "Link upstream role and authenticated
gateways") with what is proven and what is owed. No schema or conformance fixture for the Hello,
acknowledgement, catalog or `meta.traffic_class` members exists yet. Statements about behaviour
other than that implementation come from specs 21, 40, 45 and 59 and a read of the Rust
repository's `origin/main`, not from a code audit. The evidence note in
`evidence/link-upstream-key-probe-2026-10-15/` is a single **unreproduced observation** (a key
needed to reproduce it is not recorded). All bounds and timings are deliberately unspecified
because none has been measured, and any number an implementation uses is a placeholder.
Nothing here opens a production gate.

## Amendments

Defects found while implementing, and how this text now resolves each (2026-10-15):

| Defect | Resolution |
|---|---|
| Relay accounting excludes forwarded rows; "the executing gateway charges the principal" | Accounting: an upstream-executed row is ordinary, never relay-marked |
| The declared class has no wire member | `meta.traffic_class`; undeclared or unrecognised is `private` |
| "Must not send private to a recording upstream" is unreachable | `records_prompt_content` has assertion semantics; `false` only when configured and enforced |
| Deterministic request ids with a 1 h dedupe would 409 identical prompts | A fresh id for every dispatch |
| The catalog could not drive routing | Entries carry `max_context_tokens` |
| `refused` is gated on `iw.link-refusal/1`, not negotiated here | Granting `upstream` carries `refused`; vocabulary stated |
| The disjoint stream-id rule is vacuous | Replaced by dialer-minted, binding-scoped ids |
| "No output yet" is ambiguous for an empty-payload head | The head is output |
| The traffic-class vocabulary was cited to spec 44, which does not define it | Defined here; cites the Rust gateway vocabulary |
| Both roles on one link | One credential per Hello, so one role per link |
| "Optional" allow-list against "absent denies" | The allow-list is required; absent permits nothing |
| Hop limit "8" against "no default" | The operator sets it, 1 to 8, no default |
| A refused Hello got no acknowledgement | Stated: it gets none |
| Channel binding read as proof of possession | It is replay resistance; TLS protects the key |
| Token budget had no semantics | Windowed, reserved at admission, charged on completion |

## Out of scope

* Registration of nodes (spec 47), alias resolution (spec 54, 61), provisioning (spec 62).
* Pricing, billing and quota between organizations.
* Changing the `serve` role, the Hello of legacy peers, or the exact-model transport of spec 59.
