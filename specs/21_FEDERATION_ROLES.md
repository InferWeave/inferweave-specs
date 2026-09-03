# 21 — Federation, Intermediate Coordinators and Network Roles

InferWeave may form a hierarchy/mesh of gateways/coordinators without requiring every provider to connect to one central bottleneck.

## Roles

A process/site may act as one or more:
- **provider/worker:** executes inference;
- **coordinator/intermediate gateway:** accepts child node registrations, maintains regional presence, routes/relays according to authorized policy;
- **API/subscription gateway:** authenticates clients and issues request/route tickets;
- **relay:** moves streams/artifacts but does not invent scheduling authority;
- **verifier:** runs challenge/qualification checks;
- **donor provider:** contributes compute while redirecting development accounting entitlement;
- **free/trial pool:** policy classification for bounded sponsored/test traffic, not a separate insecure protocol.

## Federation rules

- prevent registration/routing cycles;
- deduplicate the same physical service across multiple discovery paths;
- one request has one authoritative accounting lineage;
- parent failure does not confiscate child identity/history;
- a node may maintain backup operational parents;
- control-plane hierarchy must not force inference bytes through the root;
- global policy/hard constraints remain enforceable across regions;
- local owner priority survives federation.

## Discovery

Clients see a unified model/capability surface rather than manually selecting a gateway. Advanced clients can express region/GPU/privacy preferences without learning private node addresses.

## Scale

Intermediate coordinators aggregate presence/capacity and return compact candidate sets upward. Global scheduling does not scan every provider for every request.

## Development accounting

If reward experiments are enabled, operational-parent and reward/accounting-parent concepts are explicit so retry/multi-parent connectivity cannot duplicate entitlement. This remains dev-only under spec 18.
