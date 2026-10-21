# Role-scoped embedded UIs Implementation Plan

**Goal:** Give the Rust gateway, node and relay each an embedded operator UI limited to the state it
owns, built from one shared design system and component package, so the Go gateway UI can be retired
with the Go gateway.

**Architecture:** One TypeScript workspace. A `shared` package (tokens, nav, API client, SSE, panels,
redaction, a11y helpers) and three entry points (`gateway`, `node`, `relay`). Each entry point builds
a bundle that its Rust binary embeds and serves from `/console`. Wire types are generated from Rust
schemas by `schema-gen`. Nothing here adds a second frontend or a new storage service.

**Decision record:** `decisions/2026-10-21-role-scoped-embedded-uis.md` (accepted for implementation).

## Global constraints

- Each UI calls only its own process's typed API and event stream.
- Rust computes; TypeScript renders. Unknown, unsupported, stale and zero are distinct states.
- Loopback by default. Config is YAML only; no environment variables.
- Existing Go UI is frozen to fixes; port behaviour, do not redesign it.
- Every route is covered by the machine-checked presentation policy (spec 10): default and narrow
  viewport, forced-colors, reduced-motion, wired or fixture, unsupported. A route missing from the
  policy fails the check.

## Tasks

### Task 1: Audit and decide the extraction boundary
Read-only. List what in Go `web/src/shared` (api.ts, nav.ts, stream.ts, theme.css, theme.ts) is
role-neutral. Confirm the gateway repo's source/dist parity check and Playwright tools. Output: the
list of modules that move to `shared`, and the endpoints each role's API already exposes.

### Task 2: Shared package and build
Create the workspace, move the role-neutral modules, generate wire types with `schema-gen`, and add a
bundle-parity CI step per entry point. Gate: `tsc`, build, and bundle parity pass for an empty
`node` entry point.

### Task 3: Node UI (first, smallest)
Pages: engine and model state, slots and KV, GPU memory, join and link status, health and recent
log lines, drain. Serves from the node's own API only. Needs a node-local read API if one does not
exist; add it to the node, additively. Gate: a11y, responsive and screenshot checks per route.

### Task 4: Relay UI
`crates/iw-relay-http/src/dashboard.rs` already serves a self-contained dashboard at `/` and
`/dashboard` (118 lines, inline CSS with its own dark palette) over `/api/overview`, `/api/gateways`,
`/api/requests`, `/api/tunnel`. Port it onto the shared tokens and components rather than writing a
new one; keep its API. Gate as Task 3.

### Task 5: Gateway UI on Rust
Serve the ported `web/` bundle from the Rust gateway at `/console`, backed by `/iw/v1/*` and
`/inferweave/v1/*` read adapters (topology, gpu-memory, aliases, alias-capabilities, events). Port
pages in this order: overview, models, usage, keys, nodes, routing, topology, GPU memory. Gate: a
page is done when its data comes from Rust and its Go counterpart is no longer the only source.

### Task 6: Missing spec-07 views
New, on Rust typed APIs only: CPU/RAM/unified memory with allocatable/reserved/free, NUMA,
deployment stages, federation approvals and leases, Slurm wait reasons, placement and fallback
decision history, benchmark evidence. Each view shows `unsupported` until its Rust API exists.

### Task 7: CI gates
Run the Playwright accessibility, responsive and screenshot-diff checks per bundle in CI (they are
un-gated in the Go repo today), with committed baselines.

### Task 8: Go UI retirement
When Tasks 5 and 6 reach parity for the listed pages, mark the Go UI read-only, then remove it with
the Go gateway. Out of scope until the operator approves the Go gateway's retirement.

## Findings (2026-10-21, read-only check of `InferWeave/inferweave` at 83ff68aa)

- **Gateway:** no `/console` or `/console/api/*` route and no embedded-asset serving anywhere in
  `crates/`. The `/iw/v1/*` read endpoints are all dispatched in `crates/iw-gateway/src/server.rs`:
  `topology`, `gpu-memory`, `occupancy`, `autoscaler`, `admission`, `federation`, `routes`,
  `routes/events`, `profiles`, `profiles/decisions`, `community`, `dynamic`, `model-intelligence/*`,
  and `provision/operator/{status,approvals,approve,reject,policy,hosting/*}`. Dispatch is not
  completeness: handler behaviour is still unverified.
- **Node:** `iw-node` and `inferweave node join` expose no HTTP listener. They only scrape the
  engine's `/metrics` and `/health`. Task 3 must add a node-local read API first.
- **Relay:** already has an embedded dashboard (see Task 4).

## Open questions

- Which gateway handlers return real data rather than empty views? Verify per page in Task 5/6.
- Shape and auth of the node-local read API (Task 3).
