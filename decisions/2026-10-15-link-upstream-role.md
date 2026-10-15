# Link upstream role and authenticated upstream gateways

**Status:** Proposed
**Decision owner:** operator
**Date:** 2026-10-15
**Authorizes:** nothing (design proposal only; not deployment, enrollment, spending or traffic)
**Relationship:** re-decides nothing; adds a role beside `serve` (spec 45, spec 59). Touches the
D-002 amendment of 2026-10-12 only through the open question below.

## Context

A developer-fabric gateway needs the lab gateway's models without being routable from the lab.
Registration only routes down. The public HTTPS API accepts a key but carries none of the link's
negotiation, binding, liveness or loop prevention.

## Proposal

Spec 63: role `upstream` (capability `iw.link-upstream/1`), typed `api_key` credential naming a
principal, a separate acceptor-created binding, N upstreams, no transit by default, acceptor-appended
federation path with a hop limit, one charge per boundary.

## Open decisions (none made here)

1. **Go acceptor side.** Whether the Go site gateway (`fry`) implements the acceptor. Spec 54 and the
   D-002 amendment limit Go to consuming, rendering and relaying; accepting an upstream role would
   make it execute and account requests. Until decided, the first acceptor is the Rust gateway.
2. **Feature ID.** Whether this deserves a new feature ID instead of extending `IW-DP-002`.
3. **Invariant 11.** The role is admitted only where direct transport is unavailable or forbidden.

## Not authorized

Any deployment, any key issuance, any production gateway change.
