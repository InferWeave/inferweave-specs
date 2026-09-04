# 41 — Inter-Gateway Capacity Requests and Standby Slot Scheduling

A gateway that is out of capacity may ask a peer gateway for some, and hold the
result as pre-warmed standby slots rather than discovering at request time that
nothing is ready. This specification defines that conversation.

`specs/40_NETWORK_TOPOLOGY_GRAPH.md` says which peers exist. This says what one
may ask another for, what an answer obliges, and — the hard part — how asking
avoids becoming the unbounded queue that `specs/06_BACKPRESSURE_RETURN_TO_SENDER.md`
forbids.

## Binding rule

**A capacity request asks for a grant of admission. It never transfers work, and
the asking gateway never holds work while it waits.**

Spec 06's rule is that no layer may convert downstream rejection into an
unbounded local queue. "Ask a peer, and park the request until they answer" is
that queue under a different name: the work sits somewhere, the client is told
nothing, and the depth is bounded only by how many peers exist. Every rule below
exists to keep capacity negotiation on the control plane, separate from the
lifetime of any particular request.

A gateway with no capacity and no grant returns to sender per spec 06. It does
not wait.

## Two clocks, deliberately separated

| | Request path | Capacity path |
|---|---|---|
| Triggered by | one client request | observed pressure over time |
| Bounded by | spec 06 admission budget | grant TTL |
| On exhaustion | 503/429 to sender | keep serving locally, retry later |
| May block a client | yes, within budget | **never** |

Capacity negotiation runs on the second clock. A grant that arrives after the
request that motivated it has already been returned to sender is still useful —
it pre-warms for the next one. That is the point of standby.

Coupling the two — blocking a client on a peer negotiation — is the single
failure this specification is written to prevent.

## Standby slots

A **standby slot** is admission capacity held ready on a granting site for a
requesting gateway: weights resident, KV reserved against the granting site's
measured envelope (`specs/04_CAPACITY_ADMISSION_SEATS.md`), nothing executing.

Standby is not free. A held slot is capacity the granting site cannot give its
own users. Three consequences:

- **Only measured envelope may be offered.** A site may offer standby only out
  of capacity it has measured, never nominal or advertised figures. Spec 04
  defines the envelope as measured resources; offering more is a promise the
  hardware never made, and the failure surfaces on the requester's users.
- **Local owner priority survives.** Per `specs/21_FEDERATION_ROLES.md`, a
  granting site may revoke standby when its own owners need the capacity.
  A grant is a loan, not a sale.
- **Cost is attributed, not absorbed.** The holding cost is recorded against the
  requesting gateway. Silently absorbing it makes standby look free and
  guarantees over-request.

## Grants

A grant states, and means:

- `slots` — how many, of which capacity envelope;
- `ttl` — when it expires if unclaimed;
- `revocable_with_notice` — how much warning before reclaim;
- `lineage` — the single authoritative accounting lineage (spec 21), so a
  request served under a grant is billed once, at the site that ran it.

Grants expire on **time since last progress**, not total elapsed time — the same
liveness rule as reservations in spec 04, and for the same reason: a long
legitimate hold must not be reclaimed for being long, while a requester that
died must not hold capacity forever.

A revoked or expired grant returns the slots to the granting site's own
envelope. A requester that keeps routing to a revoked grant is non-conformant;
the granting site rejects with `409 no_eligible_capacity` per spec 06.

## Refusing without lying

A peer that cannot help answers immediately and truthfully. Silence is not an
answer: the requester cannot distinguish a thinking peer from a dead one, and
waiting to find out is the coupling this specification forbids.

A refusal carries a reason code and, when meaningful, a bounded retry-after —
the same vocabulary spec 06 defines for return-to-sender, so operators read one
set of codes across both paths.

**A peer must not answer with capacity it has already promised elsewhere.**
Outstanding grants are subtracted from the offerable envelope before any reply.
Double-granting is the characteristic failure of this design and the conformance
suite tests for it directly.

## Loop and amplification control

Federation is a mesh; capacity requests must not circulate.

- Every request carries a **path vector** of gateway stable IDs. A gateway that
  finds itself in the path refuses immediately. This is the same cycle
  prohibition spec 21 places on registration and routing.
- Every request carries a **hop budget**, decremented at each forward. At zero,
  a gateway may answer from its own envelope but may not forward.
- A gateway may not fan a single request to more peers than a configured
  breadth. Without this, one shortage at a leaf becomes a broadcast storm across
  the federation — the amplification is multiplicative in a mesh, not additive.

Termination on adversarial input is required, not assumed: a malformed or
malicious path vector must cause refusal, never an unbounded walk.

## Relationship to forecasting

`specs/32_DEMAND_FORECASTING_PRESTAGING.md` decides what to pre-stage locally.
Standby grants are an **input** to that decision and never a substitute for it: a
site that meets forecast demand by borrowing rather than staging has moved its
shortage onto a peer and hidden it from its own planning.

Grants held and grants revoked are both forecast signals. A site whose standby
is repeatedly revoked is under-provisioned, and the record of revocations is how
that becomes visible rather than being felt as intermittent latency.

## Observability

Every grant, refusal, revocation and expiry is a receipt under
`specs/09_OBSERVABILITY_RECEIPTS.md`, carrying the path vector, the hop budget
remaining, the envelope offered, and the lineage. An operator asking "why did my
request go to another site?" gets an answer from records, not inference.

## Conformance

Per `specs/38_EXECUTABLE_EVIDENCE_AND_CONFORMANCE.md`, each test must fail when
the control it covers is removed:

1. A gateway awaiting a peer's answer does not hold the triggering client
   request beyond the spec 06 admission budget.
2. A peer with outstanding grants does not offer the same capacity twice.
3. A request whose path vector already contains the receiving gateway is refused.
4. A request at hop budget zero is answered or refused, never forwarded.
5. Fan-out to peers never exceeds the configured breadth.
6. An expired grant returns slots to the granting site's own envelope, and
   routing to it afterwards is rejected.
7. Grant expiry is evaluated on time since last progress, so a long active hold
   is not reclaimed.
8. A site may not offer standby exceeding its measured envelope.
9. Revocation honours the stated notice, and the revoked slots appear in the
   granting site's envelope afterwards.

Each is run against a deliberately broken fixture as well as the canonical one,
so a guard that has silently stopped checking is caught.
