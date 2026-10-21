# Role-scoped embedded UIs Implementation Plan

**Goal:** Each Rust role (node, relay, gateway) serves its own limited UI over its own state, sharing
one stylesheet and class vocabulary, so Go gateway pages can be retired one at a time.

**Decision record:** `decisions/2026-10-21-role-scoped-embedded-uis.md` (Proposed; awaiting operator
acceptance). Do not start Task 1 until it is accepted.

**Architecture:** No new stack. Node and gateway: the #410 server-rendered Rust module
`crates/iw-cli/src/ui/`. Relay: the existing Preact + htm relay console. Shared contract: the
stylesheet and class names.

## Global constraints

- Each UI reads only its own process's state or typed API. Rust computes; pages render.
- Unknown, unsupported, stale and zero are distinct on screen.
- Loopback by default; YAML config only; no environment variables.
- No fetch of external resources (no CDN, font URL or script); a test asserts it, as in #410.
- Work in a worktree off `origin/main`; the main checkout carries unrelated uncommitted changes.

## Tasks

### Task 1: Mount the node page in production
`inferweave node join` serves `ui::node_page` on a loopback listener from the node's own state
(engine, slots, KV, GPU memory, join and link status, health). Today only `node-ui-preview`
(`entry/dev_node_ui.rs`) mounts it. Add the listener address to the node's YAML config. Gate: the
existing `ui` tests plus a test that the page renders with the node down and with the engine
unhealthy; no external resource referenced.

### Task 2: Land the relay console
Assess `feat/relay-console` (108 ahead, 449 behind, no PR). Rebase or re-apply onto `origin/main`,
open a PR, and move its colour tokens onto the shared stylesheet. Gate: its own tests plus the
vendored-file hash test.

### Task 3: Gateway read pages
Add server-rendered pages to the Rust gateway for views backed by existing `/iw/v1/*` handlers:
topology, GPU memory, occupancy, autoscaler, admission, federation, routes, profiles and decisions,
operator approvals. Verify per page that the handler returns real data, not an empty view. Gate:
accessibility and narrow-viewport checks per page.

### Task 4: Reconcile the stylesheet
Make `ui/style.rs` the source of truth; map Go `web/src/shared/theme.css` tokens to it; record the
mapping. Gate: a check that the class vocabulary used by node, relay and gateway pages is a subset of
the shared one.

### Task 5: Chart-heavy pages decision
Decide, with the operator, how usage, topology and model-performance pages are served from Rust (see
the record's Open section). Out of scope until then.

### Task 6: Go page retirement
Per page: when a Rust replacement passes the same checks, remove that page from Go. Removing the Go
gateway itself is a separate operator decision.

## Findings (2026-10-21, `InferWeave/inferweave` origin/main da636235)

- Gateway: no `/console` route; the `/iw/v1/*` read endpoints for Task 3 are all dispatched in
  `crates/iw-gateway/src/server.rs`. Dispatch is not completeness.
- Node: no production HTTP listener; `ui::node_page` is mounted only by the dev preview.
- Relay: `dashboard.rs` (inline page) on main; the larger console is on `feat/relay-console`.
- Go `web/`: shared modules are `theme.css`, `theme.ts`, `api.ts`, `nav.ts`, `charts.ts`,
  `network.css`, `webVitals.ts`; `models.ts`, `modalities.ts`, `modelLinks.ts` and `usageFormat.ts`
  are gateway concepts with hard-coded `/console/api/*` paths. 39 Playwright scripts in `web/tools`
  are not run in CI.
