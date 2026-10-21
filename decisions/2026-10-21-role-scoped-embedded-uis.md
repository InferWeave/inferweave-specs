# ADR — Role-scoped embedded operator UIs (gateway, node, relay)

**Status:** Accepted for implementation (operator, 2026-10-21)  
**Decision owner:** operator  
**Date:** 2026-10-21  
**Authorizes:** building the plan in
`docs/superpowers/plans/2026-10-21-role-scoped-embedded-uis.md`. Never deployment, exposure beyond
loopback, or removal of the Go gateway.  
**Relationship:** `re-decides` the single-surface wording of D-002 (narrow existing-system exception,
amended 2026-10-12) and the "extend the existing gateway UI" scope of spec 58 and
`07-UI-OBSERVABILITY.md`; and `re-decides` the end state of #1013 (`InferWeave/inferweave`,
2026-10-17: "Go becomes the frontend") from *permanent frontend* to *frontend until Rust parity, then
retired*. Every other invariant of those records stands: no Go templates for new products, new
dashboards/portals/explorers/Workbench stay Next.js + TypeScript, Rust owns every calculation, the
public dashboard never administers provider nodes, alias authority is Rust only.

## Context

Each Rust role owns a different slice of state. A node knows its engine, slots, KV and GPU. A gateway
knows fleet routing, admission, usage, keys and approvals. A relay knows its upstream gateways and
routes. The operator's intent (2026-10-21): each role serves its own limited UI, all sharing one look
and components where practical, and the Go gateway is eventually retired and superseded by the Rust
gateway.

What already exists in `InferWeave/inferweave` (found 2026-10-21, after a first draft of this record
missed it):

- **#410 (2026-09-19), `crates/iw-cli/src/ui/`:** one Rust module renders server-side HTML with no
  JavaScript for node, gateway, edge and orchestrator pages. Only data differs per role. The
  stylesheet is the cross-language contract; components are deliberately not shared across languages.
  Only the dev preview `node-ui-preview` mounts it. No production binary serves it.
- **Relay console:** design on main (`docs/superpowers/specs/2026-10-07-relay-console-design.md`),
  vendored Preact + htm, no build step, embedded in `iw-relay-http`. Built on `feat/relay-console`
  (108 commits ahead of main, 449 behind, no PR). `dashboard.rs` on main is the older inline page.
- **#1013 (2026-10-17):** Rust gateway becomes the only gateway; Go keeps sign-in, sessions, the
  console backend-for-frontend and the embedded web bundle.
- **Go gateway `web/`:** esbuild TypeScript, about 40 pages, the richest UI today. It is the only
  place charts, topology, usage and key pages exist.

## Decision

1. **No new frontend stack.** Roles use what already exists, joined by one shared stylesheet.
2. **Node:** the #410 server-rendered Rust pages, mounted in `inferweave node join` on a loopback
   listener, reading only that node's own state. No JavaScript.
3. **Relay:** land the existing relay console (Preact + htm, no build step) from `feat/relay-console`,
   rebased onto main, rather than rewriting it. Its tokens move to the shared stylesheet.
4. **Gateway:** the Rust gateway serves server-rendered read pages (#410 style) over its own `/iw/v1/*`
   endpoints for the views that exist as Rust data (topology, GPU memory, occupancy, autoscaler,
   admission, federation, routes, profiles, operator approvals). The Go gateway keeps the rich
   console, sign-in and sessions until a Rust page exists for each Go page it would replace.
5. **One contract across roles:** the stylesheet (`crates/iw-cli/src/ui/style.rs` is the source) and
   the class names. The Go `web/` `theme.css` tokens are reconciled to it. Components are not shared
   across languages.
6. **Retirement:** the Go gateway is retired by migrating pages, not by a flag day. #1013's "Go is the
   frontend" holds until each page has a Rust replacement that passes the same accessibility checks;
   then that page's Go code is removed. Removing Go is a separate operator decision.
7. Every served UI binds to loopback by default. Serving beyond loopback needs explicit YAML
   configuration and authentication. No environment variables.

## Open

- Whether server-rendered pages are enough for the gateway's chart-heavy pages (usage, topology,
  model performance). Decision 4 covers only the views that are tables, status and approvals. If
  charts need client-side code, a follow-up record must say what and where.
- Whether `feat/relay-console` can be rebased: 449 commits behind main.

## Rejected

- **A new TypeScript workspace with a bundle per role** (the first draft): a third design beside #410
  and the relay console, without evidence #410's approach cannot serve the Rust roles.
- **One bundle served by every role:** ships fleet code in a node.
- **A Next.js admin app per role:** a second frontend, rejected by D-002 and spec 58.
- **Rewriting the relay console as server-rendered pages:** discards 108 commits for no gain.

## Does not authorize

Production rollout, exposure on a non-loopback address, new fleet-wide node endpoints, removal of Go
behaviour before Rust parity per page, or any change to alias authority.

## Owed

Operator acceptance; independent review of the implementation; the matching gate row in
`OPEN_GATES.md` before production acceptance.
