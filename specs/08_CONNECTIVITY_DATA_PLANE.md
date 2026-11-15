# 08 — Direct-First Connectivity, NAT Traversal, Relays and Local Proxy

## Principle

Inference data should travel through the fewest intermediaries possible.

The control plane coordinates routing and authorization; it is not the normal bulk data path.

## Control channel

Every node keeps outbound authenticated control connections to one or more coordinators/gateways.

Control messages:
- registration/heartbeat;
- deployment inventory/fingerprint;
- capacity;
- route/lease offers;
- short-lived direct connection tickets;
- cancellation/drain/preemption;
- telemetry/accounting acknowledgements;
- prompt-ledger ingestion status.

### Control liveness and data-path recovery

A heartbeat proves that the authenticated control path is live. It does not prove
that the node's registered data endpoint resolves or accepts traffic. When endpoint
resolution fails before dispatch, the gateway withdraws that route immediately and
MUST NOT restore it merely because another heartbeat arrives. A direct HTTP route
without a held Link remains withdrawn until a fresh authenticated registration
publishes the corrected endpoint.

An accepted authenticated held Link is independent data-path evidence and MAY clear
only an endpoint-unresolvable withdrawal for that node. A failed Link handshake or
bad credential clears nothing. Link acceptance never clears a leaving, released,
distrusted, revoked, or otherwise stronger withdrawal. These rules prevent a healthy
control loop from repeatedly returning a known-broken data route to selection.

## Data path preference

For every route:

```text
1. direct client/local-proxy <-> node
2. nearest regional relay
3. gateway relay only as last resort
```

A gateway may never choose itself as the byte path merely because it made the scheduling decision.

## NAT traversal

Implement a rendezvous layer supporting the best practical direct mechanism for the environment:
- ICE-like candidate exchange;
- authenticated QUIC/HTTP3 when reachable;
- reverse tunnels;
- WebRTC data channels where browser compatibility requires them.

All paths use route-scoped short-lived credentials/tickets.

## Local proxy

Strongly recommended for Pi/AutoSpec/desktop clients.

Responsibilities:
- persistent control connection;
- direct-node connection establishment;
- session affinity metadata;
- model/capacity cache;
- optional explicit durable-ingest outbox for workloads that require committed submission;
- request idempotency;
- cancellation propagation;
- optional safe prefix/request caching;
- failover to regional relay.

## Gateway protection

Track:
- direct-path success ratio;
- relay bytes;
- gateway-relay bytes;
- connection setup time;
- failed NAT traversal reason.

Define SLOs that drive the gateway-byte ratio toward zero for normal established clients.

Gateway relay has explicit concurrency/bandwidth circuit breakers.

Stream-local failure is not shared-transport failure. Credit-window overrun,
token-sequence violation, and one request's idle deadline terminate only that
request. Socket loss terminates the Link and its streams. Operator diagnostics keep
those causes distinct; public errors remain bounded and expose no raw upstream
message. An accepted request is never automatically replayed after an ambiguous or
partial response.

## Prompt persistence

Direct routing does not remove prompt recording. The gateway owns pre-route
identity derivation and the bounded asynchronous recorder, so rejected and
accepted requests follow one admission-independent recording contract. A local
proxy or selected node may publish post-route attempt, response, and accounting
events through the same typed event contract using a scoped write capability;
they do not create a second admission gate. Recording failure or saturation is
visible but does not invalidate an otherwise admissible route. A workload that
explicitly requires durable submission uses the fail-closed prompt-ingest API,
optionally through the local proxy's crash-safe outbox, before routing.

## Optional gateway topology observation on a held link

Gateway-role peers can carry spec 40's bounded canonical v2 graph in the
existing `heartbeat.status.topology` member. It is optional observation data,
not a routing instruction or new authority. Publication is asynchronous and
held-link-only; ordinary HTTP heartbeat size and liveness behavior remain
unchanged. See spec 40 for local authority isolation, byte/time limits, cache
expiry and tolerant handling of malformed optional metadata.
