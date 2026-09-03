# 17 — Scaling, Regional Gateways and High Availability

Do not optimize the prototype for a million providers at the cost of never deploying ten, but preserve scale-compatible contracts.

## Stages

### Prototype
Single gateway/control database, direct node outbound connections, bounded relay.

### Multi-gateway
Stateless API gateways behind L4/L7 ingress; shared durable registry/session/policy data; lease-based ownership of mutable coordination tasks.

### Regional
Regional gateway/controllers maintain hot node presence and route candidates; global layer handles identity/policy/catalog and cross-region fallback. Return-to-sender prevents global queue hoarding.

### Large network
Sharded presence/snapshot ingestion, compact deltas, preaggregated GPU/model/capacity buckets, regional relay pools and object-store audit history.

## Presence

Node/service advertisements are TTL based. Exact thresholds are configuration, but stale state must become unknown/ineligible quickly and public snapshots expose age.

## Browser/public API

Never push all provider rows to browsers. Use aggregates, facets, cursor pagination and immutable signed snapshots.

## Consistency

Inference routing favors freshness/availability over global serializable coordination. Money/economic settlement, if ever enabled, is a separate stronger-consistency domain.

## Failure domains

One region/gateway/node/relay failure must not corrupt global session/accounting state. Cross-region reroute obeys session and hard privacy/placement constraints.
