# ADR — Role-scoped embedded operator UIs (gateway, node, relay)

**Status:** Accepted for implementation (operator instruction, 2026-10-21)  
**Decision owner:** operator  
**Date:** 2026-10-21  
**Authorizes:** building the design in the plan
`docs/superpowers/plans/2026-10-21-role-scoped-embedded-uis.md`. It does not authorize deployment,
exposure beyond loopback, or removal of the Go gateway.  
**Relationship:** `re-decides` the single-surface wording of D-002 (narrow existing-system exception,
amended 2026-10-12) and `re-decides` the "extend the existing gateway UI" scope of spec 58 and
`07-UI-OBSERVABILITY.md`. Every other invariant of those records stands, including: no second
frontend, no Go templates for new products, new dashboards/portals/explorers/Workbench stay
Next.js + TypeScript, Rust owns every calculation, and the public dashboard never administers
provider nodes.

## Context

D-002 permits one embedded operator UI: the one in the Go site gateway
(`metabolomics-us/inferweave-gateway`). The Go gateway is being retired and superseded by the Rust
gateway (`InferWeave/inferweave`). No Rust gateway, node or relay serves a UI today: the local
gateways on bender return a JSON 404 for `/`, `/console` and `/console/api/me`.

Each Rust role owns a different slice of state. A node knows its engine, slots, KV and GPU. A gateway
knows fleet routing, admission, usage, keys and approvals. A relay knows its upstream gateways and
routes. The Go UI's `/console/api/*` views were composed from a registry that competes with Rust as a
source of truth (see the 2026-10-16 gateway-UI audit); a UI that can only call its own process's typed
API cannot repeat that.

## Decision

1. Each Rust role (**gateway**, **node**, **relay**) may embed its own operator UI, limited to the
   state that role owns. This is the same exception D-002 grants the Go site gateway, extended to
   those roles. It is not authority for any other browser application.
2. There is **one frontend codebase and one design system**. A shared package holds tokens
   (`theme.css`), navigation, the API client (poll, cache, stale handling), the SSE client, panels,
   redaction and accessibility helpers. Each role has its own entry point and builds its own bundle;
   a binary embeds only its own bundle. The existing Go `web/` bundle is the starting point for the
   shared package and the gateway entry point.
3. A role UI calls **only its own process's typed API** and event stream. A node bundle does not
   call fleet endpoints; a relay bundle does not call node endpoints. Wire types are generated from
   the Rust schemas (`schema-gen`), not hand-copied.
4. Rust owns every measure. TypeScript renders and formats; it does not recompute capacity,
   eligibility, ranking or fit.
5. Node and relay UIs bind to loopback by default. Serving beyond loopback requires explicit
   configuration and authentication. Configuration is YAML only; no environment variables.
6. The Go gateway UI is frozen to fixes. It is retired with the Go gateway, after the Rust gateway
   bundle reaches parity for the pages in the plan, and not before.

## Rejected

- **One bundle served by every role:** ships fleet code in a node and invites the node UI to reach
  for fleet state it does not own.
- **A separate Next.js admin app per role:** a second frontend, rejected by D-002 and spec 58.
- **Fork the Go UI per role:** divergent copies of tokens, nav and client within a release.
- **Move the UI into the public dashboard:** the public dashboard is read-only and public-safe.

## Does not authorize

Production rollout, exposure on a non-loopback address, new fleet-wide node endpoints, removal of
Go behaviour before Rust parity is proven, or any change to alias authority (Rust only).

## Owed

Independent review of the implementation; the matching gate row in `OPEN_GATES.md` before any
production acceptance.
