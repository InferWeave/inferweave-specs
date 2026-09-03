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
- prompt-ledger durable outbox;
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

## Prompt persistence

Direct routing does not remove the requirement to store every prompt. The local proxy or selected node performs idempotent prompt-ledger ingestion using a scoped write capability.
