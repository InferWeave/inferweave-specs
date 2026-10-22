# ADR — Status UI: client-side JavaScript, charts, Playwright, optional billing

**Status:** Accepted for implementation (operator, 2026-10-22)  
**Decision owner:** operator  
**Date:** 2026-10-22  
**Relationship:** `re-decides` two points of
[`2026-10-21-role-scoped-embedded-uis.md`](2026-10-21-role-scoped-embedded-uis.md): decision 2 ("No
JavaScript" for the node page) and the **Open** question whether server-rendered pages are enough for
chart-heavy views. Every other point of that record stands: no new frontend stack, the shared stylesheet
is the cross-role contract, Rust computes and pages render, loopback by default, YAML configuration and no
environment variables, Go retired page by page.

## Operator statement

Asked on 2026-10-22 whether the status UI may use client-side JavaScript and charts, the operator
answered: "yes we want charts and javascript is fine. We have no problem with this at all". Asked
whether to raise a gate request for external-node provider billing: "billing is optional and just nice to
see". Asked to set up Playwright for the 30 baselines: "set this up please".

## Decision

1. **Client-side JavaScript is permitted** on the node, gateway and relay role UIs. Charts, live/pause,
   theme toggle and reconnecting streams are in scope.
2. **JavaScript stays inside the existing constraints.**
   - Vendored, never fetched: no CDN, no font URL, no remote script. A test asserts it against the real
     served page, not an empty shell.
   - A CSP that allows `script-src 'self'` (or hashes); no `unsafe-inline`, no `unsafe-eval`.
   - No credential, token or provider secret in `localStorage`, `sessionStorage`, URLs or the DOM.
   - Rust still computes every figure. Script draws what the API returns and never derives a number.
   - Unknown, stale, zero and unsupported stay distinct on screen. A script failure must show an error
     state, not stale numbers presented as live.
   - A vendored file has a hash test, as the relay console already does.
3. **Charts:** drawn client-side from the role's own typed API. Rust-generated SVG remains acceptable where
   a chart needs no interaction. One chart implementation per role, shared tokens.
4. **Playwright** is accepted as a development dependency under `tests/visual/`, pinned exactly. It is not
   built into any binary. A CI browser step is **not** authorized by this record.
5. **Billing is optional.** External-node provider billing is not required for this work and no gate
   request is raised. The `OPEN_GATES.md` position stands unchanged: nothing here treats provider billing
   or external nodes as approved.

## Does not authorize

Calls to any third-party provider API; storing or reading provider credentials; budget enforcement against
money; a Claude, Anthropic or subscription integration; exposure beyond loopback; removal of any Go
behaviour; a CI browser step; any change to alias authority. Cost values, if shown at all, carry their
provenance and an unknown cost is never shown as zero.

## Owed

Independent review of the implementation (the independent-review gate in `OPEN_GATES.md` is BLOCKED; no
reviewer is enrolled). The `OPEN_GATES.md` row for role-scoped UIs that the 2026-10-21 record already owes.
